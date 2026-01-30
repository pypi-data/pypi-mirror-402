# Unreal Engine MCP 環境構築

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: unreal-mcp
  title: Unreal Engine MCP 環境構築
  tags:
  - unreal
  - mcp
  - ue
  summary: Unreal Engine MCP サーバを起動して MCP クライアントに接続する。
  prerequisites:
  - Unreal Engine 5.5+
  - Python 3.12+
  - uv
  steps:
  - title: 1) リポジトリ取得
    body: |-
      git clone https://github.com/flopperam/unreal-engine-mcp.git
  - title: 2) プラグイン有効化
    body: |-
      `FlopperamUnrealMCP/FlopperamUnrealMCP.uproject` を開き、UnrealMCP プラグインを有効化する。
  - title: 3) サーバ起動
    body: |-
      cd unreal-engine-mcp/Python
      uv run unreal_mcp_server_advanced.py
  - title: 4) MCP クライアント設定
    body: |-
      MCP 設定（Cursor/Claude/Windsurf）に追記:

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
  troubleshooting:
  - title: 起動したが応答がない
    body: Unreal Engine が起動し、UnrealMCP プラグインが有効になっていることを確認。
  - title: uv が見つからない
    body: uv をインストールするか、MCP 設定で絶対パスを指定する。
  references:
  - 'Unreal Engine MCP: https://github.com/flopperam/unreal-engine-mcp'
  - "Skill: docs/skills/game_engine_skill.md"
```
