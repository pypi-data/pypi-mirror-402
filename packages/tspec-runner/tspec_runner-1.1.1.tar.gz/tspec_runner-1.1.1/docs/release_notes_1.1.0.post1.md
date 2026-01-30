# Release Notes 1.1.0.post1 (English primary)
Skill: docs/skills/release_skill.md
JP: リリースノート（日本語は下記）

## Updates
- PyPI release for 1.1.0.post1 (README.rst long_description)
- Split README into English/Japanese files (`README.md` / `README.ja.md`, plus `.rst`)
- Split manuals into EN/JP files (`*.en.tspec.md` / `*.jp.tspec.md`)
- Manual language selection: `--lang en/jp` + `TSPEC_MANUAL_LANG`
- Added script to switch PyPI long_description (`scripts/switch_pypi_readme.py`)
- Fixed `tspec versions` to report 1.1.0.post1

## Major milestones (since 1.0.0)
- agent-browser backend with Windows protocol fallback
- Selenium/Appium docs, examples, screenshots, and reporting flow
- Blender/Unity MCP integrations + demo assets
- PyPI README rendering improvements and image handling
- Neko MCP integration (optional)

JP:
## 更新内容
- PyPI に 1.1.0.post1 を公開（README.rst を long_description に使用）
- README を英語/日本語で分離（`README.md` / `README.ja.md` + `.rst`）
- マニュアルを EN/JP に分割（`*.en.tspec.md` / `*.jp.tspec.md`）
- マニュアル言語切替: `--lang en/jp` + `TSPEC_MANUAL_LANG`
- PyPI long_description 切替スクリプトを追加（`scripts/switch_pypi_readme.py`）
- `tspec versions` の表示を 1.1.0.post1 に修正

## 主要なマイルストーン（1.0.0 以降）
- agent-browser backend と Windows での protocol フォールバック
- Selenium/Appium のドキュメント、サンプル、スクショ、レポート出力
- Blender/Unity MCP 連携とデモアセット
- PyPI README 表示改善と画像取り扱い
- Neko MCP 連携（任意）
