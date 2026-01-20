# プロジェクト構造 - 簡潔版

## 📁 ディレクトリ構成（シンプル版）

```
singyura/
├── 📄 README.md                         ← プロジェクト全体説明（80%勝率の情報）
├── 🌟 WHICH_FILE_TO_USE.md             ← 【重要】どのファイルを使うべきか完全ガイド
├── 🚀 QUICKSTART.md                     ← 5分で始めるガイド
├── 📊 AI_IMPROVEMENT_REPORT_2026_01_20.md ← 80%達成レポート
├── ✅ VERIFICATION_REPORT.md            ← ベンチマーク検証レポート
│
├── 📂 src/                              ← ソースコード
│   ├── 📄 README.md                    ← ソースコードの説明
│   ├── ⭐ main.py                      ← 開発・テスト用（80%勝率）
│   ├── ⭐ submission.py                ← 【提出用】大会用（80%勝率）
│   ├── 📄 submission_colab.py          ← Colab最適化版（65-70%）
│   ├── 🔬 main_gpu.py                  ← GPU実験版
│   ├── 📊 benchmark.py                 ← ベンチマーク（推奨）
│   ├── 📊 benchmark_full.py            ← 長時間ベンチマーク
│   ├── 📊 benchmark_gpu.py             ← GPU版ベンチマーク
│   └── 📂 archive/                     ← 過去のバージョン
│       ├── 📄 README.md               ← アーカイブ説明
│       ├── main_improved.py           ← Phase1/2版（31-40%）
│       ├── main_simplified.py         ← シンプル版（38-45%）
│       ├── benchmark_improved.py
│       ├── benchmark_simplified.py
│       ├── debug_ai.py
│       └── debug_legal_actions.py
│
├── 📂 doc/                              ← ドキュメント
│   ├── specification.md                ← ゲーム仕様
│   ├── design_strongest.md             ← PIMC法の設計
│   ├── strategy.md                     ← 戦略案
│   ├── CURRENT_STATUS_ANALYSIS.md      ← 現状分析レポート
│   ├── STRATEGY_AND_INFERENCE_MODEL_REPORT.md ← 戦略詳細
│   ├── AI_ENHANCEMENT_2026_01_19.md    ← AI強化レポート
│   ├── 📂 logs/                        ← 開発ログ
│   ├── 📂 misc/                        ← その他（Colab notebook等）
│   └── 📂 archive/                     ← 古いドキュメント
│
├── 📂 reference/                        ← 参考コード（大会提供）
│   ├── README.md
│   ├── base_game_engine.py
│   └── random_ai.py
│
├── 📂 reports_archive/                  ← 過去のレポート
│   ├── 📄 README.md                    ← アーカイブ説明
│   ├── PROJECT_COMPLETION_REPORT.md
│   ├── TASK_COMPLETION_SUMMARY.md
│   ├── FINAL_IMPROVEMENTS_SUMMARY.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── STRUCTURE.md
│
├── 📂 sankouyou/                        ← 参考資料
│   └── (他のAI実装の参考コード)
│
└── 📂 .github/
    └── copilot-instructions.md         ← GitHub Copilot用の指示
```

---

## 🎯 重要ファイル（優先度順）

### 1. 大会提出用（最優先）⭐⭐⭐
- **`src/submission.py`** - 80%勝率達成版、大会に提出するファイル
- **`WHICH_FILE_TO_USE.md`** - 使い方の完全ガイド

### 2. 理解・確認用
- **`README.md`** - プロジェクト全体の概要
- **`QUICKSTART.md`** - 5分で始めるガイド
- **`AI_IMPROVEMENT_REPORT_2026_01_20.md`** - 80%達成の詳細レポート

### 3. 開発・テスト用
- **`src/main.py`** - ローカル開発・テスト用（80%版）
- **`src/benchmark.py`** - 性能評価

### 4. ドキュメント
- **`doc/specification.md`** - ゲームルール
- **`doc/design_strongest.md`** - AI設計

---

## 📌 ファイル選択フローチャート

```
質問: 何をしたい？
│
├─ 大会に提出したい
│  └→ src/submission.py を使う ⭐
│
├─ ローカルでテストしたい
│  └→ src/main.py を使う
│
├─ ベンチマークで性能確認したい
│  └→ src/benchmark.py を実行
│
├─ AI設計を理解したい
│  └→ doc/design_strongest.md を読む
│
├─ 80%達成の経緯を知りたい
│  └→ AI_IMPROVEMENT_REPORT_2026_01_20.md を読む
│
└─ どのファイルを使うべきかわからない
   └→ WHICH_FILE_TO_USE.md を読む ⭐
```

---

## 🚫 使わなくていいファイル

以下は過去のバージョンや開発ログなので、通常は見る必要がありません：

- `src/archive/` - 過去のAIバージョン（性能が低い）
- `reports_archive/` - 過去の開発レポート
- `doc/archive/` - 古いドキュメント
- `doc/logs/` - 開発ログ（詳細な経緯）

---

## ✨ 最小限の手順（初心者向け）

### ステップ1: ベンチマーク実行
```bash
cd src
python benchmark.py
```

### ステップ2: 結果確認
```
AI Win Rate: 8/10 (80.0%)  ← これが見えればOK！
```

### ステップ3: 提出ファイルをコピー
```bash
cat src/submission.py  # 内容を確認
```

### ステップ4: Colabにペースト
Google Colab で新しいノートブックを作成し、`submission.py` の内容をコピー＆ペースト。

**完了！** 🎉

---

## 📚 さらに詳しく知りたい場合

- **[WHICH_FILE_TO_USE.md](WHICH_FILE_TO_USE.md)** - どのファイルを使うべきか完全ガイド
- **[README.md](README.md)** - プロジェクト全体の詳細説明
- **[QUICKSTART.md](QUICKSTART.md)** - クイックスタートガイド

---

**最終更新**: 2026年1月20日  
**構造バージョン**: v2.0（整理・簡潔化版）
