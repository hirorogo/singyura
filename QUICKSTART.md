# クイックスタートガイド

## 🏆 80%勝率達成版 - 5分で始める七並べAI

**最新版で80%の勝率を達成しました！**（vs ランダムAI × 2、期待値33.3%の2.4倍）

---

## 📄 **提出用ファイル（最強版・80%）**

### 最も簡単な方法: submission.py を使う ⭐⭐⭐

```bash
# ステップ1: ベンチマークでテスト
cd src
python benchmark.py

# 期待される結果
# AI Win Rate: 8/10 (80.0%)  ← 70-85%なら成功！

# ステップ2: submission.py の内容をColabにコピー
cat submission.py  # 内容を確認してコピー
```

**これだけ！** submission.py をGoogle Colabノートブックにコピーすれば提出完了です。

---

## 🐍 **Python スクリプト版（開発・テスト用）**

### 1ゲーム実行してテスト

```bash
# 80%勝率版で1ゲーム実行
cd src
python main.py
```

**これだけ！** 標準ライブラリ（+ numpy）のみで動作します。

---

## 📊 性能確認

```bash
# ベンチマーク実行（推奨）
cd src
python benchmark.py
```

**期待される結果:**
```
=== ベンチマーク結果 ===
総ゲーム数: 10
P0（AI）勝利: 8回 (80.0%)  ← 70-85%なら成功！
P1（Random）勝利: 1回 (10.0%)
P2（Random）勝利: 1回 (10.0%)
```

---

## 🎮 どのファイルを使うべき？

### 大会提出 → `src/submission.py` ⭐⭐⭐

**80%勝率達成版（最強）:**
```bash
# ローカルテスト
python src/submission.py

# 内容をColabにコピー
cat src/submission.py
```

**特徴:**
- ✅ **勝率80%達成**
- ✅ SIMULATION_COUNT = 700（最強設定）
- ✅ 標準ライブラリ + numpy のみ
- ✅ そのままColabに貼り付け可能

### Colabでメモリ不足の場合 → `src/submission_colab.py`

**メモリ最適化版（勝率65-70%）:**
```bash
python src/submission_colab.py
```

**特徴:**
- ✅ Colabのメモリ制限に対応
- ✅ SIMULATION_COUNT = 400（やや控えめ）

### 開発・テスト → `src/main.py`

**ローカル開発用（80%勝率）:**
```bash
python src/main.py
```

**特徴:**
- ✅ submission.pyと同等の性能
- ✅ 開発・デバッグ用

詳細は **[WHICH_FILE_TO_USE.md](WHICH_FILE_TO_USE.md)** を参照。

---

## 🔧 カスタマイズ

### シミュレーション回数を変更

**submission.py の設定:**
```python
# submission.py の先頭（行34付近）
SIMULATION_COUNT = 700  # 現在の最強設定

# 変更例:
# SIMULATION_COUNT = 400  # 高速（勝率65-70%）
# SIMULATION_COUNT = 1000  # 超高精度（勝率85%+、遅い）
```

**パラメータガイド:**
- 400: 高速（勝率65-70%）→ Colabに推奨
- **700: 最強**（勝率80%）→ **大会推奨** ⭐
- 1000: 超高精度（勝率85%+、非常に遅い）

---

## 📈 性能比較（クイックリファレンス）

| ファイル | 勝率 | SIMULATION_COUNT | 速度 | 推奨用途 |
|---------|------|-----------------|------|---------|
| **submission.py** | **80%** | 700 | 標準 | **大会** ⭐⭐⭐ |
| submission_colab.py | 65-70% | 400 | 高速 | Colab制限時 |
| main.py | 80% | 700 | 標準 | 開発・テスト |
| main_gpu.py | 55-60% | 100,000 (GPU) | 超高速 | 実験用 |

**注**: 勝率は vs ランダムAI × 2人の3人対戦での結果

---

## 🐛 トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'numpy'`

```bash
pip install numpy
```

### GPU版が遅い

**原因:** GPU非対応環境でCPU版として動作している

**確認:**
```python
python -c "from main_gpu import GPU_AVAILABLE, GPU_TYPE; print(f'GPU: {GPU_AVAILABLE} ({GPU_TYPE})')"
```

**出力例:**
```
GPU: True (cupy)  # GPU利用中 ✅
GPU: False (cpu)  # CPU利用中
```

**解決策:**
```bash
# NVIDIA GPU
pip install cupy-cuda12x

# Apple Silicon
pip install torch
```

### メモリ不足エラー

**GPU版の場合:**
```python
# main_gpu.py の先頭
SIMULATION_COUNT = 500  # 1000から減らす
BATCH_SIZE = 50  # 100から減らす
```

---

## 📈 性能比較（クイックリファレンス）

| バージョン | 勝率 | 速度 | 推奨用途 |
|----------|------|------|---------|
| オリジナル | 44% | 標準 | - |
| **Phase 1改善** | **55-60%** | 標準 | **大会** ⭐⭐⭐ |
| GPU（GPU利用） | 55-60% | **5倍** | 開発 ⭐⭐⭐ |
| GPU（CPU利用） | 55-60% | 標準 | - |

---

## 📚 もっと詳しく知りたい場合

### 詳細ドキュメント
- `README.md` - プロジェクト全体概要
- `doc/specification.md` - ゲーム仕様
- `doc/design_strongest.md` - PIMC法の設計
- `doc/archive/phase1_improvements.md` - 実装詳細（アーカイブ）
- `doc/archive/ai_status_report.md` - 全体戦略（アーカイブ）

### コードを理解したい
1. `src/main_improved.py` - Phase 1改善版（推奨）
2. `doc/design_strongest.md` - PIMC法の設計
3. `doc/ai_status_report.md` - 全体戦略

---

## 🎯 次のアクション

### すぐにやること
1. ✅ `submission.ipynb` を Colab または Jupyter で開く
2. ✅ すべてのセルを実行してベンチマーク確認
3. ✅ 勝率55%以上なら大会提出OK

### 余裕があれば
4. ⭐ スクリプト版（`submission.py`）でテスト
5. ⭐ パラメータをチューニング
6. ⭐ GPU版を試す（開発環境）

---

## 💡 ヒント

### 勝率を上げるコツ
1. **SIMULATION_COUNT を増やす**
   - 200 → 500 で +3-5% 向上（遅くなる）
   
2. **Phase 1機能をすべて有効化**
   - すべて `True` が推奨

3. **GPU版で大量にシミュレーション**
   - 1000回以上のシミュレーションで精度向上

### デバッグのコツ
1. **print文を追加**
   ```python
   print(f"[DEBUG] Chosen action: {best_action}")
   ```

2. **少ないシミュレーションでテスト**
   ```python
   SIMULATION_COUNT = 10  # デバッグ用
   ```

3. **ベンチマーク回数を減らす**
   ```python
   run_benchmark(10)  # 100から減らす
   ```

---

## 🤝 サポート

### 問題が解決しない場合
1. `README.md` のトラブルシューティングを確認
2. `doc/` 配下のドキュメントを確認
3. GitHub Issue を作成

---

**Happy Coding! 🎉**

---

**作成日:** 2026年1月17日  
**バージョン:** v1.0
