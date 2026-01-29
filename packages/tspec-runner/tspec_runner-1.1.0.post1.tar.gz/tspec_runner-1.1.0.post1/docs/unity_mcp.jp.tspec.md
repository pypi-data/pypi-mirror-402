# Unity MCP 連携セットアップ

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: unity-mcp
  title: Unity MCP 連携セットアップ
  tags:
  - mcp
  - unity
  - integration
  - setup
  summary: Unity の HTTP エンドポイントを MCP tool として呼び出すための設定。
  prerequisites:
  - pip install -e '.[mcp,unity]'
  - Unity MCP の HTTP サーバ（/health と /mcp）が起動していること
  steps:
  - title: 1) 環境変数を設定
    body: "UNITY_MCP_MODE=mcp-http\n  UNITY_MCP_MCP_URL=http://localhost:8080/mcp\n\
      \  UNITY_MCP_ALLOWLIST_HOSTS=localhost,localhost:8080\n  (任意) UNITY_MCP_AUTH_MODE=none|bearer|token"
  - title: 2) MCP サーバを起動
    body: tspec mcp --transport stdio --workdir .
  - title: 3) ツール動作確認
    body: 'unity.health

      unity.tool(name="debug_request_context", arguments={})'
  troubleshooting: []
  references: []
```
