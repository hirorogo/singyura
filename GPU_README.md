# GPU加速とAI最適化

## 概要

このプロジェクトは、7並べゲームのAIをGPU対応に改良し、最強のAIを目指すものです。

## 主な改善点

### 1. GPU加速対応
- **CuPy統合**: CUDA対応GPUを使用した並列計算
- **自動フォールバック**: GPUが利用できない場合は自動的にCPUを使用
- **シミュレーション数の大幅増加**: GPU使用時は2000回（CPU時の10倍）

### 2. アルゴリズム改善
- **PASS戦略の最適化**: 合法手がある場合はPASSを含めない（探索分散を防ぐ）
- **バッチ処理**: GPU使用時はバッチサイズ10で並列処理を最適化

## セットアップ

### CPU版（デフォルト）
```bash
pip install -r requirements.txt
python src/main.py
```

### GPU版（CUDA 12.x）
```bash
# CUDA 12.xがインストール済みであることを確認
pip install cupy-cuda12x>=12.0.0
python src/main.py
```

### 他のCUDAバージョン
- CUDA 11.x: `pip install cupy-cuda11x`
- CUDA 11.2-11.8: `pip install cupy-cuda11x`

詳細は[CuPy公式ドキュメント](https://docs.cupy.dev/en/stable/install.html)を参照してください。

## パフォーマンス

### シミュレーション設定

| モード | SIMULATION_COUNT | SIMULATION_DEPTH |
|--------|------------------|------------------|
| CPU    | 200              | 200              |
| GPU    | 2000             | 300              |

### 期待される改善

1. **速度**: GPU使用時、CPU比で5-10倍の高速化
2. **精度**: シミュレーション数10倍により、より正確な判断
3. **勝率**: 44% → 60%+ を目標（ランダムAI相手）

## 実装の詳細

### GPU対応の仕組み

```python
# GPU検出とモジュール選択
try:
    import cupy as cp
    GPU_AVAILABLE = cp.cuda.is_available()
    xp = cp if GPU_AVAILABLE else np
except ImportError:
    xp = np
    GPU_AVAILABLE = False
```

### 配列操作の統一

- `numpy` と `cupy` のAPIは互換性があるため、`xp`を使用することで同じコードでGPU/CPUの両方に対応
- `field_cards` などの配列操作は自動的にGPU上で実行される

### バッチ処理

```python
# GPU使用時はバッチサイズを増やして並列処理を最適化
batch_size = 10 if GPU_AVAILABLE else 1
```

## ベンチマーク実行

```bash
# 100ゲームでベンチマーク
python src/benchmark.py

# カスタムゲーム数
python -c "from benchmark import run_benchmark; run_benchmark(50)"
```

## 技術スタック

- **Python 3.8+**
- **NumPy**: CPU用の数値計算ライブラリ
- **CuPy**: GPU用の数値計算ライブラリ（オプション）
- **CUDA 12.x**: GPU並列計算プラットフォーム（オプション）

## トラブルシューティング

### CuPyのインストールエラー

CUDAのバージョンを確認:
```bash
nvcc --version
nvidia-smi
```

適切なCuPyバージョンをインストール:
```bash
pip install cupy-cuda11x  # CUDA 11.x用
pip install cupy-cuda12x  # CUDA 12.x用
```

### メモリ不足

GPU RAMが不足する場合、シミュレーション数を減らす:
```python
# main.py内で調整
SIMULATION_COUNT = 1000  # 2000から減らす
```

## 貢献

改善提案やバグ報告は Issue または Pull Request でお願いします。

## ライセンス

このプロジェクトはオープンソースです。
