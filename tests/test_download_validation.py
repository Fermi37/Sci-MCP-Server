from __future__ import annotations

from pathlib import Path

import sci_hub_search as sh


class FakeResponse:
    def __init__(self, status_code=200, headers=None, chunks=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks or []

    def iter_content(self, chunk_size=8192):
        yield from self._chunks


class FakeSession:
    def __init__(self, response):
        self._response = response

    def get(self, url, timeout=60, stream=True):
        return self._response


def test_download_paper_accepts_pdf_response(monkeypatch, tmp_path: Path):
    response = FakeResponse(
        headers={"content-type": "application/pdf", "content-length": "18"},
        chunks=[b"%PDF-1.4\npayload\n"],
    )
    monkeypatch.setattr(sh, "_create_session", lambda: FakeSession(response))

    output = tmp_path / "paper.pdf"

    assert sh.download_paper("https://example.org/paper.pdf", str(output)) is True
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")


def test_download_paper_rejects_html_body(monkeypatch, tmp_path: Path):
    response = FakeResponse(
        headers={"content-type": "text/html", "content-length": "18"},
        chunks=[b"<html>not a pdf</html>"],
    )
    monkeypatch.setattr(sh, "_create_session", lambda: FakeSession(response))

    output = tmp_path / "paper.pdf"

    assert sh.download_paper("https://example.org/paper.pdf", str(output)) is False
    assert not output.exists()


def test_download_paper_rejects_zero_length(monkeypatch, tmp_path: Path):
    response = FakeResponse(
        headers={"content-type": "application/pdf", "content-length": "0"},
        chunks=[],
    )
    monkeypatch.setattr(sh, "_create_session", lambda: FakeSession(response))

    output = tmp_path / "paper.pdf"

    assert sh.download_paper("https://example.org/paper.pdf", str(output)) is False
    assert not output.exists()
