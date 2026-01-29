import os
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

from fastmcp import Client, FastMCP

from meta_mcp.utils import load_json_from_url, registry_json_to_df


class MetaFastMCPDynamic(FastMCP):
    """FastMCP subclass that manages shared MCP client sessions with dynamic client management."""

    def __init__(
        self,
        registry_json: str,
        registry_mcp_json: str,
        registry_mcp_tools_json: str,
        connect_on_startup: bool = False,
        *,
        name: str = "meta-mcp",
        **kwargs: Any,
    ) -> None:
        # Store connect_on_startup flag first (before calling super)
        self._connect_on_startup = connect_on_startup
        # Load registry config from URL (not used for initial clients, just stored)
        self._registry_config = load_json_from_url(registry_mcp_json)
        # Load registry info from URL and parse to DataFrame
        registry_info_raw = load_json_from_url(registry_json)
        registry_df = registry_json_to_df(registry_info_raw)
        if registry_df.empty:
            raise RuntimeError("Registry DataFrame is empty")

        # Filter registry servers and update configurations
        mcp_server_names, registry_df = self._filter_and_setup_registry(registry_df)
        self._registry_info = registry_df

        # Load MCP tools JSON from URL and store as dict
        self._registry_mcp_tools = load_json_from_url(registry_mcp_tools_json)

        # Initialize _servers with all servers from registry
        self._servers: dict[str, dict[str, Any]] = {}
        mcp_servers = self._registry_config.get("mcpServers", {})
        for server_name, server_cfg in mcp_servers.items():
            # Get server info from registry DataFrame if available
            server_info = {}
            if not registry_df.empty and "identifier" in registry_df.columns:
                server_row = registry_df[registry_df["identifier"] == server_name]
                if not server_row.empty:
                    server_info = server_row.iloc[0].to_dict()
            self._servers[server_name] = {
                "config": server_cfg,
                "info": server_info,
            }

        # Initialize _tools with all tools from registry
        # Structure: server_name -> tool_name -> {"name": ..., "input_schema": ..., ...}
        self._tools: dict[str, dict[str, dict[str, Any]]] = {}
        # Note: The JSON uses 'mcp_servers' (snake_case) not 'mcpServers' (camelCase)
        registry_tools = self._registry_mcp_tools.get("mcp_servers", {})
        for server_name, server_data in registry_tools.items():
            # Only include tools from servers that are in the mcp.json file and not the server itself
            if server_name not in mcp_server_names:
                continue
            tools_list = server_data.get("tools", [])
            if server_name not in self._tools:
                self._tools[server_name] = {}
            for tool in tools_list:
                tool_name = tool.get("name", "")
                # Extract name and input_schema from tool dict
                tool_info = {
                    "name": tool_name,
                    "input_schema": tool.get("input_schema", {}),
                    "description": tool.get("description", ""),
                }
                self._tools[server_name][tool_name] = tool_info

        # Lifespan-managed clients (from config)
        self._lifespan_clients: dict[str, Client] = {}
        # Dynamically-managed clients (added at runtime)
        self._dynamic_clients: dict[str, Client] = {}
        self._dynamic_client_stacks: dict[str, AsyncExitStack] = {}

        # Call super().__init__ once with all parameters including lifespan
        super().__init__(name=name, lifespan=self._lifespan, **kwargs)

    def _filter_and_setup_registry(self, registry_df):
        # Get server names from registry config, preserving order but removing duplicates
        mcp_server_names = list(dict.fromkeys(self._registry_config.get("mcpServers", {}).keys()))

        # Exclude this server itself (meta-mcp)
        mcp_server_names = [s for s in mcp_server_names if not ("biocontext-ai" in s and "meta-mcp" in s)]

        # Update registry config to only include filtered servers
        self._registry_config = {
            "mcpServers": {
                server_name: self._registry_config.get("mcpServers", {}).get(server_name)
                for server_name in mcp_server_names
            }
        }

        # Filter registry DataFrame to match
        if "identifier" in registry_df.columns:
            registry_df = registry_df[registry_df["identifier"].isin(mcp_server_names)].copy()
        else:
            raise RuntimeError("Identifier column not found in registry DataFrame")

        return mcp_server_names, registry_df

    async def _update_tools_from_client(self, server_name: str, client: Client) -> None:
        """Update tool metadata for a server from a connected client."""
        client_tools = await client.list_tools()
        if server_name not in self._tools:
            self._tools[server_name] = {}

        for tool in client_tools:
            tool_dict = tool.model_dump()
            # Handle both inputSchema (from FastMCP) and input_schema (from registry)
            input_schema = tool_dict.get("input_schema", tool_dict.get("inputSchema", {}))
            self._tools[server_name][tool.name] = {
                "name": tool.name,
                "input_schema": input_schema,
                "description": tool_dict.get("description", ""),
            }

    @asynccontextmanager
    async def _lifespan(self, _app: FastMCP):
        async with AsyncExitStack() as stack:
            # Use registry config if connect_on_startup is True, otherwise use empty dict
            servers_to_connect = self._registry_config.get("mcpServers", {}) if self._connect_on_startup else {}

            for server_name, server_cfg in servers_to_connect.items():
                print(f"Connecting to server '{server_name}'")
                server_config = {"mcpServers": {server_name: server_cfg}}
                client = Client(server_config, name=f"{self.name}:{server_name}")
                try:
                    await stack.enter_async_context(client)
                    self._lifespan_clients[server_name] = client
                    await self._update_tools_from_client(server_name, client)
                except (RuntimeError, ConnectionError, ValueError) as e:
                    # Skip servers that fail to connect during initialization
                    print(f"Failed to connect to server '{server_name}': {e}")
            try:
                yield {"clients": self._lifespan_clients}
            finally:
                # Clean up lifespan clients
                self._lifespan_clients = {}
                # Clean up any remaining dynamic clients
                await self._cleanup_all_dynamic_clients()

    async def add_client(
        self,
        server_name: str,
        server_config: dict[str, Any],
    ) -> None:
        """Add a new client at runtime.

        Args:
            server_name: Name to identify this server
            server_config: MCP server configuration dict (should have 'mcpServers' key)

        Raises
        ------
            RuntimeError: If clients are not initialized or server already exists
            Exception: If client connection fails
        """
        if server_name in self._lifespan_clients:
            raise RuntimeError(f"Server '{server_name}' already exists in lifespan-managed clients")

        if server_name in self._dynamic_clients:
            raise RuntimeError(f"Server '{server_name}' already exists in dynamic clients")

        # Create client and manage it with its own AsyncExitStack
        client = Client(server_config, name=f"{self.name}:{server_name}")
        stack = AsyncExitStack()

        try:
            await stack.enter_async_context(client)
            self._dynamic_clients[server_name] = client
            self._dynamic_client_stacks[server_name] = stack

            # Update _servers if not already present
            if server_name not in self._servers:
                server_cfg = server_config.get("mcpServers", {}).get(server_name, {})
                self._servers[server_name] = {
                    "config": server_cfg,
                    "info": {},
                }

            # Update tools with metadata from connected client
            await self._update_tools_from_client(server_name, client)
        except Exception as e:
            # Clean up on failure
            await stack.aclose()
            raise RuntimeError(f"Failed to connect to server '{server_name}': {e}") from e

    async def remove_client(self, server_name: str) -> None:
        """Remove a dynamically-managed client at runtime.

        Args:
            server_name: Name of the server to remove

        Raises
        ------
            RuntimeError: If server doesn't exist or is lifespan-managed
        """
        if server_name in self._lifespan_clients:
            raise RuntimeError(
                f"Cannot remove lifespan-managed client '{server_name}'. Only dynamically-added clients can be removed."
            )

        if server_name not in self._dynamic_clients:
            raise RuntimeError(f"Server '{server_name}' is not in dynamic clients")

        # Remove connected client tools from _tools (but keep registry tools if present)
        # Check if server exists in registry
        is_in_registry = server_name in self._registry_config.get("mcpServers", {})
        if not is_in_registry:
            # If not in registry, remove all tools for this server
            if server_name in self._tools:
                del self._tools[server_name]
            # Also remove from _servers if it was dynamically added
            if server_name in self._servers:
                del self._servers[server_name]
        else:
            # If in registry, restore registry tools (remove connected Tool objects, keep registry dicts)
            registry_tools = self._registry_mcp_tools.get("mcp_servers", {}).get(server_name, {}).get("tools", [])
            if server_name not in self._tools:
                self._tools[server_name] = {}
            # Clear and restore registry tools
            self._tools[server_name].clear()
            for tool in registry_tools:
                tool_name = tool.get("name", "")
                input_schema = tool.get("input_schema", {})
                tool_info = {
                    "name": tool_name,
                    "input_schema": input_schema,
                    "description": tool.get("description", ""),
                }
                self._tools[server_name][tool_name] = tool_info

        # Clean up client and its stack
        stack = self._dynamic_client_stacks.pop(server_name, None)
        if stack:
            await stack.aclose()

        self._dynamic_clients.pop(server_name, None)

    async def _cleanup_all_dynamic_clients(self) -> None:
        """Clean up all dynamically-managed clients."""
        for server_name in list(self._dynamic_clients.keys()):
            await self.remove_client(server_name)

    def get_client(self, server_name: str) -> Client:
        """Get a client by name (from either pool).

        Parameters
        ----------
        server_name : str
            Name of the server.

        Returns
        -------
        Client
            Client instance.

        Raises
        ------
            RuntimeError: If clients are not initialized or server doesn't exist
        """
        # Check lifespan clients first
        if server_name in self._lifespan_clients:
            return self._lifespan_clients[server_name]

        # Check dynamic clients
        if server_name in self._dynamic_clients:
            return self._dynamic_clients[server_name]

        raise RuntimeError(f"Server '{server_name}' is not connected")

    def get_clients(self) -> dict[str, Client]:
        """Get all clients (both lifespan and dynamic).

        Returns
        -------
        dict[str, Client]
            Combined dictionary of all clients.

        Raises
        ------
            RuntimeError: If clients are not initialized
        """
        # Combine both client pools
        all_clients = dict(self._lifespan_clients)
        all_clients.update(self._dynamic_clients)
        return all_clients

    def get_lifespan_clients(self) -> dict[str, Client]:
        """Get only lifespan-managed clients.

        Returns
        -------
        dict[str, Client]
            Dictionary of lifespan-managed clients.

        Raises
        ------
            RuntimeError: If clients are not initialized
        """
        return self._lifespan_clients

    def get_dynamic_clients(self) -> dict[str, Client]:
        """Get only dynamically-managed clients.

        Returns
        -------
        dict[str, Client]
            Dictionary of dynamically-managed clients.
        """
        return dict(self._dynamic_clients)

    async def connect_to_server(self, server_name: str) -> None:
        """Connect to a server from the registry."""
        mcp_servers = self._registry_config.get("mcpServers", {})
        server_cfg = mcp_servers.get(server_name)
        if server_cfg is None:
            raise RuntimeError(f"Server '{server_name}' not found in registry")
        # Wrap in proper MCP config format expected by add_client
        server_config = {"mcpServers": {server_name: server_cfg}}
        await self.add_client(server_name, server_config)

    async def disconnect_from_server(self, server_name: str) -> None:
        """Disconnect from a dynamically-connected server."""
        await self.remove_client(server_name)


# Read connect_on_startup from environment variable, defaulting to False
_connect_on_startup = os.getenv("MCP_CONNECT_ON_STARTUP", "false").lower() == "true"

# Read file paths from environment variables, defaulting to biocontext.ai URLs
_registry_json = os.getenv("MCP_REGISTRY_JSON", "https://biocontext.ai/registry.json")
_registry_mcp_json = os.getenv("MCP_REGISTRY_MCP_JSON", "https://biocontext.ai/mcp.json")
_registry_mcp_tools_json = os.getenv("MCP_REGISTRY_MCP_TOOLS_JSON", "https://biocontext.ai/mcp_tools.json")

mcp: MetaFastMCPDynamic = MetaFastMCPDynamic(
    registry_json=_registry_json,
    registry_mcp_json=_registry_mcp_json,
    registry_mcp_tools_json=_registry_mcp_tools_json,
    instructions="The BioContext AI meta mcp enables access to all installable MCP servers in the BioContextAI registry with minimal context consumption.",
    on_duplicate_tools="error",
    connect_on_startup=_connect_on_startup,
)
