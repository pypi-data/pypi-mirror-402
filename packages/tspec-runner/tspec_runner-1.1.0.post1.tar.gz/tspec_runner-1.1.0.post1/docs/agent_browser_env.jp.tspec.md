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
    body: "npm でインストール後、install を実行。\n\nnpm install -g agent-browser\nagent-browser\
      \ install\n\nEN: If install fails on Windows, run the exe directly:\nJP: Windows\
      \ で install が失敗する場合は exe を直接実行する：\n  $env:APPDATA\\\\npm\\\\node_modules\\\\\
      agent-browser\\\\bin\\\\agent-browser-win32-x64.exe install"
  - title: 2) 動作確認
    body: 'CLI の動作確認。


      agent-browser open https://example.com

      agent-browser snapshot

      agent-browser screenshot artifacts/agent-browser/smoke.png

      agent-browser close'
  - title: 3) tspec-runner から使う
    body: "agent-browser backend でサンプルを実行。\n\ntspec run examples/agent_browser_smoke.tspec.md\
      \ --backend agent-browser --report out/agent-browser.json\n\nEN: If agent-browser\
      \ is not found on Windows, set the binary path:\nJP: Windows で agent-browser\
      \ が見つからない場合は binary を指定する：\n  [agent_browser]\n  binary = \"C:/Users/<user>/AppData/Roaming/npm/node_modules/agent-browser/bin/agent-browser-win32-x64.exe\""
  - title: 4) Windows から WSL 版にフォールバック（任意）
    body: "Windows 側に agent-browser が無い場合、WSL の agent-browser を使う設定例：\n\n  [agent_browser]\n\
      \  wsl_fallback = true\n  wsl_distro = \"Ubuntu\"\n  wsl_workdir = \"/mnt/c/WorkSpace/Private/Python/tspec-runner\"\
      \n\nEN: Run with --config:\nJP: 実行時は --config を指定する：\n  tspec run examples/agent_browser_smoke.tspec.md\
      \ --backend agent-browser --config tspec.toml --report out/agent-browser.json"
  troubleshooting:
  - title: agent-browser が見つからない
    body: PATH が通っていない可能性。npm の global bin を PATH に追加する。
  - title: Daemon failed to start
    body: Windows で CLI が daemon を起動できない場合がある。tspec-runner は内部で protocol 接続にフォールバックする。
  references:
  - 'agent-browser: https://github.com/vercel-labs/agent-browser'
```
