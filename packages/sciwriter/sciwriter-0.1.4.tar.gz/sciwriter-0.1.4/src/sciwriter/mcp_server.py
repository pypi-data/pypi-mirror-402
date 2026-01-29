#!/usr/bin/env python3
"""MCP Server for sciwriter - LaTeX Manuscript Compilation.

Provides tools for:
- Compiling LaTeX documents (manuscript, supplementary, revision)
- Checking project status and dependencies
- Cleaning compilation artifacts
- Getting project information
- Background job management for long-running compilations
"""

from __future__ import annotations

import asyncio

# Graceful MCP dependency handling
try:
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    types = None  # type: ignore
    Server = None  # type: ignore
    NotificationOptions = None  # type: ignore
    InitializationOptions = None  # type: ignore
    stdio_server = None  # type: ignore

from sciwriter import __version__

__all__ = ["WriterServer", "main", "MCP_AVAILABLE"]


class WriterServer:
    """MCP Server for LaTeX Manuscript Compilation."""

    def __init__(self):
        self.server = Server("sciwriter")
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP server handlers."""
        from sciwriter._mcp.handlers import (
            citation_handler,
            clean_handler,
            compile_async_handler,
            compile_handler,
            doc_handler,
            figure_handler,
            get_project_info_handler,
            job_handler,
            ref_handler,
            section_handler,
            status_handler,
            table_handler,
            version_handler,
        )
        from sciwriter._mcp.tool_schemas import get_tool_schemas

        @self.server.list_tools()
        async def handle_list_tools():
            return get_tool_schemas()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            # Map tool names to handlers
            handlers = {
                # Project Management
                "status": status_handler,
                "clean": clean_handler,
                "get_project_info": get_project_info_handler,
                # Compilation
                "compile": compile_handler,
                "compile_async": compile_async_handler,
                # Jobs (action-based)
                "job": job_handler,
                # Content CRUD (action-based)
                "section": section_handler,
                "figure": figure_handler,
                "table": table_handler,
                "citation": citation_handler,
                # Document analysis (action-based)
                "doc": doc_handler,
                "ref": ref_handler,
                "version": version_handler,
            }

            handler = handlers.get(name)
            if handler:
                result = await handler(arguments)
                return self._make_result(result)
            else:
                raise ValueError(f"Unknown tool: {name}")

        @self.server.list_resources()
        async def handle_list_resources():
            """List available resources."""
            return [
                types.Resource(
                    uri="sciwriter://help",
                    name="sciwriter Help",
                    description="Usage information for sciwriter",
                    mimeType="text/plain",
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str):
            """Read a resource."""
            if uri == "sciwriter://help":
                help_text = """sciwriter - LaTeX Manuscript Compilation System

Project Management:
  status           - Show project status and check dependencies
  clean            - Clean compilation artifacts
  get_project_info - Get detailed project information

Compilation:
  compile          - Compile LaTeX documents (manuscript, supplementary, revision)
  compile_async    - Start compilation as background job

Job Management (action-based):
  job              - Actions: list, get, cancel, clear

Content Management (action-based):
  section          - Actions: list, read, create, update, delete
  figure           - Actions: list, get, create, update, delete
  table            - Actions: list, get, create, update, delete
  citation         - Actions: list, get, create, update, delete

Document Analysis (action-based):
  doc              - Actions: get_outline, count_words, validate
  ref              - Actions: list, labels
  version          - Actions: list, diff

Usage:
  All tools require a project parameter pointing to a valid sciwriter project.
  Action-based tools use an 'action' parameter to specify the operation.
"""
                return types.TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=help_text,
                )
            else:
                raise ValueError(f"Unknown resource URI: {uri}")

    def _make_result(self, result: str) -> list:
        """Wrap handler result as MCP TextContent."""
        return [
            types.TextContent(
                type="text",
                text=result,
            )
        ]


async def _run_server():
    """Run the MCP server (internal)."""
    server = WriterServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sciwriter",
                server_version=__version__,
                capabilities=server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        import sys

        print("=" * 60)
        print("MCP Server 'sciwriter' requires the 'mcp' package.")
        print()
        print("Install with:")
        print("  pip install mcp")
        print()
        print("Or install sciwriter with MCP support:")
        print("  pip install sciwriter[mcp]")
        print("=" * 60)
        sys.exit(1)

    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
