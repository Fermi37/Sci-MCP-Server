from __future__ import annotations

import os
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
LIVE_TESTS_ENABLED = os.environ.get("SCIHUB_LIVE_TESTS") == "1"

pytestmark = [
    pytest.mark.live_network,
    pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="set SCIHUB_LIVE_TESTS=1 to run live MCP smoke tests"),
]


def test_mcp_stdio_smoke(tmp_path: Path):
    async def main() -> None:
        output_path = tmp_path / "smoke-download.pdf"
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

                doi_result = await session.call_tool(
                    "search_scihub_by_doi",
                    {"doi": "10.1109/TSMC.2016.2597800"},
                )
                doi_payload = doi_result.structuredContent["result"]
                assert doi_result.isError is False
                assert doi_payload["status"] == "success"
                assert doi_payload["title"]
                assert doi_payload["year"]
                assert doi_payload["pdf_url"]

                metadata_result = await session.call_tool(
                    "get_paper_metadata",
                    {"doi": "10.1109/TSMC.2016.2597800"},
                )
                metadata_payload = metadata_result.structuredContent["result"]
                assert metadata_result.isError is False
                assert metadata_payload["status"] == "success"
                assert metadata_payload["doi"] == "10.1109/TSMC.2016.2597800"
                assert metadata_payload["title"]
                assert metadata_payload["year"]
                assert metadata_payload["pdf_url"]

                download_result = await session.call_tool(
                    "download_scihub_pdf",
                    {"pdf_url": doi_payload["pdf_url"], "output_path": str(output_path)},
                )
                assert download_result.isError is False
                assert output_path.exists()
                assert output_path.stat().st_size > 0

    anyio.run(main)
