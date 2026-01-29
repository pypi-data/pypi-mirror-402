# Blender MCP tools (tspec-runner)
JP: Blender MCP ツール（tspec-runner）

We add Blender MCP REST wrapper tools to the tspec MCP server.
JP: tspec MCP サーバに Blender MCP の REST ラッパーツールを追加します。

## Prerequisites
- Provide HTTP endpoints on the Blender side (`/health`, `/rpc`)
- Set environment variables before starting `tspec` MCP server
- Install extras: `pip install -e ".[mcp,blender]"`
JP:
- Blender 側に HTTP エンドポイント（`/health`, `/rpc`）を用意
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- extras を入れる（`pip install -e ".[mcp,blender]"`）

## Environment variables
- `BLENDER_MCP_BASE_URL` (required): e.g. `http://localhost:7300`
- `BLENDER_MCP_ALLOWLIST_HOSTS` (recommended): e.g. `localhost,localhost:7300`
- `BLENDER_MCP_AUTH_MODE` (optional): `none` / `bearer` / `token`
- `BLENDER_MCP_BEARER_TOKEN` (for bearer)
- `BLENDER_MCP_TOKEN_QUERY` (for token)
- `BLENDER_MCP_TIMEOUT_MS` (optional): default 10000
- `BLENDER_MCP_VERIFY_TLS` (optional): `true` / `false`
JP: 各変数は上記の通りです。

## MCP tool names
- `blender.config`
- `blender.health`
- `blender.rpc`

## Expected endpoints
- `GET /health` -> 200 OK
- `POST /rpc` with JSON: `{ "method": "scene.list", "params": {} }`

## Notes about blender-mcp
- `blender-mcp` (ahujasid) is MCP/stdio and does NOT expose `/health` or `/rpc`
- `tspec-runner` `blender.*` tools are REST wrappers
- To use `blender-mcp` as-is, connect to it directly from your MCP client
- To use `tspec-runner`, you need a REST proxy
JP:
- `blender-mcp` (ahujasid) は stdio で動作し、REST API を持ちません
- `tspec-runner` の `blender.*` は REST ラッパーです
- 直接使う場合は MCP クライアントから接続してください

## Quick setup
- install: `pip install -e ".[mcp,blender]"`
- env: `BLENDER_MCP_BASE_URL` + `BLENDER_MCP_ALLOWLIST_HOSTS`
- run: `tspec mcp --transport stdio`

## CLI override
You can pass the URL via CLI instead of env vars:
```bash
tspec mcp --transport stdio --blender-mcp-url http://localhost:7300
```


## JP (original)
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
