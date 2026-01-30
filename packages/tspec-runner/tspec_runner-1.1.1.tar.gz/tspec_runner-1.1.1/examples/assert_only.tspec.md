# Assert only (example)

```tspec
suite:
  name: "assert-only"
  tags: [smoke]
  default_timeout_ms: 15000
  fail_fast: false
  artifact_dir: "artifacts"

vars:
  x: 1

cases:
  - id: "ASSERT-001"
    title: "assert demo"
    steps:
      - do: assert.equals
        with: { left: "a", right: "a" }

      - do: assert.contains
        with: { text: "hello world", substring: "world" }

      - do: assert.matches
        with: { text: "abc-123", regex: "^[a-z]{3}-\\d+$" }

      - do: assert.true
        with: { value: true }
```
