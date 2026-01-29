from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    transport: str
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    url: str | None = None


@dataclass(frozen=True)
class McpToolSpec:
    public_name: str
    server_name: str
    tool_name: str
    description: str
    input_schema: dict[str, Any]


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_env(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items()}


def _normalize_transport(value: str | None, config: dict[str, Any]) -> str:
    if value:
        return value
    if "url" in config:
        return "sse"
    return "stdio"


def load_mcp_servers(path: str) -> list[McpServerConfig]:
    if not path or not os.path.exists(path):
        return []
    data = _load_json(path)

    servers: list[McpServerConfig] = []
    servers_map = data.get("mcpServers")
    if isinstance(servers_map, dict):
        for name, config in servers_map.items():
            if not isinstance(config, dict):
                continue
            # Backwards-compatible guard: ignore the old template placeholder server.
            # (Older `voidchat init` wrote `python -m your_mcp_server` which is not meant to run.)
            cmd = (config.get("command") or "").strip()
            args = config.get("args", [])
            if cmd == "python" and args == ["-m", "your_mcp_server"]:
                continue
            transport = _normalize_transport(
                config.get("transport") or config.get("type"), config
            )
            servers.append(
                McpServerConfig(
                    name=str(name),
                    transport=transport,
                    command=config.get("command"),
                    args=args,
                    env=_normalize_env(config.get("env", {})),
                    url=config.get("url"),
                )
            )
        return servers

    for item in data.get("servers", []):
        if not isinstance(item, dict):
            continue
        servers.append(
            McpServerConfig(
                name=item["name"],
                transport=item.get("transport", "stdio"),
                command=item.get("command"),
                args=item.get("args", []),
                env=_normalize_env(item.get("env", {})),
                url=item.get("url"),
            )
        )
    return servers


def _schema_to_dict(schema: Any) -> dict[str, Any]:
    if isinstance(schema, dict):
        return schema
    if hasattr(schema, "model_dump"):
        return schema.model_dump()
    if hasattr(schema, "dict"):
        return schema.dict()
    return {}


async def _list_tools_for_server(server: McpServerConfig) -> list[Any]:
    if server.transport in {"sse", "http"}:
        if not server.url:
            raise ValueError(f"MCP server {server.name} missing url")
        async with sse_client(server.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return list(result.tools)
    if server.transport == "stdio":
        if not server.command:
            raise ValueError(f"MCP server {server.name} missing command")
        params = StdioServerParameters(
            command=server.command,
            args=server.args or [],
            env=server.env or {},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return list(result.tools)
    raise ValueError(f"Unsupported MCP transport: {server.transport}")


async def _call_tool_on_server(
    server: McpServerConfig, tool_name: str, args: dict[str, Any]
) -> Any:
    if server.transport in {"sse", "http"}:
        if not server.url:
            raise ValueError(f"MCP server {server.name} missing url")
        async with sse_client(server.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, args)
    if server.transport == "stdio":
        if not server.command:
            raise ValueError(f"MCP server {server.name} missing command")
        params = StdioServerParameters(
            command=server.command,
            args=server.args or [],
            env=server.env or {},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, args)
    raise ValueError(f"Unsupported MCP transport: {server.transport}")


def _format_tool_result(result: Any) -> str:
    if hasattr(result, "content"):
        parts = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text is None:
                parts.append(str(item))
            else:
                parts.append(text)
        return "\n".join(parts).strip()
    return str(result)


class McpToolRegistry:
    def __init__(self, servers: list[McpServerConfig]):
        self._servers = {server.name: server for server in servers}
        self._tools: dict[str, McpToolSpec] = {}

    @property
    def tools(self) -> list[McpToolSpec]:
        return list(self._tools.values())

    def load_tools(self) -> None:
        tool_names: set[str] = set()
        for server in self._servers.values():
            tools = asyncio.run(_list_tools_for_server(server))
            for tool in tools:
                base_name = tool.name
                public_name = base_name
                if public_name in tool_names:
                    public_name = f"{server.name}.{base_name}"
                tool_names.add(public_name)
                self._tools[public_name] = McpToolSpec(
                    public_name=public_name,
                    server_name=server.name,
                    tool_name=base_name,
                    description=tool.description or "",
                    input_schema=_schema_to_dict(tool.inputSchema),
                )

    def to_openai_tools(self) -> list[dict[str, Any]]:
        tools = []
        for spec in self._tools.values():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": spec.public_name,
                        "description": spec.description,
                        "parameters": spec.input_schema or {"type": "object", "properties": {}},
                    },
                }
            )
        return tools

    def call_tool(self, public_name: str, args: dict[str, Any]) -> str:
        spec = self._tools.get(public_name)
        if not spec:
            raise KeyError(f"Unknown tool: {public_name}")
        server = self._servers[spec.server_name]
        result = asyncio.run(_call_tool_on_server(server, spec.tool_name, args))
        return _format_tool_result(result)
