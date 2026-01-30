#!/bin/sh
# docker/entrypoint.sh
set -eu

# 読み込む .env の場所を優先順で決める
# 1) ENV_FILE が指定されていればそれ
# 2) /config/.env
# 3) /app/.env
ENV_PATH="${ENV_FILE:-}"

if [ -z "$ENV_PATH" ]; then
  if [ -f "/config/.env" ]; then
    ENV_PATH="/config/.env"
  elif [ -f "/app/.env" ]; then
    ENV_PATH="/app/.env"
  fi
fi

# .env を「安全寄り」に export（コメント/空行無視、KEY=VALUE 形式のみ）
if [ -n "${ENV_PATH:-}" ] && [ -f "$ENV_PATH" ]; then
  echo "[entrypoint] Loading env from: $ENV_PATH"
  # shellcheck disable=SC2163
  export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_PATH" | sed 's/#.*$//' | xargs || true)
else
  echo "[entrypoint] No .env file loaded (ENV_FILE or /config/.env or /app/.env not found)"
fi

exec "$@"

