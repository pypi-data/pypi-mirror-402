# Skill: Release & Packaging
Owns PyPI/GitHub release flow, versioning, and release notes.

## Purpose
- Track version bumps and release notes (`docs/release_notes_*.md`).
- Verify packaging metadata and publish steps for PyPI/GitHub.

## Workflow
1. Confirm `pyproject.toml` version and README/long_description requirements.
2. Update release notes and `docs/Knowledge.md` with publishing outcomes.
3. Validate with `python -m twine check` before upload.

## Notes
- Last synced: TODO.
