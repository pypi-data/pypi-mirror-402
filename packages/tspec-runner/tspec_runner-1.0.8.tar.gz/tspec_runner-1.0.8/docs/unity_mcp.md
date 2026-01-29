# Unity MCP tools (tspec-runner)

`tspec-runner` の MCP server に **Unity MCP** の REST エンドポイントをラップしたツール群を追加しました。

## 事前準備
- Unity MCP (HTTP) を起動して `/health` と `/mcp` を公開
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- 連携を使う場合は extras を入れる（`pip install -e ".[mcp,unity]"`）

## 環境変数
### MCP HTTP モード（推奨: Unity MCP）
- `UNITY_MCP_MODE=mcp-http`
- `UNITY_MCP_MCP_URL` (推奨): 例 `http://localhost:8080/mcp`
- `UNITY_MCP_ALLOWLIST_HOSTS` (推奨): 例 `localhost,localhost:8080`
- `UNITY_MCP_AUTH_MODE` (任意): `none` / `bearer` / `token`
- `UNITY_MCP_BEARER_TOKEN` (bearer 用)
- `UNITY_MCP_TOKEN_QUERY` (token クエリ用)
- `UNITY_MCP_TIMEOUT_MS` (任意): default 10000
- `UNITY_MCP_VERIFY_TLS` (任意): `true` / `false`

### REST モード（互換用）
- `UNITY_MCP_BASE_URL` (必須): 例 `http://localhost:7400`
- `UNITY_MCP_ALLOWLIST_HOSTS` (推奨): 例 `localhost,localhost:7400`

## MCP tool 名
- `unity.config`
- `unity.health`
- `unity.tool` (MCP HTTP)
- `unity.rpc` (REST)

## 期待するエンドポイント
- `GET /health` -> 200 OK
- `POST /mcp` (Streamable HTTP)

## 設定/手順まとめ
- install: `pip install -e ".[mcp,unity]"`
- env: `UNITY_MCP_MODE=mcp-http` + `UNITY_MCP_MCP_URL`
- run: `tspec mcp --transport stdio`
