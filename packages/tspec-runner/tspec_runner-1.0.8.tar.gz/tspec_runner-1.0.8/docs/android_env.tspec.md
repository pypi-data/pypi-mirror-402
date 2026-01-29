# Android / Appium 環境構築マニュアル（macOS）

このファイルは編集可能です。内容は ` ```tspec ` ブロックに格納されており、
`tspec manual` コマンドで読み込んで表示できます。

```tspec
manual:
  id: android-env
  title: "Android + Appium (UiAutomator2) 環境構築 (macOS)"
  tags: [android, appium, macos, setup]
  summary: |
    Appium Server は起動できるが、Android SDK / adb / emulator の不足で詰まるケースが多い。
    本マニュアルは「最短で動かす」ための手順を固定化する。
  prerequisites:
    - "macOS"
    - "Homebrew (推奨)"
    - "ネットワーク接続"
  steps:
    - title: "1) Android Studio を入れて SDK を用意"
      body: |
        - Android Studio をインストールし、SDK を導入する。
        - 典型的な SDK パス: ~/Library/Android/sdk
        - Android Studio > Preferences > Android SDK で確認できる。
    - title: "2) 環境変数を設定（zsh）"
      body: |
        ~/.zshrc に追記：

        export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
        export ANDROID_HOME="$ANDROID_SDK_ROOT"
        export PATH="$ANDROID_SDK_ROOT/platform-tools:$PATH"
        export PATH="$ANDROID_SDK_ROOT/emulator:$PATH"
        export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"

        反映：
          source ~/.zshrc
          hash -r
        確認：
          echo $ANDROID_SDK_ROOT
          which adb
          adb version
    - title: "3) AVD（エミュレータ）を作って起動"
      body: |
        - Android Studio > Device Manager で AVD を作成
        - 起動確認：
          emulator -list-avds
          emulator -avd <AVD_NAME>
        - 端末が見えるか：
          adb devices -l
    - title: "4) Appium 2/3 をインストール"
      body: |
        Node.js が必要：
          brew install node

        Appium Server：
          npm i -g appium
          appium -v

        Android ドライバ（UiAutomator2）：
          appium driver install uiautomator2
          appium driver list --installed

        起動：
          appium --address 127.0.0.1 --port 4723
    - title: "5) TSpec を実行"
      body: |
        python 側（クライアント）：
          pip install -e ".[appium]"

        実行：
          tspec run examples/android_login.tspec.md --backend appium --report out/android.json
          tspec report out/android.json --only-errors --show-steps
  troubleshooting:
    - title: "ANDROID_SDK_ROOT が無いと言われる"
      body: |
        echo $ANDROID_SDK_ROOT が空。~/.zshrc の設定を見直し、source ~/.zshrc を実行。
    - title: "adb devices が空"
      body: |
        エミュレータを起動していない／実機が未接続。
        emulator -avd <AVD_NAME> または USB デバッグ接続を確認。
    - title: "deviceName と実機/エミュレータが一致しない"
      body: |
        安定させるなら caps に udid を指定：
          caps:
            udid: "emulator-5554"
    - title: "UiAutomator2 の instrumentation が 30000ms で起動しない"
      body: |
        emulator が遅い場合はタイムアウトを延ばす：
          caps:
            uiautomator2ServerInstallTimeout: 120000
            uiautomator2ServerLaunchTimeout: 120000
    - title: "hidden_api_policy の設定がタイムアウトする"
      body: |
        端末設定の書き込みが遅い場合は以下を追加：
          caps:
            ignoreHiddenApiPolicyError: true
            adbExecTimeout: 120000
            skipDeviceInitialization: true
  references:
    - "Android SDK 環境変数: https://developer.android.com/studio/command-line/variables"
```

## 設定/手順まとめ
- SDK: Android Studio で SDK を入れ、`ANDROID_SDK_ROOT`/`ANDROID_HOME`/`PATH` を設定
- emulator: AVD を作成して起動、`adb devices -l` で確認
- appium: `npm i -g appium` + `appium driver install uiautomator2`
- run: `pip install -e ".[appium]"` → `tspec run examples/android_login.tspec.md --backend appium --report out/android.json`

## 実行イメージ（YouTube サンプル）
Home:
![android youtube home](assets/android-youtube-home.png)

Search:
![android youtube search](assets/android-youtube-search.png)

Results:
![android youtube results](assets/android-youtube-results.png)

Player:
![android youtube player](assets/android-youtube-player.png)
