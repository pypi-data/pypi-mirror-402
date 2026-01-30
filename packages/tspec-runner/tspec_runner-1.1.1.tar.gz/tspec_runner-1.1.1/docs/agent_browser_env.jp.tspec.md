# agent-browser 環境構築

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: agent-browser-env
  title: agent-browser 環境構築
  tags:
  - agent-browser
  - web
  - headless
  - setup
  summary: agent-browser は軽量な headless ブラウザ CLI。Selenium を避けたいケースの代替として使える。
  prerequisites:
  - Node.js (npm)
  steps:
  - title: 1) agent-browser をインストール
    body: |
      npm install -g agent-browser
      agent-browser install
  - title: 2) CLI での簡易確認
    body: |
      agent-browser open https://example.com
      agent-browser snapshot
      agent-browser screenshot artifacts/agent-browser/smoke.png
      agent-browser close
  - title: 3) ログとスクリーンショットを収集
    body: |
      tspec-runner は `artifacts/agent-browser/agent-browser.log` に実行ログを吐きます。
      `Run local:` / `Run wsl:` の行を見て daemon 起動や protocol fallback の状態を把握してください。
      スクリーンショットは `artifacts/agent-browser/*.png` に保存され、QA レポートに添付できます。
  - title: 4) tspec-runner から実行
    body: |
      tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json
      tspec run examples/postman_env.tspec.md --report out/postman-agent-browser.json
      (postman_env は UI を使わない Postman CLI 向けの確認用スペックです)
      tspec doctor --agent-browser で UI backend の状態確認ができます。
  - title: 5) 任意: WSL フォールバック
    body: |
      [agent_browser]
      binary = "/mnt/c/Users/<user>/AppData/Roaming/npm/node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
      wsl_fallback = true
      wsl_distro = "Ubuntu"
  - title: 6) Postman から tspec run
    body: |
      tspec mcp --transport streamable-http --host 127.0.0.1 --port 8765
      POST http://127.0.0.1:8765/run
      Headers: Content-Type: application/json
      Body:
      {
        "path": "examples/agent_browser_smoke.tspec.md",
        "backend": "agent-browser",
        "report": "out/postman-agent-browser.json"
      }
  - title: 7) Postman CLI
    body: |
      npm install -g postman-cli
      postman-cli run --collection https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0
      コレクションは MCP `/run` をターゲットにしているので、JSON body を編集して実行したい spec/backend/report を指定してください（agent-browser smoke など）。
  troubleshooting:
  - title: agent-browser が見つからない
    body: PATH に npm の global bin を含める。
  - title: Daemon failed to start
    body: Windows で daemon 起動に失敗する場合は protocol fallback が使われるのでログを参照。
  references:
  - 'agent-browser: https://github.com/vercel-labs/agent-browser'
  - 'ログ: artifacts/agent-browser/agent-browser.log'
  - 'Postman collection: https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0'
  - "Skill: docs/skills/frontend_skill.md"
```
