# Unity MCP tools (tspec-runner)

`tspec-runner` の MCP server に **Unity MCP** の REST エンドポイントをラップしたツール群を追加しました。

## 事前準備
- Unity 側に HTTP エンドポイント（`/health`, `/rpc`）を用意
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- 連携を使う場合は extras を入れる（`pip install -e ".[unity]"`）

## 環境変数
- `UNITY_MCP_BASE_URL` (必須): 例 `http://localhost:7400`
- `UNITY_MCP_ALLOWLIST_HOSTS` (推奨): 例 `localhost,localhost:7400`
- `UNITY_MCP_AUTH_MODE` (任意): `none` / `bearer` / `token`
- `UNITY_MCP_BEARER_TOKEN` (bearer 用)
- `UNITY_MCP_TOKEN_QUERY` (token クエリ用)
- `UNITY_MCP_TIMEOUT_MS` (任意): default 10000
- `UNITY_MCP_VERIFY_TLS` (任意): `true` / `false`

## MCP tool 名
- `unity.config`
- `unity.health`
- `unity.rpc`

## 期待するエンドポイント
- `GET /health` -> 200 OK
- `POST /rpc` with JSON: `{ "method": "scene.list", "params": {} }`

## 設定/手順まとめ
- install: `pip install -e ".[mcp,unity]"`
- env: `UNITY_MCP_BASE_URL` + `UNITY_MCP_ALLOWLIST_HOSTS`
- run: `tspec mcp --transport stdio`
