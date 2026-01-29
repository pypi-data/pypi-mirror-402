# TSPEC-Z1 圧縮マニュアル

```tspec
manual:
  id: tspec-z1
  title: "TSPEC-Z1 圧縮形式（AI引き渡し用）"
  tags: [tspec, compression, ai]
  summary: |
    仕様や変更点をAIに渡しやすいよう短くまとめる独自形式。
    復元規則が明示されているため、人手での再展開も可能。
  steps:
    - title: "1) 先頭に Z1| を付与"
      body: |
        例:
          Z1|...
    - title: "2) 辞書 D{...}"
      body: |
        key=value を ; 区切りで列挙する。
        例:
          D{p=path;sc=scope;ch=change}
    - title: "3) ペイロード P{...}"
      body: |
        | 区切りでセクションを分割し、各セクションは TAG:... 形式。
        例:
          P{SCOPE:...|FILES:...|CHANGES:...}
    - title: "4) 辞書参照"
      body: |
        @k は辞書参照（k は辞書キー）。
        例:
          SCOPE:@sc=@se
    - title: "5) 記号の意味"
      body: |
        # はファイルパス、! は動作要件、+ は追加/変更点、= は値。
    - title: "6) エスケープ"
      body: |
        | と } は \| と \} にエスケープする。
    - title: "7) CLI で decode"
      body: |
        構造化データに変換:
          tspec z1-decode docs/selenium_spec.tspecz1 --format text
          tspec z1-decode docs/selenium_spec.tspecz1 --format json
          tspec z1-decode docs/selenium_spec.tspecz1 --format yaml
    - title: "8) CLI で decompile"
      body: |
        人間可読な展開テキストに変換:
          tspec z1-decompile docs/selenium_spec.tspecz1 --format text
          tspec z1-decompile docs/selenium_spec.tspecz1 --format json
          tspec z1-decompile docs/selenium_spec.tspecz1 --format yaml
  references:
    - "README.md の TSPEC-Z1 圧縮（AI引き渡し用）"
```

## 設定/手順まとめ
- decode: `tspec z1-decode docs/selenium_spec.tspecz1 --format text|json|yaml`
- decompile: `tspec z1-decompile docs/selenium_spec.tspecz1 --format text|json|yaml`
