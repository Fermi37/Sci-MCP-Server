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
                assert {
                    "search_scihub_by_doi",
                    "search_scihub_by_title",
                    "search_scihub_by_keyword",
                    "download_scihub_pdf",
                    "get_paper_metadata",
                }.issubset(tool_names)

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

                title_result = await session.call_tool(
                    "search_scihub_by_title",
                    {
                        "title": "Efficient Solutions for Discreteness, Drift, and Disturbance (3D) in Electronic Olfaction"
                    },
                )
                title_payload = title_result.structuredContent["result"]
                assert title_result.isError is False
                assert title_payload["status"] == "success"
                assert title_payload["title"]
                assert title_payload["pdf_url"]

                keyword_result = await session.call_tool(
                    "search_scihub_by_keyword",
                    {"keyword": "reinforcement learning", "num_results": 3},
                )
                keyword_payload = keyword_result.structuredContent["result"]
                assert keyword_result.isError is False
                assert isinstance(keyword_payload, list)
                assert keyword_payload
                assert keyword_payload[0]["status"] == "success"
                assert keyword_payload[0]["doi"]
                assert keyword_payload[0]["title"]
                assert keyword_payload[0]["pdf_url"]

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
