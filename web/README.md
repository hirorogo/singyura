# 七並べAI Webサーバー

このディレクトリには、七並べAI (Singyura) プロジェクトのWebサイトが含まれています。

## 📋 概要

ExoClick広告統合、ドキュメントページ、サポート情報を提供するFlaskベースのWebアプリケーションです。

## 🚀 起動方法

### 1. 依存パッケージのインストール

```bash
cd web
pip install -r requirements.txt
```

### 2. サーバーの起動

```bash
python app.py
```

サーバーは `http://localhost:5000` で起動します。

## 📁 ディレクトリ構成

```
web/
├── app.py                  # Flaskアプリケーション（メイン）
├── requirements.txt        # Python依存パッケージ
├── README.md              # このファイル
├── templates/             # HTMLテンプレート
│   ├── base.html         # ベーステンプレート
│   ├── index.html        # トップページ
│   ├── guide.html        # 導入ガイド
│   ├── faq.html          # よくある質問
│   ├── pricing.html      # 料金プラン
│   ├── support.html      # サポート
│   └── specification.html # 技術仕様書
└── static/                # 静的ファイル
    ├── css/
    │   └── style.css     # メインスタイルシート
    └── js/
        └── main.js       # JavaScriptファイル
```

## 🎯 提供ページ

| URL | 説明 |
|-----|------|
| `/` | トップページ - プロジェクト概要と性能データ |
| `/guide` | ボット導入ガイド - インストール・設定方法 |
| `/faq` | よくある質問 - FAQ集 |
| `/pricing` | 料金プラン - 利用料金について |
| `/support` | サポート - コミュニティリソースとリンク |
| `/spec` | 技術仕様書 - リバースエンジニアリング完全版 |

## 🔧 ExoClick広告の設定

`app.py` ファイル内の `EXOCLICK_ZONE_ID` を実際の広告IDに置き換えてください：

```python
# app.py
EXOCLICK_ZONE_ID = "YOUR_ZONE_ID_HERE"  # ← 実際のZone IDに変更
```

## 🌐 本番環境での実行

### Gunicornを使用（推奨）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Dockerを使用

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📝 カスタマイズ

### スタイルの変更

`static/css/style.css` を編集してデザインをカスタマイズできます。

### コンテンツの更新

各HTMLテンプレート (`templates/*.html`) を編集してコンテンツを更新できます。

### 新しいページの追加

1. `templates/` に新しいHTMLファイルを作成
2. `app.py` に新しいルートを追加

```python
@app.route('/newpage')
def newpage():
    return render_template('newpage.html')
```

## 🔒 セキュリティ

本番環境では以下を設定してください：

- `DEBUG = False` に設定
- 適切なファイアウォール設定
- HTTPS/SSL証明書の使用
- セキュリティヘッダーの追加

## 📚 関連ドキュメント

- [Flask Documentation](https://flask.palletsprojects.com/)
- [ExoClick Integration Guide](https://www.exoclick.com/)
- [プロジェクトREADME](../README.md)

## 🐛 トラブルシューティング

### ポートが既に使用されている

```bash
# 別のポートを使用
python app.py --port 8000
```

または `app.py` の最後を編集：

```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

### テンプレートが見つからない

`templates/` ディレクトリが `app.py` と同じディレクトリにあることを確認してください。

## 📞 サポート

問題が発生した場合は、[GitHubのIssues](https://github.com/hirorogo/singyura/issues)で報告してください。

---

**最終更新**: 2026年1月27日
