# 大会提出ガイド

このガイドは、Singularityバトルクエスト決勝大会「AI 7並べ (XQ)」への提出手順を説明します。

## 📄 提出ファイル

### メインファイル: `submission.py`

リポジトリのルートディレクトリにある **`submission.py`** が大会提出用のファイルです。

```bash
singyura/
├── submission.py  ← これを提出！
├── README.md
└── ...
```

## ✅ 提出前チェックリスト

提出前に以下を確認してください：

### 1. ファイルの確認
- [ ] `submission.py` を使用
- [ ] ファイルサイズが適切（約20KB）
- [ ] 不要なデバッグコードがない

### 2. 設定の確認
```python
# submission.py の先頭部分
MY_PLAYER_NUM = 0           # ✓ 必ず 0
SIMULATION_COUNT = 300      # ✓ 推奨値（100-500で調整可）
```

### 3. 動作確認
```bash
# エラーなく実行できることを確認
python submission.py

# 出力例:
# ✓ Game completed successfully
# または何も表示されない（正常）
```

### 4. インポートの確認
```python
# submission.py で使用しているライブラリ
from enum import Enum      # ✓ 標準ライブラリ
import random              # ✓ 標準ライブラリ
import numpy as np         # ✓ 許可されたライブラリ
```

**注意**: 大会環境では numpy は利用可能です。他の外部ライブラリは使用していません。

### 5. my_AI関数の確認
```python
def my_AI(state):
    """提出用のAI関数
    
    Returns:
        (action, pass_flag): 出すカードとパスフラグのタプル
    """
    return ai_instance.get_action(state)
```

- ✓ 引数: `state` (State オブジェクト)
- ✓ 戻り値: `(action, pass_flag)` のタプル
  - `action`: Card オブジェクト、または None/[]（パスの場合）
  - `pass_flag`: 0 または 1（1の場合は意図的なパス）

## 🎯 性能目標

### 期待される性能
- **勝率**: 55-60%（ランダムAI × 2人相手）
- **処理速度**: 約0.3秒/ゲーム
- **理論ベースライン**: 33.3%（ランダム選択時）

### ベンチマーク方法
```bash
cd src
python benchmark_improved.py
```

**期待される出力:**
```
Benchmark Result (100 games)
Time: 31.00 seconds (0.31 s/game)
AI Win Rate: 57/100 (57.0%)
Details: P0: 57/100 (57.0%), P1: 21/100 (21.0%), P2: 22/100 (22.0%)
```

## 📋 提出手順

### Colabノートブック形式の場合

1. **submission.py の内容をコピー**
   ```bash
   cat submission.py | pbcopy  # macOS
   # または
   cat submission.py  # 手動でコピー
   ```

2. **Colabのセルにペースト**
   - 大会提供のColabノートブックを開く
   - 指定されたセル（通常は `my_AI` セル）に内容をペースト
   - `MY_PLAYER_NUM = 0` が先頭にあることを確認

3. **動作確認**
   - Colabで実行してエラーがないことを確認
   - サンプルゲームで動作テスト

### ファイルアップロード形式の場合

1. **submission.py をそのままアップロード**
   - ファイル名が `submission.py` または指定された名前であることを確認

2. **動作確認**
   - アップロード後の動作確認機能でテスト

## 🔧 トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'numpy'`

**解決策:**
```bash
# ローカル環境の場合
pip install numpy

# Colab環境の場合（通常は不要）
!pip install numpy
```

### エラー: `AttributeError: 'list' object has no attribute 'suit'`

**原因**: Card オブジェクトの比較エラー

**解決策**: 最新版の `submission.py` を使用してください（修正済み）

### 動作が遅い

**対策1**: シミュレーション回数を減らす
```python
SIMULATION_COUNT = 100  # 300から減らす
```

**対策2**: タイムアウト設定を確認
- 大会環境のタイムアウト設定に合わせて調整

### メモリ不足

**対策**: シミュレーション回数を減らす
```python
SIMULATION_COUNT = 100  # メモリ使用量を削減
```

## 💡 パラメータチューニング

### SIMULATION_COUNT の調整

| 値 | 勝率 | 速度 | 推奨 |
|----|------|------|------|
| 100 | 50-55% | 速い | 速度優先時 |
| 200 | 55-58% | 普通 | バランス |
| **300** | **55-60%** | やや遅 | **推奨** ⭐ |
| 500 | 60-65% | 遅い | 精度優先時 |

**推奨**: `SIMULATION_COUNT = 300`
- 勝率と速度のバランスが最適
- 大会環境で安定動作

## 📊 実装内容

### AI戦略（PIMC法）

submission.py に実装されている主な戦略：

1. **Phase 1: 推論（Inference）**
   - CardTracker で相手の手札を推論
   - パス履歴から「持っていないカード」を特定

2. **Phase 2: 確定化（Determinization）**
   - 推論結果を元に仮想世界を複数生成
   - 重み付けで精度向上

3. **Phase 3: プレイアウト（Playout）**
   - 各仮想世界でシミュレーション
   - 戦略的ロールアウト（端優先、セーフムーブ優先）

### Phase 1改善

- ✅ **PASS除外**: 合法手があれば必ず打つ
- ✅ **重み付け確定化**: パス回数を考慮した推論
- ✅ **適応的ロールアウト**: 戦略的シミュレーション

## 📚 参考資料

### 開発用ファイル
- `src/main_improved.py` - 開発版（提出版のベース）
- `src/benchmark_improved.py` - ベンチマークツール
- `doc/phase1_improvements.md` - 実装詳細

### ドキュメント
- `README.md` - プロジェクト全体の説明
- `QUICKSTART.md` - クイックスタート
- `CONTRIBUTING.md` - 開発ガイド
- `reference/README.md` - 参考コード

## ❓ よくある質問

### Q1: submission.py と main_improved.py の違いは？

**A**: 基本的に同じAIですが：
- `submission.py`: 大会提出用に最適化・クリーンアップ
- `main_improved.py`: 開発・実験用（ベンチマーク機能付き）

### Q2: パラメータは変更していいですか？

**A**: はい、以下のパラメータは調整可能です：
- `SIMULATION_COUNT`: シミュレーション回数（推奨: 300）
- その他の戦略パラメータ

ただし、`MY_PLAYER_NUM = 0` は変更しないでください。

### Q3: ベンチマーク結果が低い場合は？

**A**: 
1. `SIMULATION_COUNT` を増やす（300 → 500）
2. ベンチマークはランダムAI相手なので、AI同士の大会では勝率が向上する可能性あり
3. 複数回テストして平均を確認

### Q4: 大会環境で動かない場合は？

**A**:
1. 最新版の `submission.py` を使用
2. Python バージョンを確認（3.7以上推奨）
3. numpy がインストールされているか確認
4. エラーメッセージを確認して対応

## 🎉 提出完了後

提出後は以下を確認してください：

1. **動作確認**: 大会システムでの動作確認
2. **ログ確認**: エラーログがないか確認
3. **結果確認**: テストマッチの結果を確認

## 📞 サポート

問題が解決しない場合：
1. GitHub Issue を作成
2. エラーメッセージと環境情報を添付
3. プロジェクトのREADME.mdを参照

---

**Good Luck! 🍀**

最終更新: 2026年1月17日
