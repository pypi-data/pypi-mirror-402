# MCP 連携 (AI連動) セットアップ

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: mcp-env
  title: MCP 連携 (AI連動) セットアップ
  tags:
  - mcp
  - ai
  - integration
  - setup
  summary: tspec-runner は MCP Server として起動でき、AI クライアントからツール呼び出しで実行できる。
  prerequisites:
  - pip install -e '.[mcp]'
  - AI側が MCP クライアントをサポートしていること
  steps:
  - title: 1) MCP 依存を入れる
    body: pip install -e ".[mcp]"
  - title: 2) MCP サーバを起動（stdio 推奨）
    body: tspec mcp --transport stdio --workdir .
  - title: '3) Inspector で動作確認（任意: HTTP）'
    body: "HTTP で立てる：\n  tspec mcp --transport streamable-http --workdir . --host\
      \ 127.0.0.1 --port 8765\n\nInspector：\n  npx -y @modelcontextprotocol/inspector\n\
      \n接続先： http://127.0.0.1:8765/mcp"
  - title: 4) 代表ツール
    body: '- tspec_validate(path)

      - tspec_run(path, backend, report)

      - tspec_report(report, only_errors, case_id)

      - tspec_manual_show(target)

      - tspec_doctor(android/selenium/ios)'
  troubleshooting:
  - title: MCP が import できない
    body: extras を入れていない：pip install -e ".[mcp]"
  - title: path must be under workdir
    body: セキュリティのため workdir 配下のみアクセス可能。
  references: []
```
