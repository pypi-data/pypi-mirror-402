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
  - title: 4) Postman からの tspec run
    body: |
      tspec mcp --transport streamable-http --host 127.0.0.1 --port 8765
      POST http://127.0.0.1:8765/run
      Headers: Content-Type: application/json
      Body:
      {
        "path": "examples/assert_only.tspec.md",
        "backend": "selenium",
        "report": "out/postman-agent-browser.json"
      }
      レスポンスには `passed`/`failed`/`report` が含まれます。Postman の環境変数で各値を切り替えられます。
  - title: 5) Postman CLI helper
    body: |
      tspec postman-run https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0 --postman-mcp
      `--postman-arg` で `--env-var baseUrl=http://localhost:3000` のような追加オプションを渡せます。
  - title: SoloMap API への直接確認
    body: |
      `examples/api_solo_map.tspec.md` は `http.request` で https://api.solo-map.app/ を GET するスペックです。
      Postman CLI はコレクションの JSON body に `path=examples/api_solo_map.tspec.md` を指定して `/run` を呼び、API 接続を確認できます。
  - title: 5) 代表ツール
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
  references:
  - "Skill: docs/skills/backend_skill.md"
```
