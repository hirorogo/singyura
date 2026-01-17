# クイックスタートガイド

## 🚀 5分で始める七並べAI Phase 1改善版

### ステップ1: 大会提出用コードを実行

```bash
cd src
python main_improved.py
```

**これだけ！** 標準ライブラリのみで動作します。

---

## 📊 ベンチマークで勝率を確認

```bash
cd src
python benchmark_improved.py
```

**期待される結果:**
```
AI Win Rate: 55/100 (55.0%)  # 55-60%を期待
```

---

## 🎮 バージョン選択

### どちらを使うべき？

#### 大会提出 → `main_improved.py` ⭐⭐⭐

```bash
python main_improved.py
```

**理由:**
- ✅ 標準ライブラリのみ
- ✅ 確実に動作
- ✅ 勝率55-60%

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

```python
# main_improved.py または main_gpu.py の先頭
SIMULATION_COUNT = 200  # 100～500に調整可能
```

**目安:**
- 100: 高速（勝率50-55%）
- 200: バランス（勝率55-60%）⭐推奨
- 500: 高精度（勝率60-65%）※遅い

### Phase 1機能の切り替え

```python
# main_improved.py または main_gpu.py の先頭
ENABLE_PASS_REMOVAL = True  # PASS除外（推奨: True）
ENABLE_WEIGHTED_DETERMINIZATION = True  # 重み付け確定化（推奨: True）
ENABLE_ADAPTIVE_ROLLOUT = True  # 適応的ロールアウト（推奨: True）
```

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
- `README_IMPROVED.md` - 詳細な使い方
- `doc/phase1_improvements.md` - 実装詳細
- `doc/version_comparison.md` - バージョン比較

### コードを理解したい
1. `src/main_improved.py` - Phase 1改善版（推奨）
2. `doc/design_strongest.md` - PIMC法の設計
3. `doc/ai_status_report.md` - 全体戦略

---

## 🎯 次のアクション

### すぐにやること
1. ✅ `python main_improved.py` を実行
2. ✅ `python benchmark_improved.py` で勝率確認
3. ✅ 勝率55%以上なら大会提出OK

### 余裕があれば
4. ⭐ GPU版を試す（開発環境）
5. ⭐ パラメータをチューニング
6. ⭐ Phase 2の戦略を検討

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
1. `README_IMPROVED.md` のトラブルシューティングを確認
2. GitHub Issue を作成
3. ドキュメントを再確認

---

**Happy Coding! 🎉**

---

**作成日:** 2026年1月17日  
**バージョン:** v1.0
