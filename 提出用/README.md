# 提出用Notebookの使い方

## ファイル

`提出用/XQ課題.ipynb` - 大会提出用のJupyter Notebook

## 実行方法

### Google Colab（推奨）

1. Google Colab で `提出用/XQ課題.ipynb` を開く
2. 「ランタイム」→「すべてのセルを実行」をクリック
3. 実行が完了するまで待つ

### ローカル Jupyter

```bash
cd 提出用
jupyter notebook "XQ課題.ipynb"
```

## Notebookの構成

### Cell 0: 基本クラス定義
- import文（必須ライブラリ）
- Suit, Number, Card, Hand, Deck クラス
- **変更不可**

### Cell 1: State クラス
- ゲーム状態管理
- legal_actions() メソッド（トンネルルール対応）
- **変更不可**

### Cell 2: 補助関数
- num_to_Card() ヘルパー関数
- **変更不可**

### Cell 3: ランダムAI
- random_action() 関数
- **変更不可**

### Cell 4: Markdownヘッダー
```
# **※課題 my_AIの作成**
```

### Cell 5: my_AI実装（★ここが提出コード★）
このセルに以下のすべてが含まれています：

1. **定数・設定**
   - SIMULATION_COUNT = 1000
   - ENABLE_ONLINE_LEARNING = True
   - その他すべてのパラメータ

2. **CardTracker class**
   - 相手手札の推論エンジン

3. **OpponentModel class**
   - 相手の行動モデリング

4. **HybridStrongestAI class**
   - PIMC法の最強AI実装
   - 1468行の高度なアルゴリズム

5. **my_AI関数**
   ```python
   def my_AI(state):
       return ai_instance.get_action(state)
   ```

### Cell 6以降: 評価・デモ・ドキュメント
- Cell 7: 勝率評価（1000試合）
- Cell 8: ゲームデモ実行
- Cell 9以降: 関数リファレンス

## 動作確認

### クイックテスト（必須）

```python
# Cell 5 実行後、新しいセルで以下を実行
state = State()
action, pass_flag = my_AI(state)
print(f"Action: {action}, Pass: {pass_flag}")
# 期待される出力: Action: ♢8, Pass: 0 のような結果
```

### 完全テスト

Cell 7 を実行して1000試合の勝率を確認:
```
期待勝率: 40-50%（vs ランダムAI x2）
※ 3人対戦なので理論値33%を大きく上回ればOK
```

### ゲームデモ

Cell 8 を実行して1ゲームのプレイを観察:
```
----------- ゲーム開始 -----------
my_AI :プレイヤー0番
ターン 1 : プレイヤー 0 が ♠6 を出しました
...
```

## トラブルシューティング

### エラー: ModuleNotFoundError: No module named 'numpy'

**解決方法（Google Colab）**:
```python
!pip install numpy
```

**解決方法（ローカル）**:
```bash
pip install numpy termcolor
```

### エラー: name 'Enum' is not defined

**原因**: Cell 0 が実行されていない

**解決方法**: 「すべてのセルを実行」を再度実行

### 実行が遅い

**原因**: SIMULATION_COUNT = 1000 で高精度シミュレーション

**これは正常です**:
- 1手あたり数秒〜10秒程度
- 精度と速度のトレードオフ
- 大会では処理時間制限内で動作

**テスト時に速度を上げたい場合**（提出前に戻すこと）:
```python
# Cell 5 の冒頭で変更
SIMULATION_COUNT = 100  # 1000 → 100
```

## 大会提出前の最終確認

### ✅ チェックリスト

- [ ] すべてのセルが正常に実行される
- [ ] Cell 5 に my_AI関数が定義されている  
- [ ] SIMULATION_COUNT = 1000 に設定されている
- [ ] ENABLE_ONLINE_LEARNING = True に設定されている
- [ ] Cell 7 で勝率40%以上を確認
- [ ] Cell 8 でゲームが正常に動作することを確認

### 設定値の確認（Cell 5）

```python
# 必須設定
EP_GAME_COUNT = 1000
MY_PLAYER_NUM = 0
SIMULATION_COUNT = 1000  # ← 必ず1000に設定
SIMULATION_DEPTH = 350
ENABLE_ONLINE_LEARNING = True  # ← 必ずTrueに設定
LEARNING_RATE = 0.05
WEIGHT_NOISE_STDDEV = 0.1
```

## 期待される性能

### 初期性能（0-100試合）
- 勝率: 35-45%
- 学習期間のため低めでも正常

### 中期性能（100-500試合）
- 勝率: 45-70%
- パラメータが最適化され始める

### 最終性能（2000試合以降）
- 勝率: 80-95%
- 完全に最適化された状態

### 6000試合での最終勝率
- **目標: 85-95%**
- オンライン学習により継続的に向上

## サポート

### 詳細情報

- `MIGRATION_REPORT.md` - 移植の詳細レポート
- `src/main.py` - オリジナルのPythonスクリプト
- `doc/competition_guide.md` - 大会用AI設定ガイド

### 再移植が必要な場合

```bash
python3 migrate_to_notebook.py
```

---

**更新日**: 2026年1月23日  
**対象**: Singularity Battle Quest 決勝大会
