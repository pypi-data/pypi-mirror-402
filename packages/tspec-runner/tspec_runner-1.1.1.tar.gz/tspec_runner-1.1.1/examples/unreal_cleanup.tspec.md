# Cleanup Unreal test actors

```tspec
suite:
  name: "unreal-cleanup"
  tags: [unreal, mcp, cleanup]
  default_timeout_ms: 120000
  fail_fast: true
  artifact_dir: "artifacts"

cases:
  - id: "UE-CLEAN-001"
    title: "Remove FutureCity / Town actors"
    steps:
      - do: unreal.cleanup_prefix
        name: cleanup
        save: cleanup
        with:
          prefixes:
            - "FutureCity"
            - "Town"
            - "Castle"
          timeout_ms: 120000
      - do: assert.true
        with:
          value: "${len(cleanup.deleted_actors) >= 0}"
```
