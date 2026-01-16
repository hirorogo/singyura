# 七並べAI 現状レポートと強化戦略

## 目次
1. [プロジェクト概要](#プロジェクト概要)
2. [現在のAI実装状況](#現在のai実装状況)
3. [実装されたアルゴリズム](#実装されたアルゴリズム)
4. [性能と課題](#性能と課題)
5. [強化戦略](#強化戦略)

---

## プロジェクト概要

### ゲームルール
このプロジェクトは、トンネルルールを採用した七並べゲームのAI対戦システムです。

**基本ルール:**
- 3人対戦（足りない枠はランダムAIが埋める）
- 4スーツのA～Kの52枚を使用（ジョーカーなし）
- 勝利条件：「カードを最も早く使い切る」または「他プレイヤーが全員失格」
- パスは1人あたり3回まで
- 4回目のパス失格（バースト）、手札をすべて盤面に出す

**トンネルルール:**
- カードがAまで出た場合、そのスートはKからしか出せない
- Kが出た場合、同様にAからしか出せない
- 戦略的な封鎖・妨害要素が追加される

---

## 現在のAI実装状況

### 1. ランダムAI
最も基本的な実装。出せるカードからランダムに選択する。

```python
def random_action(state):
    """ランダムに行動を選択するAI"""
    my_actions = state.my_actions()
    if my_actions != []:
        return my_actions[random.randint(0, len(my_actions)-1)]
    else:
        my_actions = []
        return my_actions
```

**特徴:**
- 実装が簡単
- ベースライン性能の測定に使用
- 戦略性なし

---

### 2. PIMC (Perfect Information Monte Carlo) AI

現在の最強AIとして実装されています。不完全情報ゲーム（ポーカー、ブリッジ等）で標準的に使われる高度なアルゴリズムです。

**設計思想:**
- 学習不要：重いモデルファイル不要
- 「読み」の実装：相手のパス情報から手札を推論
- 並行世界シミュレーション：相手の手札の可能性を複数パターン生成してゲームを解く

---

## 実装されたアルゴリズム

### Phase 1: 推論エンジン (CardTracker)

相手の手札を推論する「名探偵」システム。

**機能:**
```python
class CardTracker:
    # possible[p]: プレイヤーpが持ちうるカードの集合
    def observe_action(player, action, is_pass):
        # パス観測: legal_actions()のカードを持たないと判断
        # プレイ観測: そのカードを全員が持たない
```

**推論ロジック:**
1. **初期状態**: 自分以外のカードは誰が持っているか不明
2. **確定情報**: 場に出たカード、自分のカードは確定
3. **パス検知**: プレイヤーAがパス → Aはその時出せる候補カードを持っていない
4. **履歴リプレイ**: 過去の全行動を再生して推論精度を向上

**重要な改善点:**
- トンネルルール下でも正確な推論が可能
- 履歴リプレイ機能により、各手番時点の正確な盤面で評価

---

### Phase 2: 確定化 (Determinization)

推論結果を元に「全員の手札が透けて見える仮想世界」を生成。

**マルチバース生成:**
```python
def _create_determinized_state_with_constraints():
    # CardTracker.possible[p]の制約を満たすように相手手札を割当
    # 30回リトライ、失敗時は制約なし確定化にフォールバック
```

**特徴:**
- World 1: 相手AがダイヤのKを持っている世界
- World 2: 相手BがダイヤのKを持っている世界
- ... (50~200個の仮想世界を生成)

---

### Phase 3: 評価 (Playout)

各仮想世界において、ゲーム終了まで高速にプレイ。

**ロールアウトポリシー:**
```python
def _rollout_policy_action(state, player):
    # 1. 端(A/K)優先
    # 2. Safe(次の札を自分が持つ)優先
    # 3. ランダム選択
    # PASSは基本しない（探索分散を避ける）
```

**評価方法:**
- すべての世界を通して、最も勝率が高かったアクションを採用
- 統計的に負けない手を打つ

---

## 性能と課題

### 現在の性能

#### ベンチマーク結果
| 試行 | SIMULATION_COUNT | 戦略 | 勝率(vs ランダムAI) | 時間/game |
|------|------------------|------|---------------------|-----------|
| 初期実装 | 30 | Safe優先 | 39% | 0.01s |
| 探索増強 | 200 | Safe優先 | **44%** | 0.02s |
| フィルタ撤廃 | 200 | PASS含む | 41% | 0.01s |
| AI同士想定 | 200 | ロールアウトポリシー | 32% | 0.02s |

**最高性能: 44% (探索増強版)**

---

### 主な課題

#### 1. 評価環境とプレイアウトモデルの不一致
**問題点:**
- ベンチマーク相手：ランダムAI
- プレイアウトモデル：AI同士想定（端優先・Safe優先）
- → プレイアウトで学習する最適戦略が、実際の対戦相手と乖離

**影響:**
- AI同士想定のプレイアウトを実装すると勝率が32%に低下
- ランダムAI相手の最適戦略を学習していない

---

#### 2. PASS候補の扱い
**問題点:**
- PASSを候補に入れると探索が分散して弱くなる
- トンネルルール下では「出せるカードがあるのにPASS」は損失が大きい

**現状:**
- 「合法手があるならPASSしない」が最も効果的

---

#### 3. 設計書との差分（未実装機能）

**確率分布 (Belief State):**
- 設計: `possible_hands[player_id][card_id] = probability`
- 実装: `possible[p] = Set[Card]` (制約集合のみ)
- → 重み付き決定化が未実装

**戦略モード切替:**
- `OpponentModel` は存在するが、評価への反映が弱い
- Tunnel Lock / Burst Force モードの実装が不完全

---

#### 4. 計算コスト
**問題点:**
- SIMULATION_COUNT=200で十分な精度を得られる
- しかし、リアルタイム対戦では高速化が必要

**ボトルネック:**
- State.clone() のコスト
- Card生成のコスト
- Python のループ速度

---

## 強化戦略

### 短期的改善策（即効性あり）

#### 戦略1: PASS候補の完全除外
**アプローチ:**
```python
# 合法手があるなら必ず打つ
if len(state.my_actions()) > 0:
    candidates = state.my_actions()  # PASSを含めない
else:
    candidates = [PASS]  # 出せる手がない場合のみPASS
```

**期待効果:**
- 探索分散を防ぐ
- バースト負けリスクを減らす
- **勝率: 44% → 50-55% 見込み**

---

#### 戦略2: プレイアウトモデルの調整
**アプローチ:**
```python
# ベンチマーク相手に合わせる
if opponent_type == "random":
    # プレイアウトもランダムにする
    rollout_policy = random_policy
elif opponent_type == "ai":
    # AI同士想定のロールアウト
    rollout_policy = smart_policy
```

**期待効果:**
- 評価環境との整合性向上
- **勝率: 50% → 55-60% 見込み**

---

#### 戦略3: 確定化の重み付け改善
**アプローチ:**
```python
# パス回数が多いプレイヤーほど「出しやすい札を持っていない」
def weighted_determinization(tracker, pass_counts):
    for player in players:
        weight = 1.0 - (pass_counts[player] / 3.0) * 0.5
        # 重み付きでカードを割り当て
```

**期待効果:**
- 推論精度の向上
- **勝率: +3-5%**

---

### 中期的改善策（勝率最大化）

#### 戦略4: Belief State の確率化
**アプローチ:**
```python
class ProbabilisticCardTracker:
    # possible[p][card] = probability (0.0 ~ 1.0)
    def update_belief(self, player, action, is_pass):
        if is_pass:
            # ベイズ更新
            for card in legal_actions:
                self.possible[player][card] *= 0.0
            # 正規化
            self.normalize(player)
```

**実装内容:**
- Set → Dict[Card, float] に変更
- 確率分布に基づくサンプリング
- ベイズ推論の導入

**期待効果:**
- より精密な手札推論
- **勝率: +5-8%**

---

#### 戦略5: 戦略モードの本格実装
**アプローチ:**
```python
class OpponentModel:
    def get_mode(self):
        if self.is_aggressive():
            return "tunnel_lock"  # トンネルで封鎖
        elif self.is_blocker():
            return "burst_force"  # バースト誘導
        else:
            return "neutral"

def evaluate_action_with_mode(action, mode):
    if mode == "tunnel_lock":
        # K, Q, Jの価値を極大化（出さない）
        if action.number in [KING, QUEEN, JACK]:
            score -= 1000
    elif mode == "burst_force":
        # 相手が持っていないスートを急速に進める
        if action.suit in opponent_weak_suits:
            score += 500
```

**実装内容:**
- 相手モデルの推測ロジック（アグレッシブ判定、ブロッカー判定）
- 動的評価関数（状況に応じて重み変更）
- モード別の評価スコア調整

**期待効果:**
- 対戦相手の戦略に適応
- **勝率: +5-10%**

---

#### 戦略6: トンネルロック戦略
**アプローチ:**
```python
def tunnel_lock_strategy(state, tracker):
    for suit in Suits:
        if state.field_cards[suit][0] == 1:  # Aが出ている
            # Kを持っているなら出さない（相手を封鎖）
            if has_card(suit, KING):
                avoid_actions.append(Card(suit, KING))
        
        if state.field_cards[suit][12] == 1:  # Kが出ている
            # Aを持っているなら出さない
            if has_card(suit, ACE):
                avoid_actions.append(Card(suit, ACE))
```

**実装内容:**
- 相手がトンネルを開けた瞬間を検知
- 逆側の端（K/A）やその手前（Q, J）の価値を極大化
- 絶対に出さないようにして相手のルートを封鎖

**期待効果:**
- トンネルルールを戦略的に活用
- **勝率: +3-7%**

---

#### 戦略7: バースト誘導戦略
**アプローチ:**
```python
def burst_force_strategy(state, tracker):
    # 相手のパス回数を監視
    for player, pass_count in enumerate(state.pass_count):
        if pass_count >= 2:  # 危険水域
            # このプレイヤーが持っていないスートを推論
            weak_suits = tracker.get_weak_suits(player)
            # そのスートを急速に進める
            for suit in weak_suits:
                prioritize_suit(suit)
```

**実装内容:**
- 相手のパス回数を監視
- パスが多いプレイヤーが持っていないスートを推論
- そのスートを急速に進めて「出せない状況」を維持
- 4回目のパス（失格）へ追い込む

**期待効果:**
- 相手の弱点を突く
- **勝率: +5-8%**

---

### 長期的改善策（最適化・発展）

#### 戦略8: 軽量化・高速化
**アプローチ:**
```python
# 1. State.clone() の高速化
def clone(self):
    # deepcopyを避ける
    # 必要な部分だけコピー
    
# 2. Card生成コストの削減
CARD_CACHE = {}  # カードオブジェクトをキャッシュ

# 3. numpyの効果的な使用
field_cards = np.zeros((4, 13), dtype='uint8')  # メモリ削減
```

**実装内容:**
- State.clone() の最適化
- Card オブジェクトのキャッシュ
- numpy の効果的な使用
- プロファイリングによるボトルネック特定

**期待効果:**
- 計算時間を50%削減
- より多くのシミュレーションが可能
- **勝率: +3-5%**

---

#### 戦略9: 深層学習との融合
**アプローチ:**
```python
# 価値関数の学習
class ValueNetwork(nn.Module):
    def forward(self, state):
        # 局面の価値を予測
        return value

# PIMCと組み合わせる
def hybrid_evaluation(state):
    # 終局近く: PIMC
    if remaining_cards < 10:
        return pimc_evaluation(state)
    # 序盤: 価値ネットワーク
    else:
        return value_network(state)
```

**実装内容:**
- 価値関数の深層学習
- PIMC と DL のハイブリッド
- 自己対戦による強化学習

**期待効果:**
- 序盤の判断精度向上
- **勝率: +10-15%**

---

#### 戦略10: マルチエージェント強化学習
**アプローチ:**
```python
# 複数のAIを並列に学習
agents = [
    AggressiveAI(),  # 攻撃的
    DefensiveAI(),   # 防御的
    BalancedAI(),    # バランス型
]

# トーナメント形式で進化
for generation in range(1000):
    # 総当たり戦
    results = tournament(agents)
    # 強いAIを残す
    agents = select_top_agents(results)
    # 変異・交叉
    agents = evolve(agents)
```

**実装内容:**
- 複数の戦略を持つAIを同時に開発
- トーナメント形式で評価
- 遺伝的アルゴリズムによる進化

**期待効果:**
- 多様な戦略の発見
- **勝率: +15-20%**

---

## 実装優先順位

### フェーズ1: 即効性改善（1-2週間）
1. ✓ PASS候補の完全除外
2. ✓ プレイアウトモデルの調整
3. ✓ 確定化の重み付け改善

**目標勝率: 55-60% (vs ランダムAI)**

---

### フェーズ2: 戦略強化（2-4週間）
4. ✓ Belief State の確率化
5. ✓ 戦略モードの本格実装
6. ✓ トンネルロック戦略
7. ✓ バースト誘導戦略

**目標勝率: 65-75% (vs ランダムAI)**

---

### フェーズ3: 最適化・発展（1-3ヶ月）
8. ✓ 軽量化・高速化
9. ✓ 深層学習との融合
10. ✓ マルチエージェント強化学習

**目標勝率: 80-90% (vs ランダムAI), 50-60% (vs AI同士)**

---

## まとめ

### 現在の到達点
- PIMC法の基本実装は完了
- 推論エンジン、確定化、評価の3フェーズが動作
- ランダムAI相手に44%の勝率を達成

### 主な課題
1. 評価環境とプレイアウトモデルの不一致
2. PASS候補による探索分散
3. 確率分布化・戦略モード切替の未実装
4. 計算コストの最適化

### 改善の方向性
- **短期**: PASS除外、プレイアウト調整、重み付け改善 → 勝率55-60%
- **中期**: 確率化、戦略モード、トンネルロック、バースト誘導 → 勝率65-75%
- **長期**: 高速化、深層学習、マルチエージェント → 勝率80-90%

### 技術的優位点
- 学習不要で実装可能
- 推論による「読み」が実装されている
- トンネルルール下でも動作
- 拡張性が高い設計

### 次のステップ
1. PASS候補の完全除外（即効性）
2. プレイアウトモデルの調整（整合性）
3. 確定化の重み付け改善（精度向上）

これらの実装により、**勝率60%超え**を目指します。

---

## 参考文献
- `doc/design_strongest.md` : PIMC全体設計
- `doc/strategy.md` : 相手モデルと戦略切替
- `doc/logs/01_pimc_implementation_and_tuning.md` : 実装とチューニング履歴
- `doc/misc/colab_notebook.md` : トンネルルール詳細

---

**作成日**: 2026年1月16日  
**バージョン**: 1.0
