# MCP overview

```tspec
manual:
  id: mcp
  title: MCP quick reference
  tags:
    - mcp
    - env
  summary: How to start tspec MCP helpers, check supported backends, and visit environment manuals for Blender/Unity/Unreal.
  prerequisites:
    - uv
    - tspec-runner installed with extras (mcp, blender, unity)
  steps:
    - title: Start the tspec MCP server (stdio)
      body: |
        cd <repo>
        tspec mcp --transport stdio
    - title: Start the tspec MCP server (streamable-http, optional)
      body: |
        cd <repo>
        tspec mcp --transport streamable-http --host 127.0.0.1 --port 8765
    - title: Run backend diagnostics
      body: |
        tspec doctor --selenium --android --ios
    - title: Check MCP streamable-http health
      body: |
        tspec doctor --mcp-health --mcp-host 127.0.0.1 --mcp-port 8765
        (EXPECT: HTTP 200 /health on the streamable HTTP port.)
    - title: Confirm agent-browser + uv
      body: |
        tspec doctor
        Look for `agent-browser` and `uv` rows marked OK; if missing, install the CLI or uv runtime.
    - title: Check Unity/Blender/Unreal MCP health
      body: |
        tspec doctor --unity-mcp-health --blender-mcp-health --unreal-mcp-health
        (default ports: Unity=8080, Blender=7300, Unreal=8090)
    - title: Auto-start helper MCP servers via tspec
      body: |
        tspec mcp --transport streamable-http --auto-unreal --auto-unity --auto-blender
        Use `--auto-*-cmd <path>` if you keep helper scripts elsewhere.
    - title: Run specs with auto MCP helpers
      body: |
        tspec run examples/unreal_castle.tspec.md --auto-mcp
        (This launches Unreal/Unity/Blender helper scripts via `uv` before the run.)
    - title: Build a futuristic metropolis
      body: |
        tspec run examples/unreal_city.tspec.md --auto-mcp
        (Futuristic city tool uses `town_size=metropolis` and `architectural_style=futuristic`.)
    - title: Review Blender/Unity/Unreal MCP guides
      body: |
        tspec manual show blender-mcp --lang en
        tspec manual show unity-mcp --lang en
        tspec manual show unreal-mcp --lang en
  troubleshooting:
    - title: Manual lookup still fails for "mcp"
      body: |
        Run `tspec manual list --lang en` to see available manuals. Use an exact id (e.g., `mcp-env`, `blender-mcp`, `unity-mcp`, `unreal-mcp`) or specify the file path.
  references:
  - "Skill: docs/skills/backend_skill.md"
    - 'MCP tools doc: docs/mcp_env.en.tspec.md'
```
