# QAスキル（日本語版）
テストケース、リリース検証、マニュアル表示確認を担当します。

## フォーカス
- Pytest などの自動テスト、`tspec run`/`tspec report`、言語切替表示。
- 不安定なエラーの記録、ヘルスチェックログ、トラブルシューティング。

## サポートメンバー
- QAアナリスト（受け入れテスト・回帰テストの設計）
- リリース検証者（`python -m twine check` 実行、パッケージ・PyPI検証）
- マニュアル監守（EN/JP マニュアル整合性の確認）

## 利用方法
1. QA対応が必要な依頼ではこのフォルダを参照し、必要なテストを特定。
2. 実行結果や障害は `docs/Knowledge.md` に記録。
3. PyPI公開などはサポートメンバーと連携。

## 備考
- 詳細は `../qa_skill.md` で補足しています。
- `scripts/auto_verify_assert_only.py` により assert_only + pytest 自動検証が行えるので、Bug 再発チェックに活用してください。
- Postman から `http://127.0.0.1:8765/run` を呼び出す手順（`docs/agent_browser_env.*.tspec.md`）で、HTTP 経由の `tspec run` も確認してください。
- `tspec postman-run ... --postman-mcp` を使えば Postman collection を CLI から動かせます（streamable HTTP MCP サーバが自動で起動/終了）。
- 同スクリプトは agent-browser スモーク（`examples/agent_browser_smoke.tspec.md --backend agent-browser`）も試行し、CLIが未検出の場合はスキップしてメッセージを出力します。
- `examples/api_solo_map.tspec.md` は `http.request` を使って https://api.solo-map.app/ へ GET するので、Postman CLI の run body にこのスペックを指定して API レスポンスを検証してください。
- `docs/qa_reports/testcase_inventory.md` は `scripts/qa_testcase_inventory.py` の実行結果で、全 testcases ドキュメントとコマンド一覧をまとめています。
