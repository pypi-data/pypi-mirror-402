tspec-runner 1.0.7
==================

TSpec (Markdown + ``tspec``) を読み込み、CLI で検証・実行・レポートまで完結する自動化ランナーです。
Markdown の中にある ``tspec`` ブロックを読み取り、同じ手順を複数環境で再現できます。

リンク
----------------------------------------
- GitHub: https://github.com/jack-low/tspec-runner
- PyPI: https://pypi.org/project/tspec-runner/

できること
----------------------------------------
- Spec バージョン解決（無指定＝最新 / 範囲指定 / 3世代前まで）
- validate / list / run / spec / init / doctor / report
- ``assert.*`` による簡易テスト
- **UI 自動化インターフェース（統一 API）**：``ui.*``
  - backend: ``selenium`` / ``appium``(Android/iOS) / ``pywinauto`` / ``agent-browser``
  - 依存は extras で追加（軽いコア）

.. note::
   Android/iOS は Appium を前提にしています（Appium Server + driver は別途セットアップ）。

クイックスタート（推奨: uv）
----------------------------------------
.. code-block:: bash

   uv venv
   uv sync
   tspec validate examples/assert_only.tspec.md
   tspec run examples/assert_only.tspec.md --report out/report.json

pip を使う場合:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -U pip
   pip install -e ".[dev]"

使い方（基本）
----------------------------------------
.. code-block:: bash

   tspec spec
   tspec init example.tspec.md
   tspec validate examples/assert_only.tspec.md --explain-version
   tspec run examples/assert_only.tspec.md --report out/report.json
   tspec report out/report.json --only-errors --show-steps

UI 実行（例：Selenium）
----------------------------------------
.. code-block:: bash

   tspec run examples/selenium_google.tspec.md --backend selenium --report out/ui.json

UI 実行（例：Appium/Android）
----------------------------------------
.. code-block:: bash

   tspec run examples/android_youtube_smoke.tspec.md --backend appium --report out/android_youtube_smoke.json

検索ありのサンプルは YouTube UI 変更の影響を受けやすいので、
``examples/android_youtube_search_play.tspec.md`` の selector を環境に合わせて調整してください。

UI 実行（例：agent-browser）
----------------------------------------
.. code-block:: bash

   tspec run examples/agent_browser_smoke.tspec.md --backend agent-browser --report out/agent-browser.json

画面キャプチャ（実行例）
----------------------------------------
agent-browser による smoke 実行のスクリーンショット:

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/agent-browser-smoke.png
   :alt: agent-browser smoke

Selenium（Example Domain）のスクリーンショット:

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/selenium-example.png
   :alt: selenium example

Appium（YouTube / Androidエミュレータ）のスクリーンショット:

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/android-youtube-home.png
   :alt: appium android youtube

Appium 検索フロー（Home -> Search -> Results -> Player）:

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/android-youtube-search.png
   :alt: appium youtube search

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/android-youtube-results.png
   :alt: appium youtube results

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/android-youtube-player.png
   :alt: appium youtube player

レポート HTML のスクリーンショット:

.. image:: https://raw.githubusercontent.com/jack-low/tspec-runner/main/docs/assets/report-example.png
   :alt: report example

.. note::
   Android/iOS のスクリーンショットは Appium Server と実機/エミュレータが必要です。

UI backend を使う場合（extras）
----------------------------------------
Selenium

.. code-block:: bash

   pip install -e ".[selenium]"

Appium（Android/iOS）

.. code-block:: bash

   pip install -e ".[appium]"

pywinauto（Windows GUI）

.. code-block:: bash

   pip install -e ".[pywinauto]"

agent-browser（軽量 headless）

.. code-block:: bash

   npm install -g agent-browser
   agent-browser install

Windows で install が失敗する場合は exe を直接実行する：

.. code-block:: powershell

   & "$env:APPDATA\\npm\\node_modules\\agent-browser\\bin\\agent-browser-win32-x64.exe" install

設定（任意）: tspec.toml
----------------------------------------
``--config tspec.toml`` で読み込みます。最小例：

.. code-block:: toml

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

``ui.*`` の主なアクション
----------------------------------------
- ``ui.open`` with ``{url}`` （Selenium / agent-browser）
- ``ui.open_app`` with ``{caps, server_url}`` （Appium）
- ``ui.click`` with ``{selector}``
- ``ui.type`` with ``{selector, text}``
- ``ui.wait_for`` with ``{selector, text_contains?}``
- ``ui.get_text`` with ``{selector}`` + ``save: "name"``
- ``ui.screenshot`` with ``{path}``
- ``ui.close``

.. note::
   selector は backend ごとに解釈されます（Seleniumは CSS を基本、``css=``/``xpath=``/``id=``/``name=``/``link=`` などのprefixも可）。

Neko (m1k1o/neko) MCP 連携
----------------------------------------
MCP Server で ``neko.*`` を有効化し、Neko の REST API をツールとして使えます。

準備:

- ``pip install -e ".[mcp,neko]"``
- 環境変数を設定:
  - ``NEKO_BASE_URL``（例: ``http://localhost:8080``）
  - ``NEKO_ALLOWLIST_HOSTS``（例: ``localhost,localhost:8080``）
  - 任意: ``NEKO_AUTH_MODE``, ``NEKO_USERNAME``, ``NEKO_PASSWORD``, ``NEKO_BEARER_TOKEN``

起動:

.. code-block:: bash

   tspec mcp --transport stdio --workdir .

詳細: ``docs/neko_mcp.md``

Blender / Unity MCP 連携
----------------------------------------
Blender / Unity の MCP 対応エンドポイントを呼び出すツールを追加しました。
``/health`` と ``/rpc`` を前提にしています（``/rpc`` は ``{method, params}`` を受け取る JSON）。

Blender:

- ``pip install -e ".[mcp,blender]"``
- 環境変数:
  - ``BLENDER_MCP_BASE_URL``（例: ``http://localhost:7300``）
  - ``BLENDER_MCP_ALLOWLIST_HOSTS``（推奨: ``localhost,localhost:7300``）
  - 任意: ``BLENDER_MCP_AUTH_MODE`` (``none`` / ``bearer`` / ``token``)
  - 任意: ``BLENDER_MCP_BEARER_TOKEN``, ``BLENDER_MCP_TOKEN_QUERY``

Unity:

- ``pip install -e ".[mcp,unity]"``
- 環境変数:
  - ``UNITY_MCP_BASE_URL``（例: ``http://localhost:7400``）
  - ``UNITY_MCP_ALLOWLIST_HOSTS``（推奨: ``localhost,localhost:7400``）
  - 任意: ``UNITY_MCP_AUTH_MODE`` (``none`` / ``bearer`` / ``token``)
  - 任意: ``UNITY_MCP_BEARER_TOKEN``, ``UNITY_MCP_TOKEN_QUERY``

起動:

.. code-block:: bash

   tspec mcp --transport stdio --workdir .

詳細: ``docs/blender_mcp.md``, ``docs/unity_mcp.md``

レポート表示
----------------------------------------
.. code-block:: bash

   tspec report out/report.json
   tspec report out/report.json --only-errors --show-steps
   tspec report out/report.json --case UI-001 --show-steps
   tspec report out/report.json --grep google --status failed --status error

メッセージが長い場合（Stacktrace等）
----------------------------------------
.. code-block:: bash

   tspec report out/report.json --only-errors --show-steps --full-trace --max-message-len 0

失敗時の鑑識セット（自動採取）
----------------------------------------
- ``ui.wait_for`` が失敗すると、既定で以下を ``artifacts/forensics/`` に保存します：
  - screenshot（PNG）
  - current_url（メッセージに表示）
  - page_source（HTML, Seleniumのみ）

MCP (AI連携)
----------------------------------------
MCP Server として起動し、AIクライアントから TSpec をツール呼び出しできます。

.. code-block:: bash

   pip install -e ".[mcp]"
   tspec mcp --transport stdio --workdir .

マニュアル: ``tspec manual show mcp-env --full``

TSPEC-Z1 圧縮（AI引き渡し用）
----------------------------------------
CLI:

.. code-block:: bash

   tspec z1-decode docs/selenium_spec.tspecz1 --format text
   tspec z1-decode docs/selenium_spec.tspecz1 --format json
   tspec z1-decompile docs/selenium_spec.tspecz1 --format text
   tspec z1-decompile docs/selenium_spec.tspecz1 --format yaml

Pytest reporting (pytest / pytest-html)
----------------------------------------
Install:

.. code-block:: bash

   uv pip install -e ".[report]"

Generate during run:

.. code-block:: bash

   tspec run examples/android_login.tspec.md --backend appium --report out/android.json --pytest-html out/android.html --pytest-junitxml out/android.xml

Generate from existing JSON:

.. code-block:: bash

   tspec pytest-report out/android.json --html out/android.html

Update helper (PowerShell)
----------------------------------------
.. code-block:: powershell

   # extract the update script from installed package (optional)
   tspec asset update.ps1 --to .

   # apply a downloaded zip into current repo
   .\scripts\update.ps1 -ZipPath "$HOME\Downloads\tspec-runner-<version>.zip" -RepoDir .
