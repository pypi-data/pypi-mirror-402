# Pytest / pytest-html レポート出力

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: reporting-pytest
  title: Pytest / pytest-html レポート出力
  tags:
  - report
  - pytest
  - html
  - junit
  summary: tspec の JSON レポートを pytest-html / junitxml に変換する。
  prerequisites:
  - uv pip install -e '.[report]'
  steps:
  - title: Run と同時に HTML を生成
    body: tspec run <spec> --report out/report.json --pytest-html out/report.html
  - title: 既存 JSON から HTML を生成
    body: tspec pytest-report out/report.json --html out/report.html
  - title: CI向け junitxml
    body: tspec run <spec> --report out/report.json --pytest-junitxml out/report.xml
  troubleshooting:
  - title: pytest-html が無い
    body: 'extras が未導入: uv pip install -e ".[report]"'
  references: []
```
