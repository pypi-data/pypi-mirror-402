# agent-browser Environment Setup Manual
JP: agent-browser 環境構築マニュアル

This file is editable. The actual manual content is stored in the ` ```tspec ` block and can be displayed via `tspec manual`.
JP: このファイルは編集可能です。内容は ` ```tspec ` ブロックに格納され、`tspec manual` で表示できます。

```tspec
manual:
  id: agent-browser-env
  title: "agent-browser setup"
  tags: [agent-browser, web, headless, setup]
  summary: |
    EN: agent-browser is a lightweight headless browser CLI. It can be a Selenium alternative in simple cases.
    JP: agent-browser は軽量な headless ブラウザ CLI。Selenium を避けたいケースの代替として使える。
  prerequisites:
    - "Node.js (npm)"
  steps:
    - title: "1) Install agent-browser"
      body: |
        EN: Install with npm and run the installer.
        JP: npm でインストール後、install を実行。

        npm install -g agent-browser
        agent-browser install

        EN: If install fails on Windows, run the exe directly:
        JP: Windows で install が失敗する場合は exe を直接実行する：
          $env:APPDATA\\npm\\node_modules\\agent-browser\\bin\\agent-browser-win32-x64.exe install
    - title: "2) Smoke test"
      body: |
        EN: Basic CLI smoke test.
        JP: CLI の動作確認。

        agent-browser open https://example.com
        agent-browser snapshot
        agent-browser screenshot artifacts/agent-browser/smoke.png
        agent-browser close
    - title: "3) Use from tspec-runner"
      body: |
        EN: Run the sample spec with the agent-browser backend.
        JP: agent-browser backend でサンプルを実行。

        tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json

        EN: If agent-browser is not found on Windows, set the binary path:
        JP: Windows で agent-browser が見つからない場合は binary を指定する：
          [agent_browser]
          binary = "C:/Users/<user>/AppData/Roaming/npm/node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
    - title: "4) Optional: fallback to WSL"
      body: |
        EN: If Windows agent-browser is unavailable, use a WSL fallback configuration.
        JP: Windows 側に agent-browser が無い場合、WSL の agent-browser を使う設定例：

          [agent_browser]
          wsl_fallback = true
          wsl_distro = "Ubuntu"
          wsl_workdir = "/mnt/c/WorkSpace/Private/Python/tspec-runner"

        EN: Run with --config:
        JP: 実行時は --config を指定する：
          tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --config tspec.toml --report out/agent-browser.json
  troubleshooting:
    - title: "agent-browser not found"
      body: |
        EN: PATH might be missing npm's global bin.
        JP: PATH が通っていない可能性。npm の global bin を PATH に追加する。
    - title: "Daemon failed to start"
      body: |
        EN: The Windows CLI may fail to spawn the daemon; tspec-runner falls back to protocol mode.
        JP: Windows で CLI が daemon を起動できない場合がある。tspec-runner は内部で protocol 接続にフォールバックする。
  references:
    - "agent-browser: https://github.com/vercel-labs/agent-browser"
```

## Quick summary
- install: `npm install -g agent-browser` -> `agent-browser install` (Windows: exe fallback)
- run: `tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json`
- Windows fallback: `[agent_browser] binary=...` or `wsl_fallback=true`
JP: 手順の要約は上記です。
