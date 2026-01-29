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
    body: Install with npm and run the installer.
  - title: 2) Smoke test
    body: Basic CLI smoke test.
  - title: 3) Use from tspec-runner
    body: Run the sample spec with the agent-browser backend.
  - title: '4) Optional: fallback to WSL'
    body: If Windows agent-browser is unavailable, use a WSL fallback configuration.
  troubleshooting:
  - title: agent-browser not found
    body: PATH might be missing npm's global bin.
  - title: Daemon failed to start
    body: The Windows CLI may fail to spawn the daemon; tspec-runner falls back to
      protocol mode.
  references:
  - 'agent-browser: https://github.com/vercel-labs/agent-browser'
```
