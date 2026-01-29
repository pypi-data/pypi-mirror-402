# Android + Appium (UiAutomator2) 環境構築 (macOS)

このファイルは編集可能で、内容は ` ```tspec ` ブロックにあります。

```tspec
manual:
  id: android-env
  title: Android + Appium (UiAutomator2) 環境構築 (macOS)
  tags:
  - android
  - appium
  - setup
  summary: Appium + Android SDK/エミュレータを準備して UI 自動化を行う。
  prerequisites:
  - macOS
  - Homebrew (推奨)
  - ネットワーク接続
  steps:
  - title: 1) Android Studio を入れて SDK を用意
    body: 'Appium とドライバをインストール。


      npm install -g appium

      appium driver install uiautomator2'
  - title: 2) 環境変数を設定（zsh）
    body: 'サーバ起動と /status 確認。


      appium --address 127.0.0.1 --port 4723

      curl http://127.0.0.1:4723/status'
  - title: 3) AVD（エミュレータ）を作って起動
    body: エミュレータ起動 or 実機接続。
  - title: 4) Appium 2/3 をインストール
    body: 'YouTube smoke サンプルを実行。


      tspec run examples/android_youtube_smoke.tspec.md --backend appium --report
      out/android_youtube_smoke.json'
  - title: 5) TSpec を実行
    body: "python 側（クライアント）：\n  pip install -e \".[appium]\"\n\n実行：\n  tspec run examples/android_login.tspec.md\
      \ --backend appium --report out/android.json\n  tspec report out/android.json\
      \ --only-errors --show-steps"
  troubleshooting:
  - title: ANDROID_SDK_ROOT が無いと言われる
    body: Appium サーバが起動しているか確認。
  - title: adb devices が空
    body: 'エミュレータを起動していない／実機が未接続。

      emulator -avd <AVD_NAME> または USB デバッグ接続を確認。'
  - title: deviceName と実機/エミュレータが一致しない
    body: "安定させるなら caps に udid を指定：\n  caps:\n    udid: \"emulator-5554\""
  - title: UiAutomator2 の instrumentation が 30000ms で起動しない
    body: "emulator が遅い場合はタイムアウトを延ばす：\n  caps:\n    uiautomator2ServerInstallTimeout:\
      \ 120000\n    uiautomator2ServerLaunchTimeout: 120000"
  - title: hidden_api_policy の設定がタイムアウトする
    body: "端末設定の書き込みが遅い場合は以下を追加：\n  caps:\n    ignoreHiddenApiPolicyError: true\n\
      \    adbExecTimeout: 120000\n    skipDeviceInitialization: true"
  references:
  - 'Android SDK 環境変数: https://developer.android.com/studio/command-line/variables'
```
