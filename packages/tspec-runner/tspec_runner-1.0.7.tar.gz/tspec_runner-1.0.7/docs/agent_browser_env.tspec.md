# agent-browser 環境構築マニュアル

このファイルは編集可能です。内容は ` ```tspec ` ブロックに格納されており、
`tspec manual` コマンドで読み込んで表示できます。

```tspec
manual:
  id: agent-browser-env
  title: "agent-browser 環境構築"
  tags: [agent-browser, web, headless, setup]
  summary: |
    agent-browser は軽量な headless ブラウザ CLI。
    Selenium を避けたいケースの代替として使える。
  prerequisites:
    - "Node.js (npm)"
  steps:
    - title: "1) agent-browser をインストール"
      body: |
        npm install -g agent-browser
        agent-browser install
        Windows で install が失敗する場合は exe を直接実行する：
          $env:APPDATA\\npm\\node_modules\\agent-browser\\bin\\agent-browser-win32-x64.exe install
    - title: "2) 動作確認"
      body: |
        agent-browser open https://example.com
        agent-browser snapshot
        agent-browser screenshot artifacts/agent-browser/smoke.png
        agent-browser close
    - title: "3) tspec-runner から使う"
      body: |
        tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json
        Windows で agent-browser が見つからない場合は binary を指定する：
          [agent_browser]
          binary = "C:/Users/<user>/AppData/Roaming/npm/node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
    - title: "4) Windows から WSL 版にフォールバック（任意）"
      body: |
        Windows 側に agent-browser が無い場合、WSL の agent-browser を使う設定例：
          [agent_browser]
          wsl_fallback = true
          wsl_distro = "Ubuntu"
          wsl_workdir = "/mnt/c/WorkSpace/Private/Python/tspec-runner"
        実行時は --config を指定する：
          tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --config tspec.toml --report out/agent-browser.json
  troubleshooting:
    - title: "agent-browser が見つからない"
      body: |
        PATH が通っていない可能性。
        npm の global bin を PATH に追加する。
    - title: "Daemon failed to start"
      body: |
        Windows で CLI が daemon を起動できない場合がある。
        tspec-runner は内部で protocol 接続にフォールバックする。
  references:
    - "agent-browser: https://github.com/vercel-labs/agent-browser"
```

## 設定/手順まとめ
- install: `npm install -g agent-browser` → `agent-browser install`（Windows は exe 直叩きも可）
- run: `tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json`
- Windows fallback: `[agent_browser] binary=...` または `wsl_fallback=true`
