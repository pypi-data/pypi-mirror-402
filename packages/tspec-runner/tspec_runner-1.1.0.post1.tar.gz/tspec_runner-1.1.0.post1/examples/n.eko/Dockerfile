# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 余計な .pyc を出さない & stdout を即時出力
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依存関係（requirements.txt がある想定）
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# アプリ本体
COPY . /app

# .env を読み込んで export するエントリポイント
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 非root実行（必要なら外してOK）
RUN useradd -m appuser
USER appuser

# デフォルトで /config を用意（.env や設定ファイルを置く用）
VOLUME ["/config"]

# 起動コマンドは用途に合わせて差し替え
# 例: python main.py / python app.py / python tool.py
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]
