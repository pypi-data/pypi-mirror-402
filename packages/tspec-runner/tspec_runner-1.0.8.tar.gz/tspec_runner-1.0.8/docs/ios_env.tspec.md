# iOS / Appium 環境構築マニュアル（macOS）

このファイルは編集可能です。内容は ` ```tspec ` ブロックに格納されており、
`tspec manual` コマンドで読み込んで表示できます。

```tspec
manual:
  id: ios-env
  title: "iOS + Appium (XCUITest) 環境構築 (macOS)"
  tags: [ios, appium, xcuitest, macos, setup]
  summary: |
    iOSは Android より “署名” と “Xcode” で詰まりやすい。
    まずは Simulator で通してから、実機へ段階的に進める。
  prerequisites:
    - "macOS"
    - "Xcode (App Store)"
    - "Xcode Command Line Tools"
    - "Node.js (Appium Server)"
  steps:
    - title: "1) Xcode と Command Line Tools を導入"
      body: |
        Xcode をインストール後、初回起動してライセンス同意を済ませる。

        CLI で確認：
          xcodebuild -version
          xcrun simctl list devices

        もし xcodebuild が見つからない場合、Command Line Tools を入れる：
          xcode-select --install
    - title: "2) Appium Server と XCUITest ドライバ"
      body: |
        Appium Server：
          npm i -g appium
          appium -v

        iOS driver（XCUITest）：
          appium driver install xcuitest
          appium driver list --installed

        起動：
          appium --address 127.0.0.1 --port 4723
    - title: "3) Simulator を起動して疎通"
      body: |
        まずは Simulator で通す（署名問題を避けられる）。

        起動例：
          open -a Simulator

        デバイス一覧：
          xcrun simctl list devices

        caps 例：
          caps:
            platformName: "iOS"
            automationName: "XCUITest"
            deviceName: "iPhone 15"
            platformVersion: "17.0"
            # app or bundleId を指定
    - title: "4) 実機で動かす（必要な場合）"
      body: |
        実機は “署名” の壁がある。基本は以下が必要：
        - Apple Developer Program
        - Xcode の Signing 設定
        - WebDriverAgent のビルド/署名が通ること

        Appium は WebDriverAgent を使うため、実機では以下がよく必要になる：
          caps:
            xcodeOrgId: "<TEAM_ID>"
            xcodeSigningId: "iPhone Developer"
            updatedWDABundleId: "<あなたのbundle id>"
    - title: "5) TSpec 実行"
      body: |
        python 側（クライアント）：
          pip install -e ".[appium]"

        実行例：
          tspec run examples/ios_smoke.tspec.md --backend appium --report out/ios.json
          tspec report out/ios.json --only-errors --show-steps

        事前チェック：
          tspec doctor --ios
  troubleshooting:
    - title: "xcodebuild が見つからない"
      body: |
        Xcode / Command Line Tools が未導入。
        xcode-select --install を実行し、再度 xcodebuild -version を確認。
    - title: "Simulator が見つからない / deviceName が合わない"
      body: |
        xcrun simctl list devices で正しい名前/OSバージョンを確認して caps に反映。
    - title: "実機で WDA の署名エラー"
      body: |
        Team ID / Signing の設定不足。
        - Apple Developer Program の加入
        - Xcode の Signing 設定
        - updatedWDABundleId の一意性
        が必要。
  references:
    - "Appium XCUITest driver: https://github.com/appium/appium-xcuitest-driver"
    - "Apple Xcode: https://developer.apple.com/xcode/"
```

## 設定/手順まとめ
- Xcode/CLT: `xcodebuild -version` / `xcrun simctl list devices` で確認
- appium: `npm i -g appium` + `appium driver install xcuitest`
- simulator: まず Simulator で動作確認
- run: `pip install -e ".[appium]"` → `tspec run examples/ios_smoke.tspec.md --backend appium --report out/ios.json`
