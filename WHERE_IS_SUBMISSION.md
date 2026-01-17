# 📍 提出用ファイルの場所

## ✅ 最終提出ファイル

### **`submission.ipynb`** ⭐⭐⭐

**場所:** プロジェクトルートディレクトリ

```
singyura/
└── submission.ipynb  ← これが提出ファイルです！
```

### 使い方

#### Google Colab で開く（推奨）
1. [Open in Colab](https://colab.research.google.com/github/hirorogo/singyura/blob/main/submission.ipynb)
2. 「Runtime」→「Run all」ですべてのセルを実行
3. ベンチマークで勝率を確認

#### ローカル環境で開く
```bash
# Jupyter をインストール
pip install jupyter notebook numpy

# Notebook を開く
jupyter notebook submission.ipynb
```

---

## 📝 その他のファイル

### `submission.py`
**用途:** 開発・テスト用のPythonスクリプト版

```bash
python submission.py
```

**注:** submission.ipynb と同じコードですが、スクリプト形式です。

---

## 📚 ドキュメント構成

### 重要なドキュメント（ルート）
- **README.md** - プロジェクト全体の概要
- **QUICKSTART.md** - 5分でわかるクイックガイド
- **WHERE_IS_SUBMISSION.md** - このファイル（提出先案内）

### 仕様・設計（doc/）
- **doc/specification.md** - ゲームルールと仕様
- **doc/design_strongest.md** - PIMC法のAI設計書
- **doc/strategy.md** - AI戦略案

### 詳細レポート（doc/archive/）
開発過程の詳細なレポートはこちらに移動しました：
- doc/archive/ai_status_report.md
- doc/archive/phase1_improvements.md
- doc/archive/phase2_improvements.md
- その他7ファイル

---

## 🎯 大会提出チェックリスト

提出前に以下を確認してください：

- [ ] **`submission.ipynb`** を使用している
- [ ] Google Colab または Jupyter Notebook で動作確認済み
- [ ] すべてのセルが正常に実行できる
- [ ] ベンチマークで勝率55%以上を確認
- [ ] デバッグ出力（print文）を削除済み
- [ ] `SIMULATION_COUNT = 300` に設定（推奨）
- [ ] `my_AI` 関数が正しく実装されている

---

## 💡 ヒント

### 勝率を上げたい場合

1. **シミュレーション回数を増やす**
   ```python
   # submission.ipynb の「設定」セル
   SIMULATION_COUNT = 500  # 300から増やす（遅くなります）
   ```

2. **ベンチマークで確認**
   - Notebook の最後のセルでベンチマーク実行
   - 勝率が55%以上なら良好

3. **パラメータ調整**
   - 100回: 高速（勝率50-55%）
   - 300回: **推奨**（勝率55-60%）
   - 500回: 高精度（勝率60-65%、遅い）

---

## 🆘 困ったときは

### エラーが出る場合
1. **QUICKSTART.md** のトラブルシューティングを確認
2. **README.md** の使い方を再確認
3. GitHub Issue を作成

### もっと詳しく知りたい場合
- `doc/design_strongest.md` - AI設計の詳細
- `doc/archive/ai_status_report.md` - 詳細分析レポート
- `src/main_improved.py` - 開発版のソースコード

---

**最終更新:** 2026年1月17日  
**プロジェクト:** hirorogo/singyura  
**バージョン:** Phase 1改善版
