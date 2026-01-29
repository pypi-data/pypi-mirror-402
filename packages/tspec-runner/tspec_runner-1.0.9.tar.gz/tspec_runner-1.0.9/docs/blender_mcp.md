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
