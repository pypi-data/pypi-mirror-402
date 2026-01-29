# agent-browser TestCases
JP: agent-browser テストケース

## Preconditions
- agent-browser installed (npm)
- `pip install -e ".[mcp]"` is optional for MCP usage
JP: agent-browser がインストール済み

## TestCases

### AB-001: open + wait + screenshot
- Goal: basic navigation and screenshot
- Steps: run `examples/agent_browser_smoke.tspec.md`
- Expected: report passes, screenshot saved
JP: 基本動作確認
