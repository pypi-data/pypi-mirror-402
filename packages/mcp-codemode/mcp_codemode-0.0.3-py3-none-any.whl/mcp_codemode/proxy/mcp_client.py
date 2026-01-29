# Copyright (c) 2025-2026 Datalayer, Inc.
#
# BSD 3-Clause License

"""MCP Client - Client for communicating with MCP servers."""

import asyncio
import json
from typing import Any, Optional

import httpx


class MCPClient:
    """Client for communicating with an MCP server.

    Supports both HTTP-based and stdio-based MCP servers.

    Example:
        client = MCPClient(name="bash", url="http://localhost:8001")
        tools = await client.list_tools()
        result = await client.call_tool("ls", {"path": "/tmp"})
    """

    def __init__(
        self,
        name: str,
        url: str = "",
        command: str = "",
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ):
        """Initialize MCP client.

        Args:
            name: Server name.
            url: Server URL (for HTTP-based servers).
            command: Command to run (for stdio-based servers).
            args: Command arguments.
            env: Environment variables.
        """
        self.name = name
        self.url = url.rstrip("/") if url else ""
        self.command = command
        self.args = args or []
        self.env = env or {}

        self._http_client: Optional[httpx.AsyncClient] = None
        self._stdio_process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    @property
    def is_http(self) -> bool:
        """Check if this is an HTTP-based server."""
        return bool(self.url) and not self.command

    @property
    def is_stdio(self) -> bool:
        """Check if this is a stdio-based server."""
        return bool(self.command)

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=300.0,
                    write=10.0,
                    pool=5.0,
                ),
                follow_redirects=True,
            )
        return self._http_client

    async def _start_stdio_process(self) -> asyncio.subprocess.Process:
        """Start the stdio process."""
        if self._stdio_process is None or self._stdio_process.returncode is not None:
            import os
            env = {**os.environ, **self.env}
            self._stdio_process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        return self._stdio_process

    async def _send_jsonrpc(self, method: str, params: dict) -> Any:
        """Send a JSON-RPC request.

        Args:
            method: RPC method name.
            params: Method parameters.

        Returns:
            Response result.
        """
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        if self.is_http:
            client = await self._get_http_client()
            response = await client.post(
                f"{self.url}/jsonrpc",
                json=request,
            )
            response.raise_for_status()
            result = response.json()
        elif self.is_stdio:
            process = await self._start_stdio_process()
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("Process stdin/stdout not available")

            # Send request
            request_line = json.dumps(request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read response
            response_line = await process.stdout.readline()
            result = json.loads(response_line.decode())
        else:
            raise ValueError("No server URL or command configured")

        if "error" in result:
            error = result["error"]
            raise RuntimeError(f"MCP Error {error.get('code')}: {error.get('message')}")

        return result.get("result")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the server.

        Returns:
            List of tool definitions.
        """
        try:
            result = await self._send_jsonrpc("tools/list", {})
            return result.get("tools", [])
        except Exception as e:
            # Fallback: try REST endpoint
            if self.is_http:
                try:
                    client = await self._get_http_client()
                    response = await client.get(f"{self.url}/tools")
                    response.raise_for_status()
                    data = response.json()
                    return data.get("tools", data) if isinstance(data, dict) else data
                except Exception:
                    pass
            raise

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the server.

        Args:
            tool_name: Name of the tool to call.
            arguments: Tool arguments.

        Returns:
            Tool execution result.
        """
        try:
            result = await self._send_jsonrpc(
                "tools/call",
                {"name": tool_name, "arguments": arguments},
            )
            return result
        except Exception as e:
            # Fallback: try REST endpoint
            if self.is_http:
                try:
                    client = await self._get_http_client()
                    response = await client.post(
                        f"{self.url}/tools/{tool_name}",
                        json={"arguments": arguments},
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception:
                    pass
            return {"error": str(e)}

    async def close(self) -> None:
        """Close the client and release resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        if self._stdio_process:
            self._stdio_process.terminate()
            await self._stdio_process.wait()
            self._stdio_process = None

    def __repr__(self) -> str:
        if self.is_http:
            return f"MCPClient(name={self.name!r}, url={self.url!r})"
        else:
            return f"MCPClient(name={self.name!r}, command={self.command!r})"
