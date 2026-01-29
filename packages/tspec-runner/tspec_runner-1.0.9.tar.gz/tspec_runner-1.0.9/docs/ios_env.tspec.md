# iOS / XCUITest Environment Setup
JP: iOS / XCUITest 環境構築

This file is editable; the manual is in the ` ```tspec ` block.
JP: このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: ios-env
  title: "iOS/XCUITest setup"
  tags: [ios, xctest, appium, setup]
  summary: |
    EN: Set up Xcode and Appium for iOS automation.
    JP: Xcode と Appium を準備して iOS 自動化を行う。
  prerequisites:
    - "macOS + Xcode"
    - "Appium Server"
  steps:
    - title: "1) Install Appium"
      body: |
        EN: Install Appium and drivers.
        JP: Appium とドライバをインストール。

        npm install -g appium
        appium driver install xcuitest
    - title: "2) Start Appium Server"
      body: |
        EN: Start the server and check /status.
        JP: サーバ起動と /status 確認。
    - title: "3) Run sample"
      body: |
        EN: Run iOS sample when available.
        JP: iOS サンプルがある場合は実行。
```
