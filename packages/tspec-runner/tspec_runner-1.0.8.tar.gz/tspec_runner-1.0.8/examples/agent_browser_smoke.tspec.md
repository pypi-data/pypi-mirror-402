# agent-browser smoke

```tspec
suite:
  name: "agent-browser-smoke"
  tags: [ui, agent-browser]
  default_timeout_ms: 15000
  fail_fast: true
  artifact_dir: "artifacts"

cases:
  - id: AB-001
    title: "open + wait + screenshot"
    steps:
      - do: ui.open
        with:
          url: "https://example.com"
      - do: ui.wait_for
        with:
          selector: "h1"
          text_contains: "Example"
          timeout_ms: 10000
      - do: ui.screenshot
        with:
          path: "artifacts/agent-browser/AB-001.png"
      - do: ui.close
```
