# クイックスタートガイド

## 🚀 5分で始める七並べAI

## 📓 **提出用ファイル（Jupyter Notebook形式）**

### ステップ1: Notebook を開く

**Google Colab で開く（推奨）:**
1. [Open in Colab](https://colab.research.google.com/github/hirorogo/singyura/blob/main/submission.ipynb)
2. すべてのセルを実行（Runtime > Run all）
3. ベンチマークで勝率を確認

**ローカルで開く:**
```bash
# Jupyter をインストール
pip install jupyter notebook numpy

# Notebook を開く
jupyter notebook submission.ipynb
```

**これだけ！** submission.ipynb が最終提出ファイルです。

---

## 🐍 **Python スクリプト版（開発・テスト用）**

### ステップ1: スクリプトをテスト

```bash
# リポジトリのルートディレクトリで
python submission.py
```

**これだけ！** 標準ライブラリ（+ numpy）のみで動作します。

---

## 📊 ベンチマークで勝率を確認

```bash
# 開発版でベンチマーク
cd src
python benchmark_improved.py
```

**期待される結果:**
```
AI Win Rate: 55/100 (55.0%)  # 55-60%を期待
```

**注**: `submission.py` は大会提出用の最終版です。ベンチマークは開発版（src/）で行ってください。

---

## 🎮 バージョン選択

### どちらを使うべき？

#### 大会提出 → `submission.ipynb` ⭐⭐⭐

**Jupyter Notebook形式（推奨）:**
```bash
jupyter notebook submission.ipynb
```

または [Google Colab](https://colab.research.google.com/github/hirorogo/singyura/blob/main/submission.ipynb)

**理由:**
- ✅ 大会フォーマットに準拠（Jupyter Notebook形式）
- ✅ Colab で簡単に実行可能
- ✅ Phase 1改善を含む最適化済み
- ✅ 勝率55-60%（期待値）

#### 開発・テスト → `submission.py` ⭐⭐

**Python スクリプト版:**
```bash
python submission.py
```

**理由:**
- ✅ コマンドラインから簡単実行
- ✅ 自動化・CI/CD に統合しやすい
- ✅ Notebook と同じコード

#### ローカル開発 → `main_gpu.py` ⭐⭐⭐

```bash
# 初回のみ
pip install cupy-cuda12x  # NVIDIA GPU
# または
pip install torch  # NVIDIA/Apple Silicon

# 実行
python main_gpu.py
```

**理由:**
- ✅ GPU高速化（5倍）
- ✅ 多数のシミュレーション
- ✅ 自動フォールバック

---

## 🔧 カスタマイズ

### シミュレーション回数を変更

**Notebook版:**
```python
# submission.ipynb の「設定」セル
SIMULATION_COUNT = 300  # 100～500に調整可能
```

**スクリプト版:**
```python
# submission.py の先頭（行10付近）
SIMULATION_COUNT = 300  # 100～500に調整可能
```

**目安:**
- 100: 高速（勝率50-55%）
- 200: バランス（勝率55-60%）⭐推奨
- 500: 高精度（勝率60-65%）※遅い

### Phase 1機能について

`submission.ipynb` および `submission.py` では以下の改善が有効になっています：
- ✅ PASS除外（合法手があれば必ず打つ）
- ✅ 重み付け確定化（パス履歴を考慮）
- ✅ 適応的ロールアウト（戦略的シミュレーション）

これらは `src/main_improved.py` で開発・テストされたものです。

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
