# Features ToDo (English primary)
JP: ToDo 一覧（日本語は下記）

# Features ToDo

- [x] Add agent-browser backend
- [x] Document agent-browser settings in tspec.toml / README
- [x] Add agent-browser manual and TestCase specs
- [x] Add agent-browser smoke sample
- [x] Add protocol fallback on Windows when daemon startup fails
- [x] Split README into English/Japanese files
- [x] Add script to switch PyPI long_description language

## Current errors
- [x] Re-run pytest and confirm results (27 passed)
- [x] Complete documentation output tests (manual show/validate/read)
- [x] Add Appium smoke run (YouTube open + screenshot)
- [x] Adjust android_youtube_search_play locators to match current UI structure
- [x] Resolve PyPI README image rendering by switching to reST
- [x] Embed data URI thumbnails in README.rst to address PyPI CSP
- [x] Remove PyPI images and point README.rst to GitHub screenshots
- [x] Add Blender MCP / Unity MCP tools
- [x] Add Blender/Unity MCP specs and TestCase specs
- [x] Add Unity MCP Streamable HTTP (/mcp) tool
- [x] Clear Unity Editor licensing warnings (Hub sign-in/update)
- [x] Recheck Unity Editor access token warning after short run
- [x] Fix Unity MCP TestRunnerService compile error (add com.unity.test-framework)
- [x] Reopen Unity project to resolve packages and recompile
- [x] Verify Unity MCP (HTTP 8080) connect + manage_scene
- [x] Verify Blender MCP GUI Connect + socket response


## JP (original)
# Features ToDo

- [x] agent-browser backend を追加
- [x] agent-browser 設定を tspec.toml / README に追記
- [x] agent-browser マニュアルと TestCase 仕様を追加
- [x] agent-browser smoke サンプルを追加
- [x] Windows で daemon 起動失敗時の protocol フォールバックを追加
- [x] README を英語/日本語に分割
- [x] PyPI long_description 切替スクリプトを追加

## Current errors
- [x] pytest を再実行して結果を確認（27 passed）
- [x] 全ドキュメント出力テスト完了（manual show/validate/read）
- [x] Appium smoke 実行（YouTube 起動 + スクリーンショット）を追加
- [x] android_youtube_search_play の検索/再生手順を UI 構造に合わせて locator 調整
- [x] PyPI の README 画像が表示されない問題を reST に切り替えて解消
- [x] PyPI CSP 対策で README.rst に data URI の縮小画像を埋め込み
- [x] PyPI README 画像を削除し GitHub 参照に切り替え
- [x] Blender MCP / Unity MCP のツールを追加
- [x] Blender/Unity MCP の仕様書と TestCase 仕様を追加
- [x] Unity MCP を Streamable HTTP (/mcp) で呼び出すツールを追加
- [x] Unity Editor のライセンス警告解消（Hub ログイン/更新）
- [x] Unity Editor の短時間起動ログで Access token warning が残るため要再確認
- [x] Unity MCP の TestRunnerService compile error 対応（com.unity.test-framework 追加）
- [x] Unity プロジェクト再起動でパッケージ解決・再コンパイル確認
- [x] Unity MCP (HTTP 8080) の接続と manage_scene 動作確認
- [x] Blender MCP の GUI で Connect 実行 + ソケット応答確認
