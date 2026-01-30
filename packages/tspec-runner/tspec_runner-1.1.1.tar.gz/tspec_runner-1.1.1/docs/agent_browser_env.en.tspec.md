# agent-browser setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: agent-browser-env
  title: agent-browser setup
  tags:
  - agent-browser
  - web
  - headless
  - setup
  summary: agent-browser is a lightweight headless browser CLI. It can be a Selenium
    alternative in simple cases.
  prerequisites:
  - Node.js (npm)
  steps:
  - title: 1) Install agent-browser
    body: |
      npm install -g agent-browser
      agent-browser install
  - title: 2) CLI smoke test
    body: |
      agent-browser open https://example.com
      agent-browser snapshot
      agent-browser screenshot artifacts/agent-browser/smoke.png
      agent-browser close
  - title: 3) Record logs + screenshots
    body: |
      tspec-runner writes every execution line to `artifacts/agent-browser/agent-browser.log`.
      Watch for entries such as `Run local: agent-browser click #selector` and verify daemon startup.
      Screenshots go under `artifacts/agent-browser/*.png`; include them in QA reports.
  - title: 4) Use tspec-runner with agent-browser
    body: |
      tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json
      tspec run examples/postman_env.tspec.md --report out/postman-agent-browser.json
      (postman_env is a UI-free spec for Postman CLI verification; omit UI backend to keep Postman runs lightweight)
      `tspec doctor --agent-browser` (after running `tspec run` once) shows the UI backend status.
  - title: 5) Optional: fallback to WSL
    body: |
      [agent_browser]
      binary = "/mnt/c/Users/<user>/AppData/Roaming/npm/node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
      wsl_fallback = true
      wsl_distro = "Ubuntu"
      tspec run ... --config tspec.toml
  - title: 6) Postman -> tspec run
    body: |
      Start MCP server: `tspec mcp --transport streamable-http --host 127.0.0.1 --port 8765`
      POST `http://127.0.0.1:8765/run` with `Content-Type: application/json`
      Body example:
      {
        "path": "examples/agent_browser_smoke.tspec.md",
        "backend": "agent-browser",
        "report": "out/postman-agent-browser.json"
      }
      Response contains `passed`/`failed` counts and `report` path. Use Postman's environment variables for parameters.
  - title: 7) Postman CLI
    body: |
      npm install -g postman-cli
      postman-cli run --collection https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0
      The collection already targets the MCP `/run` endpoint; edit the JSON body to point at the spec/backend/report you need (e.g., agent-browser smoke).
  troubleshooting:
  - title: agent-browser not found
    body: PATH might be missing npm's global bin.
  - title: Daemon failed to start
    body: The Windows CLI may fail to spawn the daemon; tspec-runner falls back to
      protocol mode.
  references:
  - 'agent-browser: https://github.com/vercel-labs/agent-browser'
  - 'agent-browser log: artifacts/agent-browser/agent-browser.log'
  - 'Postman collection: https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0'
  - "Skill: docs/skills/frontend_skill.md"
```
