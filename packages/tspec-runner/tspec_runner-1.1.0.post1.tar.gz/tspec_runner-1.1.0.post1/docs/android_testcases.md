# Android (Appium) TestCases
JP: Android (Appium) テストケース

## Preconditions
- Appium server running
- Android emulator/device ready
- Appium extras installed: `pip install -e ".[appium]"`
JP: Appium サーバ起動と実機/エミュレータ準備が必要

## TestCases

### AN-001: YouTube smoke
- Goal: launch YouTube app and capture screenshot
- Steps: `tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json`
- Expected: report passes; screenshot saved
JP: YouTube 起動 + スクリーンショット


## JP (original)
# Android/Appium TestCase 仕様

目的: Appium backend の起動と基本操作が期待通り動作することを確認する。

## Unit Test Cases
- TC-AU-001: ui.open_app で Appium セッションが作成できる
- TC-AU-002: ui.screenshot が PNG を出力できる
- TC-AU-003: ui.close が正常にセッション終了できる

## Manual / Integration (optional)
- TC-AI-001: `tspec run examples/android_youtube_smoke.tspec.md --backend appium` が成功する
- TC-AI-002: `tspec spec --android` で Android/Appium 環境チェックが表示される
- TC-AI-003: `tspec run examples/android_youtube_search_play.tspec.md --backend appium` が成功する（UI 変更時は selector 調整）

## 設定/手順まとめ
- prerequisites: Appium Server, Android SDK, emulator/real device
- run: `tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json`
