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
