import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

import meta_mcp
from meta_mcp.mcp import mcp

from .helpers import create_dummy_anndata


def test_package_has_version():
    """Testing package version exist."""
    assert meta_mcp.__version__ is not None


def test_mcp_server_initialized():
    """Test that the MCP server is properly initialized."""
    assert mcp is not None
    assert mcp.name == "meta-mcp"


def test_mcp_server_has_tools():
    """Test that the MCP server has tools registered."""
    # Tools are registered when the module is imported
    # Check that we can access tools through the module
    from meta_mcp import tools

    assert hasattr(tools, "__all__")
    assert len(tools.__all__) > 0

    # Verify that expected tools are available
    expected_tools = ["call_tool", "get_tool_info", "list_server_tools", "list_servers"]
    for tool_name in expected_tools:
        assert tool_name in tools.__all__


@pytest.mark.asyncio
@patch("meta_mcp.tools._search.get_structured_response_litellm")
@patch("meta_mcp.tools._search.structured_response_to_output_model")
@patch("meta_mcp.tools._call.get_structured_response_litellm")
@patch("meta_mcp.tools._call.structured_response_to_output_model")
async def test_mcp_server_works_with_anndata_mcp(
    mock_call_parse_output, mock_call_get_response, mock_search_parse_output, mock_search_get_response, tmp_path
):
    """Testing MCP server tools work with anndata-mcp."""
    # Set up mocks for LLM calls

    # Mock search LLM response - return servers including anndata-mcp
    mock_search_response = MagicMock()
    mock_search_get_response.return_value = mock_search_response

    # Create a function that returns valid selected strings based on actual candidates
    def mock_search_parse_output_func(response, output_model):
        # We know anndata-mcp should be in the results for single-cell query
        mock_output = MagicMock()
        mock_output.selected_strings = ["biocontext-ai/anndata-mcp"]
        return mock_output

    mock_search_parse_output.side_effect = mock_search_parse_output_func

    # Mock call_tool LLM responses - parse JSON arguments
    mock_call_response = MagicMock()
    mock_call_get_response.return_value = mock_call_response

    # Create a function that returns appropriate parsed output based on arguments
    def mock_call_parse_output_func(response, output_model):
        # Extract the arguments from the call
        call_args = mock_call_get_response.call_args
        if call_args:
            input_text = call_args[1]["input"]  # The arguments JSON string
            # Parse the JSON and create a mock output with those values
            try:
                parsed_args = json.loads(input_text)
                mock_output = MagicMock()
                mock_output.model_dump.return_value = parsed_args
                # Remove biocontextai_schema_reasoning if present (it's added by the reasoning logic)
                filtered_args = {k: v for k, v in parsed_args.items() if k != "biocontextai_schema_reasoning"}
                mock_output.model_dump.return_value = filtered_args
                return mock_output
            except json.JSONDecodeError:
                pass
        # Fallback mock
        mock_output = MagicMock()
        mock_output.model_dump.return_value = {}
        return mock_output

    mock_call_parse_output.side_effect = mock_call_parse_output_func

    # Register all tools from tools module (skip if already registered)
    from .helpers import register_tools

    register_tools()

    # create a dummy anndata object
    adata = create_dummy_anndata()
    test_file = tmp_path / "test_anndata.h5ad"
    adata.write_h5ad(test_file)

    async with Client(mcp) as client:
        result = await client.call_tool("list_servers", {"query": "single-cell"})
        assert result.data is not None
        print(f"Servers: {result.content}")

        server = "biocontext-ai/anndata-mcp"
        result = await client.call_tool("list_server_tools", {"server_name": server})
        assert result.data is not None
        print(f"Tools for server '{server}':", result.content)

        # Example: Get tool info using tuple-based keys (separate server_name and tool_name)
        result = await client.call_tool("get_tool_info", {"server_name": server, "tool_name": "get_summary"})
        assert result.data is not None
        print(f"Tool info for '{server}:get_summary':", result.content)

        # Example: Call a tool with arguments
        result = await client.call_tool(
            "call_tool",
            {"server_name": server, "tool_name": "get_summary", "arguments": json.dumps({"path": str(test_file)})},
        )
        assert result.data is not None
        print(f"Summary of the test anndata object: {result.content}")

        result = await client.call_tool(
            "call_tool",
            {
                "server_name": server,
                "tool_name": "get_descriptive_stats",
                "arguments": json.dumps({"path": str(test_file), "attribute": "obs"}),
            },
        )
        assert result.data is not None
        print(f"Descriptive stats of the test anndata object: {result.content}")
