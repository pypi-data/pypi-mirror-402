# Blender MCP manual
JP: Blender MCP 連携マニュアル

```tspec
manual:
  id: blender-mcp
  title: "Blender MCP setup"
  tags: [mcp, blender, integration, setup]
  summary: |
    EN: Configure Blender HTTP endpoints as tspec MCP tools.
    JP: Blender の HTTP エンドポイントを MCP tool として呼び出すための設定。
  prerequisites:
    - "pip install -e '.[mcp,blender]'"
    - "Blender exposes /health and /rpc HTTP endpoints"
    - "blender-mcp is stdio; REST requires a proxy"
  steps:
    - title: "1) Set environment variables"
      body: |
        BLENDER_MCP_BASE_URL=http://localhost:7300
        BLENDER_MCP_ALLOWLIST_HOSTS=localhost,localhost:7300
        (optional) BLENDER_MCP_AUTH_MODE=none|bearer|token
    - title: "2) Start tspec MCP server"
      body: |
        tspec mcp --transport stdio --workdir .
        EN: Optional CLI override:
          tspec mcp --transport stdio --blender-mcp-url http://localhost:7300
    - title: "3) Verify tools"
      body: |
        blender.health
        blender.rpc(method="scene.list", params={})
```
