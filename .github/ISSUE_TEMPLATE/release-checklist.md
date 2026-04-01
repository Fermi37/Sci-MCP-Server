---
name: Release checklist
about: Track the required steps for cutting a GitHub release
title: "Release v0.2.0"
labels: release
assignees: ""
---

## Release Preparation

- [ ] Confirm `develop` contains the intended release commit.
- [ ] Confirm `pyproject.toml` version matches `v0.2.0`.
- [ ] Confirm `README.md` and `README_CN.md` match the Python runtime requirement.
- [ ] Review the `0.2.0` notes in `CHANGELOG.md`.

## Validation

- [ ] Run `UV_CACHE_DIR=.uv-cache uv run pytest -q`.
- [ ] Run `UV_CACHE_DIR=.uv-cache SCIHUB_LIVE_TESTS=1 uv run pytest -q tests/test_mcp_smoke.py`.
- [ ] Confirm the required CI workflow passed.
- [ ] Confirm the live smoke workflow passed or document the reason it was skipped.
- [ ] Confirm `git status --short --branch` is clean.

## Publish

- [ ] Create annotated tag `v0.2.0`.
- [ ] Push `develop`.
- [ ] Push `v0.2.0`.
- [ ] Create the GitHub release using the notes from `CHANGELOG.md`.
