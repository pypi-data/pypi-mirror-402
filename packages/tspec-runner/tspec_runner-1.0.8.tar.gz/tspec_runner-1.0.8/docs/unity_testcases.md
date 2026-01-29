# Unity MCP TestCases

## 前提
- Unity MCP の `/health` と `/mcp` が起動している
- `UNITY_MCP_MODE=mcp-http` と `UNITY_MCP_MCP_URL` を設定済み
- `pip install -e ".[mcp,unity]"`

## TestCase 一覧

### UN-MCP-001: config 表示
- 目的: 接続設定が正しく表示される
- 手順: `unity.config`
- 期待結果: `base_url`, `auth_mode`, `allowlist_hosts` が表示され、トークンは出力されない

### UN-MCP-002: health チェック
- 目的: `/health` に接続できる
- 手順: `unity.health`
- 期待結果: `status_code=200` と `ok=true`

### UN-MCP-003: tool 呼び出し
- 目的: MCP tool が呼び出せる
- 手順: `unity.tool(name="debug_request_context", arguments={})`
- 期待結果: Unity MCP 側のレスポンス JSON が返る
