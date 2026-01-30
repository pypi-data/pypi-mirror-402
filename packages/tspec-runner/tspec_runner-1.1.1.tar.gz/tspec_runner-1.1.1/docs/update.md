# Update notes (English primary)
Skill: docs/skills/release_skill.md
JP: 更新メモ（日本語は下記）

# update.md

## 設定/手順まとめ
- 更新取り込みは `docs/update_script.en.tspec.md` を参照
- 依存更新（推奨: uv）: `uv sync --upgrade`
- PyPI の long_description 切替:
  - 英語: `python scripts/switch_pypi_readme.py --lang en`
  - 日本語: `python scripts/switch_pypi_readme.py --lang jp`
- バージョン更新時は `pyproject.toml` と `src/tspec/__init__.py` を合わせる
- リリース時は `docs/release_notes_<version>.md` を追加


## JP (original)
# update.md

## 設定/手順まとめ
- 更新取り込みは `docs/update_script.jp.tspec.md` を参照
- 依存更新（推奨: uv）: `uv sync --upgrade`
- PyPI の long_description 切替:
  - 英語: `python scripts/switch_pypi_readme.py --lang en`
  - 日本語: `python scripts/switch_pypi_readme.py --lang jp`
- バージョン更新時は `pyproject.toml` と `src/tspec/__init__.py` を合わせる
- リリース時は `docs/release_notes_<version>.md` を追加
