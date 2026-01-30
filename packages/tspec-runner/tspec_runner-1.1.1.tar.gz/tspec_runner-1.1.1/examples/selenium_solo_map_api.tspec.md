# Selenium demo: solo-map API page (screenshot evidence)

```tspec
suite:
  name: "selenium-solo-map-api"
  tags: [ui, selenium]
  default_timeout_ms: 30000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  url: "https://api.solo-map.app/"

cases:
  - id: "UI-API-001"
    title: "Open solo-map API and capture screenshot evidence"
    steps:
      - do: ui.open
        with:
          url: "${vars.url}"

      - do: ui.wait_for
        with:
          selector: "body"
        timeout_ms: 30000

      - do: ui.screenshot
        with:
          path: "artifacts/solo-map-api.png"

      - do: ui.close
        with: {}
```