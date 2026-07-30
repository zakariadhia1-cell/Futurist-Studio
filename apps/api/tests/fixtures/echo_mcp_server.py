"""A minimal real MCP server (stdio transport) used only by tests to exercise
app/mcp/client.py against the actual wire protocol instead of mocks."""
import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server


async def on_list_tools(ctx, params):
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="echo",
                description="Gibt den uebergebenen Text zurueck.",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
        ]
    )


async def on_call_tool(ctx, params):
    if params.name != "echo":
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Unbekanntes Tool: {params.name}")], is_error=True
        )
    text = (params.arguments or {}).get("text", "")
    return types.CallToolResult(content=[types.TextContent(type="text", text=f"Echo: {text}")])


server = Server("test-echo-server", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
