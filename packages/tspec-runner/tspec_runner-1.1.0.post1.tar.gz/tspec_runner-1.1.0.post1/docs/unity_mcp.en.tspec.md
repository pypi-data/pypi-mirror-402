# Unity MCP setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: unity-mcp
  title: Unity MCP setup
  tags:
  - mcp
  - unity
  - integration
  - setup
  summary: Configure Unity MCP HTTP endpoint as tspec MCP tools.
  prerequisites:
  - pip install -e '.[mcp,unity]'
  - Unity MCP HTTP server exposes /health and /mcp
  steps:
  - title: 1) Set environment variables
    body: "UNITY_MCP_MODE=mcp-http\n  UNITY_MCP_MCP_URL=http://localhost:8080/mcp\n\
      \  UNITY_MCP_ALLOWLIST_HOSTS=localhost,localhost:8080\n  (optional) UNITY_MCP_AUTH_MODE=none|bearer|token"
  - title: 2) Start tspec MCP server
    body: "Optional CLI override:\n  tspec mcp --transport stdio --unity-mcp-url http://localhost:8080/mcp"
  - title: 3) Verify tools
    body: 'unity.health

      unity.tool(name="debug_request_context", arguments={})'
  troubleshooting: []
  references: []
```
