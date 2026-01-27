# 七並べAI Webサーバー用 Dockerfile
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存パッケージをコピーしてインストール
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# アプリケーションファイルをコピー
COPY web/ .

# ポート5000を公開
EXPOSE 5000

# Gunicornでアプリケーションを起動
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
