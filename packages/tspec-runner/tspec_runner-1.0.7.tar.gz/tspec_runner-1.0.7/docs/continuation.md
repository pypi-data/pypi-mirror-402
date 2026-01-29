# Continuation Notes

Date: 2026-01-16

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
- pytest -q (19 passed)
