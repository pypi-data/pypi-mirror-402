@spec: 0.1.0

# Android YouTube: open -> search -> play -> exit
# Backend: appium (UiAutomator2)
#
# NOTE:
# - YouTube は UI が頻繁に変わるので locator は "contains" を多用して頑丈にしてあります
# - まず「YouTube が起動して前面に来る」ことを保証するため appActivity を確定値にしています

```tspec
suite:
  name: "android-youtube-search-play"
  tags: [ui, android, appium, youtube]
  default_timeout_ms: 60000
  fail_fast: true
  artifact_dir: "artifacts"

vars:
  # Appium server
  appium_server: "http://127.0.0.1:4723"

  # device
  device_name: "emulator-5554"
  udid: "emulator-5554"

  # YouTube
  youtube_package: "com.google.android.youtube"
  # adb resolve-activity --brief com.google.android.youtube で判明した入口
  youtube_activity: "com.google.android.youtube.app.honeycomb.Shell$HomeActivity"

  # search query
  query: "OpenAI"

  # ---------- Robust selectors ----------
  # Search button: top bar search icon (content-desc=検索/Search)
  sel_search_btn: "xpath=//*[@resource-id='com.google.android.youtube:id/menu_item_view' and (@content-desc='検索' or @content-desc='Search')]"

  # Search input: search box edit text
  sel_search_input: "id=com.google.android.youtube:id/search_edit_text"

  # Search suggestions list + first suggestion
  sel_suggest_list: "id=com.google.android.youtube:id/results_recycler_view"
  sel_suggest_first: "xpath=(//*[@resource-id='com.google.android.youtube:id/results_recycler_view']//android.view.ViewGroup[@clickable='true'])[1]"

  # First result: results list first video (content-desc includes 動画を再生/Play)
  sel_first_result: "xpath=(//*[@resource-id='com.google.android.youtube:id/results']//android.view.ViewGroup[contains(@content-desc,'動画を再生') or contains(@content-desc,'Play')])[1]"

  # Player area: watch player container
  sel_player_any: "id=com.google.android.youtube:id/watch_player"

cases:
  - id: "YT-001"
    title: "Launch YouTube, search query, play first result, exit"
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

            # 起動待ちを強める（ホームに戻る/遷移が遅い対策）
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

      # 起動直後の状態を保存（ホーム画面に戻っているか等が一発で分かる）
      - do: ui.screenshot
        with:
          path: "artifacts/after_open.png"

      # 検索アイコン（Search/検索/ID包含に対応）
      - do: ui.wait_for
        with:
          selector: "${vars.sel_search_btn}"
        timeout_ms: 60000

      - do: ui.click
        with:
          selector: "${vars.sel_search_btn}"

      # 検索入力
      - do: ui.wait_for
        with:
          selector: "${vars.sel_search_input}"
        timeout_ms: 60000

      - do: ui.type
        with:
          selector: "${vars.sel_search_input}"
          text: "${vars.query}"

      # サジェスト先頭をクリックして検索実行
      - do: ui.wait_for
        with:
          selector: "${vars.sel_suggest_list}"
        timeout_ms: 60000

      - do: ui.click
        with:
          selector: "${vars.sel_suggest_first}"

      # 結果先頭を再生
      - do: ui.wait_for
        with:
          selector: "id=com.google.android.youtube:id/results"
        timeout_ms: 60000
      - do: ui.wait_for
        with:
          selector: "${vars.sel_first_result}"
        timeout_ms: 60000

      - do: ui.click
        with:
          selector: "${vars.sel_first_result}"

      # プレイヤーが出るまで待つ
      - do: ui.wait_for
        with:
          selector: "${vars.sel_player_any}"
        timeout_ms: 60000

      - do: ui.screenshot
        with:
          path: "artifacts/youtube_playing.png"

      - do: ui.close
        with: {}
```
