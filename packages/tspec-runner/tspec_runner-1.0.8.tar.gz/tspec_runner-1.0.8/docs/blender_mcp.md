# Blender MCP tools (tspec-runner)

`tspec-runner` の MCP server に **Blender MCP** の REST エンドポイントをラップしたツール群を追加しました。

## 事前準備
- Blender 側に HTTP エンドポイント（`/health`, `/rpc`）を用意
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- 連携を使う場合は extras を入れる（`pip install -e ".[blender]"`）

## 環境変数
- `BLENDER_MCP_BASE_URL` (必須): 例 `http://localhost:7300`
- `BLENDER_MCP_ALLOWLIST_HOSTS` (推奨): 例 `localhost,localhost:7300`
- `BLENDER_MCP_AUTH_MODE` (任意): `none` / `bearer` / `token`
- `BLENDER_MCP_BEARER_TOKEN` (bearer 用)
- `BLENDER_MCP_TOKEN_QUERY` (token クエリ用)
- `BLENDER_MCP_TIMEOUT_MS` (任意): default 10000
- `BLENDER_MCP_VERIFY_TLS` (任意): `true` / `false`

## MCP tool 名
- `blender.config`
- `blender.health`
- `blender.rpc`

## 期待するエンドポイント
- `GET /health` -> 200 OK
- `POST /rpc` with JSON: `{ "method": "scene.list", "params": {} }`

## blender-mcp との関係
- `blender-mcp` (ahujasid) は MCP/stdio で動作し、`/health` や `/rpc` の HTTP API は持ちません
- `tspec-runner` の `blender.*` ツールは REST ラッパー用です
- `blender-mcp` をそのまま使う場合は、MCP クライアントから直接接続してください
- `tspec-runner` 経由で使う場合は REST プロキシを用意する必要があります

## 設定/手順まとめ
- install: `pip install -e ".[mcp,blender]"`
- env: `BLENDER_MCP_BASE_URL` + `BLENDER_MCP_ALLOWLIST_HOSTS`
- run: `tspec mcp --transport stdio`
