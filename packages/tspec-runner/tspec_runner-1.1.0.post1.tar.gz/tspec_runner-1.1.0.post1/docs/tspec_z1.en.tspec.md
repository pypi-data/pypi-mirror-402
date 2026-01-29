# TSPEC-Z1 usage

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: tspec-z1
  title: TSPEC-Z1 usage
  tags:
  - tspec
  - z1
  - decode
  - decompile
  summary: Decode/decompile TSPEC-Z1 files for AI handoff.
  prerequisites:
  - tspec-runner installed
  steps:
  - title: 1) Decode
    body: 'tspec z1-decode docs/selenium_spec.tspecz1 --format text

      tspec z1-decode docs/selenium_spec.tspecz1 --format json'
  - title: 2) Decompile
    body: 'tspec z1-decompile docs/selenium_spec.tspecz1 --format text

      tspec z1-decompile docs/selenium_spec.tspecz1 --format yaml'
  troubleshooting: []
  references:
  - README.md の TSPEC-Z1 圧縮（AI引き渡し用）
```
