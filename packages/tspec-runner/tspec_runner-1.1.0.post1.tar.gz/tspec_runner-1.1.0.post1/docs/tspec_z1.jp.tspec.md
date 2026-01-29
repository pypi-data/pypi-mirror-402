# TSPEC-Z1 圧縮形式（AI引き渡し用）

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: tspec-z1
  title: TSPEC-Z1 圧縮形式（AI引き渡し用）
  tags:
  - tspec
  - z1
  - decode
  - decompile
  summary: TSPEC-Z1 をデコード/デコンパイルして AI への引き渡しに使う。
  prerequisites: []
  steps:
  - title: 1) 先頭に Z1| を付与
    body: "例:\n  Z1|..."
  - title: 2) 辞書 D{...}
    body: "key=value を ; 区切りで列挙する。\n例:\n  D{p=path;sc=scope;ch=change}"
  - title: 3) ペイロード P{...}
    body: "| 区切りでセクションを分割し、各セクションは TAG:... 形式。\n例:\n  P{SCOPE:...|FILES:...|CHANGES:...}"
  - title: 4) 辞書参照
    body: "@k は辞書参照（k は辞書キー）。\n例:\n  SCOPE:@sc=@se"
  - title: 5) 記号の意味
    body: '# はファイルパス、! は動作要件、+ は追加/変更点、= は値。'
  - title: 6) エスケープ
    body: '| と } は \| と \} にエスケープする。'
  - title: 7) CLI で decode
    body: "構造化データに変換:\n  tspec z1-decode docs/selenium_spec.tspecz1 --format text\n\
      \  tspec z1-decode docs/selenium_spec.tspecz1 --format json\n  tspec z1-decode\
      \ docs/selenium_spec.tspecz1 --format yaml"
  - title: 8) CLI で decompile
    body: "人間可読な展開テキストに変換:\n  tspec z1-decompile docs/selenium_spec.tspecz1 --format\
      \ text\n  tspec z1-decompile docs/selenium_spec.tspecz1 --format json\n  tspec\
      \ z1-decompile docs/selenium_spec.tspecz1 --format yaml"
  troubleshooting: []
  references:
  - README.md の TSPEC-Z1 圧縮（AI引き渡し用）
```
