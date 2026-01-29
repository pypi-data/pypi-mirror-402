# Android / Appium Environment Setup
JP: Android / Appium 環境構築

This file is editable; the manual is in the ` ```tspec ` block.
JP: このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: android-env
  title: "Android/Appium setup"
  tags: [android, appium, setup]
  summary: |
    EN: Set up Appium + Android SDK/emulator for UI automation.
    JP: Appium + Android SDK/エミュレータを準備して UI 自動化を行う。
  prerequisites:
    - "Android SDK / Android Studio"
    - "Appium Server"
  steps:
    - title: "1) Install Appium"
      body: |
        EN: Install Appium and drivers.
        JP: Appium とドライバをインストール。

        npm install -g appium
        appium driver install uiautomator2
    - title: "2) Start Appium Server"
      body: |
        EN: Start the server and check /status.
        JP: サーバ起動と /status 確認。

        appium --address 127.0.0.1 --port 4723
        curl http://127.0.0.1:4723/status
    - title: "3) Start emulator/device"
      body: |
        EN: Launch emulator or connect device.
        JP: エミュレータ起動 or 実機接続。
    - title: "4) Run sample"
      body: |
        EN: Run the YouTube smoke sample.
        JP: YouTube smoke サンプルを実行。

        tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json
  troubleshooting:
    - title: "Appium server unreachable"
      body: |
        EN: Ensure appium is running on 127.0.0.1:4723.
        JP: Appium サーバが起動しているか確認。
```
