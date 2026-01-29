import json
import os
from typing import Annotated, Literal

import httpx
import numpy as np
from pydantic import BaseModel, Field, create_model
from rapidfuzz import process
from sentence_transformers import SentenceTransformer

from meta_mcp.mcp import mcp
from meta_mcp.utils import get_structured_response_litellm, structured_response_to_output_model


async def get_tool_info(
    server_name: Annotated[str, "The name of the server that provides the tool"],
    tool_name: Annotated[str, "The name of the tool to get information about"],
) -> str:
    """Returns the input schema for a given tool, to know how to call it."""
    if server_name not in mcp._tools or tool_name not in mcp._tools[server_name]:
        raise RuntimeError(f"Tool '{server_name}:{tool_name}' not found")
    tool_info = mcp._tools[server_name][tool_name]
    # Get the input_schema from the tool info
    input_schema = tool_info.get("input_schema", {})
    return json.dumps(input_schema)


async def list_servers(
    query: Annotated[str | None, "Optional query to filter the servers by"] = None,
) -> str:
    """Lists all (or just the filtered) MCP servers and their descriptions, offering a wide range of tools for biomedical (analysis) tasks to choose from."""
    registry_df = mcp._registry_info
    if registry_df.empty:
        return json.dumps({}, indent=4)

    # Extract identifier and description columns
    result = []
    server_ids = registry_df["identifier"].tolist()
    descriptions = registry_df["description"].tolist()
    result = dict(zip(server_ids, [des if des is not None else "" for des in descriptions], strict=True))

    top_n = int(os.environ.get("MCP_MAX_SERVERS", "10"))
    if query is not None and len(server_ids) > top_n:
        search_mode = os.environ.get("MCP_SEARCH_MODE", "llm")
        server_ids_filtered = general_search(
            query,
            server_ids,
            descriptions=descriptions,
            top_n=top_n,
            mode=search_mode,
            reasoning=os.environ.get("META_MCP_REASONING", "false") == "true",
        )
        result = {server_id: result[server_id] for server_id in server_ids_filtered}

    return json.dumps(result, indent=4)


async def list_server_tools(
    server_name: Annotated[str, "The name of the MCP server to list tools for"],
    query: Annotated[str | None, "Optional query to filter the tools by"] = None,
) -> str:
    """Returns a list of all (or just the filtered) tools for a given MCP server."""
    if server_name not in mcp._tools:
        raise RuntimeError(f"Server '{server_name}' not found")

    tools = mcp._tools[server_name]
    tool_names = list(tools.keys())
    descriptions = [tools[t].get("description", None) for t in tool_names]
    result = dict(zip(tool_names, [des if des is not None else "" for des in descriptions], strict=True))

    top_n = int(os.environ.get("MCP_MAX_TOOLS", "10"))
    if query is not None and len(tool_names) > top_n:
        search_mode = os.environ.get("MCP_SEARCH_MODE", "llm")
        tool_names_filtered = general_search(
            query,
            tool_names,
            descriptions=descriptions,
            top_n=top_n,
            mode=search_mode,
        )
        result = {tool_name: result[tool_name] for tool_name in tool_names_filtered}

    return json.dumps(result, indent=4)


def general_search(
    query: str,
    candidates: list[str],
    top_n: int = 5,
    mode: Literal["string_match", "llm", "semantic"] = "string_match",
    string_match_method: Literal["fuzzy", "substring"] = "fuzzy",
    descriptions: list[str | None] | None = None,
    reasoning: bool = True,
    **kwargs,
) -> list[str]:
    """
    Returns top-n most fitting strings from candidates list.

    Parameters
    ----------
    query : str
        The search query string.
    candidates : list[str]
        List of candidate strings to search through.
    top_n : int
        Number of top results to return (default: 5).
    mode : str
        Search mode: "string_match", "llm", or "semantic" (default: "string_match").
    string_match_method : str
        String matching method: "fuzzy" or "substring" (default: "fuzzy").
    descriptions : list[str | None] | None
        Optional list of descriptions for candidates. Must match length of candidates.
        Used in both "llm" and "semantic" search modes. In "llm" mode, descriptions
        are formatted as CSV in the system prompt. In "semantic" mode, descriptions are
        combined with candidates as "candidate (description)" for embedding computation.
    **kwargs : dict
        Mode-specific keyword arguments. "llm" mode keys: model (str), temperature (float),
        reasoning (bool). "semantic" mode keys: backend (str), model (str), http_url (str).

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance (best match first).

    Raises
    ------
    ValueError
        If invalid mode or string_match_method is provided, or if descriptions length
        doesn't match candidates length.
    RuntimeError
        If LLM search fails (when mode is "llm").
    """
    # Validate descriptions if provided
    if descriptions is not None:
        if len(descriptions) != len(candidates):
            raise ValueError(
                f"descriptions length ({len(descriptions)}) must match candidates length ({len(candidates)})"
            )

    if mode == "string_match":
        return _string_match_search(query, candidates, top_n, string_match_method)
    elif mode == "llm":
        return _llm_search(query, candidates, top_n, descriptions=descriptions, reasoning=reasoning, **kwargs)
    elif mode == "semantic":
        return _semantic_search(query, candidates, top_n, descriptions=descriptions, **kwargs)
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be one of: 'string_match', 'llm', 'semantic'")


def _string_match_search(
    query: str, candidates: list[str], top_n: int, method: Literal["fuzzy", "substring"]
) -> list[str]:
    """
    Perform string matching search using specified method.

    Parameters
    ----------
    query : str
        The search query string.
    candidates : list[str]
        List of candidate strings to search through.
    top_n : int
        Number of top results to return.
    method : str
        Matching method: "fuzzy" or "substring".

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance.
    """
    if not candidates:
        return []

    query_lower = query.lower()

    if method == "fuzzy":
        # Use rapidfuzz.process.extract for fuzzy matching (default scorer is fuzz.WRatio)
        results = process.extract(query, candidates, limit=top_n)
        return [result[0] for result in results]

    elif method == "substring":
        # Case-insensitive substring matching, ranked by position of match
        matches = [
            (candidate, candidate_lower.find(query_lower))
            for candidate in candidates
            if query_lower in (candidate_lower := candidate.lower())
        ]
        # Sort by position (earlier matches rank higher), then alphabetically
        matches.sort(key=lambda x: (x[1], x[0]))
        return [candidate for candidate, _ in matches[:top_n]]
    else:
        raise ValueError(f"Invalid string_match_method: {method}. Must be one of: 'fuzzy', 'substring'")


def _create_search_output_model(candidates: list[str], reasoning: bool = True) -> type[BaseModel]:
    """Create a dynamic Pydantic model for LLM search output.

    Parameters
    ----------
    candidates : list[str]
        List of candidate strings to create Literal types from.
    reasoning : bool
        Whether to include a reasoning field in the output model (default: True).

    Returns
    -------
    type
        Dynamically created Pydantic model with selected_strings field and optionally reasoning field.
    """
    # Create a single Literal type with all candidates unpacked from a tuple
    # This ensures type safety - each selected string must be one of the candidates
    candidates_tuple = tuple(sorted(candidates))
    candidate_literal_type = Literal[*candidates_tuple]

    # Create the model dynamically
    fields = {}
    if reasoning:
        fields["reasoning"] = (
            str,
            Field(description="Reasoning about which strings were selected and why they match the query."),
        )
    fields["selected_strings"] = (
        list[candidate_literal_type],
        Field(description="List of selected strings from the candidates."),
    )
    return create_model("SearchOutput", **fields)


def _create_search_system_prompt(
    candidates: list[str], top_n: int, descriptions: list[str | None] | None = None, reasoning: bool = True
) -> str:
    """Create a system prompt template for LLM search.

    Parameters
    ----------
    candidates : list[str]
        List of candidate strings to search through.
    top_n : int
        Number of top results to return.
    descriptions : list[str | None] | None
        Optional list of descriptions for candidates. If provided and not all None,
        formats candidates and descriptions as CSV table. Otherwise uses numbered list format.
    reasoning : bool
        Whether to include reasoning instructions in the prompt (default: True).

    Returns
    -------
    str
        System prompt string with candidates list and instructions.
    """
    # Check if descriptions should be used (not None and at least one is not None)
    use_descriptions = descriptions is not None and any(d is not None for d in descriptions)

    if use_descriptions:
        # Format as CSV table
        csv_rows = ["Candidate,Description"]
        for candidate, description in zip(candidates, descriptions, strict=True):
            desc_str = description if description is not None else ""
            csv_rows.append(f"{candidate},{desc_str}")
        candidates_table = "\n".join(csv_rows)
        prompt = f"""You are a search assistant that selects the most relevant strings from a given list based on a query.

Available candidates and their descriptions (CSV format):
{candidates_table}

Your task:
- Analyze the user's query and identify the {top_n} most fitting strings from the candidates above
- Return the selected strings ordered by relevance (best match first)
- Each selected string must be exactly one of the candidate strings listed above (use the Candidate column value)
- If available mostly rely on the descriptions to find the best matches otherwise use the candidate strings themselves{"" if reasoning else ""}
{"- Provide very concise reasoning about why these strings were selected and how they match the query" if reasoning else ""}

Return exactly {top_n} strings (or fewer if there are fewer than {top_n} candidates)."""
    else:
        # Use numbered list format (original behavior)
        candidates_list = "\n".join(f"{i + 1}. {candidate}" for i, candidate in enumerate(candidates))
        prompt = f"""You are a search assistant that selects the most relevant strings from a given list based on a query.

Available candidate strings:
{candidates_list}

Your task:
- Analyze the user's query and identify the {top_n} most fitting strings from the candidates above
- Return the selected strings ordered by relevance (best match first)
- Each selected string must be exactly one of the candidate strings listed above
{"- Provide very concise reasoning about why these strings were selected and how they match the query" if reasoning else ""}

Return exactly {top_n} strings (or fewer if there are fewer than {top_n} candidates)."""
    return prompt


def _llm_search(
    query: str,
    candidates: list[str],
    top_n: int,
    model: str = "openai/gpt-5-nano",
    temperature: float = 1.0,
    descriptions: list[str | None] | None = None,
    reasoning: bool = True,
    verbose: bool = False,
    **kwargs,
) -> list[str]:
    """Perform LLM-based search using structured outputs.

    Parameters
    ----------
    query : str
        The search query string.
    candidates : list[str]
        List of candidate strings to search through.
    top_n : int
        Number of top results to return.
    model : str
        Model name for LLM backend (default: "openai/gpt-5-nano").
    temperature : float
        Sampling temperature (default: 1.0).
    descriptions : list[str | None] | None
        Optional list of descriptions for candidates. When provided, candidates and
        descriptions are formatted as CSV in the system prompt to help the LLM
        make better matches. The function still returns only the original candidates.
    reasoning : bool
        Whether to include reasoning in LLM output and prompt (default: True).
    **kwargs
        Additional keyword arguments (unused, reserved for future use).

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance (original candidates without descriptions).

    Raises
    ------
    ValueError
        If the response contains invalid strings or parsing fails.
    RuntimeError
        If the LLM call fails.
    """
    if not candidates:
        return []

    # Limit top_n to available candidates
    top_n = min(top_n, len(candidates))

    # Create dynamic output model
    output_model = _create_search_output_model(candidates, reasoning=reasoning)

    # Create system prompt
    system_prompt = _create_search_system_prompt(candidates, top_n, descriptions=descriptions, reasoning=reasoning)

    # Get structured response from LLM
    try:
        response = get_structured_response_litellm(
            input=query,
            system_prompt=system_prompt,
            output_model=output_model,
            model=model,
            temperature=temperature,
        )
        parsed_output = structured_response_to_output_model(response, output_model)
        if verbose and reasoning and hasattr(parsed_output, "reasoning"):
            print(f"Reasoning: {parsed_output.reasoning}")
        selected_strings = parsed_output.selected_strings
    except Exception as e:
        raise RuntimeError(f"Failed to get LLM search response: {e}") from e

    # Validate that all selected strings are in candidates (safety check)
    # Note: Literal types should enforce this, but we validate for extra safety
    if invalid := [s for s in selected_strings if s not in candidates]:
        raise ValueError(f"LLM returned invalid strings not in candidates: {invalid}. Valid candidates: {candidates}")

    # Return up to top_n strings (in case LLM returned more)
    return selected_strings[:top_n]


# Model cache for direct backend
_model_cache: dict[str, SentenceTransformer] = {}


def _prepare_semantic_candidates(
    candidates: list[str], descriptions: list[str | None] | None
) -> tuple[list[str], list[str]]:
    """
    Prepare candidates for semantic search by combining with descriptions.

    Parameters
    ----------
    candidates : list[str]
        List of candidate strings.
    descriptions : list[str | None] | None
        Optional list of descriptions. If None or all None, returns original candidates.
        If provided, combines as "candidate (description)" when description exists.

    Returns
    -------
    tuple[list[str], list[str]]
        Tuple of (combined_strings_for_embedding, original_candidates).
        The combined strings are used for embedding, and original_candidates
        maintains the mapping back to original strings.
    """
    if descriptions is None or all(d is None for d in descriptions):
        return candidates, candidates

    combined_strings = [
        f"{candidate} ({description})" if description is not None else candidate
        for candidate, description in zip(candidates, descriptions, strict=True)
    ]
    return combined_strings, candidates


def _compute_cosine_similarity_ranking(
    query_embedding: np.ndarray, candidate_embeddings: np.ndarray, top_n: int
) -> np.ndarray:
    """
    Compute cosine similarity between query and candidates, return top-n indices.

    Parameters
    ----------
    query_embedding : np.ndarray
        Query embedding vector.
    candidate_embeddings : np.ndarray
        Candidate embedding vectors (2D array).
    top_n : int
        Number of top results to return.

    Returns
    -------
    np.ndarray
        Indices of top-n candidates ordered by similarity (best first).
    """
    # Normalize embeddings for cosine similarity
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
    candidate_norms = candidate_embeddings / (np.linalg.norm(candidate_embeddings, axis=1, keepdims=True) + 1e-8)

    # Compute cosine similarity (dot product of normalized vectors)
    similarities = np.dot(candidate_norms, query_norm)

    # Get top-n indices
    return np.argsort(similarities)[::-1][:top_n]


def _semantic_search(
    query: str,
    candidates: list[str],
    top_n: int,
    backend: Literal["direct", "http"] = "direct",
    model: str = "all-MiniLM-L6-v2",
    http_url: str | None = None,
    descriptions: list[str | None] | None = None,
    **kwargs,
) -> list[str]:
    """
    Perform semantic search using embeddings.

    Parameters
    ----------
    query : str
        The search query string.
    candidates : list[str]
        List of candidate strings to search through.
    top_n : int
        Number of top results to return.
    backend : str
        Backend to use: "direct" or "http" (default: "direct").
    model : str
        Model name for direct backend (default: "all-MiniLM-L6-v2").
    http_url : str
        URL for HTTP backend (default: "http://127.0.0.1:8501/embed"). When unset,
        falls back to the META_MCP_EMBEDDING_HTTP_URL environment variable.
    descriptions : list[str | None] | None
        Optional list of descriptions for candidates. Combined with candidates
        as "candidate (description)" for embedding computation.
    **kwargs
        Additional keyword arguments (unused, reserved for future use).

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance (original candidates without descriptions).

    Raises
    ------
    ValueError
        If invalid backend is provided.
    """
    if not candidates:
        return []
    if http_url is None:
        http_url = os.getenv("META_MCP_EMBEDDING_HTTP_URL", "http://127.0.0.1:8501/embed")

    # Prepare combined strings for embedding and maintain mapping to originals
    combined_strings, original_candidates = _prepare_semantic_candidates(candidates, descriptions)

    if backend == "direct":
        return _semantic_search_direct(query, combined_strings, original_candidates, top_n, model)
    elif backend == "http":
        return _semantic_search_http(query, combined_strings, original_candidates, top_n, http_url)
    else:
        raise ValueError(f"Invalid backend: {backend}. Must be one of: 'direct', 'http'")


def _semantic_search_direct(
    query: str,
    combined_strings: list[str],
    original_candidates: list[str],
    top_n: int,
    model: str,
) -> list[str]:
    """
    Perform semantic search using direct model initialization.

    Parameters
    ----------
    query : str
        The search query string.
    combined_strings : list[str]
        List of combined candidate strings (with descriptions if provided) for embedding.
    original_candidates : list[str]
        List of original candidate strings to return.
    top_n : int
        Number of top results to return.
    model : str
        Model name to use for embeddings.

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance (original candidates).
    """
    # Lazy-load and cache model
    if model not in _model_cache:
        _model_cache[model] = SentenceTransformer(model)

    encoder = _model_cache[model]

    # Compute embeddings using combined strings
    query_embedding = encoder.encode(query, convert_to_numpy=True)
    candidate_embeddings = encoder.encode(combined_strings, convert_to_numpy=True)

    # Get top-n indices by cosine similarity
    top_indices = _compute_cosine_similarity_ranking(query_embedding, candidate_embeddings, top_n)

    # Return original candidates in order of similarity
    return [original_candidates[i] for i in top_indices]


def _semantic_search_http(
    query: str,
    combined_strings: list[str],
    original_candidates: list[str],
    top_n: int,
    http_url: str,
) -> list[str]:
    """
    Perform semantic search using HTTP embedding server.

    Parameters
    ----------
    query : str
        The search query string.
    combined_strings : list[str]
        List of combined candidate strings (with descriptions if provided) for embedding.
    original_candidates : list[str]
        List of original candidate strings to return.
    top_n : int
        Number of top results to return.
    http_url : str
        URL of the embedding server endpoint.

    Returns
    -------
    list[str]
        List of top-n matching strings, ordered by relevance (original candidates).

    Raises
    ------
    RuntimeError
        If the HTTP request fails.
    ValueError
        If the server response is invalid.
    """
    # Prepare texts for embedding (query + combined strings)
    texts = [query] + combined_strings

    # Make HTTP request
    try:
        response = httpx.post(
            http_url,
            json={"texts": texts},
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Failed to get embeddings from server: {e}") from e

    # Extract embeddings from response (supports list or dict with "embeddings"/"data" key)
    if isinstance(result, dict):
        embeddings = result.get("embeddings") or result.get("data")
        if embeddings is None:
            raise ValueError("Invalid server response: no embeddings found")
    elif isinstance(result, list):
        embeddings = result
    else:
        raise ValueError(f"Invalid server response format: {type(result)}")

    if len(embeddings) != len(texts):
        raise ValueError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")

    # Convert to numpy array and extract query/candidate embeddings
    embeddings_array = np.array(embeddings)
    query_embedding = embeddings_array[0]
    candidate_embeddings = embeddings_array[1:]

    # Get top-n indices by cosine similarity
    top_indices = _compute_cosine_similarity_ranking(query_embedding, candidate_embeddings, top_n)

    # Return original candidates in order of similarity
    return [original_candidates[i] for i in top_indices]
