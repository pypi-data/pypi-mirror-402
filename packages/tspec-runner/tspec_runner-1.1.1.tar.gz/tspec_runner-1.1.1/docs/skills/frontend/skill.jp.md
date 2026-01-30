# フロントエンドエンジニアリングスキル（日本語版）
`agent-browser`/Selenium/Playwright といった UI 自動化の AgentSkills をまとめています。

## フォーカス
- ヘッドレスブラウザ、UI バックエンド、スクリーンショット、アクセシビリティチェック。
- Windows/WSL での agent-browser/selenium/playwright 設定のコツ。

## サポートメンバー
- UI オートメーションエンジニア（セレクタ/WASM周り、agent-browser 連携）
- アクセシビリティアナリスト（alt 文字列やコントラストチェック）
- ローカライズ QA（英語/日本語マニュアル整合性の確認）

## 利用方法
1. UI バックエンドに関わるマニュアル・テスト依頼時にこのフォルダを確認。
2. 英語版で実装の意図を掴み、日本語版で表現の統一を取る。
3. 実行結果のタイミング問題は `docs/Knowledge.md` に記録。

## 備考
- 詳細は `../frontend_skill.md` を確認してください。
- `artifacts/agent-browser/agent-browser.log` で実行コマンドと protocol イベントを追跡でき、Postman 連携は `docs/agent_browser_env.*.tspec.md` の `http://127.0.0.1:8765/run` 呼び出しで実行できます。
