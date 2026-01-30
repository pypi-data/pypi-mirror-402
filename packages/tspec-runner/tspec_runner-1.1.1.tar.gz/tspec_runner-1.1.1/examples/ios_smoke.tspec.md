# iOS demo (Simulator) - smoke

```tspec
suite:
  name: "ios-smoke"
  tags: [ui, ios, appium]
  default_timeout_ms: 30000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  appium_server: "http://127.0.0.1:4723"

cases:
  - id: "IOS-001"
    title: "Open Settings app (Simulator)"
    steps:
      - do: ui.open_app
        with:
          server_url: "${vars.appium_server}"
          caps:
            platformName: "iOS"
            automationName: "XCUITest"
            deviceName: "iPhone 15"
            platformVersion: "17.0"
            bundleId: "com.apple.Preferences"

      - do: ui.wait_for
        with: { selector: "xpath=//XCUIElementTypeNavigationBar" }
        timeout_ms: 30000

      - do: ui.screenshot
        with: { path: "artifacts/ios_settings.png" }

      - do: ui.close
        with: {}
```
