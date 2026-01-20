# src/ - ソースコード

## 🏆 80%勝率達成版（最強・最新）

### ⭐ main.py - 開発・テスト用（最強版）
- **勝率**: **80%** (vs ランダムAI × 2)
- **SIMULATION_COUNT**: 700
- **用途**: ローカル開発・テスト・ベンチマーク
- **実行**: `python main.py`

### ⭐ submission.py - 大会提出用（最強版）
- **勝率**: **80%** (main.pyと同等)
- **SIMULATION_COUNT**: 700
- **用途**: 大会提出（Colabノートブックにコピー）
- **実行**: `python submission.py`
- **特徴**: コメント充実、提出用に整形

### submission_colab.py - Colab最適化版
- **勝率**: 65-70%（推定）
- **SIMULATION_COUNT**: 400
- **用途**: Colabでメモリ制限がある場合
- **実行**: `python submission_colab.py`

---

## 🔬 開発・実験用

### main_gpu.py - GPU高速化版
- **勝率**: 55-60%（推定）
- **SIMULATION_COUNT**: 100,000 (GPU時)
- **用途**: GPU環境での高速シミュレーション
- **実行**: `python main_gpu.py`
- **必要**: CuPy または PyTorch

---

## 📊 ベンチマーク

### benchmark.py - 統合ベンチマーク（推奨）⭐
- **対象**: main.py（80%勝率版）
- **実行**: `python benchmark.py` または `python benchmark.py --help` でオプション表示
- **期待結果**: 70-85%の勝率
- **特徴**: コマンドライン引数でカスタマイズ可能
  - `--games N`: ゲーム数を指定（デフォルト: 100）
  - `--simulations N`: シミュレーション回数を指定
  - `--gpu`: GPU使用（CuPy必要）
  - `--progress-interval N`: 進捗表示の間隔

**使用例**:
```bash
# 標準（100ゲーム）
python benchmark.py

# 1000ゲームでテスト
python benchmark.py --games 1000

# シミュレーション回数を指定
python benchmark.py --simulations 500

# GPU使用
python benchmark.py --gpu

# すべてのオプションを組み合わせ
python benchmark.py --games 500 --simulations 700 --gpu
```

**注**: 以前の `benchmark_full.py` と `benchmark_gpu.py` は統合され、`archive/` に移動しました。

---

## 📁 アーカイブ

### archive/ - 過去のバージョン
- main_improved.py（31-40%勝率、過剰最適化版）
- main_simplified.py（38-45%勝率、シンプル版）
- debug_*.py（デバッグ用）

詳細は `archive/README.md` を参照。

---

## 🚀 クイックスタート

### 1. ベンチマーク実行（80%版）
```bash
python benchmark.py
# 期待: 70-85%の勝率
```

### 2. 1ゲーム実行
```bash
python main.py
# 80%勝率版のAIで1ゲーム実行
```

### 3. 提出ファイル確認
```bash
cat submission.py | head -50
# SIMULATION_COUNT = 700 を確認
```

---

## 📚 詳細情報

- **使い方の完全ガイド**: `../WHICH_FILE_TO_USE.md`
- **80%達成レポート**: `../AI_IMPROVEMENT_REPORT_2026_01_20.md`
- **プロジェクト全体**: `../README.md`

---

**最終更新**: 2026年1月20日  
**最強版**: main.py & submission.py（80%勝率）
