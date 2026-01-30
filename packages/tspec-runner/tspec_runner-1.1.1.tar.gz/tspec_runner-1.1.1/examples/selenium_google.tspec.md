# Selenium demo: Google search page title

```tspec
suite:
  name: "selenium-google"
  tags: [ui, selenium]
  default_timeout_ms: 20000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  url: "https://www.google.com"

cases:
  - id: "UI-001"
    title: "Open Google and capture text"
    steps:
      - do: ui.open
        with: { url: "${vars.url}" }

      - do: ui.wait_for
        with: { selector: "input[name=q]" }

      - do: ui.get_text
        with: { selector: "title" }
        save: "page_title"

      - do: assert.contains
        with: { text: "${page_title}", substring: "Google" }

      - do: ui.screenshot
        with: { path: "artifacts/google.png" }

      - do: ui.close
        with: {}
```
