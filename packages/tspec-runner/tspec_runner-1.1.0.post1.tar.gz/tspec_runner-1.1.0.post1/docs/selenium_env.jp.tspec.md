# Selenium 環境構築（Chrome中心）

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: selenium-env
  title: Selenium 環境構築（Chrome中心）
  tags:
  - selenium
  - web
  - setup
  summary: Selenium とブラウザドライバを準備して UI 自動化を行う。
  prerequisites:
  - Python 3.10+
  - Chrome or Chromium（推奨）
  steps:
  - title: 1) Python 依存を入れる
    body: 'Python extras をインストール。


      pip install -e ".[selenium]"'
  - title: 2) ブラウザを用意
    body: ドライバを入れて PATH を通す。
  - title: 3) ChromeDriver を用意
    body: 'サンプルを実行。


      tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json'
  - title: 4) 実行オプション（任意）
    body: "`tspec.toml` の `[selenium]` でドライバや起動オプションを上書きできる。\n例：\n  driver_path =\
      \ \"C:/tools/chromedriver.exe\"\n  browser_binary = \"C:/Program Files/Google/Chrome/Application/chrome.exe\"\
      \n  args = [\"--lang=ja-JP\"]\n  prefs = { \"intl.accept_languages\" = \"ja-JP\"\
      \ }\n  download_dir = \"artifacts/downloads\"\n  window_size = \"1280x720\"\n\
      \  auto_wait_ms = 3000\n  page_load_timeout_ms = 30000\n  script_timeout_ms\
      \ = 30000"
  - title: 5) 最小実行（Smoke）
    body: "実行：\n  tspec run examples/selenium_google.tspec.md --backend selenium --report\
      \ out/selenium.json\n\n表示：\n  tspec report out/selenium.json --only-errors --show-steps"
  - title: 6) 環境チェック（doctor）
    body: "Selenium環境の事前チェック：\n  tspec doctor --selenium\n\nNG が出た場合のヒント：\n  tspec\
      \ manual show selenium-env --full"
  troubleshooting:
  - title: chromedriver が見つからない
    body: tspec.toml か PATH を確認。
  - title: 'session not created: This version of ChromeDriver...'
    body: 'Chrome と ChromeDriver のバージョン不一致。

      Chromeのバージョンを確認し、同メジャーのChromeDriverに合わせる。'
  - title: Googleの同意画面などで selector が変わる
    body: 'リダイレクトや地域設定でDOMが変化する。

      - wait_for の selector を頑丈にする

      - 失敗時の鑑識セット（forensics）で page_source / screenshot を確認する'
  references:
  - 'Selenium Documentation: https://www.selenium.dev/documentation/'
  - 'ChromeDriver: https://chromedriver.chromium.org/'
```
