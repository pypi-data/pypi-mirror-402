@spec: 0.1.0
# windows_notepad_pywinauto.tspec.md
# Windows GUI automation (pywinauto)
# Goal: launch Notepad -> type text -> take screenshot -> close

```tspec
suite:
  name: "windows-notepad-pywinauto"
  tags: [ui, windows, pywinauto]
  default_timeout_ms: 30000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  # 起動するアプリ
  exe: "notepad.exe"

  # pywinauto backend: "uia" 推奨（現代Windowsで安定）
  backend: "uia"

  # メインウィンドウ特定（日本語/英語でタイトルが変わるので正規表現）
  main_title_re: ".*Notepad.*|.*メモ帳.*"

  # ---- selectors（pywinauto backend 側の解釈に合わせて調整）----
  # 多くのGUIで Edit が入力欄
  editor: "control_type=Edit"

cases:
  - id: "WIN-NP-001"
    title: "Launch Notepad, type text, screenshot, close"
    steps:
      - do: ui.open_app
        with:
          backend: "${vars.backend}"
          exe: "${vars.exe}"
          title_re: "${vars.main_title_re}"

      - do: ui.wait_for
        with:
          selector: "${vars.editor}"
        timeout_ms: 30000

      - do: ui.type
        with:
          selector: "${vars.editor}"
          text: |
            Hello from tspec (pywinauto)!
            This is a smoke test.

      - do: ui.screenshot
        with:
          path: "artifacts/notepad.png"

      # 保存ダイアログが出る場合があるので、close は backend 側で
      # "Do you want to save" を自動dismissする実装にしておくと運用が楽
      - do: ui.close
        with: {}
```