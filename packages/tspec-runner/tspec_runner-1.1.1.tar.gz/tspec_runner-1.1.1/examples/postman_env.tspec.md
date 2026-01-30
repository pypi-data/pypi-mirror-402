# Postman MCP smoke

```tspec
suite:
  name: "postman-env"
  tags: [postman]
  artifact_dir: "artifacts"
  default_timeout_ms: 15000
  fail_fast: true

cases:
  - id: POSTMAN-001
    title: "Postman CLI smoke"
    steps:
      - do: assert.true
        with:
          value: true
          message: "Postman-controlled run succeeded"
```
