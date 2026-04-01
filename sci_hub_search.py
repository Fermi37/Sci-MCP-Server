from __future__ import annotations

import re
import urllib3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"

SCIHUB_MIRRORS = [
    "https://sci-hub.hkvisa.net",
    "https://sci-hub.mksa.top",
    "https://sci-hub.ren",
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ee",
]


@dataclass
class PaperRecord:
    doi: str = ""
    title: str = ""
    author: str = ""
    year: str = ""
    pdf_url: str = ""
    status: str = "not_found"
    mirror: str = ""

    def merge_missing(self, other: "PaperRecord") -> None:
        if not self.title and other.title:
            self.title = other.title
        if not self.author and other.author:
            self.author = other.author
        if not self.year and other.year:
            self.year = other.year
        if not self.pdf_url and other.pdf_url:
            self.pdf_url = other.pdf_url
        if not self.doi and other.doi:
            self.doi = other.doi

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _create_session() -> requests.Session:
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return session


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _looks_like_doi(value: str) -> bool:
    return bool(re.match(r"^10\.\S+/\S+$", (value or "").strip(), re.IGNORECASE))


def _clean_title(value: str) -> str:
    text = _normalize_space(value)
    if not text:
        return ""
    parts = re.split(r"\s+\|\s+", text)
    for part in parts:
        if "sci-hub" not in part.casefold():
            candidate = _normalize_space(part)
            if candidate.casefold() in {"mirror page", "article page", "download page"}:
                return ""
            return candidate
    text = re.sub(r"^\s*sci-hub\s*", "", text, flags=re.IGNORECASE)
    cleaned = _normalize_space(text)
    if cleaned.casefold() in {"mirror page", "article page", "download page"}:
        return ""
    return cleaned


def _meta_contents(soup: BeautifulSoup, keys: Iterable[str]) -> list[str]:
    values: list[str] = []
    lowered = {key.casefold() for key in keys}
    for tag in soup.find_all("meta"):
        for attr in ("name", "property", "itemprop", "http-equiv"):
            raw_key = tag.get(attr)
            if raw_key and raw_key.casefold() in lowered:
                content = _normalize_space(tag.get("content", ""))
                if content:
                    values.append(content)
    return values


def _first_meta_content(soup: BeautifulSoup, keys: Iterable[str]) -> str:
    values = _meta_contents(soup, keys)
    return values[0] if values else ""


def _extract_title(soup: BeautifulSoup) -> str:
    candidates = _meta_contents(
        soup,
        [
            "citation_title",
            "dc.title",
            "og:title",
            "twitter:title",
            "title",
        ],
    )
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)
    for candidate in candidates:
        cleaned = _clean_title(candidate)
        if cleaned:
            return cleaned
    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    authors = _meta_contents(
        soup,
        [
            "citation_author",
            "dc.creator",
            "dc.contributor",
            "author",
            "parsely-author",
        ],
    )
    unique: list[str] = []
    for author in authors:
        if author not in unique:
            unique.append(author)
    return ", ".join(unique)


def _extract_year_from_value(value: str) -> str:
    match = re.search(r"(19|20)\d{2}", value or "")
    return match.group(0) if match else ""


def _extract_year(soup: BeautifulSoup) -> str:
    candidates = _meta_contents(
        soup,
        [
            "citation_publication_date",
            "citation_date",
            "dc.date",
            "dc.date.issued",
            "article:published_time",
            "publication_date",
        ],
    )
    for candidate in candidates:
        year = _extract_year_from_value(candidate)
        if year:
            return year
    return ""


def _normalize_pdf_url(url: str, base_url: str) -> str:
    normalized = _normalize_space(url)
    if not normalized:
        return ""
    normalized = normalized.replace("\\/", "/")
    if normalized.startswith("//"):
        normalized = "https:" + normalized
    normalized = urljoin(base_url + "/", normalized)
    return normalized.split("#", 1)[0]


def _extract_pdf_candidates(soup: BeautifulSoup, html: str, base_url: str) -> list[str]:
    candidates: list[str] = []

    def add(candidate: str | None) -> None:
        if not candidate:
            return
        normalized = _normalize_pdf_url(candidate, base_url)
        if ".pdf" not in normalized.casefold():
            return
        if normalized not in candidates:
            candidates.append(normalized)

    for tag_name, attr in (("iframe", "src"), ("embed", "src"), ("object", "data")):
        for tag in soup.find_all(tag_name):
            add(tag.get(attr))

    for candidate in _meta_contents(
        soup,
        [
            "citation_pdf_url",
            "eprints.document_url",
            "wkhealth_pdf_url",
            "pdf_url",
        ],
    ):
        add(candidate)

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if ".pdf" in href.casefold():
            add(href)

    onclick_pattern = re.compile(
        r"(?:location\.href|window\.open)\s*\(\s*['\"]([^'\"]+\.pdf[^'\"]*)['\"]",
        re.IGNORECASE,
    )
    assignment_pattern = re.compile(
        r"location\.href\s*=\s*['\"]([^'\"]+\.pdf[^'\"]*)['\"]",
        re.IGNORECASE,
    )
    for tag in soup.find_all(attrs={"onclick": True}):
        onclick = tag.get("onclick", "")
        for pattern in (onclick_pattern, assignment_pattern):
            match = pattern.search(onclick.replace("\\/", "/"))
            if match:
                add(match.group(1))

    for match in re.findall(r"((?:https?:)?//[^\s\"'<>]+\.pdf(?:\?[^\s\"'<>]*)?)", html, flags=re.IGNORECASE):
        add(match)

    return candidates


def _extract_record_from_html(html: str, mirror: str, doi_hint: str = "") -> PaperRecord:
    soup = BeautifulSoup(html, "html.parser")
    pdf_candidates = _extract_pdf_candidates(soup, html, mirror)
    doi = doi_hint or _first_meta_content(soup, ["citation_doi", "dc.identifier", "doi"])
    record = PaperRecord(
        doi=doi,
        title=_extract_title(soup),
        author=_extract_author(soup),
        year=_extract_year(soup),
        pdf_url=pdf_candidates[0] if pdf_candidates else "",
        mirror=mirror,
    )
    if record.pdf_url:
        record.status = "success"
    return record


def _record_from_crossref_item(item: dict, doi_hint: str = "") -> PaperRecord:
    authors = []
    for author in item.get("author", []) or []:
        given = _normalize_space(author.get("given", ""))
        family = _normalize_space(author.get("family", ""))
        full_name = _normalize_space(" ".join(part for part in (given, family) if part))
        if full_name:
            authors.append(full_name)

    title_values = item.get("title", []) or []
    year = ""
    for key in ("published-print", "published-online", "issued", "created"):
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            year = str(date_parts[0][0])
            break

    return PaperRecord(
        doi=doi_hint or item.get("DOI", ""),
        title=_normalize_space(title_values[0]) if title_values else "",
        author=", ".join(authors),
        year=year,
    )


def _fetch_crossref_work(doi: str) -> PaperRecord:
    response = requests.get(
        f"{CROSSREF_WORKS_URL}/{doi}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    item = response.json()["message"]
    return _record_from_crossref_item(item, doi_hint=doi)


def _search_crossref_candidates(title: str, rows: int = 5) -> list[dict]:
    response = requests.get(
        CROSSREF_WORKS_URL,
        params={"query.title": title, "rows": rows},
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("message", {}).get("items", [])


def _enrich_from_crossref(record: PaperRecord) -> PaperRecord:
    if not record.doi or (record.title and record.author and record.year):
        return record
    try:
        fallback = _fetch_crossref_work(record.doi)
    except Exception:
        return record
    record.merge_missing(fallback)
    return record


def _fetch_from_scihub(identifier: str, doi_hint: str = "") -> PaperRecord:
    session = _create_session()
    default = PaperRecord(doi=doi_hint or identifier)
    for mirror in SCIHUB_MIRRORS:
        try:
            url = f"{mirror}/{identifier}"
            response = session.get(url, timeout=30, allow_redirects=True)
            if response.status_code != 200 or len(response.text) <= 1000:
                continue
            record = _extract_record_from_html(response.text, mirror, doi_hint=doi_hint or identifier)
            if record.pdf_url:
                return _enrich_from_crossref(record)
        except Exception:
            continue
    return default


def search_paper_by_doi(doi: str) -> dict[str, str]:
    record = _fetch_from_scihub(doi, doi_hint=doi)
    if record.pdf_url:
        record.status = "success"
        return record.to_dict()
    return {"doi": doi, "status": "not_found"}


def search_paper_by_title(title: str) -> dict[str, str]:
    try:
        items = _search_crossref_candidates(title, rows=1)
        if items:
            doi = items[0].get("DOI", "")
            if doi:
                result = search_paper_by_doi(doi)
                if result.get("status") == "success":
                    return result
    except Exception as exc:
        print(f"CrossRef search error: {exc}")
    return {"title": title, "status": "not_found"}


def search_papers_by_keyword(keyword: str, num_results: int = 10) -> list[dict[str, str]]:
    papers: list[dict[str, str]] = []
    try:
        response = requests.get(
            CROSSREF_WORKS_URL,
            params={"query": keyword, "rows": num_results},
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        for item in response.json().get("message", {}).get("items", []):
            doi = item.get("DOI")
            if not doi:
                continue
            result = search_paper_by_doi(doi)
            if result.get("status") == "success":
                papers.append(result)
    except Exception as exc:
        print(f"Search error: {exc}")
    return papers


def _candidate_download_url(pdf_url: str) -> str:
    if "download=true" in pdf_url:
        return pdf_url
    separator = "&" if "?" in pdf_url else "?"
    return f"{pdf_url}{separator}download=true"


def download_paper(pdf_url: str, output_path: str) -> bool:
    session = _create_session()
    download_url = _candidate_download_url(pdf_url)
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = session.get(download_url, timeout=60, stream=True)
        if response.status_code == 200:
            with target_path.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_handle.write(chunk)
            return True
    except Exception as exc:
        print(f"Download error: {exc}")
        return False
    return False


if __name__ == "__main__":
    print("Sci-Hub search test\n")
    test_doi = "10.1109/TSMC.2016.2597800"
    result = search_paper_by_doi(test_doi)
    print(result)
    if result.get("status") == "success":
        out = f"paper_{test_doi.replace('/', '_')}.pdf"
        if download_paper(result["pdf_url"], out):
            print(f"Downloaded to: {out}")
        else:
            print("Download failed")
