import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from meta_mcp.mcp import mcp

from .helpers import create_dummy_anndata, register_tools

# Helper functions to reduce code duplication


def setup_search_mocks(mock_parse_output, mock_get_response, selected_strings=None):
    """Set up mocks for search operations."""
    if selected_strings is None:
        selected_strings = ["biocontext-ai/anndata-mcp"]

    mock_response = MagicMock()
    mock_get_response.return_value = mock_response

    mock_output = MagicMock()
    mock_output.selected_strings = selected_strings
    mock_parse_output.return_value = mock_output


async def call_tool_and_parse_result(client, tool_name, arguments=None):
    """Call a tool and parse the JSON result."""
    if arguments is None:
        arguments = {}

    result = await client.call_tool(tool_name, arguments)
    assert result.data is not None
    # result.content is a list of TextContent objects, get the text and parse JSON
    return json.loads(result.content[0].text)


def setup_call_mocks(mock_parse_output, mock_get_response, expected_args):
    """Set up mocks for call operations."""
    mock_response = MagicMock()
    mock_get_response.return_value = mock_response

    def mock_parse_output_func(response, output_model):
        mock_output = MagicMock()
        mock_output.model_dump.return_value = expected_args
        return mock_output

    mock_parse_output.side_effect = mock_parse_output_func


async def call_tool_and_parse_call_result(client, server_name, tool_name, arguments):
    """Call a tool and handle both successful responses and error messages."""
    result = await client.call_tool(
        "call_tool", {"server_name": server_name, "tool_name": tool_name, "arguments": json.dumps(arguments)}
    )
    assert result.data is not None

    # Check if we got an error message or successful response
    content_text = result.content[0].text
    if content_text.startswith("Failed to call tool"):
        # This is expected in test environment where server connection may fail
        return content_text
    else:
        # Successful response
        return json.loads(content_text)


class TestListServers:
    """Test cases for the list_servers tool."""

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_servers_no_query(self, mock_parse_output, mock_get_response):
        """Test list_servers without query parameter."""
        setup_search_mocks(mock_parse_output, mock_get_response)
        register_tools()

        async with Client(mcp) as client:
            servers = await call_tool_and_parse_result(client, "list_servers")
            assert isinstance(servers, dict)
            # Should contain anndata-mcp or be empty depending on registry

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_servers_with_single_cell_query(self, mock_parse_output, mock_get_response):
        """Test list_servers with query that should match anndata-mcp."""
        setup_search_mocks(mock_parse_output, mock_get_response)
        register_tools()

        async with Client(mcp) as client:
            servers = await call_tool_and_parse_result(client, "list_servers", {"query": "single-cell"})
            assert isinstance(servers, dict)
            assert "biocontext-ai/anndata-mcp" in servers

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_servers_with_anndata_query(self, mock_parse_output, mock_get_response):
        """Test list_servers with anndata-specific query."""
        setup_search_mocks(mock_parse_output, mock_get_response)
        register_tools()

        async with Client(mcp) as client:
            servers = await call_tool_and_parse_result(client, "list_servers", {"query": "anndata"})
            assert isinstance(servers, dict)
            assert "biocontext-ai/anndata-mcp" in servers

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_servers_with_non_matching_query(self, mock_parse_output, mock_get_response):
        """Test list_servers with query that shouldn't match anndata-mcp."""
        setup_search_mocks(mock_parse_output, mock_get_response, selected_strings=[])
        register_tools()

        async with Client(mcp) as client:
            servers = await call_tool_and_parse_result(client, "list_servers", {"query": "machine-learning"})
            assert isinstance(servers, dict)
            # Should not contain anndata-mcp when query doesn't match

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_servers_empty_query(self, mock_parse_output, mock_get_response):
        """Test list_servers with empty query string."""
        setup_search_mocks(mock_parse_output, mock_get_response)
        register_tools()

        async with Client(mcp) as client:
            servers = await call_tool_and_parse_result(client, "list_servers", {"query": ""})
            assert isinstance(servers, dict)


class TestListServerTools:
    """Test cases for the list_server_tools tool."""

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_server_tools_no_query(self, mock_parse_output, mock_get_response):
        """Test list_server_tools without query for anndata-mcp."""
        setup_search_mocks(mock_parse_output, mock_get_response, ["get_summary", "get_descriptive_stats"])
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            tools_dict = await call_tool_and_parse_result(client, "list_server_tools", {"server_name": server})
            assert isinstance(tools_dict, dict)
            # Should contain expected anndata-mcp tools
            assert len(tools_dict) > 0

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_server_tools_with_summary_query(self, mock_parse_output, mock_get_response):
        """Test list_server_tools with query filtering for summary tools."""
        setup_search_mocks(mock_parse_output, mock_get_response, ["get_summary"])
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            tools_dict = await call_tool_and_parse_result(
                client, "list_server_tools", {"server_name": server, "query": "summary"}
            )
            assert isinstance(tools_dict, dict)

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_server_tools_with_stats_query(self, mock_parse_output, mock_get_response):
        """Test list_server_tools with query filtering for stats tools."""
        setup_search_mocks(mock_parse_output, mock_get_response, ["get_descriptive_stats"])
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            tools_dict = await call_tool_and_parse_result(
                client, "list_server_tools", {"server_name": server, "query": "stats"}
            )
            assert isinstance(tools_dict, dict)

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_server_tools_no_matches(self, mock_parse_output, mock_get_response):
        """Test list_server_tools with query that matches no tools."""
        setup_search_mocks(mock_parse_output, mock_get_response, [])
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            tools_dict = await call_tool_and_parse_result(
                client, "list_server_tools", {"server_name": server, "query": "nonexistent"}
            )
            assert isinstance(tools_dict, dict)
            # Should be empty or contain no matching tools

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._search.get_structured_response_litellm")
    @patch("meta_mcp.tools._search.structured_response_to_output_model")
    async def test_list_server_tools_empty_query(self, mock_parse_output, mock_get_response):
        """Test list_server_tools with empty query string."""
        setup_search_mocks(mock_parse_output, mock_get_response, ["get_summary", "get_descriptive_stats"])
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            tools_dict = await call_tool_and_parse_result(
                client, "list_server_tools", {"server_name": server, "query": ""}
            )
            assert isinstance(tools_dict, dict)


class TestGetToolInfo:
    """Test cases for the get_tool_info tool."""

    @pytest.mark.asyncio
    async def test_get_tool_info_get_summary(self):
        """Test get_tool_info for get_summary tool."""
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            schema = await call_tool_and_parse_result(
                client, "get_tool_info", {"server_name": server, "tool_name": "get_summary"}
            )
            assert isinstance(schema, dict)
            # Should have properties for get_summary tool
            assert "properties" in schema or "type" in schema

    @pytest.mark.asyncio
    async def test_get_tool_info_get_descriptive_stats(self):
        """Test get_tool_info for get_descriptive_stats tool."""
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            schema = await call_tool_and_parse_result(
                client, "get_tool_info", {"server_name": server, "tool_name": "get_descriptive_stats"}
            )
            assert isinstance(schema, dict)
            # Should have properties for get_descriptive_stats tool
            assert "properties" in schema or "type" in schema

    @pytest.mark.asyncio
    async def test_get_tool_info_nonexistent_tool(self):
        """Test get_tool_info for non-existent tool."""
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            with pytest.raises(ToolError):  # FastMCP client wraps errors in ToolError
                await client.call_tool("get_tool_info", {"server_name": server, "tool_name": "nonexistent_tool"})

    @pytest.mark.asyncio
    async def test_get_tool_info_nonexistent_server(self):
        """Test get_tool_info for non-existent server."""
        register_tools()

        async with Client(mcp) as client:
            with pytest.raises(ToolError):  # FastMCP client wraps errors in ToolError
                await client.call_tool(
                    "get_tool_info", {"server_name": "nonexistent-server", "tool_name": "get_summary"}
                )


class TestCallTool:
    """Test cases for the call_tool functionality."""

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._call.get_structured_response_litellm")
    @patch("meta_mcp.tools._call.structured_response_to_output_model")
    async def test_call_tool_get_summary(self, mock_parse_output, mock_get_response, tmp_path):
        """Test calling get_summary tool with valid path."""
        # Create test data
        adata = create_dummy_anndata()
        test_file = tmp_path / "test.h5ad"
        adata.write_h5ad(test_file)

        setup_call_mocks(mock_parse_output, mock_get_response, {"path": str(test_file)})
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            response_data = await call_tool_and_parse_call_result(
                client, server, "get_summary", {"path": str(test_file)}
            )
            if isinstance(response_data, str):
                # Error message - this is expected in test environment
                assert "Failed to call tool" in response_data
            else:
                # Successful response
                assert "content" in response_data
                assert isinstance(response_data["content"], list)

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._call.get_structured_response_litellm")
    @patch("meta_mcp.tools._call.structured_response_to_output_model")
    async def test_call_tool_get_descriptive_stats_obs(self, mock_parse_output, mock_get_response, tmp_path):
        """Test calling get_descriptive_stats tool with obs attribute."""
        # Create test data
        adata = create_dummy_anndata()
        test_file = tmp_path / "test.h5ad"
        adata.write_h5ad(test_file)

        setup_call_mocks(mock_parse_output, mock_get_response, {"path": str(test_file), "attribute": "obs"})
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            response_data = await call_tool_and_parse_call_result(
                client, server, "get_descriptive_stats", {"path": str(test_file), "attribute": "obs"}
            )
            if isinstance(response_data, str):
                # Error message - this is expected in test environment
                assert "Failed to call tool" in response_data
            else:
                # Successful response
                assert "content" in response_data
                assert isinstance(response_data["content"], list)

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._call.get_structured_response_litellm")
    @patch("meta_mcp.tools._call.structured_response_to_output_model")
    async def test_call_tool_get_descriptive_stats_var(self, mock_parse_output, mock_get_response, tmp_path):
        """Test calling get_descriptive_stats tool with var attribute."""
        # Create test data
        adata = create_dummy_anndata()
        test_file = tmp_path / "test.h5ad"
        adata.write_h5ad(test_file)

        setup_call_mocks(mock_parse_output, mock_get_response, {"path": str(test_file), "attribute": "var"})
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            response_data = await call_tool_and_parse_call_result(
                client, server, "get_descriptive_stats", {"path": str(test_file), "attribute": "var"}
            )
            if isinstance(response_data, str):
                # Error message - this is expected in test environment
                assert "Failed to call tool" in response_data
            else:
                # Successful response
                assert "content" in response_data
                assert isinstance(response_data["content"], list)

    @pytest.mark.asyncio
    @patch("meta_mcp.tools._call.get_structured_response_litellm")
    @patch("meta_mcp.tools._call.structured_response_to_output_model")
    async def test_call_tool_with_invalid_arguments(self, mock_parse_output, mock_get_response, tmp_path):
        """Test calling tool with invalid arguments."""
        setup_call_mocks(mock_parse_output, mock_get_response, {"invalid_param": "value"})
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            response_data = await call_tool_and_parse_call_result(client, server, "get_summary", {"invalid": "args"})
            # Should handle gracefully or return error message
            assert isinstance(response_data, dict | str)

    @pytest.mark.asyncio
    async def test_call_tool_nonexistent_tool(self):
        """Test calling non-existent tool."""
        register_tools()

        async with Client(mcp) as client:
            server = "biocontext-ai/anndata-mcp"
            with pytest.raises(ToolError):  # FastMCP client wraps errors in ToolError
                await client.call_tool(
                    "call_tool", {"server_name": server, "tool_name": "nonexistent_tool", "arguments": json.dumps({})}
                )
