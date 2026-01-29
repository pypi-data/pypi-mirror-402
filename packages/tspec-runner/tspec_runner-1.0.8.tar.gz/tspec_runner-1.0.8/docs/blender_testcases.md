# Blender MCP TestCases

## 前提
- Blender 側に `/health` と `/rpc` の HTTP エンドポイントがある
- `BLENDER_MCP_BASE_URL` と `BLENDER_MCP_ALLOWLIST_HOSTS` を設定済み
- `pip install -e ".[mcp,blender]"`
- blender-mcp (ahujasid) は stdio のため、REST 連携にはプロキシが必要

## TestCase 一覧

### BL-MCP-001: config 表示
- 目的: 接続設定が正しく表示される
- 手順: `blender.config`
- 期待結果: `base_url`, `auth_mode`, `allowlist_hosts` が表示され、トークンは出力されない

### BL-MCP-002: health チェック
- 目的: `/health` に接続できる
- 手順: `blender.health`
- 期待結果: `status_code=200` と `ok=true`

### BL-MCP-003: rpc 呼び出し
- 目的: `/rpc` に method/params を送れる
- 手順: `blender.rpc(method="scene.list", params={})`
- 期待結果: Blender 側のレスポンス JSON が返る
