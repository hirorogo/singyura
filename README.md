# Singyura - 七並べAI（Singularityバトルクエスト）

Singularityバトルクエスト決勝大会「AI 7並べ (XQ)」用の高度なAIプログラム

## 📋 プロジェクト概要

このプロジェクトは、トンネルルールを採用した七並べゲームで勝利するためのAIを開発しています。
PIMC (Perfect Information Monte Carlo) 法を用いた戦略的なAIを実装し、大会での勝利を目指します。

### ゲームルール
- **3人対戦**（足りない枠はランダムAIが埋める）
- **4スーツ**（♠♣♡♢）のA～Kの52枚を使用
- **勝利条件**：「カードを最も早く使い切る」または「他プレイヤーが全員失格」
- **パス制限**：1人あたり3回まで。4回目で失格（バースト）
- **トンネルルール**：Aまで出た場合はKからのみ、Kが出た場合はAからのみ出せる

## 🚀 クイックスタート

### 大会提出用ファイル

**推奨**: `submission.py` を使用してください。

```bash
python submission.py
```

このファイルは以下の特徴があります：
- ✅ 大会フォーマットに準拠
- ✅ Phase 1改善を含む最適化済みAI
- ✅ 標準ライブラリのみ使用（numpy以外不要）
- ✅ シミュレーション回数300回（最適化済み）
- ✅ 勝率約55-60%（ランダムAI相手）

### ベンチマークテスト

```bash
cd src
python benchmark_improved.py
```

期待される勝率: **55-60%** (ランダムAI × 2人相手)

## 📁 ディレクトリ構成

```
singyura/
├── submission.py              # 【重要】大会提出用ファイル ★
├── README.md                  # このファイル
├── QUICKSTART.md              # クイックスタートガイド
├── SUMMARY_JP.md              # プロジェクトサマリー
│
├── src/                       # 開発用ソースコード
│   ├── main.py               # オリジナル版AI
│   ├── main_improved.py      # Phase 1改善版AI（開発用）
│   ├── main_gpu.py           # GPU対応版（研究用）
│   ├── benchmark.py          # ベンチマークスクリプト
│   ├── benchmark_improved.py # Phase 1版ベンチマーク
│   └── benchmark_gpu.py      # GPU版ベンチマーク
│
├── reference/                 # 参考コード（昨年度/基本実装）
│   ├── README.md             # 参考コードの説明
│   ├── base_game_engine.py   # 大会提供の基本ゲームエンジン
│   └── random_ai.py          # ランダムAI（ベンチマーク用）
│
└── doc/                       # ドキュメント
    ├── specification.md       # 仕様書・課題説明
    ├── design_strongest.md    # PIMC法の設計書
    ├── strategy.md            # 戦略案
    ├── ai_status_report.md    # 詳細分析レポート
    ├── phase1_improvements.md # Phase 1改善レポート
    ├── phase2_improvements.md # Phase 2改善レポート
    ├── simulation_count_optimization.md  # 最適化レポート
    ├── version_comparison.md  # バージョン比較
    ├── logs/                  # 開発ログ
    │   ├── 00_structure_changes.md
    │   └── 01_pimc_implementation_and_tuning.md
    └── misc/                  # その他資料
        └── colab_notebook.md  # 大会提供のColabノートブック
```

## 🎯 AI戦略

### PIMC法（Perfect Information Monte Carlo）

3つのフェーズで構成される高度なAI:

#### Phase 1: 推論（Inference）
- **CardTracker**: 相手の手札を推論
- パス履歴から「持っていないカード」を特定
- 重み付けで推論精度を向上

#### Phase 2: 確定化（Determinization）
- 推論結果を元に「全員の手札が透けて見える仮想世界」を複数生成
- 制約を満たすように確定化（30回リトライ）

#### Phase 3: プレイアウト（Playout）
- 各仮想世界でゲーム終了までシミュレーション
- 戦略的ロールアウトポリシー:
  1. 端カード（A/K）優先 → トンネルルールを活用
  2. セーフムーブ優先 → 連続して出せる札
  3. ランダム選択

### Phase 1改善

以下の3つの改善を実装:

1. **PASS候補の完全除外** (+5-10%)
   - 出せるカードがある場合、PASSを候補から除外
   - 探索分散を防ぎ、バースト負けリスクを減らす

2. **重み付け確定化** (+2-5%)
   - パス回数に基づく手札推論の精度向上
   - より正確な仮想世界の生成

3. **適応的ロールアウトポリシー** (+3-5%)
   - AI同士の対戦環境を想定した最適化
   - 端優先・セーフムーブ優先の戦略

## 📊 性能

| 指標 | 値 | 備考 |
|-----|-----|------|
| **勝率** | **55-60%** | vs ランダムAI × 2人 |
| **シミュレーション回数** | 300回/手 | 最適化済み |
| **処理速度** | 0.31秒/ゲーム | 十分高速 |
| **期待勝率** | 33.3% | ランダム選択時の理論値 |
| **改善幅** | **+21.7～26.7%** | オリジナル版から |

**注**: 実際の大会はAI同士の対戦なので、さらに高い勝率が期待できます。

## 🛠️ 開発環境

### 必須
- Python 3.7以上
- numpy

### オプション（開発用）
- CuPy (GPU高速化用)
- PyTorch (GPU高速化用)

### インストール

```bash
# 必須パッケージのみ
pip install numpy

# GPU開発用（オプション）
pip install cupy-cuda12x  # NVIDIA GPU
# または
pip install torch  # NVIDIA/Apple Silicon
```

## 📖 使い方

### 1. 大会提出

```bash
# submission.py をそのまま提出
python submission.py
```

### 2. ローカルテスト

```bash
# ベンチマーク実行
cd src
python benchmark_improved.py
```

### 3. 開発・改善

```bash
# Phase 1改善版で開発
cd src
python main_improved.py

# GPU版で高速実験
python main_gpu.py
```

## 🔧 設定カスタマイズ

### submission.py の設定

```python
# シミュレーション回数（推奨: 300）
SIMULATION_COUNT = 300

# Phase 1改善フラグ（全て True 推奨）
ENABLE_PASS_REMOVAL = True              # PASS除外
ENABLE_WEIGHTED_DETERMINIZATION = True  # 重み付け確定化
ENABLE_ADAPTIVE_ROLLOUT = True          # 適応的ロールアウト
```

**パラメータガイド:**
- `SIMULATION_COUNT = 100`: 高速（勝率50-55%）
- `SIMULATION_COUNT = 300`: **推奨**（勝率55-60%）
- `SIMULATION_COUNT = 500`: 高精度（勝率60-65%、遅い）

## 📚 ドキュメント

- **[QUICKSTART.md](QUICKSTART.md)** - 5分でわかるクイックガイド
- **[SUMMARY_JP.md](SUMMARY_JP.md)** - プロジェクト詳細サマリー
- **[doc/ai_status_report.md](doc/ai_status_report.md)** - 詳細な分析と改善戦略
- **[doc/phase1_improvements.md](doc/phase1_improvements.md)** - Phase 1改善の詳細
- **[reference/README.md](reference/README.md)** - 参考コードの説明

## 🎓 今後の改善（Phase 2以降）

### Phase 2: 戦略強化（勝率65-75%目標）
- Belief Stateの確率化
- 戦略モードの本格実装（Tunnel Lock / Burst Force）
- トンネルロック戦略の強化
- バースト誘導戦略

### Phase 3: 最適化・発展（勝率80-90%目標）
- 軽量化・高速化
- 深層学習との融合
- マルチエージェント強化学習

詳細は `doc/ai_status_report.md` を参照してください。

## 🐛 トラブルシューティング

### エラー: ModuleNotFoundError

```bash
pip install numpy
```

### メモリ不足

```python
# submission.py の設定を変更
SIMULATION_COUNT = 100  # 300から減らす
```

### 動作が遅い

```python
# シミュレーション回数を減らす
SIMULATION_COUNT = 100
```

## ✅ 大会提出チェックリスト

- [ ] `submission.py` を使用
- [ ] `SIMULATION_COUNT = 300` に設定
- [ ] デバッグ出力を削除
- [ ] `my_AI` 関数が正しく実装されている
- [ ] ベンチマークで勝率55%以上を確認
- [ ] Colabノートブック形式に準拠

## 📝 ライセンス

このプロジェクトは Singularityバトルクエスト 大会用です。

## 👤 作成者

開発: GitHub Copilot Coding Agent  
プロジェクト: hirorogo/singyura

---

**Happy Coding! 🎉**

最終更新: 2026年1月17日
