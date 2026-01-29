# Unity MCP tools (tspec-runner)
JP: Unity MCP ツール（tspec-runner）

We add Unity MCP REST/MCP wrapper tools to the tspec MCP server.
JP: tspec MCP サーバに Unity MCP のツールを追加します。

## Prerequisites
- Unity MCP HTTP server exposes `/health` and `/mcp`
- Set environment variables before starting `tspec` MCP server
- Install extras: `pip install -e ".[mcp,unity]"`
JP:
- Unity 側に HTTP エンドポイント（`/health`, `/mcp`）を用意
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- extras を入れる（`pip install -e ".[mcp,unity]"`）

## Environment variables
### MCP HTTP mode (recommended)
- `UNITY_MCP_MODE=mcp-http`
- `UNITY_MCP_MCP_URL` (recommended): e.g. `http://localhost:8080/mcp`
- `UNITY_MCP_ALLOWLIST_HOSTS` (recommended): e.g. `localhost,localhost:8080`
- `UNITY_MCP_AUTH_MODE` (optional): `none` / `bearer` / `token`
- `UNITY_MCP_BEARER_TOKEN` (for bearer)
- `UNITY_MCP_TOKEN_QUERY` (for token)
- `UNITY_MCP_TIMEOUT_MS` (optional): default 10000
- `UNITY_MCP_VERIFY_TLS` (optional): `true` / `false`

### REST compatibility mode
- `UNITY_MCP_BASE_URL` (required): e.g. `http://localhost:7400`
JP: 環境変数は上記の通りです。

## MCP tool names
- `unity.config`
- `unity.health`
- `unity.tool` (MCP HTTP)
- `unity.rpc` (REST)

## Expected endpoints
- `GET /health` -> 200 OK
- `POST /mcp` (Streamable HTTP)

## Quick setup
- install: `pip install -e ".[mcp,unity]"`
- env: `UNITY_MCP_MODE=mcp-http` + `UNITY_MCP_MCP_URL`
- run: `tspec mcp --transport stdio`

## CLI override
You can pass the URL via CLI instead of env vars:
```bash
tspec mcp --transport stdio --unity-mcp-url http://localhost:8080/mcp
```


## JP (original)
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
