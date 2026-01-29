# iOS + Appium (XCUITest) 環境構築 (macOS)

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: ios-env
  title: iOS + Appium (XCUITest) 環境構築 (macOS)
  tags:
  - ios
  - xctest
  - appium
  - setup
  summary: Xcode と Appium を準備して iOS 自動化を行う。
  prerequisites:
  - macOS
  - Xcode (App Store)
  - Xcode Command Line Tools
  - Node.js (Appium Server)
  steps:
  - title: 1) Xcode と Command Line Tools を導入
    body: 'Appium とドライバをインストール。


      npm install -g appium

      appium driver install xcuitest'
  - title: 2) Appium Server と XCUITest ドライバ
    body: サーバ起動と /status 確認。
  - title: 3) Simulator を起動して疎通
    body: iOS サンプルがある場合は実行。
  - title: 4) 実機で動かす（必要な場合）
    body: "実機は “署名” の壁がある。基本は以下が必要：\n- Apple Developer Program\n- Xcode の Signing\
      \ 設定\n- WebDriverAgent のビルド/署名が通ること\n\nAppium は WebDriverAgent を使うため、実機では以下がよく必要になる：\n\
      \  caps:\n    xcodeOrgId: \"<TEAM_ID>\"\n    xcodeSigningId: \"iPhone Developer\"\
      \n    updatedWDABundleId: \"<あなたのbundle id>\""
  - title: 5) TSpec 実行
    body: "python 側（クライアント）：\n  pip install -e \".[appium]\"\n\n実行例：\n  tspec run\
      \ examples/ios_smoke.tspec.md --backend appium --report out/ios.json\n  tspec\
      \ report out/ios.json --only-errors --show-steps\n\n事前チェック：\n  tspec doctor\
      \ --ios"
  troubleshooting:
  - title: xcodebuild が見つからない
    body: 'Xcode / Command Line Tools が未導入。

      xcode-select --install を実行し、再度 xcodebuild -version を確認。'
  - title: Simulator が見つからない / deviceName が合わない
    body: xcrun simctl list devices で正しい名前/OSバージョンを確認して caps に反映。
  - title: 実機で WDA の署名エラー
    body: 'Team ID / Signing の設定不足。

      - Apple Developer Program の加入

      - Xcode の Signing 設定

      - updatedWDABundleId の一意性

      が必要。'
  references:
  - 'Appium XCUITest driver: https://github.com/appium/appium-xcuitest-driver'
  - 'Apple Xcode: https://developer.apple.com/xcode/'
```
