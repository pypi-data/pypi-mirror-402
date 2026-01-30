# Unreal Engine MCP (English primary)
Skill: docs/skills/game_engine_skill.md
JP: Unreal Engine MCP（日本語は下記）

This repo integrates the Unreal Engine MCP server maintained by flopperam.
The MCP server runs separately and requires Unreal Engine + the UnrealMCP plugin.

Repo: https://github.com/flopperam/unreal-engine-mcp

## Quick steps (Windows example)
1) Clone the repo
```
git clone https://github.com/flopperam/unreal-engine-mcp.git
```

2) Open the UE project and enable plugin
- Open `FlopperamUnrealMCP/FlopperamUnrealMCP.uproject`
- Ensure the `UnrealMCP` plugin is enabled

3) Start the MCP server
```
cd unreal-engine-mcp/Python
uv run unreal_mcp_server_advanced.py
```

4) Configure your MCP client (Cursor/Claude/Windsurf)
```
{
  "mcpServers": {
    "unrealMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/unreal-engine-mcp/Python",
        "run",
        "unreal_mcp_server_advanced.py"
      ]
    }
  }
}
```

Notes:
- The server communicates with UE via the UnrealMCP plugin.
- If UE is not running, the server will wait or time out.
- For issues, see `DEBUGGING.md` in the repo.


## JP (original)
# Unreal Engine MCP

flopperam の Unreal Engine MCP サーバに対応するための手順メモです。
MCP サーバは別プロセスで起動し、Unreal Engine と UnrealMCP プラグインが必要です。

リポジトリ: https://github.com/flopperam/unreal-engine-mcp

## 手順（Windows例）
1) リポジトリを取得
```
git clone https://github.com/flopperam/unreal-engine-mcp.git
```

2) UE プロジェクトを開いてプラグインを有効化
- `FlopperamUnrealMCP/FlopperamUnrealMCP.uproject` を開く
- `UnrealMCP` プラグインを有効化

3) MCP サーバを起動
```
cd unreal-engine-mcp/Python
uv run unreal_mcp_server_advanced.py
```

4) MCP クライアント設定（Cursor/Claude/Windsurf）
```
{
  "mcpServers": {
    "unrealMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/unreal-engine-mcp/Python",
        "run",
        "unreal_mcp_server_advanced.py"
      ]
    }
  }
}
```

補足:
- UE 側プラグイン経由で通信するため、UE が起動していないと待機またはタイムアウトします。
- 詳細はリポジトリ内 `DEBUGGING.md` を参照してください。
