# Core TestCase 仕様

目的: tspec-runner のコア機能とオプション機能（Neko/Manual）の動作確認を行う。

## Unit Test Cases
- TC-CORE-001: manual id 指定で正しいマニュアルが取得できる
- TC-CORE-002: manual tag 指定で正しいマニュアルが取得できる
- TC-CORE-003: manual path key 指定で正しいマニュアルが取得できる
- TC-CORE-004: agent-browser backend を指定できる（alias も含む）
- TC-NEKO-001: Neko base_url 未指定で ValidationError
- TC-NEKO-002: allowlist に無い host が ValidationError
- TC-NEKO-003: bearer 認証が Authorization ヘッダに反映される

## Manual / Integration (optional)
- TC-CORE-005: `tspec manual show android --full` が android-env を表示する

## 設定/手順まとめ
- unit: `pytest -q`
- manual: `tspec manual show <id> --full`
