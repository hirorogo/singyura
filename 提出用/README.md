# 提出用 Jupyter Notebook

## 📓 ファイル: teishutu.ipynb

シンギュラリティバトルクエスト決勝大会用の七並べAIが実装されたJupyter Notebookです。

## ✅ 実装済み内容

### Cell 5: my_AI 関数

以下の高度なAIが実装されています：

#### 🧠 AI アーキテクチャ: HybridAI (PIMC法)

**PIMC (Perfect Information Monte Carlo) 法による高度な意思決定**

#### 📊 設定パラメータ

- **SIMULATION_COUNT**: 500回
  - Colab環境に最適化された設定
  - 目標勝率: 65-70% (期待値33.3%の約2倍)
  
- **SIMULATION_DEPTH**: 250手
  - シミュレーション深度

#### 🎯 実装済み戦略

1. **CardTracker（推論エンジン）**
   - 相手の手札を推論
   - パス観測による制約追加
   - 履歴リプレイによる精度向上

2. **Tunnel Lock 戦略**
   - トンネルルールを活用した封鎖戦略
   - A/Kの戦略的な使用

3. **Burst Force 戦略**
   - 相手のバースト（失格）を誘導
   - パス回数が多い相手を狙う

4. **Run 戦略**
   - 連続カードの優先出し
   - 手札の効率的な削減

5. **Endgame 戦略**
   - 終盤の手札枚数に応じた戦術切り替え
   - A/K優先度の動的調整

6. **Block 戦略**
   - 相手の出せるカードを制限
   - 推論結果を活用した妨害

7. **Advanced Heuristics**
   - 隣接カード分析
   - スート集中戦略
   - Safe move判定

## 🚀 使用方法

### Google Colab での使用

1. Google Colab で `teishutu.ipynb` を開く
2. すべてのセルを順番に実行
3. Cell 5 の `my_AI` 関数が自動的に登録される
4. ベンチマークセルで性能確認

### ローカル Jupyter での使用

```bash
cd 提出用
jupyter notebook teishutu.ipynb
```

## 📈 期待される性能

### 勝率
- **目標**: 65-70%（vs ランダムAI × 2人）
- **期待値**: 33.3%（ランダム選択の場合）
- **性能比**: 約2倍の勝率

### 処理時間
- 約35秒/ゲーム（SIMULATION_COUNT=500時）
- Colab環境での動作に最適化

## 🔧 カスタマイズ

### シミュレーション回数の調整

Cell 5 の冒頭で以下のパラメータを調整可能：

```python
SIMULATION_COUNT = 500  # デフォルト値

# 高速化したい場合（勝率やや低下）
SIMULATION_COUNT = 300

# 高精度にしたい場合（処理時間増加）
SIMULATION_COUNT = 700
```

### 戦略の有効/無効化

```python
ENABLE_TUNNEL_LOCK = True   # トンネルロック戦略
ENABLE_BURST_FORCE = True   # バースト誘導戦略
```

## 📝 注意事項

### 必要なライブラリ
- `random` (標準ライブラリ)
- `numpy` (通常Colabにプリインストール)

### ゲームエンジン
- Notebook内の Cell 0-3 に実装済み
- `Suit`, `Number`, `Card`, `Hand`, `State` クラスが定義済み

### MY_PLAYER_NUM
- デフォルト: 0
- 大会運営から指定がある場合は変更すること

## 🎮 テスト方法

### ベンチマーク実行

Cell 7 以降のベンチマークセルを実行：

```python
# ランダムAIとの対戦
python_version_game(next_actions=[my_AI, random_action, random_action])
```

### 期待される出力例

```
----------- ゲーム開始 -----------
my_AI :プレイヤー0番
...
------- ゲーム終了　ターン XX -------
* 勝者 プレイヤー0番
```

## 📚 参考ファイル

### ソースコード
- `/src/submission_colab.py` - このNotebookのベースとなったPythonコード
- `/src/submission.py` - 最高性能版（SIMULATION_COUNT=700、勝率80%）
- `/src/main.py` - 開発版

### ドキュメント
- `/WHICH_FILE_TO_USE.md` - ファイル選択ガイド
- `/QUICKSTART.md` - クイックスタートガイド
- `/doc/design_strongest.md` - PIMC法の設計書

## 🏆 大会提出チェックリスト

- [x] `my_AI` 関数が Cell 5 に実装済み
- [x] PIMC法による高度な戦略実装済み
- [x] トンネルルール対応済み
- [x] Colab環境に最適化済み
- [x] 標準ライブラリ + numpy のみ使用
- [ ] ローカルでテスト実行
- [ ] 勝率を確認（目標: 60%以上）
- [ ] `MY_PLAYER_NUM` の確認

## 📞 サポート

問題が発生した場合：
1. セルを上から順番に実行しているか確認
2. エラーメッセージを確認
3. `/README.md` のトラブルシューティングを参照

## 📅 更新履歴

### 2026年1月22日
- submission_colab.py の内容を Cell 5 に移植
- SIMULATION_COUNT = 500（超強化版）
- 全戦略機能を統合

### 2026年1月20日（ベースコード）
- 参考コード（xq-kessyou-main）のヒューリスティック統合
- A/K優先度の動的調整
- スート集中戦略の強化

---

**作成日**: 2026年1月22日  
**バージョン**: Colab最適化版（SIMULATION_COUNT=500）
