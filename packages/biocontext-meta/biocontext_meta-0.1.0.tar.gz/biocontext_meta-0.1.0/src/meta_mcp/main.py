import logging
import os
import sys

import click


@click.command(name="run")
@click.option(
    "-t",
    "--transport",
    "transport",
    type=str,
    help="MCP transport option. Defaults to 'stdio'.",
    default="stdio",
    envvar="MCP_TRANSPORT",
)
@click.option(
    "-p",
    "--port",
    "port",
    type=int,
    help="Port of MCP server. Defaults to '8000'",
    default=8000,
    envvar="MCP_PORT",
    required=False,
)
@click.option(
    "-h",
    "--host",
    "hostname",
    type=str,
    help="Hostname of MCP server. Defaults to '0.0.0.0'",
    default="0.0.0.0",
    envvar="MCP_HOSTNAME",
    required=False,
)
@click.option("-v", "--version", "version", is_flag=True, help="Get version of package.")
@click.option(
    "--connect-on-startup",
    "connect_on_startup",
    is_flag=True,
    default=False,
    help="Connect to all MCP servers in the registry.json file on startup. Sets MCP_CONNECT_ON_STARTUP environment variable. Not recommended.",
    envvar="MCP_CONNECT_ON_STARTUP",
)
@click.option(
    "--registry-json",
    "registry_json",
    type=str,
    help="URL or path to registry.json file. Defaults to 'https://biocontext.ai/registry.json'.",
    default="https://biocontext.ai/registry.json",
    envvar="MCP_REGISTRY_JSON",
)
@click.option(
    "--registry-mcp-json",
    "registry_mcp_json",
    type=str,
    help="URL or path to mcp.json file. Defaults to 'https://biocontext.ai/mcp.json'.",
    default="https://biocontext.ai/mcp.json",
    envvar="MCP_REGISTRY_MCP_JSON",
)
@click.option(
    "--registry-mcp-tools-json",
    "registry_mcp_tools_json",
    type=str,
    help="URL or path to mcp_tools.json file. Defaults to 'https://biocontext.ai/mcp_tools.json'.",
    default="https://biocontext.ai/mcp_tools.json",
    envvar="MCP_REGISTRY_MCP_TOOLS_JSON",
)
@click.option(
    "--model",
    "model",
    type=str,
    help="Model name to use for structured output generation. Defaults to 'openai/gpt-5-nano'.",
    default="openai/gpt-5-nano",
    envvar="META_MCP_MODEL",
)
@click.option(
    "--search-mode",
    "search_mode",
    type=click.Choice(["string_match", "llm", "semantic"]),
    default="llm",
    envvar="MCP_SEARCH_MODE",
    help="Search mode for server/tool filtering. Defaults to 'llm'.",
)
@click.option(
    "--reasoning/--no-reasoning",
    "reasoning",
    default=False,
    help="Enable/disable reasoning output in tool calls. Sets META_MCP_REASONING environment variable. Can also be set via META_MCP_REASONING env var (true/false). Defaults to False.",
    envvar="META_MCP_REASONING",
)
@click.option(
    "-n",
    "--max-servers",
    "max_servers",
    type=int,
    help="Maximum number of servers to return in search results. Defaults to '10'.",
    default=10,
    envvar="MCP_MAX_SERVERS",
)
@click.option(
    "-x",
    "--max-tools",
    "max_tools",
    type=int,
    help="Maximum number of tools to return in search results. Defaults to '10'.",
    default=10,
    envvar="MCP_MAX_TOOLS",
)
@click.option(
    "--output-args",
    "output_args",
    is_flag=True,
    help="Output schema-conformed arguments in tool calls. Sets META_MCP_OUTPUT_ARGS environment variable to true when present. Can also be set via META_MCP_OUTPUT_ARGS env var (true/false). Defaults to False.",
    envvar="META_MCP_OUTPUT_ARGS",
)
def run_app(
    transport: str = "stdio",
    port: int = 8000,
    hostname: str = "0.0.0.0",
    version: bool = False,
    connect_on_startup: bool = False,
    registry_json: str = "https://biocontext.ai/registry.json",
    registry_mcp_json: str = "https://biocontext.ai/mcp.json",
    registry_mcp_tools_json: str = "https://biocontext.ai/mcp_tools.json",
    model: str = "openai/gpt-5-nano",
    search_mode: str = "llm",
    reasoning: bool = True,
    max_servers: int = 10,
    max_tools: int = 10,
    output_args: bool = False,
):
    """Run the MCP server "meta-mcp".

    The BioContext AI meta mcp enables access to all installable MCP servers in the BioContextAI registry with minimal context consumption.
    The MCP server runs via the configured transport, defaulting to stdio.
    The port is set via "-p/--port" or the MCP_PORT environment variable, defaulting to "8000" if not set.
    The hostname is set via "-h/--host" or the MCP_HOSTNAME environment variable, defaulting to "0.0.0.0" if not set.
    To specify the transport method of the MCP server, set "-t/--transport" or the MCP_TRANSPORT environment variable, which defaults to "stdio".
    """
    if version is True:
        from meta_mcp import __version__

        click.echo(__version__)
        sys.exit(0)

    # Set environment variables based on CLI flags BEFORE importing modules that use mcp
    os.environ["MCP_CONNECT_ON_STARTUP"] = "true" if connect_on_startup else "false"
    os.environ["MCP_REGISTRY_JSON"] = registry_json
    os.environ["MCP_REGISTRY_MCP_JSON"] = registry_mcp_json
    os.environ["MCP_REGISTRY_MCP_TOOLS_JSON"] = registry_mcp_tools_json
    os.environ["META_MCP_MODEL"] = model
    os.environ["MCP_SEARCH_MODE"] = search_mode
    # Set reasoning env var based on click option (handles CLI flag, env var, or default)
    os.environ["META_MCP_REASONING"] = "true" if reasoning else "false"
    os.environ["MCP_MAX_SERVERS"] = str(max_servers)
    os.environ["MCP_MAX_TOOLS"] = str(max_tools)
    os.environ["META_MCP_OUTPUT_ARGS"] = "true" if output_args else "false"

    logger = logging.getLogger(__name__)

    from meta_mcp.mcp import mcp

    # Import tools after setting environment variables so conditional imports work
    # This ensures __all__ is populated correctly based on environment variables
    from . import tools

    # Register all tools from __all__ dynamically
    for name in tools.__all__:
        tool_func = getattr(tools, name)
        mcp.tool(tool_func)

    logger.info("Starting MCP server")
    if transport == "http":
        mcp.run(transport=transport, port=port, host=hostname)
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    run_app()
