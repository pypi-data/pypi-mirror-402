# Selenium TestCases
JP: Selenium テストケース

## Preconditions
- Selenium extras installed: `pip install -e ".[selenium]"`
- Driver available (chromedriver/geckodriver)
JP: Selenium をインストール済み

## TestCases

### SE-001: open + screenshot
- Goal: open a page and capture screenshot
- Steps: `tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json`
- Expected: report passes; screenshot saved
JP: ページ表示とスクリーンショット


## JP (original)
# Selenium 強化 TestCase 仕様

目的: Selenium 強化の追加機能が設定・解析・診断で期待通り動作することを確認する。

## Unit Test Cases
- TC-SU-001: selector 解析 (css=) が By=css selector を返す
- TC-SU-002: selector 解析 (xpath=) が By=xpath を返す
- TC-SU-003: selector 解析 (prefix無し) が css selector 扱いになる
- TC-SU-004: window_size 解析 (1280x720) が (1280, 720) を返す
- TC-SU-005: window_size 解析 (invalid) は ValueError を返す
- TC-SU-006: version 抽出 (Chrome/ChromeDriver 出力) の major が取得できる

## Manual / Integration (optional)
- TC-SI-001: `tspec doctor --selenium` で Chrome/ChromeDriver の major 乖離が検出できる
- TC-SI-002: `selenium.args`/`selenium.prefs`/`selenium.download_dir` が起動オプションに反映される

## 設定/手順まとめ
- unit: `pytest -q`
- manual: `tspec doctor --selenium`
