# Core TestCases
JP: コア機能テストケース

## Preconditions
- `pip install -e ".[dev]"`
JP: 開発用 extras が必要

## TestCases

### TC-CORE-001: validate
- Goal: validate a spec
- Steps: `tspec validate examples/assert_only.tspec.md`
- Expected: `OK`
JP: validate の基本動作

### TC-CORE-002: run + report
- Goal: run a spec and read report
- Steps:
  - `tspec run examples/assert_only.tspec.md --report out/report.json`
  - `tspec report out/report.json --only-errors --show-steps`
- Expected: report renders
JP: run と report の基本動作

### TC-NEKO-003: bearer auth
- Goal: bearer header is set
- Steps: run Neko client test
- Expected: Authorization header is `Bearer <token>`
JP: bearer 認証が Authorization ヘッダに反映される

### TC-CORE-004: manual show (lang)
- Goal: manual shows language-specific content
- Steps:
  - `tspec manual show android-env --full --lang en`
  - `tspec manual show android-env --full --lang jp`
- Expected: English vs Japanese titles/summaries are shown
JP: マニュアルの言語切替が反映される

### TC-CORE-005: manual default language (env)
- Goal: default language uses TSPEC_MANUAL_LANG
- Steps:
  - `set TSPEC_MANUAL_LANG=jp` (Windows) / `export TSPEC_MANUAL_LANG=jp`
  - `tspec manual show android-env --full`
- Expected: Japanese manual is displayed
JP: TSPEC_MANUAL_LANG で既定言語が切り替わる


## JP (original)
# Core TestCase 仕様

目的: tspec-runner のコア機能とオプション機能（Neko/Manual）の動作確認を行う。

## Unit Test Cases
- TC-CORE-001: manual id 指定で正しいマニュアルが取得できる
- TC-CORE-002: manual tag 指定で正しいマニュアルが取得できる
- TC-CORE-003: manual path key 指定で正しいマニュアルが取得できる
- TC-CORE-004: agent-browser backend を指定できる（alias も含む）
- TC-CORE-005: manual --lang en/jp が適用される
- TC-CORE-006: TSPEC_MANUAL_LANG の既定言語が適用される
- TC-NEKO-001: Neko base_url 未指定で ValidationError
- TC-NEKO-002: allowlist に無い host が ValidationError
- TC-NEKO-003: bearer 認証が Authorization ヘッダに反映される

## Manual / Integration (optional)
- TC-CORE-006: `tspec manual show android-env --full --lang jp` が日本語を表示する
- TC-CORE-007: `TSPEC_MANUAL_LANG=jp` の場合、`tspec manual show android-env --full` で日本語を表示する

## 設定/手順まとめ
- unit: `pytest -q`
- manual: `tspec manual show <id> --full --lang en/jp`
- env: `TSPEC_MANUAL_LANG=jp` で既定言語を切り替え
