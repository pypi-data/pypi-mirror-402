# FEATURES.md - Roadmap
JP: 将来実装予定のまとめ（ロードマップ）

## Phase 0 (browser testing)
- [x] Added integration: https://github.com/vercel-labs/agent-browser
- [x] Adopt lightweight headless browser (agent-browser) for faster UI runs.
- Related ToDo: docs/todo_features.md
JP:
- [x] 実装追加：https://github.com/vercel-labs/agent-browser
- [x] ヘッダーレスブラウザ「agent-browser」を導入し、軽量、高速化を図りたい。
- 関連 ToDo: docs/todo_features.md

## Phase 1 (Android/Appium)
- [x] Add Android smoke sample (YouTube open + screenshot)
- [x] Add Appium run example + screenshots to README
JP:
- [x] Android smoke サンプル追加（YouTube 起動 + スクリーンショット）
- [x] README に Appium 実行例とスクリーンショットを追加

## Phase 2 (Blender / Unity MCP)
- [x] Add Blender MCP connection tools
- [x] Add Unity MCP connection tools
- [x] Support Unity MCP Streamable HTTP (`/mcp`)
- [x] Add documentation and TestCase specs
JP:
- [x] Blender MCP の接続ツールを追加
- [x] Unity MCP の接続ツールを追加
- [x] Unity MCP の Streamable HTTP (`/mcp`) 呼び出しに対応
- [x] ドキュメント / TestCase 仕様を追加

## Phase 3 (next proposals)
- [ ] Standardize Unity MCP on `unity.tool` and add CLI subcommands for `unity_instances` / `read_resource`
- [ ] One-command Blender demo generation (e.g., `tspec demo blender`, with GIF output)
- [x] Unify demo asset update flow (optimize `docs/assets` and document the process)
- [x] Add `tspec mcp --unity-mcp-url` / `--blender-mcp-url`
- [ ] Add CI job to run `pytest -q` and publish test results
JP:
- [ ] Unity MCP を `unity.tool` ベースに統一し、`unity_instances` / `read_resource` を CLI から扱えるサブコマンドを追加
- [ ] Blender MCP デモ生成を `tspec demo blender` のようなワンコマンドに統合（GIF生成まで自動化）
- [x] README/PyPI のデモアセット更新手順を一本化（`docs/assets` の最適化と更新フロー整備）
- [x] `tspec mcp` に `--unity-mcp-url` / `--blender-mcp-url` を追加
- [ ] CI で `pytest -q` を実行しテスト結果を可視化

---
Last updated: 2026-01-17
JP: 最終更新: 2026-01-17


## JP (original)
# FEATURES.md — 将来実装予定のまとめ（ロードマップ）

## フェーズ0（ブラウザテスト実行について）
- [x] 実装追加：https://github.com/vercel-labs/agent-browser
- [x] ヘッダーレスブラウザ「agent-browser」を導入し、軽量、高速化を図りたい。
- 関連 ToDo: docs/todo_features.md

## フェーズ1（Android/Appium）
- [x] Android smoke サンプル追加（YouTube 起動 + スクリーンショット）
- [x] README に Appium 実行例とスクリーンショットを追加

## フェーズ2（Blender / Unity MCP）
- [x] Blender MCP の接続ツールを追加
- [x] Unity MCP の接続ツールを追加
- [x] Unity MCP の Streamable HTTP (`/mcp`) 呼び出しに対応
- [x] ドキュメント / TestCase 仕様を追加


---
最終更新: 2026-01-17
