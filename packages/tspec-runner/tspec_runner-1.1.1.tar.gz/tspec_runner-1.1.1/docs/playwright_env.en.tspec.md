# Playwright setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: playwright-env
  title: Playwright setup
  tags:
  - playwright
  - web
  - setup
  summary: Install Playwright and run UI automation with the Playwright backend.
  prerequisites:
  - Python 3.11+
  steps:
  - title: 1) Install Playwright extras
    body: |-
      pip install -e ".[playwright]"
  - title: 2) Install browsers
    body: |-
      python -m playwright install chromium
  - title: 3) Run a sample
    body: |-
      tspec run examples/selenium_google.tspec.md --backend playwright --report out/ui.json
  - title: 4) Optional config
    body: |-
      Use `tspec.toml` to set browser/args/allowlist:

        [playwright]
        browser = "chromium"
        window_size = "1280x720"
        allowlist_hosts = ["example.com", "localhost"]
  troubleshooting:
  - title: Browser not installed
    body: Run `python -m playwright install`.
  - title: Executable not found
    body: Set `executable_path` in `tspec.toml` or reinstall Playwright browsers.
  references:
  - 'Playwright Python: https://playwright.dev/python/'
  - "Skill: docs/skills/frontend_skill.md"
```
