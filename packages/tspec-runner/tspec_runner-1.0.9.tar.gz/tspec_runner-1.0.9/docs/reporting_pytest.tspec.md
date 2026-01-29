# pytest reporting manual
JP: pytest レポート生成マニュアル

```tspec
manual:
  id: reporting-pytest
  title: "pytest report generation"
  tags: [report, pytest, html, junit]
  summary: |
    EN: Convert tspec JSON reports into pytest-html / junitxml.
    JP: tspec の JSON レポートを pytest-html / junitxml に変換する。
  prerequisites:
    - "pip install -e '.[report]'"
  steps:
    - title: "1) Run a spec with JSON report"
      body: |
        tspec run examples/assert_only.tspec.md --report out/report.json
    - title: "2) Generate pytest-html / junitxml"
      body: |
        tspec report out/report.json --only-errors --show-steps
        tspec pytest-report out/report.json --html out/report.html
        tspec pytest-report out/report.json --junitxml out/report.xml
```
