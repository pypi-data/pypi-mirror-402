# Playwright TestCases
Skill: docs/skills/qa_skill.md
JP: Playwright テストケース

## Preconditions
- `pip install -e ".[playwright]"`
- `python -m playwright install chromium`
JP: Playwright extras とブラウザが必要

## TestCases

### PW-001: run spec via Playwright
- Goal: run UI spec with playwright backend
- Steps: `tspec run examples/selenium_google.tspec.md --backend playwright --report out/playwright.json`
- Expected: report passes, screenshot saved (if defined)
JP: Playwright backend の基本動作

### PW-002: allowlist guard
- Goal: prevent unexpected hosts when allowlist is set
- Steps: set `allowlist_hosts = ["example.com"]` and run `ui.open` to other host
- Expected: error about host not allowed
JP: allowlist に無いホストは拒否される


## JP (original)
# Playwright TestCase 仕様

目的: Playwright backend の基本動作と allowlist 制御を確認する。

## Manual / Integration (optional)
- TC-PW-001: `tspec run examples/selenium_google.tspec.md --backend playwright` が完走する
- TC-PW-002: `allowlist_hosts` を設定した場合、許可外の host をブロックする
