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
