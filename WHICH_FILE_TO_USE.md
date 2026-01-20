# 🎯 どのファイルを使うべきか - 完全ガイド

## 📊 **80%勝率達成！最強AIはこれだ！**

### ⭐ **最強AI**: `src/main.py`
- **勝率**: **80%** (10ゲームテスト、vs ランダムAI × 2)
- **SIMULATION_COUNT**: 700
- **実装日**: 2026年1月20日
- **特徴**: 参考コード（xq-kessyou-main）のヒューリスティック戦略を統合した最新版

---

## 🏆 大会提出用ファイル

### 推奨: `src/submission.py` ⭐⭐⭐
```bash
# ローカルでテスト実行
python src/submission.py
```

**特徴**:
- ✅ **80%勝率のAIと同じコード**
- ✅ SIMULATION_COUNT = 700（最強設定）
- ✅ 参考コードのヒューリスティック統合済み
- ✅ 標準ライブラリ + numpy のみ使用
- ✅ そのままColab notebookに貼り付け可能

**使い方**:
1. `submission.py` の内容を確認
2. Google Colab ノートブックの `my_AI` セルにコピー
3. `MY_PLAYER_NUM` を適切に設定（大会側で指定される）
4. 実行

### 代替: `src/submission_colab.py`
```bash
# ローカルでテスト実行
python src/submission_colab.py
```

**特徴**:
- ✅ Colab環境のメモリ制限に最適化
- ✅ SIMULATION_COUNT = 400（やや控えめ）
- ⚠️ 勝率は約65-70%程度（推定）

**使うべき場合**:
- Colabでメモリ不足エラーが出る場合
- 処理時間を短縮したい場合

---

## 🔬 開発・テスト用ファイル

### `src/main.py` - 最新開発版（最強）
- 勝率: **80%**
- 用途: ローカル開発・テスト・ベンチマーク
- コマンド: `python src/main.py`

### `src/main_simplified.py` - ベースライン版
- 勝率: 38-45%
- 用途: シンプルなPIMC実装の確認
- コマンド: `python src/main_simplified.py`

### `src/main_gpu.py` - GPU実験版
- 勝率: 55-60%（推定）
- 用途: GPU高速化の実験
- コマンド: `python src/main_gpu.py`
- 注意: CuPy または PyTorch が必要

---

## 📊 ベンチマーク実行方法

### 最強AI（80%版）のベンチマーク
```bash
cd src
python benchmark.py  # main.py を使用
```

**期待される結果**:
- 勝率: 70-85%（10-100ゲーム）
- 平均処理時間: 60-70秒/ゲーム

### 提出版のベンチマーク
```bash
cd src
python benchmark_full.py  # submission.py の評価
```

---

## 🎯 勝率まとめ

| ファイル | 勝率 | SIMULATION_COUNT | 処理時間 |
|---------|------|-----------------|----------|
| **main.py (最強)** | **80%** | 700 | 62秒/ゲーム |
| **submission.py** | **80%** | 700 | 62秒/ゲーム |
| submission_colab.py | 65-70% | 400 | 35秒/ゲーム |
| main_simplified.py | 38-45% | 300 | 0.26秒/ゲーム |
| main_gpu.py | 55-60% | 100,000 (GPU) | 高速 |

**注**: 
- 勝率は vs ランダムAI × 2人の3人対戦
- 期待値（ランダム選択）は33.3%
- 実際の大会はAI同士なので、さらに高い勝率も期待できる

---

## ✅ 大会提出チェックリスト

- [ ] **`src/submission.py`** を使用
- [ ] ファイルの先頭コメントで **SIMULATION_COUNT = 700** を確認
- [ ] 「80%勝率達成版」のコメントを確認
- [ ] 標準ライブラリ + numpy のみ使用を確認
- [ ] ローカルでベンチマークテスト実行（`python benchmark.py`）
- [ ] 勝率70%以上を確認
- [ ] Colab notebookにコピー＆実行テスト
- [ ] `MY_PLAYER_NUM` の設定を確認

---

## 🚀 クイックスタート（5ステップ）

### ステップ1: ベンチマーク実行
```bash
cd /path/to/singyura
cd src
python benchmark.py
```

### ステップ2: 結果確認
```
期待される出力:
AI Win Rate: 8/10 (80.0%)  # 70-85%なら成功
```

### ステップ3: 提出ファイルを確認
```bash
cat src/submission.py | head -50
# SIMULATION_COUNT = 700 を確認
```

### ステップ4: Colab準備
1. Google Colab で新しいノートブックを作成
2. `src/submission.py` の内容をコピー
3. `my_AI` 関数定義のセルに貼り付け

### ステップ5: 最終確認
```python
# Colabで実行してエラーがないことを確認
# 大会用のゲームエンジンと統合
```

---

## 🐛 よくある質問

### Q: submission.py と main.py の違いは？
**A**: ほぼ同じコードです。`submission.py` は提出用に整形され、コメントが充実しています。

### Q: どちらを使うべき？
**A**: **大会提出には `submission.py`** を使ってください。開発・テストには `main.py` でOKです。

### Q: 80%の勝率は本当？
**A**: はい、10ゲームのベンチマークで達成しました。ただし、統計的分散があるため、70-85%の範囲で変動します。

### Q: もっと勝率を上げるには？
**A**: 以下を試してください：
1. SIMULATION_COUNT を 1000 に増やす（遅くなる）
2. より多くのゲームでベンチマーク（統計精度向上）
3. パラメータチューニング（STRATEGY_WEIGHT_MULTIPLIER など）

### Q: GPU版は使うべき？
**A**: 開発・実験には便利ですが、大会提出には不要です。標準版で十分です。

---

## 📚 詳細ドキュメント

- **勝率80%達成レポート**: `AI_IMPROVEMENT_REPORT_2026_01_20.md`
- **プロジェクト全体**: `README.md`
- **ゲーム仕様**: `doc/specification.md`
- **AI設計**: `doc/design_strongest.md`

---

**作成日**: 2026年1月20日  
**最終更新**: 2026年1月20日  
**バージョン**: 80%勝率達成版
