# Pytest / pytest-html レポート（追加出力）

```tspec
manual:
  id: reporting-pytest
  title: "Pytest / pytest-html レポート出力"
  tags: [report, pytest, pytest-html]
  summary: |
    tspec の既存 JSON レポートはそのまま維持しつつ、必要な場合のみ pytest / pytest-html を使って
    HTML や junitxml を追加出力する。
  prerequisites:
    - "uv pip install -e '.[report]'"
  steps:
    - title: "Run と同時に HTML を生成"
      body: |
        tspec run <spec> --report out/report.json --pytest-html out/report.html
    - title: "既存 JSON から HTML を生成"
      body: |
        tspec pytest-report out/report.json --html out/report.html
    - title: "CI向け junitxml"
      body: |
        tspec run <spec> --report out/report.json --pytest-junitxml out/report.xml
  troubleshooting:
    - title: "pytest-html が無い"
      body: |
        extras が未導入: uv pip install -e ".[report]"
```

## 設定/手順まとめ
- install: `uv pip install -e ".[report]"`
- run + html: `tspec run <spec> --report out/report.json --pytest-html out/report.html`
- json -> html: `tspec pytest-report out/report.json --html out/report.html`
