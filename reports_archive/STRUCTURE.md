# 📂 プロジェクト構成（整理後）

## 🎯 最重要ファイル

### **提出用ファイル**

```
submission.ipynb ★★★★★
```

**これが大会提出用の最終ファイルです！**

- 形式: Jupyter Notebook
- 場所: プロジェクトルート
- 使い方: [Google Colab で開く](https://colab.research.google.com/github/hirorogo/singyura/blob/main/submission.ipynb)

---

## 📁 ルートディレクトリ（整理後）

```
singyura/
├── submission.ipynb         ★ 提出用Notebook（最終版）
├── submission.py            ○ 開発・テスト用スクリプト
├── README.md                ○ プロジェクト概要
├── QUICKSTART.md            ○ クイックガイド
├── WHERE_IS_SUBMISSION.md   ○ 提出ファイル案内
└── STRUCTURE.md             ○ このファイル（構成説明）
```

**変更点:**
- ✅ 提出ファイルが明確（submission.ipynb）
- ✅ 不要なMDファイルを削減（7個 → 4個）
- ✅ わかりやすいファイル名

---

## 📚 ドキュメント（整理後）

### doc/ ディレクトリ

```
doc/
├── specification.md         ゲームルールと仕様
├── design_strongest.md      PIMC法のAI設計書
├── strategy.md              AI戦略案
│
├── logs/                    開発ログ
│   ├── 00_structure_changes.md
│   └── 01_pimc_implementation_and_tuning.md
│
├── misc/                    その他資料
│   └── colab_notebook.md    大会提供のColabノート
│
└── archive/                 詳細レポート（アーカイブ）
    ├── ai_status_report.md
    ├── phase1_improvements.md
    ├── phase2_improvements.md
    ├── simulation_count_optimization.md
    ├── version_comparison.md
    ├── COMPLETION_SUMMARY.md
    ├── CONTRIBUTING.md
    ├── README_IMPROVED.md
    ├── SUBMISSION_GUIDE.md
    └── SUMMARY_JP.md
```

**変更点:**
- ✅ 主要ドキュメント3つを doc/ 直下に配置
- ✅ 詳細レポート10個を archive/ に移動
- ✅ 開発ログとその他資料を分離

---

## 💻 ソースコード

### src/ ディレクトリ（変更なし）

```
src/
├── main.py                  オリジナル版AI
├── main_improved.py         Phase 1改善版AI
├── main_gpu.py              GPU対応版（研究用）
├── benchmark.py             ベンチマーク
├── benchmark_improved.py    Phase 1版ベンチマーク
└── benchmark_gpu.py         GPU版ベンチマーク
```

### reference/ ディレクトリ（変更なし）

```
reference/
├── README.md                参考コードの説明
├── base_game_engine.py      大会提供の基本エンジン
└── random_ai.py             ランダムAI
```

---

## 📊 整理の効果

### Before（整理前）
- ルートMDファイル: **7個**（多すぎて混乱）
- doc/直下MDファイル: **10個**（詳細すぎて分かりにくい）
- 提出ファイル: **submission.py**（形式が不明確）

### After（整理後）
- ルートMDファイル: **4個**（必須のみ、明確）
- doc/直下MDファイル: **3個**（主要ドキュメントのみ）
- doc/archive/: **10個**（詳細レポートを分離）
- 提出ファイル: **submission.ipynb**（Notebook形式、明確）

### 改善点
✅ **提出ファイルが一目で分かる**
✅ **ドキュメントが整理されている**
✅ **必要な情報にすぐアクセスできる**
✅ **詳細情報はarchiveに整理**

---

## 🚀 使い方

### 1. 提出する場合
```bash
# Notebook を開く
jupyter notebook submission.ipynb

# または Colab で開く
# https://colab.research.google.com/github/hirorogo/singyura/blob/main/submission.ipynb
```

### 2. 開発・テストする場合
```bash
# スクリプト版を実行
python submission.py

# ベンチマーク
cd src
python benchmark_improved.py
```

### 3. ドキュメントを読む場合
```bash
# クイックスタート
cat QUICKSTART.md

# 詳細な仕様
cat doc/specification.md

# AI設計
cat doc/design_strongest.md
```

---

## 📖 推奨読書順序

### 初めての方
1. **WHERE_IS_SUBMISSION.md** - 提出ファイルの場所
2. **QUICKSTART.md** - 5分で始める
3. **README.md** - プロジェクト全体像

### 詳しく知りたい方
4. **doc/specification.md** - ゲームルール
5. **doc/design_strongest.md** - AI設計
6. **doc/archive/phase1_improvements.md** - 実装詳細

### 開発者向け
7. **src/main_improved.py** - ソースコード
8. **doc/archive/ai_status_report.md** - 詳細分析
9. **doc/logs/** - 開発ログ

---

## ✅ チェックリスト

提出前に確認：

- [ ] `submission.ipynb` を使用
- [ ] Google Colab で動作確認
- [ ] ベンチマークで勝率55%以上
- [ ] デバッグ出力を削除

---

**作成日:** 2026年1月17日  
**プロジェクト:** hirorogo/singyura  
**整理完了:** ✅
