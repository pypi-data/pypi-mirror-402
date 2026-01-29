# MCP integration setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: mcp-env
  title: MCP integration setup
  tags:
  - mcp
  - ai
  - integration
  - setup
  summary: Start tspec-runner as an MCP server and call validate/run/report/manual/doctor
    from AI clients.
  prerequisites:
  - pip install -e '.[mcp]'
  - MCP client support (e.g., Claude Desktop)
  steps:
  - title: 1) Install MCP extras
    body: pip install -e ".[mcp]"
  - title: 2) Start MCP server (stdio recommended)
    body: "Optional CLI override for Unity/Blender URLs:\n  tspec mcp --transport\
      \ stdio --unity-mcp-url http://localhost:8080/mcp\n  tspec mcp --transport stdio\
      \ --blender-mcp-url http://localhost:7300"
  - title: 3) Inspector check (optional HTTP)
    body: "Start HTTP server:\n  tspec mcp --transport streamable-http --workdir .\
      \ --host 127.0.0.1 --port 8765\n\nInspector:\n  npx -y @modelcontextprotocol/inspector\n\
      \nEndpoint: http://127.0.0.1:8765/mcp"
  - title: 4) Example tools
    body: '- tspec_validate(path)

      - tspec_run(path, backend, report)

      - tspec_report(report, only_errors, case_id)

      - tspec_manual_show(target)

      - tspec_doctor(android/selenium/ios)'
  troubleshooting:
  - title: MCP import failed
    body: 'MCP extras not installed: pip install -e ".[mcp]"'
  - title: path must be under workdir
    body: For safety, only paths under workdir are allowed.
  references: []
```
