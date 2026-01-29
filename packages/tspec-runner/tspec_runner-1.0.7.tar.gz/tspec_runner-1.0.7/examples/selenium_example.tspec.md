# Selenium demo: Example Domain

```tspec
suite:
  name: "selenium-example"
  tags: [ui, selenium]
  default_timeout_ms: 20000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  url: "https://example.com"

cases:
  - id: "UI-EX-001"
    title: "Open Example and capture screenshot"
    steps:
      - do: ui.open
        with: { url: "${vars.url}" }

      - do: ui.wait_for
        with: { selector: "h1", text_contains: "Example" }

      - do: ui.screenshot
        with: { path: "artifacts/selenium-example.png" }

      - do: ui.close
        with: {}
```
