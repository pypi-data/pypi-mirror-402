# Selenium Environment Setup
JP: Selenium 環境構築

This file is editable; the manual is in the ` ```tspec ` block.
JP: このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: selenium-env
  title: "Selenium setup"
  tags: [selenium, web, setup]
  summary: |
    EN: Install Selenium and browser drivers for UI automation.
    JP: Selenium とブラウザドライバを準備して UI 自動化を行う。
  prerequisites:
    - "Chrome or Firefox"
    - "ChromeDriver / GeckoDriver"
  steps:
    - title: "1) Install Selenium extras"
      body: |
        EN: Install Python extras.
        JP: Python extras をインストール。

        pip install -e ".[selenium]"
    - title: "2) Install driver"
      body: |
        EN: Install the matching driver and add to PATH.
        JP: ドライバを入れて PATH を通す。
    - title: "3) Run sample"
      body: |
        EN: Run a sample spec.
        JP: サンプルを実行。

        tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json
  troubleshooting:
    - title: "Driver not found"
      body: |
        EN: Set driver path in tspec.toml or PATH.
        JP: tspec.toml か PATH を確認。
```
