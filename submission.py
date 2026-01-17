# Singularity Battle Quest - AI 7並べ (XQ) 提出用コード
# PIMC法（Perfect Information Monte Carlo）を用いた戦略的AI

from enum import Enum
import random
import numpy as np

# --- 設定 ---
MY_PLAYER_NUM = 0
SIMULATION_COUNT = 300  # 最適化済みのシミュレーション回数

# --- データクラス定義 ---

class Suit(Enum):
    SPADE = '♠'
    CLUB = '♣'
    HEART = '♡'
    DIAMOND = '♢'
    def __str__(self):
        return self.value
    def __repr__(self):
        return f"Suit.{self.name}"

class Number(Enum):
    ACE = (1, 'A')
    TWO = (2, '2')
    THREE = (3, '3')
    FOUR = (4, '4')
    FIVE = (5, '5')
    SIX = (6, '6')
    SEVEN = (7, '7')
    EIGHT = (8, '8')
    NINE = (9, '9')
    TEN = (10, '10')
    JACK = (11, 'J')
    QUEEN = (12, 'Q')
    KING = (13, 'K')

    def __init__(self, val, string):
        self.val = val
        self.string = string

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"Number.{self.name}"

class Card:
    def __init__(self, suit, number):
        self.suit = suit
        self.number = number

    def __str__(self):
        return str(self.suit) + str(self.number)

    def __repr__(self):
        return f"Card({self.__str__()})"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return (self.suit, self.number) == (other.suit, other.number)

    def __hash__(self):
        return hash((self.suit, self.number))

class Hand(list):
    def __init__(self, card_list):
        super().__init__(i for i in card_list)

    def check_number(self):
        return [i.number.val for i in self]

    def check_suit(self):
        return [str(i.suit) for i in self]

    def choice(self, card):
        if card in self:
            self.remove(card)
            return card
        else:
            raise ValueError

    def check(self, card):
        return card in self

class Deck(list):
    def __init__(self):
        from random import shuffle
        super().__init__(
            Card(suit, number) for suit in Suit for number in Number
        )
        shuffle(self)

    def deal(self, players_num):
        cards = [Hand(i) for i in np.array_split(self, players_num)]
        cards = [Hand(list(c)) for c in cards]
        self.clear()
        return cards


# --- 推論エンジン: 相手手札を推測 ---

class CardTracker:
    """パス履歴から相手の手札可能性を推論"""

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num
        self.all_cards = [Card(s, n) for s in Suit for n in Number]
        
        # possible[p] = プレイヤーpが持ちうるカード集合
        self.possible = [set(self.all_cards) for _ in range(self.players_num)]
        self.pass_counts = [0] * self.players_num
        
        # 場に出たカードは誰も持たない
        self._apply_field(state)
        
        # 自分の手札は確定
        my_hand = set(state.players_cards[my_player_num])
        for p in range(self.players_num):
            if p == my_player_num:
                self.possible[p].intersection_update(my_hand)
            else:
                self.possible[p].difference_update(my_hand)
        
        self.out_player = set(state.out_player)

    def _apply_field(self, state):
        """場に出たカードを除外"""
        for s_idx, s in enumerate(Suit):
            for n_idx, n in enumerate(Number):
                if state.field_cards[s_idx][n_idx] == 1:
                    card = Card(s, n)
                    for p in range(self.players_num):
                        self.possible[p].discard(card)

    def observe_action(self, state, player, action, is_pass):
        """行動観測で可能性を更新"""
        if player in self.out_player:
            return

        if is_pass:
            self.pass_counts[player] += 1
            # パス時、出せるカードを持っていないと推論
            legal = state.legal_actions()
            for c in legal:
                self.possible[player].discard(c)
        elif action is not None:
            # カードを出したら全員が持っていない
            for p in range(self.players_num):
                self.possible[p].discard(action)

    def mark_out(self, player):
        self.out_player.add(player)
        self.possible[player].clear()

    def get_player_weight(self, player):
        """パス回数に基づく重み（0.5～1.0）"""
        weight = 1.0 - (self.pass_counts[player] / 4.0) * 0.5
        return max(0.5, weight)


# --- ゲームエンジン ---

class State:
    def __init__(self, players_num=3, field_cards=None, players_cards=None, 
                 turn_player=None, pass_count=None, out_player=None, history=None):
        if players_cards is None:
            self.players_num = players_num
            self._init_deal_and_open_sevens()
        else:
            self.players_cards = players_cards
            self.field_cards = field_cards
            self.players_num = players_num
            self.turn_player = turn_player
            self.pass_count = pass_count
            self.out_player = out_player
            self.history = history if history is not None else []

    def _init_deal_and_open_sevens(self):
        deck = Deck()
        self.players_cards = deck.deal(self.players_num)
        self.field_cards = np.zeros((4, 13), dtype='int64')
        self.pass_count = [0] * self.players_num
        self.out_player = []
        self.history = []

        # 7を自動で場に出す
        start_flags = [0] * self.players_num
        for p in range(self.players_num):
            start_flags[p] = self.choice_seven(hand=self.players_cards[p], player=p)

        self.turn_player = start_flags.index(1) if 1 in start_flags else 0

    def clone(self):
        """シミュレーション用のコピー"""
        return State(
            players_num=self.players_num,
            field_cards=self.field_cards.copy(),
            players_cards=[Hand(list(h)) for h in self.players_cards],
            turn_player=self.turn_player,
            pass_count=list(self.pass_count),
            out_player=list(self.out_player),
            history=list(self.history),
        )

    def choice_seven(self, hand, player=None):
        """手札の7を場に出す"""
        is_start_player = 0
        sevens = [Card(suit, Number.SEVEN) for suit in Suit]

        if hand.check(Card(Suit.DIAMOND, Number.SEVEN)):
            is_start_player = 1

        for card in sevens:
            if hand.check(card):
                hand.choice(card)
                self.put_card(card)
                if player is not None:
                    self.history.append((player, card, 0))

        return is_start_player

    def put_card(self, card):
        """場にカードを置く"""
        suit_index = 0
        for i, s in enumerate(Suit):
            if card.suit == s:
                suit_index = i
                break
        self.field_cards[suit_index][card.number.val - 1] = 1

    def legal_actions(self):
        """場で出せるカード（トンネルルール対応）"""
        actions = []
        for suit, n in zip(Suit, range(4)):
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            # 7より小さい側（Kが出ている時のみ伸ばせる）
            if is_king_out:
                small_side = self.field_cards[n][0:6]
                if small_side[5] == 0:
                    actions.append(Card(suit, Number.SIX))
                else:
                    for i in range(5, -1, -1):
                        if small_side[i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

            # 7より大きい側（Aが出ている時のみ伸ばせる）
            if is_ace_out:
                if self.field_cards[n][7] == 0:
                    actions.append(Card(suit, Number.EIGHT))
                else:
                    for i in range(7, 13):
                        if self.field_cards[n][i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

        return list(set(actions))

    def num_to_Enum(self, num):
        enum_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                   Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                   Number.NINE, Number.TEN, Number.JACK, Number.QUEEN,
                   Number.KING]
        return enum_list[num - 1]

    def my_actions(self):
        """現在のプレイヤーが出せるカード"""
        actions = []
        current_hand = self.players_cards[self.turn_player]
        legal = self.legal_actions()
        for card in legal:
            if current_hand.check(card):
                actions.append(card)
        return actions

    def my_hands(self):
        return self.players_cards[self.turn_player]

    def is_done(self):
        """ゲーム終了判定"""
        for i, hand in enumerate(self.players_cards):
            if len(hand) == 0 and i not in self.out_player:
                return True
        active_count = self.players_num - len(self.out_player)
        return active_count <= 1

    def next(self, action, pass_flag=0):
        """状態を更新して次へ"""
        p_idx = self.turn_player
        self.history.append((p_idx, action, 1 if (pass_flag == 1 or action is None) else 0))

        if pass_flag == 1 or action is None:
            # パス処理
            self.pass_count[p_idx] += 1
            if self.pass_count[p_idx] > 3:
                # バースト: 手札をすべて場に出す
                hand = self.players_cards[p_idx]
                for card in list(hand):
                    try:
                        self.put_card(card)
                    except:
                        pass
                hand.clear()
                self.out_player.append(p_idx)
        else:
            # カードを出す
            if action:
                try:
                    self.players_cards[p_idx].choice(action)
                    self.put_card(action)
                except ValueError:
                    pass

        # 勝利判定
        if len(self.players_cards[p_idx]) == 0 and p_idx not in self.out_player:
            return self
              
        # 次のプレイヤーへ
        self.next_player()
        return self

    def next_player(self):
        """次の有効なプレイヤーへ"""
        original = self.turn_player
        for i in range(1, self.players_num + 1):
            next_p = (original + i) % self.players_num
            if next_p not in self.out_player:
                self.turn_player = next_p
                return


# --- AI実装: PIMC法（Phase 1改善版） ---

class HybridStrongestAI:
    """PIMC法を用いた戦略的AI
    
    Phase 1: 推論エンジン（CardTracker）で相手手札を推測
    Phase 2: 確定化（Determinization）で複数の仮想世界を生成
    Phase 3: 各仮想世界でプレイアウトして勝率を評価
    
    改善点:
    - PASS候補の完全除外
    - 重み付け確定化
    - 適応的ロールアウトポリシー
    """
    
    def __init__(self, my_player_num, simulation_count=300):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count
        self._in_simulation = False

    def get_action(self, state):
        """行動を決定"""
        # シミュレーション中は軽量なロールアウトポリシー
        if self._in_simulation:
            return self._rollout_policy_action(state)

        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # Phase 1改善: PASS候補を除外（合法手があれば必ず打つ）
        candidates = list(my_actions)

        if len(candidates) == 1:
            return candidates[0], 0

        # Phase 1: 履歴から相手手札を推論
        tracker = self._build_tracker_from_history(state)
        
        # Phase 2 & 3: 各候補をシミュレーションで評価
        action_scores = {action: 0 for action in candidates}

        for _ in range(self.simulation_count):
            # Phase 2: 確定化（推論に基づき相手手札を生成）
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            for first_action in candidates:
                sim_state = determinized_state.clone()
                sim_state.next(first_action, 0)

                # Phase 3: プレイアウト
                winner = self._playout(sim_state)

                if winner == self.my_player_num:
                    action_scores[first_action] += 1
                elif winner != -1:
                    action_scores[first_action] -= 1

        best_action = max(action_scores, key=action_scores.get)
        return best_action, 0

    def _rollout_policy_action(self, state):
        """軽量なロールアウトポリシー
        
        1. 端優先（A/K）：トンネルを活用
        2. Safe優先：連続して出せる札を優先
        3. ランダム選択
        """
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # 1. 端優先
        ends = [a for a in my_actions if a.number in (Number.ACE, Number.KING)]
        if ends:
            return random.choice(ends), 0

        # 2. Safe優先
        hand_strs = [str(c) for c in state.players_cards[state.turn_player]]
        safe = [a for a in my_actions if self._is_safe_move(a, hand_strs)]
        if safe:
            return random.choice(safe), 0

        # 3. ランダム
        return random.choice(my_actions), 0

    def _build_tracker_from_history(self, state):
        """履歴を再生して推論"""
        tracker = CardTracker(state, self.my_player_num)

        # 盤面のみ再現する軽量state
        replay_state = State(
            players_num=state.players_num,
            field_cards=np.zeros((4, 13), dtype='int64'),
            players_cards=[Hand([]) for _ in range(state.players_num)],
            turn_player=0,
            pass_count=[0] * state.players_num,
            out_player=[],
            history=[],
        )

        # 履歴から開始プレイヤーを復元
        start_player = None
        for (p0, a0, pf0) in state.history:
            if pf0 == 0 and isinstance(a0, Card) and a0 == Card(Suit.DIAMOND, Number.SEVEN):
                start_player = p0
                break
        replay_state.turn_player = start_player if start_player is not None else 0

        # 履歴を再生
        for (p, a, pf) in state.history:
            # 観測
            tracker.observe_action(replay_state, p, a, is_pass=(pf == 1 or a is None))

            # 盤面更新
            if pf == 1 or a is None:
                replay_state.pass_count[p] += 1
                if replay_state.pass_count[p] > 3 and p not in replay_state.out_player:
                    replay_state.out_player.append(p)
                    tracker.mark_out(p)
            else:
                if a is not None:
                    try:
                        replay_state.put_card(a)
                    except:
                        pass

            # 次手番へ
            original = replay_state.turn_player
            for i in range(1, replay_state.players_num + 1):
                np_ = (original + i) % replay_state.players_num
                if np_ not in replay_state.out_player:
                    replay_state.turn_player = np_
                    break

        return tracker

    def _create_determinized_state_with_constraints(self, original_state, tracker):
        """重み付け確定化: 推論制約を満たすように相手手札を生成"""
        base = original_state.clone()

        # 相手のカードプール
        pool = []
        for p in range(base.players_num):
            if p != self.my_player_num:
                pool.extend(base.players_cards[p])

        # いったん空にして再配分
        for p in range(base.players_num):
            if p != self.my_player_num:
                base.players_cards[p] = Hand([])

        need = {p: len(original_state.players_cards[p]) for p in range(base.players_num) if p != self.my_player_num}

        # 30回リトライ
        for _ in range(30):
            random.shuffle(pool)
            remain = list(pool)
            hands = {p: [] for p in need.keys()}
            ok = True

            # 各プレイヤーに可能なカードを割り当て
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

            # 残りを分配
            if remain:
                ps = list(need.keys())
                idx = 0
                for c in remain:
                    hands[ps[idx % len(ps)]].append(c)
                    idx += 1

            # 反映
            for p, cards in hands.items():
                base.players_cards[p] = Hand(cards)

            return base

        # フォールバック: ランダム確定化
        return self._create_determinized_state(original_state, pool)

    def _is_safe_move(self, card, hand_card_strs):
        """次のカードを自分が持っていればSafe"""
        val = card.number.val
        suit = card.suit
        
        if val == 1 or val == 13:
            return True
            
        next_target_val = -1
        if val < 7:
            next_target_val = val - 1
        elif val > 7:
            next_target_val = val + 1
        else:
            return False
        
        target_number = None
        for n in Number:
            if n.val == next_target_val:
                target_number = n
                break
        
        if target_number:
            target_card_str = str(suit) + str(target_number)
            return target_card_str in hand_card_strs
            
        return False

    def _create_determinized_state(self, original_state, unknown_cards):
        """フォールバック用のランダム確定化"""
        shuffled_unknown = list(unknown_cards)
        random.shuffle(shuffled_unknown)
        new_state = original_state.clone()
        card_idx = 0
        for p_idx in range(new_state.players_num):
            if p_idx != self.my_player_num:
                count = len(new_state.players_cards[p_idx])
                cards_for_p = shuffled_unknown[card_idx : card_idx + count]
                new_state.players_cards[p_idx] = Hand(cards_for_p)
                card_idx += count
        return new_state

    def _playout(self, state):
        """プレイアウト: ゲーム終了まで高速に進める"""
        ais = [HybridStrongestAI(p, simulation_count=0) for p in range(state.players_num)]
        for a in ais:
            a._in_simulation = True

        for _ in range(200):
            if state.is_done():
                break

            p_idx = state.turn_player
            actions = state.my_actions()

            if not actions:
                state.next(None, 1)
                continue

            action, pass_flag = ais[p_idx].get_action(state)
            state.next(action if pass_flag == 0 else None, pass_flag)

        # 勝者を返す
        for i, hand in enumerate(state.players_cards):
            if len(hand) == 0 and i not in state.out_player:
                return i
        return -1


# --- 提出用インターフェース ---

ai_instance = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)

def my_AI(state):
    """提出用のAI関数
    
    Returns:
        (action, pass_flag): 出すカードとパスフラグのタプル
    """
    return ai_instance.get_action(state)
