# Skill: Game Engine MCP Integrations
Describes the game-engine-related automation captured in this repo (Blender/Unity/Unreal MCP) and the supporting documentation/cases.

## Purpose
- Record the current integration points for each engine (Blender, Unity, Unreal) so future agents can quickly understand how to connect, run specs, and clean up generated objects.
- Highlight the relevant docs/manuals/tests (`docs/blender_mcp.*`, `docs/unity_mcp.*`, `docs/unreal_mcp.*`, `docs/unreal_testcases.md`).

## Workflow
1. Determine which engine is targeted (Blender, Unity, Unreal). Open the corresponding manual (`docs/blender_mcp.jp.tspec.md`, etc.) for setup steps, prerequisites, and troubleshooting notes such as Blender requiring UI or Unity licensing status.
2. For specs/tests, run `tspec run examples/unreal_castle.tspec.md`, `tspec run examples/unreal_cleanup.tspec.md`, or other listed cases in `docs/unreal_testcases.md`. Capture artifact paths in `docs/Knowledge.md` if issues occur.
3. When documenting or updating features, note any MCP-specific tools, environment URLs, or health checks (e.g., `tspec doctor --unreal-mcp-health`) so the skill remains current.

## Key considerations
- Blender MCP: requires UI startup with `bpy.ops.blendermcp.start_server()`; refer to `docs/blender_mcp.*` for connection guidance.
- Unity MCP: uses Streamable HTTP `/mcp`, `UNITY_MCP_MODE`, and requires `com.unity.test-framework`; check `docs/unity_mcp.*` and release notes for license steps.
- Unreal MCP: automation is managed via `local_notes/unreal-engine-mcp/Python/unreal_mcp_server_advanced.py` and its helper docs plus the cleanup spec covering `RaceCourse/Town/Castle` prefixes.

## Notes
- Last synced: TODO.
