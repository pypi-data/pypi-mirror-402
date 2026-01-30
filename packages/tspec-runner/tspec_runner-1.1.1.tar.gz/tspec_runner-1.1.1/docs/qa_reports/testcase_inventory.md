# QA Testcase Inventory
Skill: docs/skills/qa/skill.en.md

Generated: 2026-01-19 12:19 UTC

## Summary
- QA confirms each testcase document contains at least one actionable tspec command.
- Files with zero commands are marked for follow-up.

## Files
- ✅ `agent_browser_testcases.md` (9 tspec commands)
  - `pip install -e ".[mcp]"`
  - `examples/agent_browser_smoke.tspec.md`
- ✅ `android_testcases.md` (6 tspec commands)
  - `pip install -e ".[appium]"`
  - `tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json`
- ✅ `blender_testcases.md` (37 tspec commands)
  - `/health`
  - `/rpc`
- ✅ `core_testcases.md` (21 tspec commands)
  - `pip install -e ".[dev]"`
  - `tspec validate examples/assert_only.tspec.md`
- ✅ `playwright_testcases.md` (7 tspec commands)
  - `pip install -e ".[playwright]"`
  - `python -m playwright install chromium`
- ✅ `selenium_testcases.md` (8 tspec commands)
  - `pip install -e ".[selenium]"`
  - `tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json`
- ✅ `unity_testcases.md` (31 tspec commands)
  - `/health`
  - `/mcp`
- ✅ `unreal_testcases.md` (20 tspec commands)
  - `uv`
  - `uv run unreal_mcp_server_advanced.py`

## Next steps
- QA agent assigned to monitor these documents; report new failures in `docs/Knowledge.md`.
- PM to prioritize missing commands before automation.
