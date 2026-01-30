# Android demo: login flow (Appium)

```tspec
suite:
  name: "android-login-demo"
  tags: [ui, android, appium]
  default_timeout_ms: 30000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  appium_server: "http://127.0.0.1:4723"
  device_name: "emulator-5554"          # 実機なら任意名でもOK（環境次第）
  app_package: "com.example.app"         # ←あなたのアプリに変更
  app_activity: ".MainActivity"          # ←あなたのアプリに変更
  username: "demo@example.com"
  password: "password123"

cases:
  - id: "A-LOGIN-001"
    title: "Login success"
    steps:
      - do: ui.open_app
        with:
          server_url: "${vars.appium_server}"
          caps:
            platformName: "Android"
            automationName: "UiAutomator2"
            deviceName: "${vars.device_name}"
            appPackage: "${vars.app_package}"
            appActivity: "${vars.app_activity}"
            newCommandTimeout: 120
            noReset: true

      # 例：AccessibilityId が設定されているなら aid= が最強（壊れにくい）
      - do: ui.wait_for
        with: { selector: "aid=login_username" }
        timeout_ms: 30000

      - do: ui.type
        with: { selector: "aid=login_username", text: "${vars.username}" }

      - do: ui.type
        with: { selector: "aid=login_password", text: "${vars.password}" }

      - do: ui.click
        with: { selector: "aid=login_button" }

      # 成功メッセージ確認
      - do: ui.wait_for
        with: { selector: "aid=home_welcome" }
        timeout_ms: 30000

      - do: ui.get_text
        with: { selector: "aid=home_welcome" }
        save: "welcome_text"

      - do: assert.contains
        with: { text: "${welcome_text}", substring: "Welcome" }

      - do: ui.screenshot
        with: { path: "artifacts/android_login_success.png" }

      - do: ui.close
        with: {}
```