# tspec-runner 1.1.0.post1

TSpec runner for Markdown + `tspec` blocks. Validate, run, and report from the CLI with a single, spec-versioned flow.

## Links
- GitHub: https://github.com/jack-low/tspec-runner
- PyPI: https://pypi.org/project/tspec-runner/
- Japanese: https://github.com/jack-low/tspec-runner/blob/main/README.ja.md

## What you can do
- Spec resolution (latest / range / last 3 generations)
- validate / list / run / spec / init / doctor / report
- Simple assertions via `assert.*`
- Unified UI automation API: `ui.*`
  - backends: `selenium` / `appium` (Android/iOS) / `pywinauto` / `agent-browser`
  - install extras only when needed

> Appium (Android/iOS) requires Appium Server + driver setup.

---

## PyPI long_description language
Default: `README.rst` (English).

Switch:
```bash
python scripts/switch_pypi_readme.py --lang en
python scripts/switch_pypi_readme.py --lang jp
```

---

## Quick start (recommended: uv)
```bash
uv venv
uv sync
tspec validate examples/assert_only.tspec.md
tspec run examples/assert_only.tspec.md --report out/report.json
```

Using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
```

## Basic usage
```bash
tspec spec
tspec init example.tspec.md
tspec validate examples/assert_only.tspec.md --explain-version
tspec run examples/assert_only.tspec.md --report out/report.json
tspec report out/report.json --only-errors --show-steps
```

## UI run (Selenium)
```bash
tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json
```

## UI run (Appium/Android)
```bash
tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json
```
Search flow examples can be fragile; adjust selectors in `examples/android_youtube_search_play.tspec.md` to your environment.

## UI run (agent-browser)
```bash
tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json
```

---

## Screenshots
agent-browser smoke:

![agent-browser smoke](docs/assets/agent-browser-smoke.png)

Selenium (Example Domain):

![selenium example](docs/assets/selenium-example.png)

Appium (YouTube / Android emulator):

![appium android youtube](docs/assets/android-youtube-home.png)

Appium search flow (Home -> Search -> Results -> Player):

![appium youtube search](docs/assets/android-youtube-search.png)
![appium youtube results](docs/assets/android-youtube-results.png)
![appium youtube player](docs/assets/android-youtube-player.png)

Report HTML:

![report example](docs/assets/report-example.png)

> Android/iOS screenshots require Appium Server + device/emulator.

---

## Unity MCP demos
Example: “Create cube -> change material -> move/rotate”.

![unity mcp demo](docs/assets/unity-mcp-demo.gif)

Actions used:
- `manage_gameobject` create cube
- `manage_material` create + recolor + assign to renderer
- `manage_gameobject` update position/rotation

Extra demo: create a sphere, apply material, then create a prefab.

![unity mcp prefab demo](docs/assets/unity-mcp-prefab-demo.gif)

Actions used:
- `manage_gameobject` create sphere
- `manage_material` recolor + assign
- `manage_prefabs` create prefab

Update guide: `docs/demo_assets.md`

## Blender MCP demos
Viewport screenshot example.

![blender mcp demo](docs/assets/blender-mcp-demo.png)

Modeling flow demo (create objects -> bevel/subdivision -> material -> transform).

![blender mcp modeling demo](docs/assets/blender-mcp-modeling-demo.gif)

Update guide: `docs/demo_assets.md`

---

## UI backends (extras)
### Selenium
```bash
pip install -e ".[selenium]"
```

### Appium (Android/iOS)
```bash
pip install -e ".[appium]"
```

### pywinauto (Windows GUI)
```bash
pip install -e ".[pywinauto]"
```

### agent-browser (lightweight headless)
```bash
npm install -g agent-browser
agent-browser install
```
If install fails on Windows, run the exe directly:
```powershell
& "$env:APPDATA\npm\node_modules\agent-browser\bin\agent-browser-win32-x64.exe" install
```

---

## Optional config: tspec.toml
Load with `--config tspec.toml`.

```toml
[ui]
backend = "selenium"  # selenium|appium|pywinauto|agent-browser
headless = true
implicit_wait_ms = 2000

[selenium]
browser = "chrome"  # chrome|firefox
driver_path = ""    # optional: chromedriver/geckodriver path
browser_binary = "" # optional: custom browser binary
args = ["--lang=ja-JP"]
prefs = { "intl.accept_languages" = "ja-JP" }
download_dir = "artifacts/downloads"
window_size = "1280x720"
auto_wait_ms = 3000
page_load_timeout_ms = 30000
script_timeout_ms = 30000

[agent_browser]
binary = "agent-browser"
timeout_ms = 30000
poll_ms = 250
extra_args = []
wsl_fallback = false
wsl_distro = ""
wsl_workdir = ""
```

---

## Common `ui.*` actions
- `ui.open` with `{url}` (Selenium / agent-browser)
- `ui.open_app` with `{caps, server_url}` (Appium)
- `ui.click` with `{selector}`
- `ui.type` with `{selector, text}`
- `ui.wait_for` with `{selector, text_contains?}`
- `ui.get_text` with `{selector}` + `save: "name"`
- `ui.screenshot` with `{path}`
- `ui.close`

> Selector syntax depends on backend (Selenium uses CSS by default; `css=`, `xpath=`, `id=`, etc. are supported).

---

## Neko (m1k1o/neko) MCP integration
Use `neko.*` tools to call Neko REST API from the MCP server.

Setup:
- `pip install -e ".[mcp,neko]"`
- env vars:
  - `NEKO_BASE_URL` (e.g. `http://localhost:8080`)
  - `NEKO_ALLOWLIST_HOSTS` (e.g. `localhost,localhost:8080`)
  - optional: `NEKO_AUTH_MODE`, `NEKO_USERNAME`, `NEKO_PASSWORD`, `NEKO_BEARER_TOKEN`

Run:
```bash
tspec mcp --transport stdio --workdir .
```

Details: `docs/neko_mcp.md`

---

## Blender / Unity MCP integration
We provide tools that call Blender/Unity MCP endpoints.

Blender:
- `pip install -e ".[mcp,blender]"`
- env vars:
  - `BLENDER_MCP_BASE_URL` (e.g. `http://localhost:7300`)
  - `BLENDER_MCP_ALLOWLIST_HOSTS` (recommended: `localhost,localhost:7300`)
  - optional: `BLENDER_MCP_AUTH_MODE` (`none` / `bearer` / `token`)
  - optional: `BLENDER_MCP_BEARER_TOKEN`, `BLENDER_MCP_TOKEN_QUERY`
  - note: blender-mcp (ahujasid) is stdio; not REST compatible
  - CLI: `tspec mcp --blender-mcp-url http://localhost:7300`

Unity:
- `pip install -e ".[mcp,unity]"`
- env vars:
  - `UNITY_MCP_MODE=mcp-http`
  - `UNITY_MCP_MCP_URL` (e.g. `http://localhost:8080/mcp`)
  - `UNITY_MCP_ALLOWLIST_HOSTS` (recommended: `localhost,localhost:8080`)
  - optional: `UNITY_MCP_AUTH_MODE` (`none` / `bearer` / `token`)
  - optional: `UNITY_MCP_BEARER_TOKEN`, `UNITY_MCP_TOKEN_QUERY`
  - REST compatibility: `UNITY_MCP_BASE_URL`
  - CLI: `tspec mcp --unity-mcp-url http://localhost:8080/mcp`

Run:
```bash
tspec mcp --transport stdio --workdir .
```

Details: `docs/blender_mcp.md`, `docs/unity_mcp.md`

---

## Report view
```bash
tspec report out/report.json
tspec report out/report.json --only-errors --show-steps
tspec report out/report.json --case UI-001 --show-steps
tspec report out/report.json --grep google --status failed --status error
```

Long messages (stacktraces):
```bash
tspec report out/report.json --only-errors --show-steps --full-trace --max-message-len 0
```

---

## Failure forensics (auto capture)
When `ui.wait_for` fails, the following are saved under `artifacts/forensics/` by default:
- screenshot (PNG)
- current_url (shown in message)
- page_source (HTML, Selenium only)

---

## MCP (AI integration)
Start `tspec` as an MCP server and call tools from AI clients.

```bash
pip install -e ".[mcp]"
tspec mcp --transport stdio --workdir .
```

Manual (EN/JP): `tspec manual show mcp-env --full --lang en` / `tspec manual show mcp-env --full --lang jp`
Default language can be set via `TSPEC_MANUAL_LANG`.

---

## TSPEC-Z1 (compressed handoff)
CLI:
```bash
tspec z1-decode docs/selenium_spec.tspecz1 --format text
tspec z1-decode docs/selenium_spec.tspecz1 --format json
tspec z1-decompile docs/selenium_spec.tspecz1 --format text
tspec z1-decompile docs/selenium_spec.tspecz1 --format yaml
```

Japanese: https://github.com/jack-low/tspec-runner/blob/main/README.ja.md
