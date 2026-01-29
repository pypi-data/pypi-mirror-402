# Android/Appium setup

This file is editable; the manual is in the ` ```tspec ` block.

```tspec
manual:
  id: android-env
  title: Android/Appium setup
  tags:
  - android
  - appium
  - setup
  summary: Set up Appium + Android SDK/emulator for UI automation.
  prerequisites:
  - Android SDK / Android Studio
  - Appium Server
  steps:
  - title: 1) Install Appium
    body: Install Appium and drivers.
  - title: 2) Start Appium Server
    body: Start the server and check /status.
  - title: 3) Start emulator/device
    body: Launch emulator or connect device.
  - title: 4) Run sample
    body: Run the YouTube smoke sample.
  troubleshooting:
  - title: Appium server unreachable
    body: Ensure appium is running on 127.0.0.1:4723.
  references:
  - 'Android SDK 環境変数: https://developer.android.com/studio/command-line/variables'
```
