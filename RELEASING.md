# Releasing

This repository currently uses GitHub source releases.

## Release Inputs

- Release branch: `develop`
- Release version: `0.3.0`
- Release tag: `v0.3.0`
- Release notes source: [CHANGELOG.md](./CHANGELOG.md)

## Pre-release Validation

Run these commands from the repository root:

```bash
git checkout develop
git pull --ff-only
UV_CACHE_DIR=.uv-cache uv run pytest -q
UV_CACHE_DIR=.uv-cache SCIHUB_LIVE_TESTS=1 uv run pytest -q tests/test_mcp_smoke.py
git status --short --branch
```

The working tree must be clean before tagging.
The live smoke suite validates `tools/list`, DOI search, metadata retrieval, and PDF download.

## Tag and Push

```bash
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin develop
git push origin v0.3.0
```

## Create GitHub Release

If `gh` is available:

```bash
gh release create v0.3.0 \
  --title "v0.3.0" \
  --notes-file CHANGELOG.md
```

If the GitHub release is created in the web UI, copy the `0.3.0` section from [CHANGELOG.md](./CHANGELOG.md).

## Release Checklist

1. Confirm [pyproject.toml](./pyproject.toml) version matches the planned tag.
2. Confirm [README.md](./README.md) and [README_CN.md](./README_CN.md) match the runtime requirement.
3. Run the offline test suite, including the offline MCP tool inventory regression.
4. Run the live MCP smoke test suite for DOI search, metadata retrieval, and PDF download.
5. Confirm `git status --short --branch` is clean.
6. Create and push the annotated tag.
7. Publish the GitHub release with the notes from [CHANGELOG.md](./CHANGELOG.md).
