# Neko MCP tools (tspec-runner)

`tspec-runner` の MCP server に **m1k1o/neko** の REST API をラップしたツール群を追加しました。

## 事前準備
- Neko を起動しておく（Docker 推奨）
- `tspec` MCP server 起動前に、接続先を環境変数で指定
- Neko 連携を使う場合は extras を入れる（`pip install -e ".[neko]"`）

## 環境変数
- `NEKO_BASE_URL` (必須): 例 `http://localhost:8080`
- `NEKO_ALLOWLIST_HOSTS` (推奨): 例 `localhost,localhost:8080,neko:8080`
- `NEKO_AUTH_MODE` (任意): `cookie` / `bearer` / `token`（default: cookie）
- `NEKO_USERNAME`, `NEKO_PASSWORD` (cookie login 用)
- `NEKO_BEARER_TOKEN` (bearer 用)
- `NEKO_TOKEN_QUERY` (token クエリ用)
- `NEKO_TIMEOUT_MS` (任意): default 10000

## MCP tool 名
FastMCP の `name=` が使える環境では `neko.*` 形式で登録します。
もしクライアント側で `neko_*` として見える場合は、ランタイム側の FastMCP が tool 名上書きを未対応です。

## 代表ツール
- `neko.health`
- `neko.login`
- `neko.whoami`
- `neko.stats`
- `neko.screen.screenshot`（JPEG を base64 で返却）
- `neko.clipboard.get` / `neko.clipboard.set`
- `neko.upload.dialog` / `neko.upload.drop`

## 設定/手順まとめ
- install: `pip install -e ".[neko]"`
- env: `NEKO_BASE_URL` + `NEKO_ALLOWLIST_HOSTS` を設定
- run: `tspec mcp --transport stdio`（NEKO_* を事前設定）
