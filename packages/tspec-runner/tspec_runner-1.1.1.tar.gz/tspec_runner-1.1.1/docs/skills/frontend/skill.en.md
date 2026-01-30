# Frontend Engineering Skill (English)
This folder documents frontend automation skills such as `agent-browser`, Selenium, and Playwright.

## Focus
- Headless browsers, UI backends, screenshot pipelines, and accessibility checks.
- Documenting agent-browser/selenium/playwright configuration tips for Windows/WSL.

## Support members
- UI Automation Engineer (manages selectors, waits, agent-browser integration)
- Accessibility Analyst (verifies alt text, contrast, and compliance)
- Localization QA (confirms English/Japanese manual parity)

## How to use
1. Review this folder when manual/testcase requests involve UI backends.
2. Use the English doc for behavior clarifications and Japanese doc for localization guidance.
3. After test runs, record flaky selectors or timing issues in `docs/Knowledge.md`.

## Notes
- The main summary is in `../frontend_skill.md`.
- `artifacts/agent-browser/agent-browser.log` now records each run, and Postman instructions in `docs/agent_browser_env.*.tspec.md` describe calling `http://127.0.0.1:8765/run` to trigger specs via the MCP HTTP transport.
