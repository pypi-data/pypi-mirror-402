# Unity MCP manual
JP: Unity MCP 連携マニュアル

```tspec
manual:
  id: unity-mcp
  title: "Unity MCP setup"
  tags: [mcp, unity, integration, setup]
  summary: |
    EN: Configure Unity MCP HTTP endpoint as tspec MCP tools.
    JP: Unity の HTTP エンドポイントを MCP tool として呼び出すための設定。
  prerequisites:
    - "pip install -e '.[mcp,unity]'"
    - "Unity MCP HTTP server exposes /health and /mcp"
  steps:
    - title: "1) Set environment variables"
      body: |
        EN:
          UNITY_MCP_MODE=mcp-http
          UNITY_MCP_MCP_URL=http://localhost:8080/mcp
          UNITY_MCP_ALLOWLIST_HOSTS=localhost,localhost:8080
          (optional) UNITY_MCP_AUTH_MODE=none|bearer|token
        JP:
          UNITY_MCP_MODE=mcp-http
          UNITY_MCP_MCP_URL=http://localhost:8080/mcp
          UNITY_MCP_ALLOWLIST_HOSTS=localhost,localhost:8080
          (任意) UNITY_MCP_AUTH_MODE=none|bearer|token
    - title: "2) Start tspec MCP server"
      body: |
        tspec mcp --transport stdio --workdir .
        EN: Optional CLI override:
          tspec mcp --transport stdio --unity-mcp-url http://localhost:8080/mcp
    - title: "3) Verify tools"
      body: |
        unity.health
        unity.tool(name="debug_request_context", arguments={})
```
