# MCP integration manual (tspec)
JP: MCP 連携マニュアル（AIから tspec を操作する）

This file is editable. The manual is stored in the ` ```tspec ` block and can be shown by `tspec manual`.
JP: このファイルは編集可能で、内容は ` ```tspec ` ブロックに格納されます。

```tspec
manual:
  id: mcp-env
  title: "MCP integration setup"
  tags: [mcp, ai, integration, setup]
  summary: |
    EN: Start tspec-runner as an MCP server and call validate/run/report/manual/doctor from AI clients.
    JP: tspec-runner は MCP Server として起動でき、AI クライアントからツール呼び出しで実行できる。
  prerequisites:
    - "pip install -e '.[mcp]'"
    - "MCP client support (e.g., Claude Desktop)"
  steps:
    - title: "1) Install MCP extras"
      body: |
        pip install -e ".[mcp]"
    - title: "2) Start MCP server (stdio recommended)"
      body: |
        tspec mcp --transport stdio --workdir .
        EN: Optional CLI override for Unity/Blender URLs:
          tspec mcp --transport stdio --unity-mcp-url http://localhost:8080/mcp
          tspec mcp --transport stdio --blender-mcp-url http://localhost:7300
    - title: "3) Inspector check (optional HTTP)"
      body: |
        EN: Start HTTP server:
          tspec mcp --transport streamable-http --workdir . --host 127.0.0.1 --port 8765

        Inspector:
          npx -y @modelcontextprotocol/inspector

        Endpoint: http://127.0.0.1:8765/mcp
    - title: "4) Example tools"
      body: |
        - tspec_validate(path)
        - tspec_run(path, backend, report)
        - tspec_report(report, only_errors, case_id)
        - tspec_manual_show(target)
        - tspec_doctor(android/selenium/ios)
  troubleshooting:
    - title: "MCP import failed"
      body: |
        EN: MCP extras not installed: pip install -e ".[mcp]"
        JP: extras を入れていない：pip install -e ".[mcp]"
    - title: "path must be under workdir"
      body: |
        EN: For safety, only paths under workdir are allowed.
        JP: セキュリティのため workdir 配下のみアクセス可能。
```

## Quick summary
- install: `pip install -e ".[mcp]"`
- run: `tspec mcp --transport stdio --workdir .`
- HTTP: `tspec mcp --transport streamable-http --host 127.0.0.1 --port 8765`
- CLI: `tspec mcp --unity-mcp-url http://localhost:8080/mcp`
JP: 手順の要約は上記です。
