# 七並べAI Webサーバー - Dockerデプロイガイド

## 🐳 Dockerを使った起動方法

### 前提条件
- Docker Desktop または Docker Engine がインストールされていること
- Docker Compose がインストールされていること

### クイックスタート

#### 1. Docker Composeで起動（推奨）

```bash
# ExoClick Zone IDを環境変数に設定（オプション）
export EXOCLICK_ZONE_ID="your_actual_zone_id"

# コンテナをビルド・起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

#### 2. Dockerコマンドで起動

```bash
# イメージをビルド
docker build -t singyura-web .

# コンテナを起動
docker run -d -p 5000:5000 --name singyura-web singyura-web

# ログを確認
docker logs -f singyura-web
```

### アクセス

ブラウザで http://localhost:5000 を開く

### コンテナの管理

```bash
# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f web

# コンテナ内に入る
docker-compose exec web /bin/bash
```

## 🚀 本番環境でのデプロイ

### Nginx リバースプロキシ設定例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS設定（Let's Encrypt）

```bash
# Certbotのインストール
sudo apt-get install certbot python3-certbot-nginx

# SSL証明書の取得
sudo certbot --nginx -d your-domain.com

# 自動更新の設定
sudo certbot renew --dry-run
```

## 🔧 環境変数

`.env` ファイルを作成して環境変数を設定できます：

```bash
# .env
EXOCLICK_ZONE_ID=your_actual_zone_id
FLASK_ENV=production
```

## 📊 ヘルスチェック

```bash
# ヘルスチェックエンドポイント
curl http://localhost:5000/

# Docker Composeのヘルスチェック確認
docker-compose ps
```

## 🐛 トラブルシューティング

### ポートが既に使用されている

```bash
# docker-compose.ymlのポートを変更
ports:
  - "8000:5000"  # 5000 → 8000 に変更
```

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs web

# コンテナを再ビルド
docker-compose build --no-cache
docker-compose up -d
```

### パーミッションエラー

```bash
# 所有権を修正
sudo chown -R $USER:$USER web/
```

## 📝 参考リンク

- [Docker公式ドキュメント](https://docs.docker.com/)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [Flask Deployment](https://flask.palletsprojects.com/en/latest/deploying/)

---

**最終更新**: 2026年1月27日
