# Webサーバー・広告統合 実装ドキュメント

## 📅 実装日
2026年1月27日

## 🎯 実装目的

ExoClick広告を統合したWebサーバーを構築し、以下の機能を提供：
1. トップページ（プロジェクト紹介）
2. ボット導入ガイド
3. よくある質問（FAQ）
4. 料金プラン
5. サポート・サーバーリンク
6. 技術仕様書（リバースエンジニアリング結果）

## 📁 追加されたファイル

### Webサーバー関連

```
web/
├── app.py                  # Flaskアプリケーション（メイン）
├── requirements.txt        # Flask依存パッケージ
├── README.md              # Webサーバーのドキュメント
├── templates/             # HTMLテンプレート
│   ├── base.html         # ベーステンプレート（ナビゲーション・広告エリア）
│   ├── index.html        # トップページ
│   ├── guide.html        # 導入ガイド
│   ├── faq.html          # よくある質問
│   ├── pricing.html      # 料金プラン
│   ├── support.html      # サポート・リンク集
│   └── specification.html # 技術仕様書
└── static/                # 静的ファイル
    ├── css/
    │   └── style.css     # メインスタイルシート
    └── js/
        └── main.js       # クライアントサイドJS
```

## 🌐 URL構成

| URL | ページ | 説明 |
|-----|--------|------|
| `/` | トップページ | プロジェクト概要、性能データ、特徴 |
| `/guide` | 導入ガイド | インストール手順、設定方法 |
| `/faq` | FAQ | よくある質問と回答 |
| `/pricing` | 料金プラン | フリー/プロ/エンタープライズプラン |
| `/support` | サポート | コミュニティリソース、リンク集 |
| `/spec` | 技術仕様書 | リバースエンジニアリング完全版 |

## 💰 広告統合 (ExoClick)

### 実装箇所

1. **トップバナー広告** (`base.html`)
   - 全ページのヘッダー下に表示
   - 水平バナー形式

2. **サイドバー広告** (`base.html`)
   - 右側固定サイドバー
   - スクロールに追従

### 設定方法

`web/app.py` の `EXOCLICK_ZONE_ID` を実際のZone IDに変更：

```python
EXOCLICK_ZONE_ID = "YOUR_ZONE_ID_HERE"  # ← 実際のZone IDに変更
```

### 広告表示条件

```python
{% if exoclick_zone_id and exoclick_zone_id != 'YOUR_ZONE_ID_HERE' %}
    <!-- 広告コード -->
{% endif %}
```

デフォルト値のままの場合は広告が表示されません。

## 📄 技術仕様書の内容

`/spec` ページには以下のリバースエンジニアリング結果を掲載：

### 1. ゲーム概要
- ゲームルール詳細
- トンネルルール説明

### 2. コアクラス・データ構造
- `Card`, `Hand`, `Deck`, `State` クラスの仕様
- データ構造の詳細

### 3. 推論エンジン (CardTracker)
- 対戦相手手札の推論ロジック
- 重み付け計算式

### 4. AIアルゴリズム
- Phase 1: 推論制約付き確定化
- Phase 2: PIMCシミュレーションループ
- Phase 3: ロールアウトポリシー

### 5. 戦略評価レイヤー
- トンネルロック戦略
- バースト強制戦略
- 高度ヒューリスティック

### 6. 対戦相手モデリング
- `OpponentModel` クラス
- モード分類（tunnel_lock/burst_force/neutral）

### 7. パフォーマンス指標
- 勝率: 80% (vs ランダムAI × 2)
- 処理速度: 0.2-0.5秒/手

### 8. 設定パラメータ
- 全ての設定可能パラメータ
- 有効化フラグ

### 9. ファイル構成
- 各ファイルの役割
- エントリポイント

### 10. アルゴリズムフロー
- 意思決定フロー図
- 時間/空間計算量

## 🎨 デザイン

### カラーテーマ

```css
--primary-color: #2563eb;    /* ブルー */
--secondary-color: #7c3aed;  /* パープル */
--success-color: #10b981;    /* グリーン */
--danger-color: #ef4444;     /* レッド */
--dark-bg: #1f2937;          /* ダークグレー */
--light-bg: #f9fafb;         /* ライトグレー */
```

### レスポンシブデザイン

- デスクトップ: 3カラムグリッド
- タブレット: 2カラムグリッド
- モバイル: 1カラム表示
- サイドバー広告は768px以下で非表示

## 🚀 起動方法

### 開発環境

```bash
cd web
pip install -r requirements.txt
python app.py
```

サーバーは `http://localhost:5000` で起動。

### 本番環境

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

または環境変数で設定：

```bash
export FLASK_APP=app.py
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000
```

## 📊 ページ別コンテンツ

### トップページ (`/`)
- ヒーローセクション（勝率80%達成を強調）
- 主な特徴（4つの特徴カード）
- プロジェクト概要
- 性能データテーブル
- CTAボタン（導入ガイド、料金、サポート）

### 導入ガイド (`/guide`)
- 必要な環境
- インストール手順（ステップバイステップ）
- Jupyter Notebook使用方法
- Google Colab使用方法
- 設定のカスタマイズ
- トラブルシューティング

### FAQ (`/faq`)
- 性能について（5問）
- 技術的な質問（4問）
- ゲームルールについて（3問）
- 料金について（1問）
- サポート（2問）

### 料金プラン (`/pricing`)
- 3つのプラン（フリー/プロ/エンタープライズ）
- 機能比較表
- 料金に関するFAQ（5問）
- CTAボタン

### サポート (`/support`)
- サポート窓口（4つのカード）
- サーバーリンク（GitHub, Colab, Docs, Discord）
- 学習リソース（4つのリンク）
- 開発者向けリソース
- お問い合わせ方法
- コミュニティ統計

### 技術仕様書 (`/spec`)
- 11セクションの詳細仕様
- コードサンプル
- テーブルでの情報整理
- アルゴリズムフロー

## 🔧 カスタマイズガイド

### 新しいページの追加

1. `templates/` に新しいHTMLファイルを作成
2. `base.html` を継承
3. `app.py` にルートを追加

```python
@app.route('/newpage')
def newpage():
    return render_template('newpage.html', exoclick_zone_id=EXOCLICK_ZONE_ID)
```

4. ナビゲーションメニューに追加（`base.html`）

### スタイルの変更

`static/css/style.css` を編集：

```css
/* カスタムスタイル */
.custom-class {
    /* スタイル定義 */
}
```

### JavaScriptの追加

`static/js/main.js` に関数を追加：

```javascript
function customFunction() {
    // カスタムロジック
}
```

## 🔒 セキュリティ考慮事項

### 本番環境での設定

1. **デバッグモードを無効化**
   ```python
   app.run(debug=False)
   ```

2. **HTTPS/SSL証明書の使用**
   - Let's Encrypt推奨
   - Nginxリバースプロキシ経由

3. **セキュリティヘッダー**
   ```python
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

4. **CORS設定**（必要に応じて）
   ```python
   from flask_cors import CORS
   CORS(app)
   ```

## 📈 今後の拡張案

### フェーズ1: 基本機能の強化
- [ ] お問い合わせフォームの追加
- [ ] ユーザー登録・ログイン機能
- [ ] ダッシュボード機能

### フェーズ2: 高度な機能
- [ ] AIのオンラインデモ（ブラウザで実行）
- [ ] ベンチマーク結果の可視化
- [ ] リアルタイム対戦機能

### フェーズ3: コミュニティ機能
- [ ] ユーザーフォーラム
- [ ] AI共有プラットフォーム
- [ ] ランキングシステム

## 📝 開発ログ

### 2026年1月27日
- ✅ Flaskアプリケーション基盤構築
- ✅ 6つのHTMLページ作成
- ✅ レスポンシブCSSスタイル実装
- ✅ ExoClick広告統合
- ✅ ナビゲーションシステム実装
- ✅ 技術仕様書のリバースエンジニアリング
- ✅ ドキュメント作成

## 🐛 既知の問題

現時点で既知の問題はありません。

## 📞 サポート

問題や質問がある場合：
- GitHub Issues: https://github.com/hirorogo/singyura/issues
- Email: support@singyura.example.com

---

**ドキュメントバージョン**: 1.0  
**最終更新**: 2026年1月27日  
**作成者**: GitHub Copilot Coding Agent
