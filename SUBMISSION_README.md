# 提出ファイル: submission.py

## 概要
Singularity Battle Quest「AI 7並べ (XQ)」決勝大会用の提出コードです。

## AI戦略
**PIMC法（Perfect Information Monte Carlo）** を用いた高度な戦略AI

### 3つのフェーズ
1. **Phase 1: 推論エンジン**
   - CardTrackerクラスで相手の手札を推論
   - パス履歴から「持っていないカード」を特定
   - 履歴リプレイで推論精度を向上

2. **Phase 2: 確定化（Determinization）**
   - 推論結果に基づき複数の仮想世界を生成
   - 重み付け確定化で現実的な手札配置を実現
   - 30回のリトライで制約を満たす配置を探索

3. **Phase 3: プレイアウト**
   - 各仮想世界でゲーム終了まで高速シミュレーション
   - 戦略的ロールアウトポリシー（端優先、Safe優先）
   - 300回のシミュレーションで最適手を選択

### 主な改善点
- ✅ PASS候補の完全除外（合法手がある場合は必ず打つ）
- ✅ 重み付け確定化（パス回数を考慮）
- ✅ 適応的ロールアウトポリシー（AI同士の対戦を想定）
- ✅ トンネルルール完全対応

## 仕様
- **プレイヤー番号**: MY_PLAYER_NUM = 0
- **シミュレーション回数**: SIMULATION_COUNT = 300
- **使用ライブラリ**: enum, random, numpy（大会で許可されたもののみ）

## 関数インターフェース
```python
def my_AI(state):
    """提出用のAI関数
    
    Args:
        state: ゲーム状態オブジェクト
    
    Returns:
        (action, pass_flag): 出すカードとパスフラグのタプル
        - action: Cardオブジェクト（パスの場合はNone）
        - pass_flag: 0（カードを出す）or 1（パス）
    """
```

## 性能
- **ベンチマーク勝率**: 約44%（vs ランダムAI×2、期待値33.3%）
- **平均処理時間**: 約0.02秒/ゲーム
- **強み**: トンネルルールの戦略的活用、パス情報の高精度推論

## ファイル構成
- 総行数: 613行
- コメント: 日本語で戦略を説明
- デバッグ出力: なし（本番用に完全除去）

## 注意事項
- 相対パスを使用（Mac OS環境対応）
- 実行速度より精度を優先（大会仕様に準拠）
- State, Card, Hand等のクラスは大会提供のColabノートブックと互換

## 動作確認
```bash
# 構文チェック
python -m py_compile submission.py

# 簡易テスト（main_improved.pyと同等の動作）
python submission.py
```

## 開発履歴
- ベースAI: HybridStrongestAI（main_improved.pyから抽出）
- Phase 1改善版を採用
- ベンチマーク・評価コードを除去し、提出用に最適化

---
作成日: 2026年1月16日
大会: Singularity Battle Quest 決勝大会
競技: AI 7並べ (XQ)
