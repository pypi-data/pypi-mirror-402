# Unity MCP 連携マニュアル

```tspec
manual:
  id: unity-mcp
  title: "Unity MCP 連携セットアップ"
  tags: [mcp, unity, integration, setup]
  summary: |
    Unity の HTTP エンドポイントを MCP tool として呼び出すための設定。
  prerequisites:
    - "pip install -e '.[mcp,unity]'"
    - "Unity 側に /health と /rpc の HTTP エンドポイントがあること"
  steps:
    - title: "1) 環境変数を設定"
      body: |
        UNITY_MCP_BASE_URL=http://localhost:7400
        UNITY_MCP_ALLOWLIST_HOSTS=localhost,localhost:7400
        (任意) UNITY_MCP_AUTH_MODE=none|bearer|token
    - title: "2) MCP サーバを起動"
      body: |
        tspec mcp --transport stdio --workdir .
    - title: "3) ツール動作確認"
      body: |
        unity.health
        unity.rpc(method="scene.list", params={})
```
