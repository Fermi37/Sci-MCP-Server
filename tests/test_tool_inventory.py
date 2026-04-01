from __future__ import annotations

from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def test_mcp_tool_inventory_matches_supported_contract():
    async def main() -> None:
        server = StdioServerParameters(
            command="uv",
            args=["run", "python", "sci_hub_server.py"],
            cwd=str(ROOT),
            env={"UV_CACHE_DIR": ".uv-cache"},
        )

        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                tool_names = {tool.name for tool in tools_result.tools}

                assert tool_names == {
                    "search_scihub_by_doi",
                    "download_scihub_pdf",
                    "get_paper_metadata",
                }

    anyio.run(main)
