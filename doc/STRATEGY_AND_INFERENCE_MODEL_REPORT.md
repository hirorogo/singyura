# 七並べAI 戦略と推論モデル 詳細レポート

## 作成日
2026年1月18日

## 目次
1. [はじめに](#はじめに)
2. [PIMC法の理論的背景](#pimc法の理論的背景)
3. [推論モデル（Inference Engine）](#推論モデルinference-engine)
4. [確定化（Determinization）](#確定化determinization)
5. [評価（Evaluation）](#評価evaluation)
6. [戦略的要素](#戦略的要素)
7. [実装の現状と課題](#実装の現状と課題)
8. [推奨される改善案](#推奨される改善案)

---

## はじめに

### プロジェクト概要
本プロジェクトは、トンネルルールを採用した七並べゲームで勝利するためのAIを開発するものです。
PIMC（Perfect Information Monte Carlo）法を中核とした高度なAI実装を目指しています。

### ゲームの特性
- **不完全情報ゲーム**: 相手の手札が見えない
- **確率的要素**: 初期配布がランダム
- **戦略的深さ**: トンネルルール、パス制限、バースト
- **多人数対戦**: 3人でのゼロサムではない競争

---

## PIMC法の理論的背景

### PIMC法とは

Perfect Information Monte Carlo（完全情報モンテカルロ法）は、不完全情報ゲームにおいて、
見えない情報（相手の手札）を確率的に補完し、複数の「仮想世界」でシミュレーションを行うことで、
最適な行動を決定する手法です。

### 基本的なアルゴリズム

```
function PIMC_Action(state, my_hand):
    action_scores = {}
    
    for _ in range(N):  # Nはシミュレーション回数
        # 1. 確定化：相手の手札を推論情報に基づいて生成
        determinized_state = Determinize(state, beliefs)
        
        # 2. 各候補手を評価
        for action in possible_actions:
            # その手を打った後の状態を作成
            sim_state = determinized_state.clone()
            sim_state.apply(action)
            
            # 3. ゲーム終了までプレイアウト
            winner = Playout(sim_state)
            
            # 4. スコアリング
            if winner == me:
                action_scores[action] += 1
            else:
                action_scores[action] -= 1
    
    # 最もスコアが高い手を選択
    return argmax(action_scores)
```

### PIMC法の利点

1. **学習不要**: 事前の訓練や大規模データセットが不要
2. **柔軟性**: ルール変更に容易に対応可能
3. **解釈可能性**: なぜその手を選んだか説明しやすい
4. **実績**: ポーカー、ブリッジなど多くの不完全情報ゲームで成功

### PIMC法の課題

1. **計算コスト**: 多数のシミュレーションが必要
2. **Strategy Fusion Problem**: 相手の戦略が混ざってしまう問題
3. **確定化バイアス**: 推論が不正確だと誤った評価につながる

---

## 推論モデル（Inference Engine）

### 目的
相手の手札を推論し、確率分布（Belief State）を維持する。

### CardTrackerクラスの設計

#### データ構造
```python
class CardTracker:
    possible[player]: set[Card]  # プレイヤーが持ちうるカードの集合
    pass_counts[player]: int     # パス回数
    out_player: set[int]         # バーストしたプレイヤー
```

#### 初期化
```python
def __init__(self, state, my_player_num):
    # 全52枚のカードから開始
    all_cards = {全てのカード}
    
    # 各プレイヤーは全てのカードを持ちうる
    for p in range(players_num):
        self.possible[p] = all_cards.copy()
    
    # 場に出たカードは誰も持たない
    for card in field_cards:
        for p in range(players_num):
            self.possible[p].remove(card)
    
    # 自分の手札は確定
    self.possible[my_player_num] = my_hand.copy()
    
    # 他プレイヤーは自分の手札を持たない
    for p in other_players:
        self.possible[p] -= my_hand
```

### 推論の更新

#### カードプレイの観測
```python
def observe_play(self, player, card):
    # そのカードを出したプレイヤー以外は持たない
    for p in range(players_num):
        if p != player:
            self.possible[p].discard(card)
```

**推論**: 確実な情報。そのカードはそのプレイヤーだけが持っていた。

#### パスの観測（重要）
```python
def observe_pass(self, state, player):
    # その時点で出せたカードを持っていない可能性が高い
    legal_actions = state.legal_actions()
    
    # オプション1: 完全除外（強い制約）
    for card in legal_actions:
        self.possible[player].discard(card)
    
    # オプション2: 確率的除外（柔軟な制約）
    for card in legal_actions:
        # 80%の確率で持っていないと判断
        if random.random() < 0.8:
            self.possible[player].discard(card)
    
    # オプション3: 重み付け（Belief State）
    for card in legal_actions:
        self.belief[player][card] *= 0.2  # 20%に減衰
```

**課題**: パスは「持っていない」だけでなく「戦略的に出さない」場合もある。

### 戦略的パスの問題

#### ゲーム理論的考察
七並べにおいて、戦略的パス（出せるカードがあるのにあえて出さない）は以下の状況で有効：

1. **トンネルロック**: 相手のトンネルを封鎖するため、自分の端カードを温存
2. **相手誘導**: 相手に特定のカードを出させるための待ち
3. **情報秘匿**: 自分の手札情報を隠すためのフェイント

**問題**: 現在の実装では、これらを区別できない。

#### 推奨アプローチ

**段階的な制約強化**:
```python
def observe_pass(self, state, player):
    legal = state.legal_actions()
    pass_count = self.pass_counts[player]
    
    if pass_count == 0:
        # 初回パス：戦略的可能性が高い、弱く除外
        removal_rate = 0.3
    elif pass_count == 1:
        # 2回目：やや本格的に除外
        removal_rate = 0.6
    elif pass_count >= 2:
        # 3回目以上：強く除外（バースト目前）
        removal_rate = 0.9
    
    for card in legal:
        if random.random() < removal_rate:
            self.possible[player].discard(card)
```

### 履歴リプレイ

#### 目的
過去の全行動を正確な盤面で再評価し、推論精度を向上させる。

#### 実装
```python
def replay_history(self, state):
    # 初期盤面から開始
    replay_state = create_initial_state()
    
    for (player, action, is_pass) in state.history:
        # その手番での盤面で推論
        self.observe_action(replay_state, player, action, is_pass)
        
        # 盤面を更新
        replay_state.apply(action, is_pass)
```

**効果**: 各手番での正確なlegal_actions()で評価できる。

---

## 確定化（Determinization）

### 目的
推論情報（possible集合）を元に、「完全情報の仮想世界」を生成する。

### アルゴリズム

#### 基本的な確定化
```python
def determinize(state, tracker):
    # 相手の手札プールを作成
    unknown_cards = [全カード - 場のカード - 自分の手札]
    random.shuffle(unknown_cards)
    
    # 各プレイヤーに配分
    new_state = state.clone()
    index = 0
    for player in other_players:
        count = len(state.players_cards[player])
        new_state.players_cards[player] = unknown_cards[index:index+count]
        index += count
    
    return new_state
```

#### 制約付き確定化
```python
def determinize_with_constraints(state, tracker):
    for _ in range(MAX_RETRY):  # 例: 30回
        unknown_cards = [...]
        random.shuffle(unknown_cards)
        
        hands = {}
        remaining = unknown_cards.copy()
        
        # 各プレイヤーに制約を満たすように配分
        for player in other_players:
            count = len(state.players_cards[player])
            
            # possible集合に含まれるカードのみ選択
            possible_cards = [c for c in remaining if c in tracker.possible[player]]
            
            if len(possible_cards) < count:
                # 制約を満たせない → リトライ
                break
            
            hands[player] = sample(possible_cards, count)
            remaining = [c for c in remaining if c not in hands[player]]
        else:
            # 成功：この確定化を使用
            return create_state_with_hands(hands)
    
    # 失敗：制約なし確定化にフォールバック
    return determinize_basic(state)
```

### 問題点と改善

#### 現在の問題
1. **リトライ回数不足**: 30回で失敗すると情報が失われる
2. **all-or-nothing**: 制約を満たすか完全に諦めるかの2択
3. **重み付けの誤用**: 重み付け確定化の実装が不適切

#### 推奨改善

**段階的制約緩和**:
```python
def determinize_progressive(state, tracker):
    for strictness in [1.0, 0.9, 0.8, 0.7, 0.5, 0.0]:
        for _ in range(20):  # 各厳格度で20回試行
            # strictnessに応じて制約を緩める
            if strictness == 0.0:
                # 完全にランダム
                return determinize_basic(state)
            
            # 部分的に制約違反を許容
            result = try_determinize(state, tracker, strictness)
            if result is not None:
                return result
    
    # 最終フォールバック
    return determinize_basic(state)
```

---

## 評価（Evaluation）

### プレイアウト（Playout）

#### 目的
確定化された状態から、ゲーム終了まで高速にシミュレーションする。

#### ロールアウトポリシー

**シンプル版（高速）**:
```python
def rollout_policy(state):
    actions = state.my_actions()
    if not actions:
        return None
    return random.choice(actions)
```

**戦略的版（精度重視）**:
```python
def rollout_policy_strategic(state):
    actions = state.my_actions()
    if not actions:
        return None
    
    # 1. 端カード（A/K）優先
    ends = [a for a in actions if a.number in (ACE, KING)]
    if ends:
        return random.choice(ends)
    
    # 2. セーフムーブ優先（次も出せる）
    safe = [a for a in actions if is_safe_move(a, my_hand)]
    if safe:
        return random.choice(safe)
    
    # 3. ランダム
    return random.choice(actions)
```

#### トレードオフ
- **シンプル版**: 高速だが精度が低い
- **戦略的版**: 精度が高いが遅い
- **AI vs AI**: 戦略的版の方が現実的
- **AI vs Random**: シンプル版でも十分

### スコアリング

#### 基本スコアリング
```python
if winner == me:
    score += 1
else:
    score -= 1
```

#### 詳細スコアリング
```python
if winner == me:
    score += 2  # 勝利
elif winner == -1:
    score += 0  # 引き分け
else:
    score -= 1  # 負け
    
    # 手札差による補正
    my_remaining = len(sim_state.players_cards[me])
    winner_remaining = len(sim_state.players_cards[winner])
    
    if my_remaining < winner_remaining:
        score += 0.3  # 惜しい負け
    elif my_remaining - winner_remaining >= 3:
        score -= 0.3  # 大差の負け
```

---

## 戦略的要素

### トンネルルールの活用

#### トンネルルールとは
- Aが出たスートは、Kからしか低い方向に伸ばせない
- Kが出たスートは、Aからしか高い方向に伸ばせない

#### 戦略的意義
1. **封鎖**: 相手が端カードを持っていない場合、そのスートは進まない
2. **支配**: 両端を持っていれば、そのスートをコントロールできる
3. **誘導**: あえて端を出して、相手に反対側を出させる

### トンネルロック戦略

#### コンセプト
相手がトンネルを開けた（Aを出した）場合、逆側の端（K）を温存して封鎖する。

#### 実装
```python
def evaluate_tunnel_lock(state, my_hand, actions):
    bonus = {}
    
    for suit in Suits:
        if is_ace_played(state, suit):
            # Aが出ている → Kを温存
            k_card = Card(suit, KING)
            if k_card in my_hand and k_card in actions:
                bonus[k_card] = -15  # 出さない方向にペナルティ
    
    return bonus
```

#### 問題点
- ボーナス値（-15）が大きすぎる
- シミュレーション結果（±1～2点）を完全に上書きしてしまう
- 実質的にルールベースAIになっている

#### 推奨改善
```python
# ボーナスを大幅に削減
bonus[k_card] = -2  # シミュレーション結果と同程度の影響
```

### バースト誘導戦略

#### コンセプト
パス回数が多い相手が持っていないスートを急速に進めて、4回目のパス（バースト）に追い込む。

#### 実装
```python
def evaluate_burst_force(state, tracker, actions):
    bonus = {}
    
    for player in other_players:
        if state.pass_count[player] >= 2:
            # 危険水域のプレイヤー
            weak_suits = infer_weak_suits(tracker, player)
            
            for action in actions:
                if action.suit in weak_suits:
                    bonus[action] = +5  # そのスートを進める
    
    return bonus
```

#### 問題点
- 弱いスートの推論が不正確
- バースト誘導が必ずしも自分の勝利につながらない（他のプレイヤーが得をする可能性）

---

## 実装の現状と課題

### 現在の実装（main_improved.py）

#### Phase 1改善
1. **PASS除外**: 合法手がある場合はPASSを候補から除外
2. **重み付け確定化**: パス回数に基づく重み付け
3. **適応的ロールアウト**: AI同士を想定した戦略的ポリシー

#### Phase 2改善
1. **トンネルロック戦略**: 端カードの温存
2. **バースト誘導戦略**: 弱いスートを攻める

### 測定された性能
- **main_improved.py (SIMULATION_COUNT=300)**: 39-40%
- **main_improved.py (SIMULATION_COUNT=200)**: 31%
- **main.py (SIMULATION_COUNT=500)**: 44%（推定）

### 主な問題点

1. **過剰な最適化**: 複雑性が増し、本質的な強みが失われた
2. **シミュレーション回数不足**: 統計的信頼性が低い
3. **パラメータ未調整**: 戦略ボーナスなどが適切でない
4. **段階的検証不足**: どの改善が効いているか不明

---

## 推奨される改善案

### 短期改善（即座に実施）

#### 1. シンプル版への回帰
```python
# Phase 2改善を全て無効化
ENABLE_TUNNEL_LOCK = False
ENABLE_BURST_FORCE = False

# Phase 1改善も一時的に無効化
ENABLE_WEIGHTED_DETERMINIZATION = False

# PASS除外のみ有効
ENABLE_PASS_REMOVAL = True

# シミュレーション回数を増やす
SIMULATION_COUNT = 500
```

**期待効果**: 44%程度の勝率を再現

#### 2. パス観測の保守化
```python
def observe_pass(self, state, player):
    self.pass_counts[player] += 1
    
    # 完全除外ではなく、記録のみ
    # または、パス回数が3回以上の場合のみ除外
    if self.pass_counts[player] >= 3:
        legal = state.legal_actions()
        for c in legal:
            self.possible[player].discard(c)
```

**期待効果**: 確定化の成功率向上

#### 3. 確定化のリトライ回数増加
```python
# 30回 → 100回
for _ in range(100):
    ...
```

**期待効果**: 推論情報をより活用できる

### 中期改善（1-2週間）

#### 1. 段階的な改善追加
各改善を個別に追加し、効果を測定：
- まずPASS除外のみ
- 次に重み付け確定化のみ
- 次に適応的ロールアウトのみ

#### 2. パラメータチューニング
- 戦略ボーナスの値を調整（-15 → -2 など）
- 確率的パス除外の導入
- 動的シミュレーション回数の調整

#### 3. 詳細なベンチマーク
- 位置バイアスの検証
- 複数回実行して標準偏差を測定
- 対戦相手を変えてテスト

### 長期改善（1-3ヶ月）

#### 1. Belief Stateの完全実装
確率分布を維持し、確率的な確定化を行う。

#### 2. 相手モデリングの高度化
相手の戦略タイプを推定し、それに応じた対策を取る。

#### 3. 深層学習との融合
ロールアウトポリシーをニューラルネットワークで学習。

---

## 結論

### 現状のまとめ
- PIMC法の基本は実装されているが、過剰な最適化により性能が低下
- シンプルな実装の方が、この段階では効果的
- 各改善の効果を個別に検証する必要がある

### 推奨アプローチ
1. **まずシンプルに戻す**: 複雑性を削減し、ベースラインを確立
2. **1つずつ改善**: 各改善の効果を個別に測定
3. **データ駆動**: 実際のベンチマーク結果に基づく改善

### 期待される成果
- **短期（即座）**: 44%程度の勝率を再現
- **中期（1-2週間）**: 55-60%の勝率を達成
- **長期（1-3ヶ月）**: 65-75%以上の勝率を目指す

---

**作成者**: GitHub Copilot Coding Agent  
**日時**: 2026年1月18日  
**プロジェクト**: hirorogo/singyura
