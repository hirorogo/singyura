# 開発ガイド

このドキュメントは、singyuraプロジェクトの開発に貢献する際のガイドラインです。

## 📁 ファイル構成の理解

### 提出用ファイル
- **`submission.py`** - 大会提出用の最終コード（これを提出）

### 開発用ファイル（src/）
- **`main.py`** - オリジナル版AI（ベースライン）
- **`main_improved.py`** - Phase 1改善版AI（開発のメイン）
- **`main_gpu.py`** - GPU対応版（高速実験用）
- **`benchmark*.py`** - 各バージョンのベンチマーク

### 参考コード（reference/）
- **`base_game_engine.py`** - 大会提供の基本ゲームエンジン
- **`random_ai.py`** - ランダムAI（ベンチマーク用）

### ドキュメント（doc/）
- **`ai_status_report.md`** - 詳細な分析と改善戦略
- **`phase1_improvements.md`** - Phase 1改善の実装詳細
- **`design_strongest.md`** - PIMC法の設計書
- その他、戦略・分析レポート

## 🔧 開発ワークフロー

### 1. 新しい改善を試す

```bash
# main_improved.py を編集
cd src
vim main_improved.py

# テスト実行
python main_improved.py
```

### 2. ベンチマークで評価

```bash
cd src
python benchmark_improved.py
```

### 3. 改善が成功したらsubmission.pyに反映

```bash
# main_improved.py の変更を submission.py にマージ
# 以下を確認:
# - MY_PLAYER_NUM = 0
# - SIMULATION_COUNT = 300 (最適値)
# - デバッグ出力なし
# - my_AI関数が正しく実装されている
```

### 4. 最終テスト

```bash
# submission.py を実行してエラーがないか確認
python submission.py

# ベンチマーク（100ゲーム）
cd src
python -c "
from submission import my_AI
# ... ベンチマークコード ...
"
```

## 🎯 改善のガイドライン

### Phase 1改善（実装済み）
- ✅ PASS候補の完全除外
- ✅ 重み付け確定化
- ✅ 適応的ロールアウトポリシー

### Phase 2改善（今後の課題）
- [ ] Belief Stateの確率化
- [ ] 戦略モードの本格実装
- [ ] トンネルロック戦略の強化
- [ ] バースト誘導戦略

### Phase 3改善（長期目標）
- [ ] 軽量化・高速化
- [ ] 深層学習との融合
- [ ] マルチエージェント強化学習

## 📊 パフォーマンス測定

### ベンチマーク基準
- **勝率**: 55-60%以上（ランダムAI × 2人相手）
- **処理速度**: 1ゲームあたり1秒以内
- **理論値**: 33.3%（ランダム選択時）

### 測定方法

```python
import time

# 100ゲームのベンチマーク
start = time.time()
wins = 0
for i in range(100):
    # ... ゲーム実行 ...
    if winner == MY_PLAYER_NUM:
        wins += 1
elapsed = time.time() - start

print(f"Win rate: {wins}% ({wins}/100)")
print(f"Time: {elapsed:.2f}s ({elapsed/100:.3f}s/game)")
```

## 🐛 デバッグのヒント

### 1. 推論の確認

```python
# CardTracker の状態を確認
tracker = CardTracker(state, MY_PLAYER_NUM)
for p in range(state.players_num):
    print(f"Player {p}: {len(tracker.possible[p])} possible cards")
```

### 2. シミュレーション結果の確認

```python
# 各アクションのスコアを表示
for action, score in action_scores.items():
    print(f"{action}: {score:.3f}")
```

### 3. トンネルルールの動作確認

```python
# 場の状態を確認
print(state.field_cards)
print(f"Legal actions: {state.legal_actions()}")
print(f"My actions: {state.my_actions()}")
```

## 📝 コーディング規約

### Python スタイル
- PEP 8 に準拠
- 4スペースインデント
- クラス名: PascalCase
- 関数名: snake_case
- 定数: UPPER_CASE

### コメント
- 日本語コメントOK（仕様書が日本語のため）
- 複雑なロジックには必ずコメント
- 関数にはdocstringを付ける

### 例

```python
def calculate_action_score(state, action, simulations=300):
    """
    アクションのスコアを計算
    
    Args:
        state: ゲーム状態
        action: 評価するアクション
        simulations: シミュレーション回数
        
    Returns:
        float: アクションのスコア (0.0～1.0)
    """
    # 実装...
    pass
```

## 🧪 テストのベストプラクティス

### ユニットテスト

```python
# test_card_tracker.py
def test_card_tracker_inference():
    state = State()
    tracker = CardTracker(state, 0)
    # パス後の推論をテスト
    tracker.observe_action(1, None, is_pass=True)
    # ...
```

### 統合テスト

```bash
# 複数回実行して安定性を確認
for i in {1..10}; do
    python submission.py
done
```

## 🚀 リリース手順

### 1. コードレビュー
- [ ] SIMULATION_COUNT が最適値（300）
- [ ] デバッグ出力が削除されている
- [ ] エラーハンドリングが適切
- [ ] コメントが適切

### 2. ベンチマーク
- [ ] 勝率が55%以上
- [ ] 処理速度が適切（<1秒/ゲーム）
- [ ] メモリ使用量が適切

### 3. ドキュメント更新
- [ ] README.md に変更点を記載
- [ ] CHANGELOG（あれば）を更新
- [ ] コメントを日本語で明確に

### 4. 提出
- [ ] `submission.py` を大会システムにアップロード
- [ ] 動作確認
- [ ] バックアップを保存

## 💡 改善のアイデア

### 短期的な改善
1. シミュレーション回数の動的調整
2. 序盤・中盤・終盤での戦略切り替え
3. 相手のパターン学習

### 中期的な改善
1. 機械学習による評価関数の学習
2. 開局定跡の構築
3. エンドゲームの完全読み

### 長期的な改善
1. アルファ碁スタイルの自己対局学習
2. トーナメント形式での進化的アルゴリズム
3. アンサンブル学習

## 📚 参考資料

### 論文・記事
- PIMC法について
- モンテカルロ木探索（MCTS）
- 不完全情報ゲームのAI

### 関連プロジェクト
- AlphaGo
- Libratus（ポーカーAI）

## 🤝 コントリビューション

改善案やバグ報告は Issue または Pull Request でお願いします。

### Pull Request のガイドライン
1. 変更内容を明確に記述
2. ベンチマーク結果を添付
3. コーディング規約に準拠
4. テストを追加（可能であれば）

---

**Happy Coding! 🎉**
