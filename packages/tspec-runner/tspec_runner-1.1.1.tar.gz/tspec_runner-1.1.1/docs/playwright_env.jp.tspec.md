# Playwright 環境構築

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: playwright-env
  title: Playwright 環境構築
  tags:
  - playwright
  - web
  - setup
  summary: Playwright を導入して Playwright backend で UI 自動化を実行する。
  prerequisites:
  - Python 3.11+
  steps:
  - title: 1) Playwright extras を入れる
    body: |-
      pip install -e ".[playwright]"
  - title: 2) ブラウザをインストール
    body: |-
      python -m playwright install chromium
  - title: 3) サンプル実行
    body: |-
      tspec run examples/selenium_google.tspec.md --backend playwright --report out/ui.json
  - title: 4) 任意設定
    body: |-
      `tspec.toml` で browser/args/allowlist を指定できる：

        [playwright]
        browser = "chromium"
        window_size = "1280x720"
        allowlist_hosts = ["example.com", "localhost"]
  troubleshooting:
  - title: ブラウザが未インストール
    body: "python -m playwright install を実行。"
  - title: 実行ファイルが見つからない
    body: "tspec.toml の executable_path を指定するか、再インストールする。"
  references:
  - 'Playwright Python: https://playwright.dev/python/'
  - "Skill: docs/skills/frontend_skill.md"
```
