# Unity MCP TestCases

## 前提
- Unity 側に `/health` と `/rpc` の HTTP エンドポイントがある
- `UNITY_MCP_BASE_URL` と `UNITY_MCP_ALLOWLIST_HOSTS` を設定済み
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

### UN-MCP-003: rpc 呼び出し
- 目的: `/rpc` に method/params を送れる
- 手順: `unity.rpc(method="scene.list", params={})`
- 期待結果: Unity 側のレスポンス JSON が返る
