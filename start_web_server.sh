#!/bin/bash
# 七並べAI Webサーバー起動スクリプト

echo "🚀 七並べAI Webサーバーを起動します..."
echo ""

# webディレクトリに移動
cd "$(dirname "$0")/web"

# 依存パッケージのチェックとインストール
echo "📦 依存パッケージを確認中..."
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Flaskがインストールされていません。インストール中..."
    pip install -q -r requirements.txt
    echo "✅ 依存パッケージのインストールが完了しました"
else
    echo "✅ 依存パッケージは既にインストールされています"
fi

echo ""
echo "🌐 サーバーを起動しています..."
echo "📍 URL: http://localhost:5000"
echo "⚠️  終了するには Ctrl+C を押してください"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Flaskアプリを起動
python app.py
