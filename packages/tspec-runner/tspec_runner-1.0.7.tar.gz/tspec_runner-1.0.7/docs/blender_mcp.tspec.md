# Blender MCP 連携マニュアル

```tspec
manual:
  id: blender-mcp
  title: "Blender MCP 連携セットアップ"
  tags: [mcp, blender, integration, setup]
  summary: |
    Blender の HTTP エンドポイントを MCP tool として呼び出すための設定。
  prerequisites:
    - "pip install -e '.[mcp,blender]'"
    - "Blender 側に /health と /rpc の HTTP エンドポイントがあること"
  steps:
    - title: "1) 環境変数を設定"
      body: |
        BLENDER_MCP_BASE_URL=http://localhost:7300
        BLENDER_MCP_ALLOWLIST_HOSTS=localhost,localhost:7300
        (任意) BLENDER_MCP_AUTH_MODE=none|bearer|token
    - title: "2) MCP サーバを起動"
      body: |
        tspec mcp --transport stdio --workdir .
    - title: "3) ツール動作確認"
      body: |
        blender.health
        blender.rpc(method="scene.list", params={})
```
