# pytest report generation

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: reporting-pytest
  title: pytest report generation
  tags:
  - report
  - pytest
  - html
  - junit
  summary: Convert tspec JSON reports into pytest-html / junitxml.
  prerequisites:
  - pip install -e '.[report]'
  steps:
  - title: 1) Run a spec with JSON report
    body: tspec run examples/assert_only.tspec.md --report out/report.json
  - title: 2) Generate pytest-html / junitxml
    body: 'tspec report out/report.json --only-errors --show-steps

      tspec pytest-report out/report.json --html out/report.html

      tspec pytest-report out/report.json --junitxml out/report.xml'
  troubleshooting: []
  references: []
```
