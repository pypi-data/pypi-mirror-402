# TSPEC-Z1 manual
JP: TSPEC-Z1 マニュアル

```tspec
manual:
  id: tspec-z1
  title: "TSPEC-Z1 usage"
  tags: [tspec, z1, decode, decompile]
  summary: |
    EN: Decode/decompile TSPEC-Z1 files for AI handoff.
    JP: TSPEC-Z1 をデコード/デコンパイルして AI への引き渡しに使う。
  prerequisites:
    - "tspec-runner installed"
  steps:
    - title: "1) Decode"
      body: |
        tspec z1-decode docs/selenium_spec.tspecz1 --format text
        tspec z1-decode docs/selenium_spec.tspecz1 --format json
    - title: "2) Decompile"
      body: |
        tspec z1-decompile docs/selenium_spec.tspecz1 --format text
        tspec z1-decompile docs/selenium_spec.tspecz1 --format yaml
```
