"""MCP Server for JAX documentation."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

from jax_mcp.docs_source import DocsSource
from jax_mcp.tools.list_sections import list_sections
from jax_mcp.tools.get_documentation import get_documentation
from jax_mcp.tools.jax_checker import jax_checker

logger = logging.getLogger(__name__)

# Initialize server
server = Server("jax-mcp")

# Initialize docs source (handles local/GitHub resolution)
docs_source = DocsSource()


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list-sections",
            description=(
                "List all available JAX documentation sections. "
                "Returns sections organized by category (concepts, gotchas, transforms, "
                "advanced, performance, api, examples) with use_cases to help identify relevant docs. "
                "Optionally filter by category."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["concepts", "gotchas", "transforms", "advanced", "performance", "api", "examples"],
                        "description": "Optional category to filter sections",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="get-documentation",
            description=(
                "Retrieve full JAX documentation content for requested sections. "
                "Accepts section name(s) or path(s) like 'pytrees', 'key-concepts', "
                "'notebooks/thinking_in_jax', or ['pytrees', 'jit-compilation']. "
                "Notebooks are automatically converted to markdown."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Section name(s) or path(s) to retrieve",
                    }
                },
                "required": ["section"],
            },
        ),
        Tool(
            name="jax-checker",
            description=(
                "Analyze JAX code for common mistakes and gotchas. "
                "Checks for: in-place mutations, side effects in jit, improper random key usage, "
                "dynamic shapes, Python control flow in traced code, missing block_until_ready, "
                "and float64 without config. Returns actionable suggestions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The JAX code to check",
                    }
                },
                "required": ["code"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list-sections":
            category = arguments.get("category")
            result = await list_sections(docs_source, category)
        elif name == "get-documentation":
            section = arguments.get("section", "")
            result = await get_documentation(docs_source, section)
        elif name == "jax-checker":
            code = arguments.get("code", "")
            result = await jax_checker(code)
        else:
            result = f"Unknown tool: {name}"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {e}")]


def main():
    """Run the MCP server."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting JAX MCP server...")
    logger.info(f"Docs source: {docs_source.source_type}")

    asyncio.run(run_server())


async def run_server():
    """Run the stdio server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
