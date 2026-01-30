# Unreal Engine castle creation (MCP)

```tspec
suite:
  name: "unreal-castle-fortress"
  tags: [unreal, mcp, castle]
  default_timeout_ms: 420000
  fail_fast: true
  artifact_dir: "artifacts"

cases:
  - id: "UE-CASTLE-001"
    title: "Create a small medieval castle via Unreal MCP"
    steps:
      - do: unreal.create_castle
        name: build
        save: castle
        timeout_ms: 420000
        with:
          castle_size: "small"
          location: [0.0, 0.0, 0.0]
          name_prefix: "Castle"
          include_siege_weapons: false
          include_village: false
          architectural_style: "medieval"
      - do: assert.true
        with:
          value: "${castle.success}"
          message: "Castle creation failed: ${castle.message}"
```
