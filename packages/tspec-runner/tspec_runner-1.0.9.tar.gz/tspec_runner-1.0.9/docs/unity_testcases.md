# Unity MCP TestCases
JP: Unity MCP テストケース

## Preconditions
- Unity MCP `/health` and `/mcp` are running
- `UNITY_MCP_MODE=mcp-http` and `UNITY_MCP_MCP_URL` set
- `pip install -e ".[mcp,unity]"`
JP:
- Unity MCP の `/health` と `/mcp` が起動している
- `UNITY_MCP_MODE=mcp-http` と `UNITY_MCP_MCP_URL` を設定済み
- `pip install -e ".[mcp,unity]"`

## TestCases

### UN-MCP-001: config
- Goal: show connection config
- Steps: `unity.config`
- Expected: config fields are shown (tokens redacted)
JP: 接続設定が正しく表示される

### UN-MCP-002: health
- Goal: `/health` reachable
- Steps: `unity.health`
- Expected: `status_code=200` and `ok=true`
JP: `/health` に接続できる

### UN-MCP-003: tool
- Goal: MCP tool call works
- Steps: `unity.tool(name="debug_request_context", arguments={})`
- Expected: Unity MCP response JSON
JP: MCP tool の呼び出しが成功する
