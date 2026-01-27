"""
七並べAI - Webサーバー
ExoClick広告統合とドキュメントページを提供するFlaskアプリケーション
"""

from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)

# ExoClick広告設定（実際の広告IDに置き換える必要があります）
EXOCLICK_ZONE_ID = "YOUR_ZONE_ID_HERE"


@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html', exoclick_zone_id=EXOCLICK_ZONE_ID)


@app.route('/guide')
def guide():
    """ボット導入ガイド"""
    return render_template('guide.html', exoclick_zone_id=EXOCLICK_ZONE_ID)


@app.route('/faq')
def faq():
    """よくある質問"""
    return render_template('faq.html', exoclick_zone_id=EXOCLICK_ZONE_ID)


@app.route('/pricing')
def pricing():
    """料金プラン"""
    return render_template('pricing.html', exoclick_zone_id=EXOCLICK_ZONE_ID)


@app.route('/support')
def support():
    """サポート・サーバーリンク"""
    return render_template('support.html', exoclick_zone_id=EXOCLICK_ZONE_ID)


@app.route('/spec')
def specification():
    """仕様書（リバースエンジニアリング結果）"""
    return render_template('specification.html')


if __name__ == '__main__':
    # 開発環境での実行
    app.run(host='0.0.0.0', port=5000, debug=True)
