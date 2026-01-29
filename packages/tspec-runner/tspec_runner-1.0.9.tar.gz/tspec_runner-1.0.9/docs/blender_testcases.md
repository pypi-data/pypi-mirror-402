# Blender MCP TestCases
JP: Blender MCP テストケース

## Preconditions
- Blender exposes `/health` and `/rpc` HTTP endpoints
- `BLENDER_MCP_BASE_URL` and `BLENDER_MCP_ALLOWLIST_HOSTS` set
- `pip install -e ".[mcp,blender]"`
- blender-mcp (ahujasid) is stdio; REST requires a proxy
JP:
- Blender 側に `/health` と `/rpc` の HTTP エンドポイントがある
- `BLENDER_MCP_BASE_URL` と `BLENDER_MCP_ALLOWLIST_HOSTS` を設定済み
- `pip install -e ".[mcp,blender]"`
- blender-mcp は stdio のため REST 連携にはプロキシが必要

## TestCases

### BL-MCP-001: config
- Goal: show connection config
- Steps: `blender.config`
- Expected: `base_url`, `auth_mode`, `allowlist_hosts` shown; tokens redacted
JP: 接続設定が正しく表示される

### BL-MCP-002: health
- Goal: `/health` reachable
- Steps: `blender.health`
- Expected: `status_code=200` and `ok=true`
JP: `/health` へ接続できる

### BL-MCP-003: rpc
- Goal: `/rpc` accepts method/params
- Steps: `blender.rpc(method="scene.list", params={})`
- Expected: Blender JSON response
JP: `/rpc` に method/params を送れる
