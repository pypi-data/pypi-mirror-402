# Skill: TSpec Runner Core Operations
This skill summarizes the core `tspec-runner` capabilities, documentation, and diagnostics that the project currently implements.

## Purpose
- Capture how to run the CLI, MCP server, and automation testers (`tspec run`, `tspec mcp`, `tspec doctor`) based on the project docs (`docs/Knowledge.md`, `docs/mcp_env.*`, `docs/unreal_testcases.md`, etc.).
- Provide a single reference for new agents when they need to touch agent-browser, MCP, or CLI tooling.

## Workflow
1. Identify the target backend (agent-browser, selenium, appium, pywinauto, playwright, Unity/Blender/Unreal MCP). Consult `docs/Knowledge.md` and the relevant manual (`docs/mcp_env.en.tspec.md`, `docs/unreal_mcp.*`, etc.) for current status and known issues.
2. When composing a spec or doc change, reference `docs/unreal_testcases.md`, `docs/todo_features.md`, and `docs/FEATURES.md` to keep tracked test cases and roadmap aligned.
3. For release/test validation, refer to `docs/Knowledge.md` entries (e.g., PyPI screenshot, agent-browser, MCP health) and rerun `tspec doctor`/`pytest -q` when necessary.

## Key references
- CLI usage: `README.md` / `README.rst` (from root) and `docs/mcp.tspec.md`.
- MCP environments: `docs/mcp_env.*`, `docs/blender_mcp.*`, `docs/unreal_mcp.*`, `docs/unity_mcp.*`.
- Issue log: `docs/Knowledge.md` and release notes under `docs/release_notes_*.md`.

## Notes
- Last updated: TODO (replace with actual date after next edit).
