# QA Skill (English)
Focuses on test cases, release verification, and manual display validation.

## Focus
- Pytest suites, `tspec run`, `tspec report`, manual language checks.
- Capturing flaky errors, health consultancy, and documented troubleshooting.

## Support members
- QA Analyst (designs acceptance tests, regression checks)
- Release Verifier (runs `python -m twine check`, publishes packages)
- Manual Guardian (ensures EN/JP docs stay in sync and languages render correctly)

## How to use
1. QA requests check this folder, then refer to `docs/*_testcases.md`.
2. Document test results and manual discrepancies in `docs/Knowledge.md`.
3. Include support members when additional validation (e.g., PyPI packaging) is required.

## Notes
- Consolidated summary exists in `../qa_skill.md`.
- QA inventory report: `docs/qa_reports/testcase_inventory.md` lists current testcase docs and demonstrates that `scripts/qa_testcase_inventory.py` verifies each file has commands.
- `scripts/auto_verify_assert_only.py` automates the assert_only smoke check plus pytest; run it before releasing if the bug resurfaces.
- Use `tspec postman-run ... --postman-mcp` when QA needs a CLI-driven Postman collection run; the streamable HTTP MCP server is started automatically and terminates after execution.
- `examples/api_solo_map.tspec.md` uses the new `http.request` action to GET `https://api.solo-map.app/`; include this spec in Postman CLI runs to validate the API endpoint without UI automation.
- QA should also exercise the Postman `http://127.0.0.1:8765/run` call documented in `docs/agent_browser_env.*.tspec.md` to confirm `tspec run` triggers work via HTTP.
- The script now also touches the `agent-browser` smoke scenario when the binary exists; failure or absence of that backend is surfaced in the log.
