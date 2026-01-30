# Unreal Engine MCP TestCases
Skill: docs/skills/qa_skill.md
JP: Unreal Engine MCP テストケース

## Preconditions
- Unreal Engine 5.5+ running with UnrealMCP plugin enabled
- `uv` available
JP: UE とプラグイン起動が前提

## TestCases

### UE-001: MCP server start
- Goal: start the MCP server
- Steps: `uv run unreal_mcp_server_advanced.py` (in `unreal-engine-mcp/Python`)
- Expected: server starts and waits for UE connection
JP: サーバ起動確認

### UE-002: MCP client connect
- Goal: MCP client can call tools
- Steps: connect from MCP client (Cursor/Claude/Windsurf) and list tools
- Expected: tools list returned
JP: MCP クライアントでツール一覧取得

### UE-003: Castle creation spec
- Goal: Run the `examples/unreal_castle.tspec.md` spec that calls `unreal.create_castle`.
- Steps: `tspec run examples/unreal_castle.tspec.md`
- Expected: spec finishes with `castle.success == true` and reports the castle message (~769 actors).
JP: `examples/unreal_castle.tspec.md` を実行し、`unreal.create_castle` による城づくりを検証

### UE-004: Futuristic metropolis spec
- Goal: Run `examples/unreal_city.tspec.md` to build a metropolis-style town.
- Steps: `tspec run examples/unreal_city.tspec.md --auto-mcp`
- Expected: spec completes with `city.success == true` and records the futuristic town summary.
JP: `examples/unreal_city.tspec.md` を `--auto-mcp` で実行し、未来都市生成を検証

### UE-005: Cleanup Unreal actors
- Goal: Remove previously created FutureCity/Town/Castle actors.
- Steps: `tspec run examples/unreal_cleanup.tspec.md --auto-mcp`
- Expected: spec catalogs deleted actor names under `cleanup.deleted_actors`.
JP: `examples/unreal_cleanup.tspec.md` を `--auto-mcp` で実行し、作成済みアクターを削除

## JP (original)
# Unreal Engine MCP TestCase 仕様

目的: Unreal Engine MCP サーバの起動と MCP クライアント接続を確認する。

## Manual / Integration (optional)
- TC-UE-001: サーバが起動し、UE から接続できる
- TC-UE-002: MCP クライアントからツールを呼び出せる
- TC-UE-003: `examples/unreal_castle.tspec.md` で `unreal.create_castle` スペックを実行し、城を作りきる
