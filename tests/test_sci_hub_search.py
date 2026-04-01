from __future__ import annotations

import sci_hub_search as sh


class FakeResponse:
    def __init__(self, text="", status_code=200, json_data=None, headers=None, content_chunks=None):
        self.text = text
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
        self._content_chunks = content_chunks or []

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size=8192):
        yield from self._content_chunks


def test_extract_record_from_html_supports_meta_and_object_pdf():
    html = """
    <html>
      <head>
        <title>Sci-Hub | Example Paper Title</title>
        <meta name="citation_author" content="Alice Smith" />
        <meta name="citation_author" content="Bob Jones" />
        <meta name="citation_publication_date" content="2021-03-11" />
        <meta name="citation_pdf_url" content="/downloads/example-paper.pdf" />
      </head>
      <body>
        <object data="/downloads/example-paper.pdf"></object>
      </body>
    </html>
    """

    record = sh._extract_record_from_html(html, "https://sci-hub.example", doi_hint="10.1234/example")

    assert record.doi == "10.1234/example"
    assert record.title == "Example Paper Title"
    assert record.author == "Alice Smith, Bob Jones"
    assert record.year == "2021"
    assert record.pdf_url == "https://sci-hub.example/downloads/example-paper.pdf"
    assert record.status == "success"


def test_search_paper_by_doi_backfills_missing_metadata_from_crossref(monkeypatch):
    html = """
    <html>
      <head>
        <title>Sci-Hub | Mirror Page</title>
      </head>
      <body>
        <iframe src="//cdn.example.org/papers/example.pdf#view=Fit"></iframe>
      </body>
    </html>
    """ + (" " * 1200)

    class FakeSession:
        def get(self, url, timeout=30, allow_redirects=True):
            return FakeResponse(text=html, status_code=200)

    def fake_requests_get(url, headers=None, timeout=15, params=None):
        assert url == "https://api.crossref.org/works/10.1234/example"
        return FakeResponse(
            status_code=200,
            json_data={
                "message": {
                    "DOI": "10.1234/example",
                    "title": ["Recovered Title"],
                    "author": [
                        {"given": "Jane", "family": "Doe"},
                        {"given": "John", "family": "Roe"},
                    ],
                    "issued": {"date-parts": [[2019, 6, 1]]},
                }
            },
        )

    monkeypatch.setattr(sh, "_create_session", lambda: FakeSession())
    monkeypatch.setattr(sh.requests, "get", fake_requests_get)

    result = sh.search_paper_by_doi("10.1234/example")

    assert result["status"] == "success"
    assert result["title"] == "Recovered Title"
    assert result["author"] == "Jane Doe, John Roe"
    assert result["year"] == "2019"
    assert result["pdf_url"] == "https://cdn.example.org/papers/example.pdf"


def test_search_paper_by_title_prefers_best_crossref_candidate(monkeypatch):
    monkeypatch.setattr(
        sh,
        "_search_crossref_candidates",
        lambda title, rows=5: [
            {"DOI": "10.0000/wrong", "title": ["Deep Learning"]},
            {
                "DOI": "10.0000/right",
                "title": ["Attention Is All You Need"],
            },
        ],
    )
    monkeypatch.setattr(
        sh,
        "search_paper_by_doi",
        lambda doi: {
            "doi": doi,
            "title": "",
            "author": "A. Author",
            "year": "2017",
            "pdf_url": "https://cdn.example.org/attention.pdf",
            "status": "success",
            "mirror": "https://sci-hub.example",
        },
    )

    result = sh.search_paper_by_title("Attention Is All You Need")

    assert result["status"] == "success"
    assert result["doi"] == "10.0000/right"
    assert result["title"] == "Attention Is All You Need"


def test_search_paper_by_title_rejects_weak_match(monkeypatch):
    monkeypatch.setattr(
        sh,
        "_search_crossref_candidates",
        lambda title, rows=5: [
            {"DOI": "10.0000/wrong", "title": ["Completely Different Paper"]},
            {"DOI": "10.0000/other", "title": ["Another Unrelated Result"]},
        ],
    )

    result = sh.search_paper_by_title("Attention Is All You Need")

    assert result == {"title": "Attention Is All You Need", "status": "not_found"}


def test_search_paper_by_title_retries_next_relevant_candidate(monkeypatch):
    monkeypatch.setattr(
        sh,
        "_search_crossref_candidates",
        lambda title, rows=5: [
            {"DOI": "10.0000/unavailable", "title": ["Attention Is All You Need"]},
            {"DOI": "10.0000/available", "title": ["Attention Is All You Need"]},
        ],
    )

    def fake_search_by_doi(doi):
        if doi == "10.0000/unavailable":
            return {"doi": doi, "status": "not_found"}
        return {
            "doi": doi,
            "title": "Attention Is All You Need",
            "author": "A. Author",
            "year": "2017",
            "pdf_url": "https://cdn.example.org/attention.pdf",
            "status": "success",
            "mirror": "https://sci-hub.example",
        }

    monkeypatch.setattr(sh, "search_paper_by_doi", fake_search_by_doi)

    result = sh.search_paper_by_title("Attention Is All You Need")

    assert result["status"] == "success"
    assert result["doi"] == "10.0000/available"
