import json
from typing import Annotated
from urllib.request import Request, urlopen

import litellm
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

litellm.enable_json_schema_validation = True


def load_config(mcp_json_path: str) -> dict:
    """Load MCP configuration from a JSON file.

    Parameters
    ----------
    mcp_json_path : str
        Path to the MCP configuration JSON file.

    Returns
    -------
    dict
        MCP configuration data.
    """
    with open(mcp_json_path) as f:
        config = json.load(f)
    return config


def to_message(content: str, role: str = "user", content_type: str = "input_text"):
    """Create a message dictionary for LLM API calls.

    Parameters
    ----------
    content : str
        The message content text.
    role : str
        The role of the message sender (default: "user").
    content_type : str
        The type of content (default: "input_text").

    Returns
    -------
    dict
        Message payload for LLM API calls.
    """
    return {
        "role": role,
        "content": [
            {"type": content_type, "text": content},
        ],
    }


def get_structured_response_litellm(
    input: str,
    system_prompt: str,
    output_model: type[BaseModel],
    model: str = "openai/gpt-5-nano",
    temperature: float = 1.0,
) -> BaseModel:
    """Get a structured response from LiteLLM using JSON schema validation.

    Parameters
    ----------
    input : str
        The user input text.
    system_prompt : str
        The system prompt to guide the model.
    output_model : type
        Pydantic model class defining the expected output schema.
    model : str
        The model name to use (default: "openai/gpt-5-nano").
    temperature : float
        Sampling temperature (default: 1.0).

    Returns
    -------
    object
        LiteLLM response object containing the structured output.

    Raises
    ------
        RuntimeError: If the LLM call fails
    """
    schema = output_model.model_json_schema()
    # OpenAI requires additionalProperties to be explicitly set to false
    schema["additionalProperties"] = False
    # OpenAI's response format requires all properties to be in the required array
    if "properties" in schema:
        schema["required"] = list(schema["properties"].keys())
    try:
        response = litellm.responses(
            input=[
                to_message(system_prompt, role="system"),
                to_message(input, role="user"),
            ],
            model=model,
            temperature=temperature,
            text_format={
                "type": "json_schema",
                "json_schema": {
                    "name": output_model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to get structured response from litellm: {e}") from e


def structured_response_to_output_model(response: litellm.Response, output_model: type[BaseModel]) -> BaseModel:
    """Convert a LiteLLM Response to a Pydantic model instance.

    Parameters
    ----------
    response : object
        LiteLLM response object containing the structured output.
    output_model : type
        Pydantic model class to instantiate.

    Returns
    -------
    object
        Instance of the output_model populated with data from the response.

    Raises
    ------
        ValueError: If the response is invalid or cannot be parsed into the model
    """
    if not response.output or len(response.output) == 0:
        raise ValueError("No output found in response")

    output_message = response.output[-1]
    if not output_message.content or len(output_message.content) == 0:
        raise ValueError("No content found in response output message")

    json_text = output_message.content[0].text

    # Check if the text looks like JSON before parsing
    json_text = json_text.strip()
    if not json_text.startswith(("{", "[")):
        raise ValueError(
            f"Response text does not appear to be valid JSON. "
            f"Expected JSON object or array, but got: {json_text[:100]}..."
        )

    try:
        parsed_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from response. Error: {e}. Response text (first 200 chars): {json_text[:200]}"
        ) from e

    try:
        return output_model(**parsed_data)
    except Exception as e:
        raise ValueError(
            f"Failed to create {output_model.__name__} from parsed data. Error: {e}. Parsed data: {parsed_data}"
        ) from e


class SchemaReasoningOutput(BaseModel):
    """Output model for schema reasoning."""

    biocontextai_schema_reasoning: Annotated[
        str, Field(description="Any reasoning that might help to arrive at an answer that matches the given schema.")
    ]


def load_json_from_url(url_or_path: str, timeout: float = 10.0):
    """Download and parse a JSON file from URL or load from file path.

    Parameters
    ----------
    url_or_path : str
        URL to download JSON from or local file path.
    timeout : float
        Timeout in seconds for URL requests (default: 10.0).

    Returns
    -------
    dict
        Parsed JSON data.
    """
    # Check if it's a URL (starts with http:// or https://) or a file path
    if url_or_path.startswith(("http://", "https://")):
        # Create a request with User-Agent header to avoid 403 Forbidden errors
        req = Request(url_or_path)
        req.add_header("User-Agent", "meta-mcp/1.0 (Python urllib)")
        with urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        return data
    else:
        # It's a file path
        with open(url_or_path) as f:
            data = json.load(f)
        return data


def fix_schema(schema: dict) -> dict:
    """Recursively fix arrays with prefixItems but no items by converting prefixItems to items."""
    if isinstance(schema, dict):
        schema = schema.copy()
        # If array has prefixItems but no items, convert prefixItems to items
        if schema.get("type") == "array" and "prefixItems" in schema and "items" not in schema:
            # Use the last prefixItem as the items schema (or create a union if multiple)
            prefix_items = schema.get("prefixItems", [])
            if prefix_items:
                # For tuple-like arrays, we'll use the last item type as items
                # This is a simplified approach - full support would require tuple types
                schema["items"] = prefix_items[-1] if len(prefix_items) == 1 else {"anyOf": prefix_items}
            else:
                # Fallback to any if no prefixItems
                schema["items"] = {}

        # Recursively fix nested schemas
        for key, value in schema.items():
            if isinstance(value, dict):
                schema[key] = fix_schema(value)
            elif isinstance(value, list):
                schema[key] = [fix_schema(item) if isinstance(item, dict) else item for item in value]

    return schema


def registry_json_to_df(registry_json: list[dict]) -> pd.DataFrame:
    """Convert registry JSON (list of dicts) to a pandas DataFrame.

    Collects all possible columns from all elements, handling missing keys.
    Nested JSON structures are converted to JSON strings.

    Parameters
    ----------
    registry_json : list[dict]
        List of dictionaries representing registry entries.

    Returns
    -------
    pd.DataFrame
        DataFrame with all columns from all registry entries.
    """
    if not registry_json:
        return pd.DataFrame()

    # First pass: collect all possible keys from all entries
    all_keys = set()
    for entry in registry_json:
        all_keys.update(entry.keys())

    # Second pass: build rows, converting nested structures to JSON strings
    rows = []
    for entry in registry_json:
        row = {}
        for key in all_keys:
            value = entry.get(key)
            # Convert nested structures (dict, list) to JSON strings
            if isinstance(value, dict | list):
                row[key] = json.dumps(value)
            else:
                row[key] = value
        rows.append(row)

    return pd.DataFrame(rows)
