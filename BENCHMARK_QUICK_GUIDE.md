# ベンチマーククイックガイド 🚀

## 📌 変更点（重要！）

以前の3つのベンチマークファイルが **1つに統合** されました！

### Before ❌
```bash
python benchmark.py          # 標準
python benchmark_full.py     # フル版
python benchmark_gpu.py      # GPU版
```

### After ✅
```bash
python benchmark.py [オプション]  # すべて統合！
```

---

## 🎯 よく使うコマンド

### 標準実行（100ゲーム）
```bash
cd src
python benchmark.py
```

### 素早くテスト（10ゲーム）
```bash
python benchmark.py --games 10
```

### 高精度テスト（1000ゲーム）
```bash
python benchmark.py --games 1000
```

### シミュレーション回数を指定
```bash
python benchmark.py --simulations 500
```

### GPU使用（CuPy必要）
```bash
python benchmark.py --gpu
```

### すべて指定
```bash
python benchmark.py --games 500 --simulations 700 --gpu
```

---

## 📊 期待される結果

- **勝率**: 70-85%（vs ランダムAI × 2）
- **ベースライン**: 33.3%（ランダム選択の期待値）
- **処理時間**: 約60-70秒/ゲーム（SIMULATION_COUNT=700時）

---

## 💡 ヘルプ

```bash
python benchmark.py --help
```

すべてのオプションと使い方を表示します。

---

## 📚 詳細情報

- **完全ガイド**: `BENCHMARK_CONSOLIDATION_SUMMARY.md`
- **使い方**: `WHICH_FILE_TO_USE.md`
- **プロジェクト**: `README.md`

---

**最終更新**: 2026年1月20日  
**問題解決**: "ベンチマーク複数あってこまる" ✅ 完了
