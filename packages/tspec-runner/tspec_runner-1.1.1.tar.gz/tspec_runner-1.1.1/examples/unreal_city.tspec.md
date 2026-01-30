# Unreal future city creation (MCP)

```tspec
suite:
  name: "unreal-future-city"
  tags: [unreal, mcp, city, futuristic]
  default_timeout_ms: 600000
  fail_fast: true
  artifact_dir: "artifacts"

cases:
  - id: "UE-CITY-001"
    title: "Build a futuristic metropolis via Unreal MCP"
    steps:
      - do: unreal.create_city
        name: metropolis
        save: city
        timeout_ms: 1200000
        with:
          town_size: "metropolis"
          building_density: 0.95
          location: [0.0, 0.0, 0.0]
          name_prefix: "FutureCity"
          include_infrastructure: true
          architectural_style: "futuristic"
      - do: assert.true
        with:
          value: "${city.success}"
          message: "Future city creation failed: ${city.message}"
```
