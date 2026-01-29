# Knowledge.md - 作業中のエラー/知見

## 2026-01-15
### "tspec manual show android --full"で失敗
╭───────────────────────────────────────── Traceback (most recent call last) ──────────────────────────────────────────╮
│ C:\WorkSpace\Private\Python\tspec-runner\src\tspec\cli.py:221 in manual_show                                         │
│                                                                                                                      │
│   218 │   if p.exists():                                                                                             │
│   219 │   │   mf = load_manual(p)                                                                                    │
│   220 │   else:                                                                                                      │
│ ❱ 221 │   │   _p, mf = find_manual_by_id(base, target)                                                               │
│   222 │   man = mf.manual                                                                                            │
│   223 │                                                                                                              │
│   224 │   console.print(f"[bold]{man.title}[/bold]  (id={man.id})")                                                  │
│                                                                                                                      │
│ ╭──────────── locals ─────────────╮                                                                                  │
│ │   base = WindowsPath('docs')    │                                                                                  │
│ │   full = True                   │                                                                                  │
│ │      p = WindowsPath('android') │                                                                                  │
│ │ target = 'android'              │                                                                                  │
│ ╰─────────────────────────────────╯                                                                                  │
│                                                                                                                      │
│ C:\WorkSpace\Private\Python\tspec-runner\src\tspec\manual_loader.py:51 in find_manual_by_id                          │
│                                                                                                                      │
│   48 │   for p, mf in discover_manuals(base):                                                                        │
│   49 │   │   if mf.manual.id == manual_id:                                                                           │
│   50 │   │   │   return p, mf                                                                                        │
│ ❱ 51 │   raise ValidationError(f"Manual id not found: {manual_id!r} (searched under {base})")                        │
│   52                                                                                                                 │
│                                                                                                                      │
│ ╭───────────────────────────────────────────────────── locals ─────────────────────────────────────────────────────╮ │
│ │      base = WindowsPath('docs')                                                                                  │ │
│ │ manual_id = 'android'                                                                                            │ │
│ │        mf = ManualFile(                                                                                          │ │
│ │             │   manual=ManualDoc(                                                                                │ │
│ │             │   │   id='update-script',                                                                          │ │
│ │             │   │   title='更新取り込み（PowerShell update.ps1）',                                               │ │
│ │             │   │   tags=['update', 'powershell', 'git'],                                                        │ │
│ │             │   │                                                                                                │ │
│ │             summary='配布zipを既存リポジトリに取り込む際の事故（上書き、タグ忘れ）を減らすための補助。\nブラン … │ │
│ │             を一括で行う。\n',                                                                                   │ │
│ │             │   │   prerequisites=['Windows PowerShell / PowerShell 7', 'git が利用可能'],                       │ │
│ │             │   │   steps=[                                                                                      │ │
│ │             │   │   │   ManualStep(                                                                              │ │
│ │             │   │   │   │   title='1) update.ps1 を使う（repo直下で）',                                          │ │
│ │             │   │   │   │   body='.\\scripts\\update.ps1 -ZipPath "$HOME\\Downloads\\tspec-runner-<version>.zip" │ │
│ │             -Repo'+6                                                                                             │ │
│ │             │   │   │   ),                                                                                       │ │
│ │             │   │   │   ManualStep(                                                                              │ │
│ │             │   │   │   │   title='2) ZipPath 省略（Downloadsから最新を自動選択）',                              │ │
│ │             │   │   │   │   body='.\\scripts\\update.ps1 -RepoDir .\n'                                           │ │
│ │             │   │   │   ),                                                                                       │ │
│ │             │   │   │   ManualStep(                                                                              │ │
│ │             │   │   │   │   title='3) install版から取り出す（任意）',                                            │ │
│ │             │   │   │   │   body='tspec asset list\ntspec asset update.ps1 --to .\n'                             │ │
│ │             │   │   │   )                                                                                        │ │
│ │             │   │   ],                                                                                           │ │
│ │             │   │   troubleshooting=[                                                                            │ │
│ │             │   │   │   ManualStep(                                                                              │ │
│ │             │   │   │   │   title='not a git repository',                                                        │ │
│ │             │   │   │   │   body='先に git init / commit を作ってから利用する。'                                 │ │
│ │             │   │   │   )                                                                                        │ │
│ │             │   │   ],                                                                                           │ │
│ │             │   │   references=[]                                                                                │ │
│ │             │   ),                                                                                               │ │
│ │             │   meta={}                                                                                          │ │
│ │             )                                                                                                    │ │
│ │         p = WindowsPath('docs/update_script.tspec.md')                                                           │ │
│ ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯ │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
ValidationError: Manual id not found: 'android' (searched under docs)
## 2026-01-16
### pytest collection error: httpx missing
- cause: tests/test_neko_client.py imports httpx but dependency not declared
- fix: add httpx to optional extras "neko" and dev deps
- status: resolved

### "tspec manual show android --full" failed to resolve manual
- cause: manual lookup matched id only; android is a tag for android-env
- fix: allow lookup by tag/path key; add unit tests for tag/path/ambiguous match
- status: resolved

### "tspec spec"で失敗
                     Spec support
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ latest ┃ supported generations ┃ supported versions ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 0.1.0  │ -2..1                 │ 0.1.0              │
└────────┴───────────────────────┴────────────────────┘
╭───────────────────────────────────────── Traceback (most recent call last) ──────────────────────────────────────────╮
│ C:\WorkSpace\Private\Python\tspec-runner\src\tspec\cli.py:115 in spec                                                │
│                                                                                                                      │
│   112 │   console.print(table)                                                                                       │
│   113 │                                                                                                              │
│   114 │                                                                                                              │
│ ❱ 115 │   if android:                                                                                                │
│   116 │   │   at = Table(title="Android/Appium checks")                                                              │
│   117 │   │   at.add_column("check")                                                                                 │
│   118 │   │   at.add_column("status")                                                                                │
│                                                                                                                      │
│ ╭────────────────────────── locals ──────────────────────────╮                                                       │
│ │ g_latest = 1                                               │                                                       │
│ │    g_min = -2                                              │                                                       │
│ │   latest = <Version('0.1.0')>                              │                                                       │
│ │    table = <rich.table.Table object at 0x0000024A9D6A8CB0> │                                                       │
│ ╰────────────────────────────────────────────────────────────╯                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
NameError: name 'android' is not defined

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
- fix: start appium server (see docs/android_env.tspec.md)
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
