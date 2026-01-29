# Continuation Notes (English primary)
JP: 継続メモ（日本語は下記）

# Continuation Notes

Date: 2026-01-17

Status
- agent-browser backend works on Windows via protocol fallback when CLI daemon fails.
- WSL fallback is optional (use tspec.toml if Windows CLI not available).
- main branch merged with all upgrade branches; main is current default.
- TestPyPI and PyPI release published for 1.0.0.
- docs/ restored from remote main after local disappearance.
- Appium Android smoke example added (YouTube open + screenshot).
- PyPI long description switched to README.rst for image rendering.
- PyPI CSP (img-src self) workaround: embed data URI thumbnails in README.rst.
- PyPI screenshots removed; README.rst points to GitHub for images.
- Blender/Unity MCP tools added (config/health/rpc).
- Repo made public to enable raw GitHub images.
- Unity MCP streamable HTTP tool added (unity.tool).
- Unity MCP debug_request_context call succeeded over /mcp (http://localhost:8090).
- Unity Hub login/update resolved the Editor licensing warning.
- Unity Editor access token warning cleared after ~60s run (log shows token updated).
- Unity Test Framework not in manifest; added com.unity.test-framework=1.4.5, reopen project to resolve.
- Unity batch recompile completed without TestRunnerService errors.
- Unity MCP HTTP 8080 verified (instances + manage_scene get_hierarchy).
- Unity MCP demo captured (GIF) and added to README.
- Unity MCP prefab demo captured (GIF) and added to README.
- Blender MCP viewport screenshot captured and added to README.
- Blender MCP modeling demo captured (GIF) and added to README.
- PyPI 1.0.9 already uploaded; repeat upload fails (file already exists).
- Demo assets update flow documented (docs/demo_assets.md).
- `tspec mcp` supports --unity-mcp-url / --blender-mcp-url flags.
- Docs switched to English-first with Japanese subtext; version bumped to 1.0.9.
- README.rst formatting validated via twine check.
- pytest.ini added to ignore local_notes during test discovery.
- Blender MCP UI auto-start script succeeded (socket get_scene_info OK).
- Knowledge.md rebuilt with English primary + JP appendix.
- Manuals split into EN/JP files with `--lang en/jp` support in manual list/show.
- README Japanese content moved into separate files (README.ja.md / README.ja.rst).
- Added script to switch PyPI long_description between README.rst and README.ja.rst.
- Manual default language can be set via TSPEC_MANUAL_LANG.
- Bumped version to 1.1.0.post1 for PyPI upload.

Last known good command
- tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report "out/agent-browser.json"
- tspec run examples/android_youtube_smoke.tspec.md --backend appium --report "out/android_youtube_smoke.json"

Windows install workaround
- & "$env:APPDATA\\npm\\node_modules\\agent-browser\\bin\\agent-browser-win32-x64.exe" install

WSL fallback config (optional)
- In tspec.toml:
  [agent_browser]
  wsl_fallback = true
  wsl_distro = "Ubuntu-24.04"
  wsl_workdir = "/mnt/c/WorkSpace/Private/Python/tspec-runner"

Tests
- pytest -q (27 passed)


## JP (original)
# 継続メモ

Date: 2026-01-17

Status
- Windows では daemon 起動失敗時に protocol フォールバックで agent-browser が動作。
- WSL フォールバックは任意（Windows CLI が使えない場合のみ tspec.toml を利用）。
- main ブランチへ統合済み（main が最新）。
- TestPyPI / PyPI の 1.0.0 リリース済み。
- docs/ 消失から復旧済み（remote main から復元）。
- Appium Android smoke 例（YouTube 起動 + スクリーンショット）を追加。
- PyPI の long_description を README.rst に切り替え。
- PyPI CSP 対策で README.rst に data URI の縮小画像を埋め込み。
- PyPI は画像を削除し、README.rst で GitHub を参照。
- Blender/Unity MCP のツール追加（config/health/rpc）。
- リポジトリを public 化して raw 画像の 404 を解消。
- Unity MCP の Streamable HTTP ツール（unity.tool）追加。
- Unity MCP `debug_request_context` を /mcp で確認（http://localhost:8090）。
- Unity Hub ログイン/更新でライセンス警告を解消。
- Unity Editor の access token warning は ~60 秒起動で解消。
- Unity Test Framework を manifest に追加（com.unity.test-framework=1.4.5）。
- Unity の再コンパイル完了（TestRunnerService エラーなし）。
- Unity MCP HTTP 8080 接続確認（instances + manage_scene get_hierarchy）。
- Unity MCP デモ GIF を README に追加。
- Unity MCP prefab デモ GIF を README に追加。
- Blender MCP ビューポートのスクショを README に追加。
- Blender MCP モデリングデモ GIF を README に追加。
- PyPI 1.0.9 は既にアップロード済みで再アップロード不可（file already exists）。
- Demo assets 更新フローを docs/demo_assets.md に整理。
- `tspec mcp` に --unity-mcp-url / --blender-mcp-url を追加。
- Docs を英語主体 + 日本語併記に更新（version 1.0.9）。
- README.rst の書式を twine check で検証済み。
- pytest.ini 追加（local_notes をテスト対象から除外）。
- Blender MCP の UI 自動起動で get_scene_info 応答を確認。
- Knowledge.md を英語主体 + JP 付録に再構成。
- マニュアルを EN/JP に分割し、manual list/show で `--lang en/jp` を指定可能にした。
- README の日本語版を README.ja.md / README.ja.rst に分離。
- PyPI long_description 切替スクリプトを追加（README.rst / README.ja.rst）。
- TSPEC_MANUAL_LANG でマニュアル既定言語を指定可能。
- PyPI アップロードのため 1.1.0.post1 に更新。

Last known good command
- tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report "out/agent-browser.json"
- tspec run examples/android_youtube_smoke.tspec.md --backend appium --report "out/android_youtube_smoke.json"

Windows install workaround
- & "$env:APPDATA\\npm\\node_modules\\agent-browser\\bin\\agent-browser-win32-x64.exe" install

WSL fallback config (optional)
- In tspec.toml:
  [agent_browser]
  wsl_fallback = true
  wsl_distro = "Ubuntu-24.04"
  wsl_workdir = "/mnt/c/WorkSpace/Private/Python/tspec-runner"

Tests
- pytest -q (27 passed)
