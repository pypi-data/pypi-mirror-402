# Android YouTube: open -> screenshot -> exit (smoke)

```tspec
suite:
  name: "android-youtube-smoke"
  tags: [ui, android, appium, youtube, smoke]
  default_timeout_ms: 120000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  appium_server: "http://127.0.0.1:4723"
  device_name: "emulator-5554"
  udid: "emulator-5554"
  youtube_package: "com.google.android.youtube"
  youtube_activity: "com.google.android.youtube.app.honeycomb.Shell$HomeActivity"

cases:
  - id: "YT-SMOKE-001"
    title: "Launch YouTube and take a screenshot"
    steps:
      - do: ui.open_app
        timeout_ms: 120000
        with:
          server_url: "${vars.appium_server}"
          caps:
            platformName: "Android"
            automationName: "UiAutomator2"
            deviceName: "${vars.device_name}"
            udid: "${vars.udid}"
            appPackage: "${vars.youtube_package}"
            appActivity: "${vars.youtube_activity}"
            appWaitPackage: "com.google.android.youtube"
            appWaitActivity: "com.google.android.youtube.*"
            appWaitDuration: 60000
            newCommandTimeout: 180
            noReset: true
            forceAppLaunch: true
            autoGrantPermissions: true
            adbExecTimeout: 120000
            uiautomator2ServerInstallTimeout: 120000
            uiautomator2ServerLaunchTimeout: 120000
            ignoreHiddenApiPolicyError: true
            skipDeviceInitialization: true

      - do: ui.screenshot
        with:
          path: "artifacts/youtube_home.png"

      - do: ui.close
        with: {}
```
