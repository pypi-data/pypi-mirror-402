# Knowledge.md - Issue log (English primary)
JP: 作業中のエラー/知見（日本語は下記）

## Skill mapping
- `docs/mcp_env*.tspec.md` / `docs/mcp.tspec.md` / `docs/neko_mcp.md` → `docs/skills/backend_skill.md`
- `docs/agent_browser_env*.tspec.md` / `docs/selenium_env*.tspec.md` / `docs/playwright_env*.tspec.md` → `docs/skills/frontend_skill.md`
- `docs/android_env*.tspec.md` / `docs/ios_env*.tspec.md` → `docs/skills/mobile_skill.md`
- `docs/blender_mcp*.tspec.md` / `docs/unity_mcp*.tspec.md` / `docs/unreal_mcp*.tspec.md` / `docs/*_mcp.md` → `docs/skills/game_engine_skill.md`
- `docs/tspec_z1*.tspec.md` → `docs/skills/tspec_runner_skill.md`
- `docs/reporting_pytest*.tspec.md` / `docs/*_testcases.md` → `docs/skills/qa_skill.md`
- `docs/update*.tspec.md` / `docs/update.md` / `docs/release_notes_*.md` → `docs/skills/release_skill.md`
- `docs/FEATURES.md` / `docs/todo_features.md` / `docs/todo_selenium.md` / `docs/continuation.md` → `docs/skills/pm_skill.md`
- `docs/demo_assets.md` / `docs/tools_urls.md` → `docs/skills/docs_writer_skill.md`
- `docs/Knowledge.md` → `docs/skills/pm_skill.md` + `docs/skills/qa_skill.md`
- Skill folders now include English and Japanese leaf files:
  - `docs/skills/<role>` → `skill.en.md` + `skill.jp.md` describe duties and list support members.
  - Roles: backend, frontend, mobile, game_engine, qa, docs_writer, release, pm, tspec_runner.

### Unreal MCP health hints
- `tspec doctor --unreal-mcp-health` only probes `http://<host>:<port>/health`. Unreal Engine + UnrealMCP plugin must be running and have accepted `uv run unreal_mcp_server_advanced.py` before this check can succeed.  
- If the health probe reports `WinError 10061`, start the UE project manually, wait for the plugin to connect, then rerun the doctor command; it is not an install failure.  
- Documented because health failure is common when Unreal is not running and the CLI does not auto-start the editor.

## 2026-01-15
### "tspec manual show android --full" failed
- error: Manual id not found: 'android'
- cause: manual lookup matched id only; android is a tag for android-env
- fix: allow lookup by tag/path key; add unit tests for tag/path/ambiguous match
- status: resolved

## 2026-01-16
### pytest collection error: httpx missing
- cause: tests/test_neko_client.py imports httpx but dependency not declared
- fix: add httpx to optional extras "neko" and dev deps
- status: resolved

### "tspec spec" NameError
- cause: spec() referenced android/selenium/ios options without defining them
- fix: add options to spec() signature
- status: resolved

### agent-browser WSL fallback: UnicodeDecodeError in subprocess
- cause: WSL command output decoded with cp932 by default, non-ASCII bytes raised decode errors
- fix: set subprocess encoding to utf-8 with errors=replace
- status: resolved

### agent-browser WSL error output caused Windows console encoding failure
- cause: agent-browser error output included Unicode symbols not encodable in cp932
- fix: sanitize error text to ASCII before raising ExecutionError
- status: resolved

### agent-browser "Daemon failed to start" on Windows
- cause: rust CLI could not connect/start daemon; Windows client reported generic error
- fix: add protocol-based fallback via direct daemon TCP commands
- status: resolved

### examples/selenium_google.tspec.md YAML parse failure
- cause: stray trailing "a" after ui.screenshot path line
- fix: remove extra character
- status: resolved

### docs directory missing in local working tree
- cause: local checkout missing docs directory
- fix: restore docs from remote main
- status: resolved

### selenium google smoke timeout
- cause: ui.wait_for timed out on https://www.google.com
- fix: add stable selenium example (example.com) for screenshots
- status: resolved

### appium android login could not reach server
- cause: Appium server not running on 127.0.0.1:4723
- fix: start appium server (see docs/android_env.en.tspec.md)
- status: blocked (env)

### pytest-report html generation failures
- cause: generated test module string formatting errors and JSON null usage
- fix: escape newline in generated code and parse JSON via json.loads
- status: resolved

### Appium session creation timeouts on Android emulator
- cause: UiAutomator2 hidden_api_policy setup and instrumentation launch timed out on API 36 emulator
- fix: add capabilities to examples:
  - forceAppLaunch: true
  - ignoreHiddenApiPolicyError: true
  - adbExecTimeout: 120000
  - uiautomator2ServerInstallTimeout: 120000
  - uiautomator2ServerLaunchTimeout: 120000
  - skipDeviceInitialization: true
  - open_app timeout_ms: 120000
- status: mitigated (android_youtube_smoke passes; search/play flow may still be flaky)

### android_youtube_search_play locator adjustments
- cause: YouTube UI search/results resource-id structure changed; wait_for timed out
- fix: update selectors for search icon/input/suggestions/results/player to match live UI
- status: resolved

### PyPI screenshots not rendering in Markdown README
- cause: PyPI did not render Markdown image syntax in long_description
- fix: switch long_description to README.rst (reStructuredText) with image directives
- status: resolved

### PyPI screenshots still not rendering after reST switch
- cause: PyPI CSP blocks external images (img-src 'self' data:)
- fix: embed resized screenshots as data URIs in README.rst
- status: resolved

### PyPI screenshots not visible for some clients
- cause: PyPI rendering/CSP and client-side blocking
- fix: remove images from PyPI README and refer to GitHub for screenshots
- status: resolved

## 2026-01-17
### Blender/Unity MCP integration added
- change: add blender/unity MCP clients and MCP tools (config/health/rpc)
- status: resolved

### PyPI screenshots restored (public repo)
- cause: repo was private so raw URLs returned 404
- fix: make repo public and restore README.rst image directives
- status: resolved

### Blender MCP background run does not respond
- cause: Blender addon server relies on bpy.app.timers; background/headless execution does not progress timers
- fix: start Blender UI and click "Connect" in BlenderMCP panel, then test socket
- status: pending (UI action required)

### Blender MCP UI auto-start test succeeded
- action: started Blender UI with a startup script that calls `bpy.ops.blendermcp.start_server()`
- result: TCP `get_scene_info` returned normal response (Scene/Cube/Light/Camera)
- status: resolved (UI flow)

### Unity MCP /rpc returns 404
- cause: unity-mcp HTTP server exposes `/health` and `/mcp` (Streamable HTTP), not `/rpc`
- fix: add MCP HTTP client (`unity.tool`) with `UNITY_MCP_MODE=mcp-http` + `UNITY_MCP_MCP_URL`, update docs/testcases
- status: resolved

### Unity MCP streamable HTTP tool call confirmed
- action: `UnityMcpHttpClient` -> `debug_request_context` on `http://localhost:8090/mcp`
- result: response payload returned (structuredContent + content)
- status: resolved

### Unity Editor launch shows licensing warnings
- cause: Unity licensing client reports missing entitlements / access token (log shows Code 404 and com.unity.editor.ui not found)
- fix: sign in via Unity Hub and refresh license/entitlements, then reopen project
- status: resolved (Hub login/update)

### Unity Editor short-run log still shows access token warning
- action: launch Unity Editor for ~15s and scan log
- result: `Licensing::Module` reported "Access token is unavailable; failed to update"
- status: resolved (after ~60s run, access token updated successfully)

### pytest -q picked up local_notes unity-mcp tests and failed
- cause: local_notes contains cloned unity-mcp repo with its own tests and missing deps
- fix: add pytest.ini to limit testpaths to tests and ignore local_notes
- status: resolved

### Unity MCP package compile error: ITestResultAdaptor not found
- error: `Library\PackageCache\com.coplaydev.unity-mcp@...\Editor\Services\TestRunnerService.cs(483,88)`
- cause: Unity Test Framework package is missing (type defined in test framework)
- fix: install `com.unity.test-framework` via Package Manager, then reimport/recompile
- status: resolved (manifest updated, batch recompile OK)

### Unity Test Framework not in manifest.json
- action: checked `UnityMCPTest/Packages/manifest.json`
- result: `com.unity.test-framework` entry missing; added `1.4.5` manually
- status: resolved (batch recompile has no related errors)

### Unity MCP HTTP session verified (localhost:8080)
- action: started MCP for Unity from Editor (HTTP 8080)
- result: `debug_request_context`, `mcpforunity://instances`, and `manage_scene(action=get_hierarchy)` returned OK
- status: resolved

### twine upload failed on Windows console encoding
- cause: rich progress bar emitted Unicode bullet that cp932 couldn't encode
- fix: use `python -m twine upload --disable-progress-bar dist/*`
- status: resolved

## 2026-01-19
### `tspec run examples/assert_only.tspec.md --report out/report.json`
- observation: QA + PM verified the previously reported failure; the command now completes with `Passed: 1  Failed: 0` and produces `out/report.json`.
- follow-up: `pytest -q` also runs cleanly (29 tests; see pyproject/dev suite).
- status: verified (QA/PM alerted the engineer that no reproducible bug exists; monitoring continues for new reports).

### Auto verification script
- action: added `scripts/auto_verify_assert_only.py` to run the failing `tspec run` + `pytest -q` sequence automatically.
- benefit: future checks can be invoked without manually typing the command list, and the QA/PM team can call it from CI or their local shell.
- status: ready (documented and stored under QA skill follow-up).
- update: `scripts/auto_verify_assert_only.py` now also attempts `examples/agent_browser_smoke.tspec.md --backend agent-browser` when the CLI is available, and skips gracefully when the binary cannot be found.

### Auto verification run
- action: ran `python scripts/auto_verify_assert_only.py` locally; it executed `assert_only`, `agent-browser` smoke, and `pytest -q`.
- status: passed (all commands exited 0 and the script reported success).

### agent-browser logging & Postman run
- action: `AgentBrowserUIDriver` now writes `Run local`/`Run wsl` logs plus protocol exchanges to `artifacts/agent-browser/agent-browser.log`, so every command, fallback, and protocol message can be audited.
- action: Added Postman instructions for hitting `http://127.0.0.1:8765/run` (compatible with `tspec mcp --transport streamable-http`) to execute `tspec run` via agent-browser or other backends.
- follow-up: QA/PM should attach the log and screenshot artifacts to bug reports and rerun via Postman if CLI automation is needed; doc updates also mention `artifacts/agent-browser/agent-browser.log`.
- status: documented (skill files and `docs/tools_urls.md` link to the new Postman endpoint).
- resources: Postman public workspace collection linked in `docs/tools_urls.md` for quick import (https://www.postman.com/postman/postman-public-workspace/collection/681dc649440b35935978b8b7?action=share&source=copy-link&creator=0).
- update: Documented Postman CLI usage (`postman-cli run ...`) in the agent-browser manual so CLI-only teams can execute the same MCP call without the Postman UI.
- enhancement: Added `tspec postman-run` command to start the MCP streamable HTTP server (`--postman-mcp`/`--auto-mcp`), optionally pass `--postman-arg` flags, and execute a Postman collection from the CLI. This covers the `tspec run examples/postman_env.tspec.md` workflow mentioned in QA/PM requests.
- note: `examples/postman_env.tspec.md` now defines a Postman-friendly assert-only spec so CLI runs do not require agent-browser; use it to validate the Postman/MCP pipeline via `tspec postman-run`.
- http tool: Added `http.request` action so specs (e.g., `examples/api_solo_map.tspec.md`) can call `https://api.solo-map.app/` directly; combine with Postman CLI or `tspec postman-run` to verify connectivity without agent-browser.
- execution: `tspec run examples/postman_env.tspec.md --backend agent-browser --report out/postman-agent-browser.json` failed because `agent-browser` reported "Browser not launched" (daemon not started yet). Starting the daemon via `agent-browser launch` or running another sample first resolves it; re-run once the agent-browser CLI is ready so `POSTMAN-001` can succeed.
### agent-browser local search check
- action: added `examples/agent_browser_local_search.tspec.md` to open `http://localhost:3000/search` via agent-browser and capture a screenshot.
- run: `tspec run examples/agent_browser_local_search.tspec.md --backend agent-browser --report out/agent-browser-local.json`.
- result: failed at `ui.open` because agent-browser reported `net::ERR_CONNECTION_REFUSED` (localhost:3000 not serving). Report logged in `out/agent-browser-local.json`.
- follow-up: document reminds QA/PM that the local service must be running before this test; if the page is reachable, re-run the spec to gather the screenshot at `artifacts/agent-browser/AB-LOCAL-001.png`.
### agent-browser local search check
- action: initially created `examples/agent_browser_local_search.tspec.md` for local `http://localhost:3000/search` verification.
- status: moved the spec into `local_notes/agent_browser_local_search.tspec.md` per project-local handling conventions.
- run: `tspec run local_notes/agent_browser_local_search.tspec.md --backend agent-browser --report out/agent-browser-local.json`.
- result: failure persists until localhost:3000 is available; once the service responds, rerun from the local_notes path to capture `artifacts/agent-browser/AB-LOCAL-001.png`.

### QA testcase inventory audit
- action: QA skill executed `scripts/qa_testcase_inventory.py` and generated `docs/qa_reports/testcase_inventory.md`, confirming each `_testcases.md` document contains reusable commands; PM asked engineering to treat this generated report as the canonical checklist and keep it current.
- follow-up: QA agent has requested any missing or outdated commands be updated by the respective backend/frontend/game-engine teams via the report; no failures were detected during this run.
- status: documented for PM/QA alignment and will be rerun whenever manual changes occur.

### Doctor health probes now report availability
- action: `_health_probe` now labels connection refusals (WinError 10061/ECONNREFUSED) as `[yellow]... unavailable` and explicitly notes the helper is not running rather than crashing.
- benefit: When Unreal/Unity/Blender MCP helpers or other environment-dependent tools are not present, `tspec doctor --unreal-mcp-health` (or similar) now clarifies the backend is unavailable instead of surfacing a generic error.
- status: behavior shipped; QA/PM notified the relevant service owners to mention the new messaging in manuals.

### PyPI README.rst render error (text/x-rst)
- cause: README.rst had list formatting without blank lines
- fix: reformat README.rst and validate with `python -m twine check dist/*`
- status: resolved

### PyPI upload failed (file already exists)
- cause: version 1.0.9 already uploaded; PyPI rejects filename reuse
- fix: skip upload or bump version
- status: resolved

### PyPI upload prepared for 1.1.0.post1
- action: bump version to 1.1.0.post1 and keep README.rst as long_description
- status: resolved (uploaded 1.1.0.post1)

### tspec versions showed 1.0.7 after 1.1.0.post1 install
- cause: __version__ in src/tspec/__init__.py remained 1.0.7
- fix: update __version__ to 1.1.0.post1 (editable install reflects correct version)
- status: resolved (repo)

### JP manual showed EN text in agent-browser env
- cause: JP manual body still contained EN: lines after split
- fix: remove EN lines from docs/agent_browser_env.jp.tspec.md and re-scan manuals
- status: resolved

### Playwright backend added
- action: add Playwright UI driver + allowlist guard, docs, and manuals
- status: resolved

### Version bump for Playwright release
- action: bump version to 1.1.1 and add release notes
- status: resolved (repo)

### Unreal Engine MCP setup attempt
- action: cloned unreal-engine-mcp and ran `uv run unreal_mcp_server_advanced.py`
- result: uv environment created; server run timed out waiting for UE/plugin connection
- status: blocked (requires Unreal Engine running)

### Unreal Engine MCP verified (stdio)
- action: MCP stdio client listed tools and called `get_actors_in_level`
- result: tools list returned (43 tools), actor list returned from UE
- status: resolved

### Unreal Engine MCP create_castle_fortress is long-running
- action: ran `create_castle_fortress` (small, medieval, no village/siege) on level `LandscapeStreamingProxy_4_4_0`
- result: completed after extended timeout (~6 min), 769 actors created
- fix: allow longer client timeout for large operations
- status: resolved

## 2026-01-18
### Unreal city creation spec timed out at 10 minutes
- action: `tspec run examples/unreal_city.tspec.md --auto-mcp`
- result: helper launched, but spec timed out after 600000ms before recording success (future metropolis is large)
- fix: extended `timeout_ms` to 1200000 and added cleanup spec; auto-MCP runner now handles helper processes
- status: pending verification

### Cleanup spec removes generated actors
- change: add `examples/unreal_cleanup.tspec.md` + `unreal.cleanup_prefix` action to delete FutureCity/Town/Castle actors via `find_actors_by_name` + `delete_actor`
- result: cleanup_prefix now removes matching actors, and `tspec run examples/unreal_cleanup.tspec.md --backend unreal-mcp --auto-mcp` succeeds
- status: resolved


### Unreal cleanup spec parsing failure
- cause: the spec was missing a closing ```tspec fence, so the parser raised "No ```tspec blocks found"
- fix: add the trailing code fence to `examples/unreal_cleanup.tspec.md` and rerun the spec
- result: `tspec run examples/unreal_cleanup.tspec.md --backend unreal-mcp --auto-mcp` now completes successfully (auto-MCP helper adds the cleanup steps)
- status: resolved

### Unreal cleanup tool result normalization
- cause: `_run_tool` returned `CallToolResult` but handlers treated the response as a plain dict
- fix: normalize MCP tool responses by preferring `structuredContent` (or falling back to JSON text) before returning to callers
- result: cleanup, castle, and city actions now see consistent dict outputs; cleanup spec verified
- status: resolved

### Unreal Engine castle automation spec
- change: add `unreal.create_castle` action + `examples/unreal_castle.tspec.md` spec that runs `create_castle_fortress`
- result: spec records castle creation and can be re-run with `tspec run examples/unreal_castle.tspec.md`
- status: resolved

### Release notes policy
- action: add release notes per version in docs/release_notes_<version>.md
- status: resolved (documented in update.md)

## 2026-01-19
### Unreal race prototype rollback
- reason: race track builder implementation rejected
- action: removed race MCP tools/spec (`helpers/race_creation.py`, `examples/unreal_race.tspec.md`) and restored cleanup prefixes to FutureCity/Town/Castle only
- status: resolved

## JP (original)
# Knowledge.md - 作業中のエラー/知見

## 2026-01-19
### Unreal レース試作のロールバック
- 理由: レーストラック実装が不要と判断
- 対応: race MCP ツール/スペックを削除し、cleanup も FutureCity/Town/Castle のみに戻す
- ステータス: 対応済み

## 2026-01-15
### "tspec manual show android --full"で失敗
- 原因: manual の検索が id のみ対象で、android は android-env のタグだった
- 対応: タグ/パスキーでの検索を許可し、タグ/パス/曖昧一致のテストを追加
- 状態: 解決済み

## 2026-01-16
### pytest collection error: httpx missing
- cause: tests/test_neko_client.py imports httpx but dependency not declared
- fix: add httpx to optional extras "neko" and dev deps
- status: resolved

### "tspec manual show android --full" failed to resolve manual
- cause: manual lookup matched id only; android is a tag for android-env
- fix: allow lookup by tag/path key; add unit tests for tag/path/ambiguous match
- status: resolved

### "tspec spec"でNameError
- 原因: spec() が android/selenium/ios オプション定義前に参照していた
- 対応: spec() のシグネチャに各オプションを追加
- 状態: 解決済み

## 2026-01-16
### "tspec spec" NameError
- cause: spec() referenced android/selenium/ios options without defining them
- fix: add options to spec() signature
- status: resolved

### agent-browser WSL fallback: UnicodeDecodeError in subprocess
- cause: WSL command output decoded with cp932 by default, non-ASCII bytes raised decode errors
- fix: set subprocess encoding to utf-8 with errors=replace
- status: resolved

### agent-browser WSL error output caused Windows console encoding failure
- cause: agent-browser error output included Unicode symbols not encodable in cp932
- fix: sanitize error text to ASCII before raising ExecutionError
- status: resolved

### agent-browser "Daemon failed to start" on Windows
- cause: rust CLI could not connect/start daemon; Windows client reported generic error
- fix: add protocol-based fallback via direct daemon TCP commands
- status: resolved

### examples/selenium_google.tspec.md YAML parse failure
- cause: stray trailing "a" after ui.screenshot path line
- fix: remove extra character
- status: resolved

## 2026-01-16
### docs directory missing in local working tree
- cause: local checkout missing docs directory
- fix: restore docs from remote main
- status: resolved

### selenium google smoke timeout
- cause: ui.wait_for timed out on https://www.google.com
- fix: add stable selenium example (example.com) for screenshots
- status: resolved

### appium android login could not reach server
- cause: Appium server not running on 127.0.0.1:4723
- fix: start appium server (see docs/android_env.jp.tspec.md)
- status: blocked (env)

### pytest-report html generation failures
- cause: generated test module string formatting errors and JSON null usage
- fix: escape newline in generated code and parse JSON via json.loads
- status: resolved

## 2026-01-16
### Appium session creation timeouts on Android emulator
- cause: UiAutomator2 hidden_api_policy setup and instrumentation launch timed out on API 36 emulator
- fix: add capabilities to examples:
  - forceAppLaunch: true
  - ignoreHiddenApiPolicyError: true
  - adbExecTimeout: 120000
  - uiautomator2ServerInstallTimeout: 120000
  - uiautomator2ServerLaunchTimeout: 120000
  - skipDeviceInitialization: true
  - open_app timeout_ms: 120000
- status: mitigated (android_youtube_smoke passes; search/play flow may still be flaky)

### android_youtube_search_play の locator 調整
- cause: YouTube UI の検索/結果画面の resource-id 構造が想定と異なり wait_for がタイムアウト
- fix: 検索アイコン/検索入力/サジェスト/結果/プレーヤーの selector を実機 UI に合わせて更新
- status: resolved

## 2026-01-16
### PyPI screenshots not rendering in Markdown README
- cause: PyPI did not render Markdown image syntax in long_description
- fix: switch long_description to README.rst (reStructuredText) with image directives
- status: resolved

## 2026-01-16
### PyPI screenshots still not rendering after reST switch
- cause: PyPI CSP blocks external images (img-src 'self' data:)
- fix: embed resized screenshots as data URIs in README.rst
- status: resolved

## 2026-01-16
### PyPI screenshots not visible for some clients
- cause: PyPI rendering/CSP and client-side blocking
- fix: remove images from PyPI README and refer to GitHub for screenshots
- status: resolved

## 2026-01-17
### Blender/Unity MCP integration added
- change: add blender/unity MCP clients and MCP tools (config/health/rpc)
- status: resolved

### PyPI screenshots restored (public repo)
- cause: repo was private so raw URLs returned 404
- fix: make repo public and restore README.rst image directives
- status: resolved

## 2026-01-17
### Blender MCP background run does not respond
- cause: Blender addon server relies on bpy.app.timers; background/headless execution does not progress timers
- fix: start Blender UI and click "Connect" in BlenderMCP panel, then test socket
- status: pending (UI action required)

## 2026-01-17
### Blender MCP UI auto-start test succeeded
- action: started Blender UI with a startup script that calls `bpy.ops.blendermcp.start_server()`
- result: TCP `get_scene_info` returned 正常レスポンス (Scene/Cube/Light/Camera)
- status: resolved (UI flow)

### Unity MCP /rpc returns 404
- cause: unity-mcp HTTP server exposes `/health` and `/mcp` (Streamable HTTP), not `/rpc`
- fix: add MCP HTTP client (`unity.tool`) with `UNITY_MCP_MODE=mcp-http` + `UNITY_MCP_MCP_URL`, update docs/testcases
- status: resolved

### Unity MCP streamable HTTP tool call confirmed
- action: `UnityMcpHttpClient` -> `debug_request_context` on `http://localhost:8090/mcp`
- result: response payload returned (structuredContent + content)
- status: resolved

### Unity Editor launch shows licensing warnings
- cause: Unity licensing client reports missing entitlements / access token (log shows Code 404 and com.unity.editor.ui not found)
- fix: sign in via Unity Hub and refresh license/entitlements, then reopen project
- status: resolved (Hub login/update)

### Unity Editor short-run log still shows access token warning
- action: launch Unity Editor for ~15s and scan log
- result: `Licensing::Module` reported "Access token is unavailable; failed to update"
- status: resolved (after ~60s run, access token updated successfully)

### pytest -q picked up local_notes unity-mcp tests and failed
- cause: local_notes contains cloned unity-mcp repo with its own tests and missing deps
- fix: add `pytest.ini` to limit testpaths to `tests` and ignore local_notes
- status: resolved

### Unity MCP package compile error: ITestResultAdaptor not found
- error: `Library\\PackageCache\\com.coplaydev.unity-mcp@...\\Editor\\Services\\TestRunnerService.cs(483,88)`
- cause: Unity Test Framework package is missing (type defined in test framework)
- fix: install `com.unity.test-framework` via Package Manager, then reimport/recompile
- status: resolved (manifest updated, batch recompile OK)

### Unity Test Framework not in manifest.json
- action: checked `UnityMCPTest/Packages/manifest.json`
- result: `com.unity.test-framework` entry missing; added `1.4.5` manually
- status: resolved (batch recompile has no related errors)

### Unity MCP HTTP session verified (localhost:8080)
- action: started MCP for Unity from Editor (HTTP 8080)
- result: `debug_request_context`, `mcpforunity://instances`, and `manage_scene(action=get_hierarchy)` returned OK
- status: resolved

### twine upload failed on Windows console encoding
- cause: rich progress bar emitted Unicode bullet that cp932 couldn't encode
- fix: use `python -m twine upload --disable-progress-bar dist/*`
- status: resolved
