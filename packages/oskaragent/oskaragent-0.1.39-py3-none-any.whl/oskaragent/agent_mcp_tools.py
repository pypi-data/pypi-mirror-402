import asyncio
from typing import Iterable, Any

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

from .helpers import ToolContext, log_msg


def build_mcp_tool_schemas(tool_names: Iterable[str], mcp_tools_schemas: list) -> list[dict[str, Any]]:
    """Generate minimal JSON schema definitions for API-exposed tools.

    Args:
        tool_names (Iterable[str]): Conjunto de nomes de ferramentas permitidos na sessão.
        mcp_tools_schemas: Optional[dict]: Definições das ferramentas externas

    Returns:
        list[dict[str, Any]]: Lista de esquemas no formato esperado pela OpenAI Responses API.
    """
    schemas: list[dict[str, Any]] = []
    for name in tool_names:
        for mcp_tool_schema in mcp_tools_schemas:
            if mcp_tool_schema["name"] == name:
                schemas.append(mcp_tool_schema)
                break

    return schemas


async def build_mcp_tools_schemas(mcp_tools: list[dict]) -> list[dict]:
    """Carrega e valida as definições das ferramentas externas disponíveis para o MCP."""
    mcp_tools_schemas = []
    for server in mcp_tools:
        server_url = server["mcpServerUrl"]

        async with streamable_http_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                for tool in tools.tools:
                    for tool_name in server["tools"]:
                        if tool_name == tool.name:
                            tool_schema = {
                                "type": "function",
                                "name": tool.name,
                                "description": tool.description,
                                "args_obj": tool.inputSchema,
                                "mcpServerUrl": server_url,
                            }
                            tool_schema["args_obj"]["title"] = tool_schema["name"] + "_arguments"
                            mcp_tools_schemas.append(tool_schema)
                            break

    return mcp_tools_schemas


def get_mcp_tools_names(mcp_tools_schemas: list[dict[str, Any]]) -> list[str]:
    """Gera uma lista com os nomes das ferramentas configuradas para o MCP."""
    return [tool_schema["name"] for tool_schema in mcp_tools_schemas]


def get_mcp_tools_schema(mcp_tools_schemas: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    """Retorna o esquema de uma ferramenta MCP específica a partir de uma lista de esquemas."""
    return next((tool_schema for tool_schema in mcp_tools_schemas if tool_schema.get("name") == tool_name), None)


def exec_mcp_tool(tool_name: str,
                  args_obj: dict[str, Any],
                  ctx: ToolContext) -> Any:
    """Executa uma ferramenta personalizada disponibilizada pelo MCP."""
    return asyncio.run(mcp_tool(tool_name, args_obj, ctx))


async def mcp_tool(tool_name: str,
                   args_obj: dict[str, Any],
                   ctx: ToolContext) -> Any:
    """Executa uma ferramenta personalizada disponibilizada pelo MCP."""
    tool_schema = get_mcp_tools_schema(ctx.mcp_tools_schema, tool_name)
    server_url = tool_schema["mcpServerUrl"]

    msg_id = getattr(ctx, "message_id", "-")
    if getattr(ctx, "is_verbose", False):
        log_msg(f"id={msg_id} mcp_call server={server_url} tool_name={tool_name}", func="mcp_tool", action="tools", color="MAGENTA")

    tool_parameters = {
        param_name: args_obj[param_name] if param_name in args_obj else tool_schema["args_obj"][param_name].get("default")
        for param_name in tool_schema.get("args_obj", {}).get("properties", {}).keys()
    }

    async with streamable_http_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=tool_parameters,
            )

            if isinstance(result.content[0], types.TextContent):
                result = result.content[0].text

    return result
