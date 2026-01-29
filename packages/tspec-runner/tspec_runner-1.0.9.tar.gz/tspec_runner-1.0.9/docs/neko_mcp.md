# Neko MCP tools (tspec-runner)
JP: Neko MCP ツール（tspec-runner）

Expose Neko REST API as MCP tools under `neko.*`.
JP: Neko の REST API を MCP ツールとして使えます。

## Prerequisites
- Neko server is reachable
- Install extras: `pip install -e ".[mcp,neko]"`
JP:
- Neko サーバが起動済み
- extras を入れる（`pip install -e ".[mcp,neko]"`）

## Environment variables
- `NEKO_BASE_URL` (required): e.g. `http://localhost:8080`
- `NEKO_ALLOWLIST_HOSTS` (recommended): e.g. `localhost,localhost:8080`
- `NEKO_AUTH_MODE` (optional): `cookie` / `bearer` / `token`
- `NEKO_USERNAME`, `NEKO_PASSWORD` (cookie login)
- `NEKO_BEARER_TOKEN` (bearer)
- `NEKO_TOKEN_QUERY` (token query)
JP: 変数は上記の通りです。

## MCP tool names (examples)
- `neko.config`
- `neko.health`
- `neko.sessions.list`
- `neko.screen.screenshot`

## Quick setup
```bash
pip install -e ".[mcp,neko]"
tspec mcp --transport stdio --workdir .
```
