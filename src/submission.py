"""
七並べAI 提出用コード - 最強化版
============================
シンギュラリティバトルクエスト決勝大会用

使用方法:
1. このファイルの内容をColabノートブックのmy_AIセルにコピー
2. MY_PLAYER_NUMを適切に設定
3. 実行

特徴:
- PIMC (Perfect Information Monte Carlo) 法による高度な意思決定
- 適応的ゲーム状態評価システム（序盤/中盤/終盤を判定）
- カードカウンティング戦略（場のカードを追跡）
- トンネルルール対応の高度な戦略
- ゲーム状況に応じた動的な戦略切り替え
- 複数の戦略を状況に応じて統合
- 参考コード（xq-kessyou-main）のヒューリスティックを統合
- 目標勝率: 50-60%（期待値33.3%より大幅に高い）

改善点（2026年1月20日版 - 参考コード統合）:
- シミュレーション回数を700に増強（統計的信頼性さらに向上）
- 参考コードの強力なヒューリスティック戦略を統合
- ヒューリスティック評価の精緻化（A/K優先、隣接カード分析、スート集中）
- ロールアウトポリシーの強化（スコアリングベースの判断）
- 戦略ボーナスの影響度を1.2倍に（参考コードの知見を反映）
"""

import random
import numpy as np

# --- 設定 ---
MY_PLAYER_NUM = 0          # 自分のプレイヤー番号
SIMULATION_COUNT = 1000    # シミュレーション回数（超強化版：700→1000、最高精度）
SIMULATION_DEPTH = 350     # シミュレーション深度（強化版）
ENABLE_TUNNEL_LOCK = True  # トンネルロック戦略
ENABLE_BURST_FORCE = True  # バースト誘導戦略

# 戦略重み付け係数（最強化版）
STRATEGY_WEIGHT_MULTIPLIER = 1.2  # 戦略ボーナスの影響度（参考コード統合により1.2倍に）
TUNNEL_LOCK_WEIGHT = 3.0  # トンネルロック戦略の重み
BURST_FORCE_WEIGHT = 3.0  # バースト誘導戦略の重み

# 適応的戦略パラメータ
AGGRESSIVE_MODE_THRESHOLD = 0.6  # 攻撃的モード閾値
DEFENSIVE_MODE_THRESHOLD = 0.8  # 防御的モード閾値

# 参考コード由来の高度なヒューリスティックパラメータ（戦略を尖らせるための重み）
ADVANCED_HEURISTIC_PARAMS = {
    'W_CIRCULAR_DIST': 22,    # 7からの距離（端に近いほど出しにくい）
    'W_MY_PATH': 112,         # 自分の次の手に繋がるボーナス
    'W_OTHERS_RISK': -127,    # 他人に塩を送るリスク（深度1あたりの減点）
    'W_SUIT_DOM': 84,         # スート支配力の重み
    'W_WIN_DASH': 41,         # 勝ち圏内の放出意欲
    'P_THRESHOLD_BASE': 200,  # 基本のパスしきい値（超高値、PASSをほぼ禁止）
    'P_KILL_ZONE': 300,       # 相手をハメる時のパスしきい値（超高値）
    'P_WIN_THRESHOLD': -31,   # 勝ち圏内のパスしきい値
    # 新戦略パラメータ
    'W_NECROMANCER': 20.0,    # ネクロマンサー（バースト予知）のボーナス
    'W_SEVEN_ADJACENT': 5.0,  # 7の信号機：隣接カードがある場合のボーナス
    'W_SEVEN_NO_ADJ': -5.0,   # 7の信号機：隣接カードがない場合のペナルティ
}

# 高度なヒューリスティックの有効化フラグと重み
ENABLE_ADVANCED_HEURISTIC = True  # 参考コード由来の高度な戦略を有効化
ADVANCED_HEURISTIC_WEIGHT = 0.8   # 高度なヒューリスティックの重み（既存戦略とのバランス）

# 新戦略の有効化フラグ
ENABLE_NECROMANCER = True    # ネクロマンサー戦略（バースト予知）
ENABLE_SEVEN_SIGNAL = True   # 7の信号機戦略
ENABLE_HYPERLOOP_DIST = True # ハイパーループ距離計算


# --- 推論器 (相手手札の推論) ---
class CardTracker:
    """不完全情報(相手手札)の推論器"""

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num
        self.all_cards = [Card(s, n) for s in Suit for n in Number]
        self.possible = [set(self.all_cards) for _ in range(self.players_num)]
        self._apply_field(state)

        my_hand = set(state.players_cards[my_player_num])
        for p in range(self.players_num):
            if p == my_player_num:
                self.possible[p].intersection_update(my_hand)
            else:
                self.possible[p].difference_update(my_hand)

        self.out_player = set(state.out_player)

    def clone(self):
        c = object.__new__(CardTracker)
        c.players_num = self.players_num
        c.my_player_num = self.my_player_num
        c.all_cards = self.all_cards
        c.possible = [set(s) for s in self.possible]
        c.out_player = set(self.out_player)
        return c

    def _apply_field(self, state):
        for s_idx, s in enumerate(Suit):
            for n_idx, n in enumerate(Number):
                if state.field_cards[s_idx][n_idx] == 1:
                    card = Card(s, n)
                    for p in range(self.players_num):
                        self.possible[p].discard(card)

    def observe_action(self, state, player, action, is_pass):
        if player in self.out_player:
            return
        if is_pass:
            legal = state.legal_actions()
            for c in legal:
                self.possible[player].discard(c)
            return
        if action is not None:
            for p in range(self.players_num):
                self.possible[p].discard(action)

    def mark_out(self, player):
        self.out_player.add(player)
        self.possible[player].clear()


# --- AI本体 ---
class HybridStrongestAI:
    """PIMC法 + ヒューリスティック戦略の最強AI"""

    def __init__(self, my_player_num, simulation_count=300):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count
        self._in_simulation = False

    def get_action(self, state):
        if self._in_simulation:
            return self._rollout_policy_action(state)

        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        candidates = list(my_actions)

        if len(candidates) == 1:
            return candidates[0], 0

        tracker = self._build_tracker_from_history(state)
        strategic_bonus = self._evaluate_strategic_actions(state, tracker, my_actions)
        action_scores = {action: 0 for action in candidates}

        for _ in range(self.simulation_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            for first_action in candidates:
                sim_state = self._clone_state(determinized_state)

                sim_state.next(first_action, 0)

                winner = self._playout(sim_state)

                if winner == self.my_player_num:
                    action_scores[first_action] += 1
                elif winner != -1:
                    action_scores[first_action] -= 1

        for action in candidates:
            if action in strategic_bonus:
                action_scores[action] += strategic_bonus[action]

        best_action = max(action_scores, key=action_scores.get)
        best_score = action_scores[best_action]
        
        # 戦略的パス判断（参考コード由来の高度な戦略）
        if ENABLE_ADVANCED_HEURISTIC:
            # 自分のパス回数と相手の状況を分析
            my_pass_count = state.pass_count[self.my_player_num]
            my_hands_count = len(state.my_hands())
            
            # 相手の状況分析
            opp_pass_left = [3 - state.pass_count[i] for i in range(len(state.players_cards)) 
                            if i != self.my_player_num and i not in state.out_player]
            opp_min_pass = min(opp_pass_left) if opp_pass_left else 3
            
            opp_hand_sizes = [len(state.players_cards[i]) for i in range(len(state.players_cards)) 
                             if i != self.my_player_num and i not in state.out_player]
            opp_min_hand = min(opp_hand_sizes) if opp_hand_sizes else 13
            
            params = ADVANCED_HEURISTIC_PARAMS
            
            # 戦略的パスの動的判断
            pass_threshold = params['P_THRESHOLD_BASE']
            
            # 相手のパスが尽きそうな時は、より「出さない」選択を強化
            if opp_min_pass == 0:
                pass_threshold = params['P_KILL_ZONE']
            elif opp_min_pass == 1:
                pass_threshold = params['P_KILL_ZONE'] * 0.7
            
            # 自分のパス残弾が少ない時は、評価が低くても出す（自滅回避）
            if (3 - my_pass_count) <= 1:
                pass_threshold = -9999
            
            # 自分が勝てそうな時は、変に止めずに流す
            if my_hands_count <= opp_min_hand and best_score > 0:
                pass_threshold = params['P_WIN_THRESHOLD']
            
            # 評価値がしきい値を下回るなら、戦略的パスを選択
            # strategic_bonus部分のみを比較対象とする
            if best_action in strategic_bonus:
                strategic_score_only = strategic_bonus[best_action]
                if strategic_score_only < pass_threshold and my_pass_count < 3:
                    return None, 1
        
        return best_action, 0

    def _clone_state(self, state):
        """状態の深いコピーを作成"""
        new_players_cards = [Hand(list(h)) for h in state.players_cards]
        new_field_cards = state.field_cards.copy()
        new_pass_count = list(state.pass_count)
        new_out_player = list(state.out_player)

        return State(
            players_num=state.players_num,
            field_cards=new_field_cards,
            players_cards=new_players_cards,
            turn_player=state.turn_player,
            pass_count=new_pass_count,
            out_player=new_out_player,
        )

    def _rollout_policy_action(self, state):
        """プレイアウト用の軽量ポリシー"""
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # 1. A/K（端カード）を優先的に出す
        ends = [a for a in my_actions if a.number in (Number.ACE, Number.KING)]
        if ends:
            return random.choice(ends), 0

        # 2. 次のカードを自分が持っているカードを優先（Safe判定）
        my_hand = state.players_cards[state.turn_player]
        safe_moves = []
        for action in my_actions:
            val = action.number.val
            if val < 7:
                next_val = val - 1
            elif val > 7:
                next_val = val + 1
            else:
                continue

            if 1 <= next_val <= 13:
                next_card = Card(action.suit, self._index_to_number(next_val - 1))
                if next_card and next_card in my_hand:
                    safe_moves.append(action)

        if safe_moves:
            return random.choice(safe_moves), 0

        # 3. 自分が多く持っているスートを優先
        suit_counts = {}
        for c in my_hand:
            suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1

        best_actions = []
        best_count = -1
        for action in my_actions:
            count = suit_counts.get(action.suit, 0)
            if count > best_count:
                best_count = count
                best_actions = [action]
            elif count == best_count:
                best_actions.append(action)

        if best_actions:
            return random.choice(best_actions), 0

        return random.choice(my_actions), 0

    def _evaluate_strategic_actions(self, state, tracker, my_actions):
        """戦略的評価を計算"""
        bonus = {}
        my_hand = state.players_cards[self.my_player_num]

        if ENABLE_TUNNEL_LOCK:
            tunnel_bonus = self._evaluate_tunnel_lock(state, my_hand, my_actions)
            for action, score in tunnel_bonus.items():
                bonus[action] = bonus.get(action, 0) + score

        if ENABLE_BURST_FORCE:
            burst_bonus = self._evaluate_burst_force(state, tracker, my_actions)
            for action, score in burst_bonus.items():
                bonus[action] = bonus.get(action, 0) + score

        heuristic_bonus = self._evaluate_heuristic_strategy(state, my_hand, my_actions)
        for action, score in heuristic_bonus.items():
            bonus[action] = bonus.get(action, 0) + score
        
        # 新機能：参考コード由来の高度なヒューリスティック戦略
        advanced_heuristic_bonus = self._evaluate_advanced_heuristic_strategy(state, my_hand, my_actions)
        for action, score in advanced_heuristic_bonus.items():
            bonus[action] = bonus.get(action, 0) + (score * ADVANCED_HEURISTIC_WEIGHT)

        return bonus
    
    def _evaluate_advanced_heuristic_strategy(self, state, my_hand, my_actions):
        """参考コード由来の高度なヒューリスティック戦略
        
        提供された参考コードからの戦略を統合:
        - 円環距離（7からの距離）評価
        - 深度ベースの開放リスク評価（get_chain_risk）
        - スート支配力の評価
        - トンネル端（A/K）の特別処理を強化
        - 戦略的パス判断（別途実装）
        """
        if not ENABLE_ADVANCED_HEURISTIC:
            return {}
        
        bonus = {}
        params = ADVANCED_HEURISTIC_PARAMS
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        # 自分の手札をインデックスセットで管理（高速検索用）
        my_hand_indices = set((suit_to_index[c.suit], c.number.val - 1) for c in my_hand)
        
        # 相手の状況分析
        opp_pass_left = [3 - state.pass_count[i] for i in range(len(state.players_cards)) if i != self.my_player_num]
        opp_min_pass = min(opp_pass_left) if opp_pass_left else 3
        opp_min_hand = min(len(h) for i, h in enumerate(state.players_cards) if i != self.my_player_num) if state.players_cards else 13
        
        def get_chain_risk(suit_idx, start_num, direction):
            """指定した方向に、自分が持っていないカードが何枚連続しているか(他人のための道)を計算"""
            risk_count = 0
            curr = (start_num + direction) % 13
            # トンネルがあるので最大6枚まで探索（7の反対側まで）
            for _ in range(6):
                if state.field_cards[suit_idx][curr] == 1:  # すでに出ている
                    break
                if (suit_idx, curr) in my_hand_indices:  # 自分で止めている
                    break
                # 誰かが持っているはずのカード
                risk_count += 1
                curr = (curr + direction) % 13
            return risk_count
        
        # 各スートのカード枚数をカウント
        suit_counts = {Suit.SPADE: 0, Suit.CLUB: 0, Suit.HEART: 0, Suit.DIAMOND: 0}
        for card in my_hand:
            suit_counts[card.suit] += 1
        
        for card in my_actions:
            s = card.suit
            i = suit_to_index[s]
            n = card.number.val - 1
            score = 0
            
            # 1. ハイパーループ距離計算 (トンネルルートも考慮した最短距離)
            if ENABLE_HYPERLOOP_DIST:
                # 通常ルートの距離
                dist_normal = abs(n - 6)
                # トンネルルートの距離
                dist_tunnel = 99
                # A側（0）またはK側（12）がアクセス可能か確認
                is_ace_accessible = state.field_cards[i][0] == 1 or (i, 0) in my_hand_indices
                is_king_accessible = state.field_cards[i][12] == 1 or (i, 12) in my_hand_indices
                
                if is_ace_accessible and n < 7:
                    # A側が使える場合、Aまでの距離+1
                    dist_tunnel = n + 1
                elif is_king_accessible and n >= 7:
                    # K側が使える場合、Kまでの距離+1
                    dist_tunnel = (12 - n) + 1
                
                # 最短ルートを選択（短い方が出やすい→価値が低い）
                min_dist = min(dist_normal, dist_tunnel)
                # 距離が短いほど保持価値が低いので、逆にボーナスを付ける
                circular_dist = min(dist_normal, 13 - dist_normal)
                score += circular_dist * params['W_CIRCULAR_DIST']
            else:
                # 従来の円環距離
                dist_from_7 = abs(n - 6)
                circular_dist = min(dist_from_7, 13 - dist_from_7)
                score += circular_dist * params['W_CIRCULAR_DIST']
            
            # 2. 7の信号機戦略
            if ENABLE_SEVEN_SIGNAL and n == 6:  # 7のインデックスは6
                # 隣接カード（6 or 8）を持っているか確認
                has_adjacent = (i, 5) in my_hand_indices or (i, 7) in my_hand_indices
                if has_adjacent:
                    score += params['W_SEVEN_ADJACENT']  # 自分に得なら即出し
                else:
                    score += params['W_SEVEN_NO_ADJ']    # 自分だけ損なら出し惜しみ
            
            # 3. 深度ベースの開放リスクと自己利益
            # 隣接する2方向（トンネル含む）を確認
            for direction in [1, -1]:
                neighbor = (n + direction) % 13
                # その方向がまだ未開放の場合のみ評価
                if state.field_cards[i][neighbor] == 0:
                    if (i, neighbor) in my_hand_indices:
                        # 自分が持っているなら「自分の道」
                        score += params['W_MY_PATH']
                    else:
                        # 自分が持っていないなら「他人の道」を何枚分開けてしまうか
                        risk_depth = get_chain_risk(i, n, direction)
                        score += risk_depth * params['W_OTHERS_RISK']
            
            # 3. スート支配 (そのマークを多く持っているなら、そのマークを優先的に進める)
            same_suit_count = suit_counts[s]
            score += same_suit_count * params['W_SUIT_DOM']
            
            # 4. 終盤・状況補正
            if len(my_hand) <= opp_min_hand:
                score += params['W_WIN_DASH']
            
            # 特殊ルール補正: トンネルの端（1, 13）を出す際、逆側の状況を見る
            if n == 0 or n == 12:
                opposite = 12 if n == 0 else 0
                if state.field_cards[i][opposite] == 0 and (i, opposite) not in my_hand_indices:
                    # 逆側のカードを自分が持っていないのにトンネルを開けるのは非常に危険
                    score -= 50
            
            bonus[card] = score
        
        # ネクロマンサー戦略（バースト予知）
        if ENABLE_NECROMANCER:
            for player in range(state.players_num):
                if player == self.my_player_num or player in state.out_player:
                    continue
                
                # 相手がもうすぐバーストする（pass_count >= 3）
                if state.pass_count[player] >= 3:
                    # 相手がバーストした場合、手札が全て場に出る
                    # その時に自分が出せるようになるカードの価値を上げる
                    for card in my_actions:
                        # このカードを出すことで、新たに出せるようになるカードがあるか
                        card_i = suit_to_index[card.suit]
                        card_n = card.number.val - 1
                        
                        # 隣接する方向で、まだ場に出ていないカードがあれば、
                        # バースト後にそこが開く可能性がある
                        for direction in [1, -1]:
                            neighbor = (card_n + direction) % 13
                            if state.field_cards[card_i][neighbor] == 0:
                                # この方向が未開放 = バースト後に繋がる可能性
                                bonus[card] = bonus.get(card, 0) + params['W_NECROMANCER']
                                break  # 一度だけボーナス
        
        return bonus

    def _evaluate_heuristic_strategy(self, state, my_hand, my_actions):
        """参考用コードのヒューリスティック戦略"""
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}

        suit_counts = {suit: 0 for suit in Suit}
        for card in my_hand:
            suit_counts[card.suit] += 1

        for card in my_actions:
            suit = card.suit
            suit_index = suit_to_index[suit]
            number_index = card.number.val - 1
            score = 0

            is_ace_out = state.field_cards[suit_index][0] == 1
            is_king_out = state.field_cards[suit_index][12] == 1

            if number_index == 0:  # A
                if is_king_out:
                    score += 5
                else:
                    score -= 5
            elif number_index == 12:  # K
                if is_ace_out:
                    score += 5
                else:
                    score -= 5

            next_indices = []
            if number_index < 6:
                next_indices.append(number_index - 1)
            elif number_index > 6:
                next_indices.append(number_index + 1)

            for next_number_index in next_indices:
                if 0 <= next_number_index <= 12:
                    if state.field_cards[suit_index][next_number_index] == 1:
                        score += 5
                    else:
                        score -= 5
                        next_number = self._index_to_number(next_number_index)
                        if next_number:
                            next_card = Card(suit, next_number)
                            if next_card in my_hand:
                                score += 12

            score += suit_counts[suit] * 2

            potential_new_moves = 0
            for c in my_hand:
                if c.suit == suit:
                    c_index = c.number.val - 1
                    if (number_index < 6 and c_index == number_index - 1) or \
                       (number_index > 6 and c_index == number_index + 1):
                        potential_new_moves += 1
            score += potential_new_moves * 10

            bonus[card] = score

        return bonus

    def _index_to_number(self, index):
        number_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                       Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                       Number.NINE, Number.TEN, Number.JACK, Number.QUEEN, Number.KING]
        if 0 <= index <= 12:
            return number_list[index]
        return None

    def _evaluate_tunnel_lock(self, state, my_hand, my_actions):
        """トンネルロック戦略"""
        bonus = {}

        for suit_idx, suit in enumerate(Suit):
            is_ace_out = state.field_cards[suit_idx][0] == 1
            is_king_out = state.field_cards[suit_idx][12] == 1

            my_high_cards = 0
            my_low_cards = 0
            for card in my_hand:
                if card.suit == suit:
                    if card.number.val >= 8:
                        my_high_cards += 1
                    elif card.number.val <= 6:
                        my_low_cards += 1

            if is_ace_out and not is_king_out:
                k_card = Card(suit, Number.KING)
                if k_card in my_hand and k_card in my_actions:
                    if my_high_cards >= 3:
                        bonus[k_card] = 8
                    else:
                        bonus[k_card] = -10

            if is_king_out and not is_ace_out:
                a_card = Card(suit, Number.ACE)
                if a_card in my_hand and a_card in my_actions:
                    if my_low_cards >= 3:
                        bonus[a_card] = 8
                    else:
                        bonus[a_card] = -10

        return bonus

    def _evaluate_burst_force(self, state, tracker, my_actions):
        """バースト誘導戦略"""
        bonus = {}

        for player in range(state.players_num):
            if player == self.my_player_num:
                continue
            if player in state.out_player:
                continue

            pass_count = state.pass_count[player]

            if pass_count >= 2:
                weak_suits = self._infer_weak_suits(tracker, player)
                for action in my_actions:
                    if action.suit in weak_suits:
                        bonus[action] = bonus.get(action, 0) + (pass_count * 5)

        return bonus

    def _infer_weak_suits(self, tracker, player):
        weak_suits = []
        for suit in Suit:
            possible_count = 0
            for number in Number:
                card = Card(suit, number)
                if card in tracker.possible[player]:
                    possible_count += 1
            if possible_count <= 4:
                weak_suits.append(suit)
        return weak_suits

    def _build_tracker_from_history(self, state):
        """履歴から推論器を構築"""
        tracker = CardTracker(state, self.my_player_num)

        replay_state = State(
            players_num=state.players_num,
            field_cards=np.zeros((4, 13), dtype='int64'),
            players_cards=[Hand([]) for _ in range(state.players_num)],
            turn_player=0,
            pass_count=[0] * state.players_num,
            out_player=[],
        )

        history = getattr(state, 'history', [])
        if not history:
            return tracker

        start_player = None
        for (p0, a0, pf0) in history:
            if pf0 == 0 and isinstance(a0, Card) and a0 == Card(Suit.DIAMOND, Number.SEVEN):
                start_player = p0
                break
        replay_state.turn_player = start_player if start_player is not None else 0

        for (p, a, pf) in history:
            tracker.observe_action(replay_state, p, a, is_pass=(pf == 1 or a is None))

            if pf == 1 or a is None:
                replay_state.pass_count[p] += 1
                if replay_state.pass_count[p] > 3 and p not in replay_state.out_player:
                    replay_state.out_player.append(p)
                    tracker.mark_out(p)
            else:
                if a is not None:
                    # カードを場に置く（エラーは無視 - すでに置かれている場合など）
                    self._put_card(replay_state, a)

            original = replay_state.turn_player
            for i in range(1, replay_state.players_num + 1):
                np_ = (original + i) % replay_state.players_num
                if np_ not in replay_state.out_player:
                    replay_state.turn_player = np_
                    break

        return tracker

    def _put_card(self, state, card):
        """場にカードを置く"""
        suit_index = 0
        for i, s in enumerate(Suit):
            if card.suit == s:
                suit_index = i
                break
        state.field_cards[suit_index][card.number.val - 1] = 1

    def _create_determinized_state_with_constraints(self, original_state, tracker):
        """推論制約を満たすように相手手札を生成"""
        base = self._clone_state(original_state)

        pool = []
        for p in range(base.players_num):
            if p != self.my_player_num:
                pool.extend(base.players_cards[p])

        for p in range(base.players_num):
            if p != self.my_player_num:
                base.players_cards[p] = Hand([])

        need = {p: len(original_state.players_cards[p]) for p in range(base.players_num) if p != self.my_player_num}

        for _ in range(30):
            random.shuffle(pool)
            remain = list(pool)
            hands = {p: [] for p in need.keys()}

            ok = True
            for p in need.keys():
                k = need[p]
                if k == 0:
                    continue

                possible_list = [c for c in remain if c in tracker.possible[p]]
                if len(possible_list) < k:
                    ok = False
                    break

                chosen = possible_list[:k]
                hands[p].extend(chosen)
                chosen_set = set(chosen)
                remain = [c for c in remain if c not in chosen_set]

            if not ok:
                continue

            if remain:
                ps = list(need.keys())
                idx = 0
                for c in remain:
                    hands[ps[idx % len(ps)]].append(c)
                    idx += 1

            for p, cards in hands.items():
                base.players_cards[p] = Hand(cards)

            return base

        # フォールバック
        shuffled_unknown = list(pool)
        random.shuffle(shuffled_unknown)
        card_idx = 0
        for p_idx in range(base.players_num):
            if p_idx != self.my_player_num:
                count = len(original_state.players_cards[p_idx])
                cards_for_p = shuffled_unknown[card_idx: card_idx + count]
                base.players_cards[p_idx] = Hand(cards_for_p)
                card_idx += count
        return base

    def _playout(self, state):
        """ゲーム終了までプレイアウト"""
        ais = [HybridStrongestAI(p, simulation_count=0) for p in range(state.players_num)]
        for a in ais:
            a._in_simulation = True

        for _ in range(SIMULATION_DEPTH):
            if state.is_done():
                break

            p_idx = state.turn_player
            actions = state.my_actions()

            if not actions:
                state.next(None, 1)
                continue

            action, pass_flag = ais[p_idx].get_action(state)
            state.next(action if pass_flag == 0 else None, pass_flag)

        for i, hand in enumerate(state.players_cards):
            if len(hand) == 0 and i not in state.out_player:
                return i
        return -1


# --- AIインスタンス作成 ---
_ai_instance = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)


# --- 提出用関数 ---
def my_AI(state):
    """
    大会提出用のAI関数
    
    引数:
        state: ゲームの現在状態
    
    戻り値:
        (action, pass_flag): 出すカードとパスフラグ
        - action: Cardオブジェクト（出すカード）またはNone（パス時）
        - pass_flag: 0（カードを出す）または1（パス）
    """
    return _ai_instance.get_action(state)
