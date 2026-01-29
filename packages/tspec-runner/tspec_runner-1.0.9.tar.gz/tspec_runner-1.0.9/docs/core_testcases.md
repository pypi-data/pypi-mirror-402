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
