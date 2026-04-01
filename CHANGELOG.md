# Changelog

## Unreleased

### Removed

- Removed the public MCP tools `search_scihub_by_title` and `search_scihub_by_keyword`.

### Changed

- Reduced smoke and regression coverage to the supported tool surface: DOI search, metadata retrieval, and PDF download.

## 0.2.0

### Added

- Offline and live GitHub Actions workflows for release validation.
- MCP smoke tests for `initialize`, `tools/list`, DOI search, title search, and PDF download.
- Download validation checks for content type, file signature, and zero-length responses.

### Changed

- Filled DOI search results with `title`, `author`, and `year` metadata more consistently.
- Improved title search by ranking multiple Crossref candidates instead of accepting the first result blindly.
- Expanded Sci-Hub HTML parsing to detect PDF links in `object`, `citation_pdf_url`, and additional fallback patterns.
- Updated the documented server launch path to use direct file execution.
- Standardized the repository runtime contract on Python 3.14.

### Removed

- Removed the stray `main.py` stub from the release path.
