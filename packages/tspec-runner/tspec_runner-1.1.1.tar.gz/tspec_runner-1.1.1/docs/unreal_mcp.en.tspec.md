# Unreal Engine MCP setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: unreal-mcp
  title: Unreal Engine MCP setup
  tags:
  - unreal
  - mcp
  - ue
  summary: Run the Unreal Engine MCP server and connect it to an MCP client.
  prerequisites:
  - Unreal Engine 5.5+
  - Python 3.12+
  - uv
  steps:
  - title: 1) Clone repo
    body: |-
      git clone https://github.com/flopperam/unreal-engine-mcp.git
  - title: 2) Enable plugin
    body: |-
      Open `FlopperamUnrealMCP/FlopperamUnrealMCP.uproject` and enable the UnrealMCP plugin.
  - title: 3) Start server
    body: |-
      cd unreal-engine-mcp/Python
      uv run unreal_mcp_server_advanced.py
  - title: 4) Configure MCP client
    body: |-
      Add to your MCP config (Cursor/Claude/Windsurf):

        {
          "mcpServers": {
            "unrealMCP": {
              "command": "uv",
              "args": [
                "--directory",
                "/path/to/unreal-engine-mcp/Python",
                "run",
                "unreal_mcp_server_advanced.py"
              ]
            }
          }
        }
  troubleshooting:
  - title: Server starts but no responses
    body: Ensure Unreal Engine is running with the UnrealMCP plugin enabled and that `uv run unreal_mcp_server_advanced.py` has connected before running health checks.
  - title: uv not found
    body: Install uv or set an absolute path in MCP config.
  references:
  - 'Unreal Engine MCP: https://github.com/flopperam/unreal-engine-mcp'
  - "Skill: docs/skills/game_engine_skill.md"
```
