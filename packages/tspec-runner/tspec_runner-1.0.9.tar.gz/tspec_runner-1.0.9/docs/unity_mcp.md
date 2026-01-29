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
