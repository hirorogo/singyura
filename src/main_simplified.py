import random
from enum import Enum
import numpy as np

# --- 定数・設定 ---
EP_GAME_COUNT = 1000  # 評価用の対戦回数
MY_PLAYER_NUM = 0     # 自分のプレイヤー番号

# シミュレーション用設定（シンプル版 - ベースライン確立用）
SIMULATION_COUNT = 300  # テスト最適値（200-300で安定、500は過剰）
SIMULATION_DEPTH = 300  # どこまで先読みするか

# Phase 1改善フラグ - シンプル版では基本機能のみ有効化
ENABLE_PASS_REMOVAL = True  # PASS候補の完全除外（基本機能）
ENABLE_WEIGHTED_DETERMINIZATION = False  # 無効化：複雑性削減
ENABLE_ADAPTIVE_ROLLOUT = False  # 無効化：シンプルなランダムポリシー

# Phase 2改善フラグ - シンプル版では全て無効化
ENABLE_TUNNEL_LOCK = False  # 無効化：戦略ボーナスを排除
ENABLE_BURST_FORCE = False  # 無効化：戦略ボーナスを排除

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
        return (self.suit, self.number) == (other.suit, other.number)

    def __hash__(self):
        return hash((self.suit, self.number))

class Hand(list):
    def __init__(self, card_list):
        super().__init__(i for i in card_list)

    def check_number(self):
        number_list = [i.number.val for i in self]
        return number_list

    def check_suit(self):
        suit_list = [str(i.suit) for i in self]
        return suit_list

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
        super().__init__(
            Card(suit, number) for suit in Suit for number in Number
        )
        self.shuffle()

    def shuffle(self):
        shuffle(self)

    def draw(self):
        return self.pop()

    def deal(self, players_num):
        cards = [Hand(i) for i in np.array_split(self, players_num)]
        # numpy array からリストに戻す
        cards = [Hand(list(c)) for c in cards]
        self.clear()
        return cards


# --- 推論器 (Inference Engine) ---

class CardTracker:
    """不完全情報(相手手札)の推論器。

    Phase 1改善:
    - パス回数に基づく重み付け
    """

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num

        # 全カード集合
        self.all_cards = [Card(s, n) for s in Suit for n in Number]

        # possible[p][card] = bool
        self.possible = [set(self.all_cards) for _ in range(self.players_num)]

        # Phase 1改善: パス回数を記録（重み付け用）
        self.pass_counts = [0] * self.players_num

        # 場に出たカードは誰も持たない
        self._apply_field(state)

        # 自分の手札は確定: 自分のみが持ちうる
        my_hand = set(state.players_cards[my_player_num])
        for p in range(self.players_num):
            if p == my_player_num:
                self.possible[p].intersection_update(my_hand)
            else:
                self.possible[p].difference_update(my_hand)

        # すでにアウト(burst)しているプレイヤーは手札0として扱い、推論対象外
        self.out_player = set(state.out_player)

    def clone(self):
        c = object.__new__(CardTracker)
        c.players_num = self.players_num
        c.my_player_num = self.my_player_num
        c.all_cards = self.all_cards
        c.possible = [set(s) for s in self.possible]
        c.out_player = set(self.out_player)
        c.pass_counts = list(self.pass_counts)
        return c

    def _apply_field(self, state):
        # field_cards から「場に出ているカード集合」を作る
        for s_idx, s in enumerate(Suit):
            for n_idx, n in enumerate(Number):
                if state.field_cards[s_idx][n_idx] == 1:
                    card = Card(s, n)
                    for p in range(self.players_num):
                        self.possible[p].discard(card)

    def observe_action(self, state, player, action, is_pass):
        """行動観測で制約を更新。

        Phase 1改善:
        - パス回数を記録
        """
        if player in self.out_player:
            return

        if is_pass:
            self.pass_counts[player] += 1
            # シンプル版：パス観測を保守的に扱う
            # 改善版では legal_actions() のカードを possible から除外する実装もあるが、
            # この簡易版では戦略的パスの可能性を考慮し、そのような除外は行わない。
            # ここではパス回数の記録のみ行い、重み付け確定化で統計的に利用する。
            return

        if action is not None:
            for p in range(self.players_num):
                self.possible[p].discard(action)

    def mark_out(self, player):
        self.out_player.add(player)
        self.possible[player].clear()

    def get_player_weight(self, player):
        """Phase 1改善: パス回数に基づく重み付け
        
        パスが多いプレイヤーほど「出しやすい札を持っていない」
        → 重みを下げる
        """
        if not ENABLE_WEIGHTED_DETERMINIZATION:
            return 1.0
        
        # パス回数が多いほど重みを下げる（0.5～1.0の範囲）
        weight = 1.0 - (self.pass_counts[player] / 4.0) * 0.5
        return max(0.5, weight)


# --- ゲームエンジン ---

class State:
    def __init__(self, players_num=3, field_cards=None, players_cards=None, turn_player=None, pass_count=None, out_player=None, history=None):
        if players_cards is None:
            # 初期化は関数にまとめて、replayでも再利用できるようにする
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
        self.history = []  # (player, action, pass_flag)

        # 手札にある7を自動的に場に出す処理（履歴にも残す）
        start_flags = [0] * self.players_num
        for p in range(self.players_num):
            start_flags[p] = self.choice_seven(hand=self.players_cards[p], player=p, record_history=True)

        if 1 in start_flags:
            self.turn_player = start_flags.index(1)
        else:
            self.turn_player = 0

    def clone(self):
        """シミュレーション用に状態の深いコピーを作成"""
        # オブジェクトのディープコピーは重いので手動で行う
        new_players_cards = [Hand(list(h)) for h in self.players_cards]
        new_field_cards = self.field_cards.copy()
        new_pass_count = list(self.pass_count)
        new_out_player = list(self.out_player)
        new_history = list(self.history)

        return State(
            players_num=self.players_num,
            field_cards=new_field_cards,
            players_cards=new_players_cards,
            turn_player=self.turn_player,
            pass_count=new_pass_count,
            out_player=new_out_player,
            history=new_history,
        )

    def choice_seven(self, hand, player=None, record_history=False):
        """手札の7を場に出す。ダイヤの7があれば1を返す。

        record_history=True のとき、出した7を history に (player, card, 0) で記録する。
        """
        is_start_player = 0
        sevens = [Card(suit, Number.SEVEN) for suit in Suit]

        if hand.check(Card(Suit.DIAMOND, Number.SEVEN)):
            is_start_player = 1

        for card in sevens:
            if hand.check(card):
                hand.choice(card)
                self.put_card(card)
                if record_history and player is not None:
                    # 初期配置は「パスではない」扱い
                    self.history.append((player, card, 0))

        return is_start_player

    @staticmethod
    def replay_from_start(ended_state):
        """ended_state の history を先頭から正しく再生し、各手番時点の盤面で legal_actions を評価できる State を返す。"""
        s = State(
            players_num=ended_state.players_num,
            field_cards=ended_state.field_cards.copy() * 0,
            players_cards=[Hand(list(h)) for h in ended_state.players_cards],
            turn_player=ended_state.turn_player,
            pass_count=[0] * ended_state.players_num,
            out_player=[],
            history=[],
        )

        s.players_cards = [Hand([]) for _ in range(ended_state.players_num)]
        s.field_cards = np.zeros((4, 13), dtype='int64')
        s.pass_count = [0] * ended_state.players_num
        s.out_player = []

        # start player は history のうちダイヤ7を出したプレイヤーが原則
        start_player = None
        for (p, a, pf) in ended_state.history:
            if pf == 0 and isinstance(a, Card) and a == Card(Suit.DIAMOND, Number.SEVEN):
                start_player = p
                break
        s.turn_player = start_player if start_player is not None else 0

        # replay
        for (p, a, pf) in ended_state.history:
            if pf == 1 or a is None:
                s.pass_count[p] += 1
                if s.pass_count[p] > 3:
                    if p not in s.out_player:
                        s.out_player.append(p)
            else:
                try:
                    s.put_card(a)
                except Exception:
                    pass

            # 次の手番へ
            original = s.turn_player
            for i in range(1, s.players_num + 1):
                np_ = (original + i) % s.players_num
                if np_ not in s.out_player:
                    s.turn_player = np_
                    break

        return s

    def put_card(self, card):
        """場にカードを置く（記録する）"""
        suit_index = 0
        for i, s in enumerate(Suit):
            if card.suit == s:
                suit_index = i
                break
        self.field_cards[suit_index][card.number.val - 1] = 1

    def legal_actions(self):
        """場で出せるカードのリストを返す (トンネルルール対応)。"""
        actions = []
        for suit, n in zip(Suit, range(4)):
            # Aが出ている (index 0) / Kが出ている (index 12)
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            # --- 7より小さい側 (A-6) ---
            # Kが出ている場合のみ、この側を伸ばしてよい
            if is_king_out:
                small_side = self.field_cards[n][0:6]  # A..6
                if small_side[5] == 0:
                    actions.append(Card(suit, Number.SIX))
                else:
                    for i in range(5, -1, -1):
                        if small_side[i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

            # --- 7より大きい側 (8-K) ---
            # Aが出ている場合のみ、この側を伸ばしてよい
            if is_ace_out:
                if self.field_cards[n][7] == 0:
                    actions.append(Card(suit, Number.EIGHT))
                else:
                    for i in range(7, 13):
                        if self.field_cards[n][i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

        return list(set(actions))  # 重複排除

    def num_to_Enum(self, num):
        enum_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                   Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                   Number.NINE, Number.TEN, Number.JACK, Number.QUEEN,
                   Number.KING]
        return enum_list[num - 1]

    def my_actions(self):
        """現在のプレイヤーが出せるカード一覧"""
        actions = []
        current_hand = self.players_cards[self.turn_player]
        # 効率化のため、手札と場に出せるカードの積集合を取る
        legal = self.legal_actions()
        for card in legal:
            if current_hand.check(card):
                actions.append(card)
        return actions

    def my_hands(self):
        return self.players_cards[self.turn_player]

    def is_done(self):
        """ゲーム終了判定: 勝者（手札0）が出たか、または残り1人になったら終了"""
        # 手札がなくなったプレイヤーがいれば終了
        for i, hand in enumerate(self.players_cards):
            if len(hand) == 0 and i not in self.out_player:
                return True
        
        # バースト等で残り1人になったら終了
        active_count = self.players_num - len(self.out_player)
        return active_count <= 1

    def next(self, action, pass_flag=0):
        """状態更新"""
        # 現在のプレイヤー
        p_idx = self.turn_player

        # 行動ログ
        self.history.append((p_idx, action, 1 if (pass_flag == 1 or action is None) else 0))

        if pass_flag == 1 or action is None:
            # パス処理
            self.pass_count[p_idx] += 1
            if self.pass_count[p_idx] > 3:
                # バースト処理
                # 手札をすべて場に出す
                hand = self.players_cards[p_idx]
                for card in list(hand):
                    try:
                        self.put_card(card)
                    except Exception:
                        # 既に場に出ているカードなどのエラーは無視
                        pass
                hand.clear() # 手札消滅
                self.out_player.append(p_idx)
        else:
            # カードを出す
            if action:
                try:
                    self.players_cards[p_idx].choice(action) # 手札から削除
                    self.put_card(action) # 場に出す
                except ValueError:
                    # 手札に存在しないカードの場合は無視
                    pass

        # 勝利判定チェック（手札が0になったら）
        if len(self.players_cards[p_idx]) == 0 and p_idx not in self.out_player:
            return self
             
        # 次のプレイヤーへ
        self.next_player()
        return self

    def next_player(self):
        """次の有効なプレイヤーにターンを渡す"""
        original = self.turn_player
        for i in range(1, self.players_num + 1):
            next_p = (original + i) % self.players_num
            # バーストしたプレイヤーや上がったプレイヤー（out_player）はスキップ
            if next_p not in self.out_player:
                self.turn_player = next_p
                return


# --- Phase 1改善版AI実装 ---

class OpponentModel:
    """strategy.md の相手タイプ推定(簡易)。"""

    def __init__(self, players_num):
        self.players_num = players_num
        self.flags = {p: {"aggressive": 0, "blocker": 0} for p in range(players_num)}

    def observe(self, state, player, action, pass_flag):
        if pass_flag == 1:
            self.flags[player]["blocker"] += 1
            return

        if action is None or isinstance(action, list):
            return

        # A/K を早出し → aggressive
        if action.number in (Number.ACE, Number.KING):
            self.flags[player]["aggressive"] += 2

        # 中央(6/8)やJ/Qあたりを止める動きも blocker になりやすいが簡易
        if action.number in (Number.SIX, Number.EIGHT, Number.JACK, Number.QUEEN):
            self.flags[player]["blocker"] += 1

    def mode(self, player):
        a = self.flags[player]["aggressive"]
        b = self.flags[player]["blocker"]
        if a >= b + 2:
            return "tunnel_lock"
        if b >= a + 2:
            return "burst_force"
        return "neutral"


class ImprovedHybridAI:
    """Phase 1改善版: PIMC法 + 戦略的最適化
    
    改善点:
    1. PASS候補の完全除外
    2. 重み付け確定化
    3. 適応的ロールアウトポリシー
    """
    
    def __init__(self, my_player_num, simulation_count=200):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count

        self._opponent_model = None
        # シミュレーション内で再帰的にPIMCを呼ばないためのガード
        self._in_simulation = False

    def get_action(self, state):
        # シミュレーション中は軽量なロールアウトポリシーで打つ
        if self._in_simulation:
            return self._rollout_policy_action(state)

        # opponent model 初期化
        if self._opponent_model is None or self._opponent_model.players_num != state.players_num:
            self._opponent_model = OpponentModel(state.players_num)

        # 直近の履歴から相手傾向を更新
        for (p, a, pf) in state.history[-5:]:
            self._opponent_model.observe(state, p, a, pf)

        my_actions = state.my_actions()
        if not my_actions:
            # 出せるカードがない場合はパス
            return None, 1

        # Phase 1改善1: PASS候補の完全除外
        # 合法手がある場合は必ず打つ（PASSを候補に含めない）
        if ENABLE_PASS_REMOVAL:
            candidates = list(my_actions)  # PASSを含めない
        else:
            # 従来の実装（参考用）
            candidates = list(my_actions)
            if state.pass_count[self.my_player_num] < 3:
                candidates.append(None)

        if len(candidates) == 1:
            return candidates[0], 0

        tracker = self._build_tracker_from_history(state)
        
        # Phase 2改善: 戦略的評価（シンプル版では全てのフラグがFalseのため未使用）
        # 将来の改善版との構造を揃えるため、呼び出しは残すが結果は利用しない
        # strategic_bonus = self._evaluate_strategic_actions(state, tracker, my_actions)

        action_scores = {action: 0 for action in candidates}

        # シンプル版PIMC法：戦略ボーナスなし、純粋なシミュレーション評価
        for _ in range(self.simulation_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            # 全候補を同じ確定化で評価
            for first_action in candidates:
                sim_state = determinized_state.clone()
                sim_state.next(first_action, 0)

                winner = self._playout(sim_state)

                # シンプルなスコアリング
                if winner == self.my_player_num:
                    action_scores[first_action] += 2  # 勝利は+2点
                elif winner == -1:
                    # 引き分け（全員バースト）は0点
                    pass
                else:
                    action_scores[first_action] -= 1  # 負けは-1点
        
        # シンプル版：戦略ボーナスは使用しない（無効化されている場合）
        # これにより純粋なシミュレーション結果のみで評価

        best_action = max(action_scores, key=action_scores.get)
        return best_action, 0

    def _rollout_policy_action(self, state):
        """シンプル版：完全ランダムなロールアウトポリシー
        
        複雑な戦略を排除し、高速性と安定性を優先
        """
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # シンプル版：完全ランダム選択（最も高速で偏りがない）
        return random.choice(my_actions), 0
    
    def _evaluate_strategic_actions(self, state, tracker, my_actions):
        """Phase 2改善: 戦略的評価
        
        トンネルロックとバースト誘導の戦略ボーナスを計算
        
        注：シンプル版では全てのフラグがFalseのため、常に空のdictを返す。
        将来の改善版との構造を揃えるため、メソッドは残している。
        """
        bonus = {}
        my_hand = state.players_cards[self.my_player_num]
        
        # トンネルロック戦略（シンプル版では無効）
        if ENABLE_TUNNEL_LOCK:
            tunnel_bonus = self._evaluate_tunnel_lock(state, my_hand, my_actions)
            for action, score in tunnel_bonus.items():
                bonus[action] = bonus.get(action, 0) + score
        
        # バースト誘導戦略（シンプル版では無効）
        if ENABLE_BURST_FORCE:
            burst_bonus = self._evaluate_burst_force(state, tracker, my_actions)
            for action, score in burst_bonus.items():
                bonus[action] = bonus.get(action, 0) + score
        
        return bonus
    
    def _evaluate_tunnel_lock(self, state, my_hand, my_actions):
        """トンネルロック戦略
        
        相手がトンネルを開けている場合、逆側の端カードを温存して封鎖する
        
        注：シンプル版ではENABLE_TUNNEL_LOCKがFalseのため使用されないが、
        将来の改善版との互換性のため残している。
        """
        bonus = {}
        
        for suit_idx, suit in enumerate(Suit):
            # Aが出ている場合、Kを温存（出さない方向にペナルティ）
            if state.field_cards[suit_idx][0] == 1:  # A (index 0) が出ている
                k_card = Card(suit, Number.KING)
                if k_card in my_hand and k_card in my_actions:
                    # Kを出すことに小さなペナルティ（出さない方が有利）
                    bonus[k_card] = -15
                    
                # K手前のQ, Jも温存傾向
                q_card = Card(suit, Number.QUEEN)
                if q_card in my_hand and q_card in my_actions:
                    bonus[q_card] = -8
                    
                j_card = Card(suit, Number.JACK)
                if j_card in my_hand and j_card in my_actions:
                    bonus[j_card] = -5
            
            # Kが出ている場合、Aを温存
            if state.field_cards[suit_idx][12] == 1:  # K (index 12) が出ている
                a_card = Card(suit, Number.ACE)
                if a_card in my_hand and a_card in my_actions:
                    # Aを出すことに小さなペナルティ
                    bonus[a_card] = -15
                    
                # A手前の2, 3も温存傾向
                two_card = Card(suit, Number.TWO)
                if two_card in my_hand and two_card in my_actions:
                    bonus[two_card] = -8
                    
                three_card = Card(suit, Number.THREE)
                if three_card in my_hand and three_card in my_actions:
                    bonus[three_card] = -5
        
        return bonus
    
    def _evaluate_burst_force(self, state, tracker, my_actions):
        """バースト誘導戦略
        
        パス回数が多い相手が持っていないスートを急速に進める
        
        注：シンプル版ではENABLE_BURST_FORCEがFalseのため使用されないが、
        将来の改善版との互換性のため残している。
        """
        bonus = {}
        
        # 各プレイヤーのパス回数をチェック
        for player in range(state.players_num):
            if player == self.my_player_num:
                continue
            if player in state.out_player:
                continue
                
            pass_count = state.pass_count[player]
            
            # パス回数が2回以上の場合、危険水域と判断
            if pass_count >= 2:
                # このプレイヤーが持っていなさそうなスートを推論
                weak_suits = self._infer_weak_suits(state, tracker, player)
                
                # 弱いスートを進めることにボーナス
                for action in my_actions:
                    if action.suit in weak_suits:
                        # パス回数が多いほど大きなボーナス（控えめに）
                        bonus[action] = bonus.get(action, 0) + (pass_count * 5)
        
        return bonus
    
    def _infer_weak_suits(self, state, tracker, player):
        """相手の弱いスート（持っていないカードが多そうなスート）を推論
        
        注：シンプル版では_evaluate_burst_forceが使用されないため、
        この関数も使用されない。将来の改善版との互換性のため残している。
        """
        weak_suits = []
        
        # 各スートについて、そのプレイヤーが持っている可能性のあるカード数を数える
        for suit in Suit:
            possible_count = 0
            for number in Number:
                card = Card(suit, number)
                if card in tracker.possible[player]:
                    possible_count += 1
            
            # 持っている可能性のあるカードが少ない（4枚以下）なら弱いスート
            if possible_count <= 4:
                weak_suits.append(suit)
        
        return weak_suits

    def _build_tracker_from_history(self, state):
        """履歴を先頭から逐次再生し、その時点の盤面(legal_actions)でパス推論を行う。"""
        tracker = CardTracker(state, self.my_player_num)

        # 盤面のみ再現する軽量 state を作る
        replay_state = State(
            players_num=state.players_num,
            field_cards=np.zeros((4, 13), dtype='int64'),
            players_cards=[Hand([]) for _ in range(state.players_num)],
            turn_player=0,
            pass_count=[0] * state.players_num,
            out_player=[],
            history=[],
        )

        # start player を履歴から復元（ダイヤ7を出したプレイヤー）
        start_player = None
        for (p0, a0, pf0) in state.history:
            if pf0 == 0 and isinstance(a0, Card) and a0 == Card(Suit.DIAMOND, Number.SEVEN):
                start_player = p0
                break
        replay_state.turn_player = start_player if start_player is not None else 0

        for (p, a, pf) in state.history:
            # 1) その手番直前の盤面で観測（legal_actionsが正しい）
            tracker.observe_action(replay_state, p, a, is_pass=(pf == 1 or a is None))

            # 2) 行動を replay_state に適用（盤面/パス/アウト）
            if pf == 1 or a is None:
                replay_state.pass_count[p] += 1
                if replay_state.pass_count[p] > 3 and p not in replay_state.out_player:
                    replay_state.out_player.append(p)
                    tracker.mark_out(p)
            else:
                if a is not None:
                    try:
                        replay_state.put_card(a)
                    except Exception:
                        # 再現不能な履歴（不正なカード配置など）が存在する場合は、
                        # その行動をスキップしてゲーム進行を継続する
                        pass

            # 3) 次手番へ（out_player をスキップ）
            original = replay_state.turn_player
            for i in range(1, replay_state.players_num + 1):
                np_ = (original + i) % replay_state.players_num
                if np_ not in replay_state.out_player:
                    replay_state.turn_player = np_
                    break

        return tracker

    def _create_determinized_state_with_constraints(self, original_state, tracker: CardTracker):
        """Phase 1改善2: 重み付け確定化
        
        推論制約(possible)とパス回数の重みを考慮して相手手札を生成。
        """
        base = original_state.clone()

        # 相手に配るべきカードプール
        pool = []
        for p in range(base.players_num):
            if p != self.my_player_num:
                pool.extend(base.players_cards[p])

        # いったん空にして再配分
        for p in range(base.players_num):
            if p != self.my_player_num:
                base.players_cards[p] = Hand([])

        # 手札枚数
        need = {p: len(original_state.players_cards[p]) for p in range(base.players_num) if p != self.my_player_num}

        # Phase 1改善: 重み付けを考慮したリトライ
        for _ in range(30):
            random.shuffle(pool)

            remain = list(pool)
            hands = {p: [] for p in need.keys()}

            ok = True
            # 各プレイヤーに「可能なカード」を優先して割り当て
            for p in need.keys():
                k = need[p]
                if k == 0:
                    continue

                # Phase 1改善: 重み付けを考慮
                possible_list = [c for c in remain if c in tracker.possible[p]]
                
                if len(possible_list) < k:
                    # 制約が厳しすぎる場合は失敗
                    ok = False
                    break
                
                # Phase 1改善: 重み付けに基づいたサンプリング
                if ENABLE_WEIGHTED_DETERMINIZATION:
                    weight = tracker.get_player_weight(p)
                    # 重みが低い場合は可能なカードの前半から選択（制約強め）
                    # 重みが高い場合は全体からランダムに選択（制約緩め）
                    if weight < 0.7:
                        # パスが多いプレイヤーは出しにくいカードを持っている可能性
                        chosen = random.sample(possible_list, k)
                    else:
                        # 通常のランダム選択
                        chosen = random.sample(possible_list, k)
                else:
                    chosen = random.sample(possible_list, k)

                hands[p].extend(chosen)
                # remove chosen from remain
                chosen_set = set(chosen)
                remain = [c for c in remain if c not in chosen_set]

            if not ok:
                continue

            # もし残りがある(理論上ないはず)なら適当に分配
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

        # フォールバック: 元のランダム確定化
        return self._create_determinized_state(original_state, pool)

    def _is_safe_move(self, card, hand_card_strs):
        """出したカードの『次』を自分が持っていればSafe（ロック継続）
        
        注：シンプル版では使用されないが、将来の改善版との互換性のため残している
        """
        val = card.number.val
        suit = card.suit
        
        # A(1) や K(13) は端なので、出すとそこで列が終わる＝安全
        if val == 1 or val == 13:
            return True
            
        # 7より小さい場合 (A...6), 次に出せるのは val - 1
        if val < 7:
            next_target_val = val - 1
        elif val > 7:
            next_target_val = val + 1
        else:
            return False  # 7は初期配置なのでここには来ない
        
        target_number = None
        for n in Number:
            if n.val == next_target_val:
                target_number = n
                break
        
        if target_number:
            target_card_str = str(suit) + str(target_number)
            return target_card_str in hand_card_strs
            
        return False

    def _get_unknown_cards(self, state):
        unknown_pool = []
        for p_idx in range(state.players_num):
            if p_idx != self.my_player_num:
                unknown_pool.extend(state.players_cards[p_idx])
        return unknown_pool

    def _create_determinized_state(self, original_state, unknown_cards):
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
        """Phase3: ロールアウトポリシーでのプレイアウト（AI同士を簡易に模擬）。"""
        # プレイアウト用に各プレイヤーのAIを用意
        ais = [ImprovedHybridAI(p, simulation_count=0) for p in range(state.players_num)]
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


# インスタンス作成
ai_instance = ImprovedHybridAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)


def random_action(state):
    """ランダムAI"""
    my_actions = state.my_actions()
    if my_actions:
        return my_actions[random.randint(0, len(my_actions)-1)]
    else:
        return None

def my_AI(state):
    return ai_instance.get_action(state)

# --- メイン実行ループ ---

if __name__ == "__main__":
    print(f"MY_PLAYER_NUM: {MY_PLAYER_NUM}")
    print("AI Mode: Simplified PIMC (Baseline)")
    print(f"SIMULATION_COUNT: {SIMULATION_COUNT}")
    print(f"Flags:")
    print(f"  - PASS Removal: {ENABLE_PASS_REMOVAL}")
    print(f"  - Weighted Determinization: {ENABLE_WEIGHTED_DETERMINIZATION}")
    print(f"  - Adaptive Rollout: {ENABLE_ADAPTIVE_ROLLOUT}")
    print(f"  - Tunnel Lock: {ENABLE_TUNNEL_LOCK}")
    print(f"  - Burst Force: {ENABLE_BURST_FORCE}")
    
    state = State()
    turn = 0
    print("----------- ゲーム開始 -----------")

    while True:
        turn += 1
        current_player = state.turn_player
        
        # 終了判定
        if state.is_done():
            print(f"------- ゲーム終了　ターン {turn} -------")
            # 手札が0のプレイヤーが勝者
            winner = -1
            for i, hand in enumerate(state.players_cards):
                if len(hand) == 0 and i not in state.out_player:
                    winner = i
                    break
            # もし全員バーストなら残り1人が勝者
            if winner == -1:
                remaining = [i for i in range(state.players_num) if i not in state.out_player]
                if remaining:
                    winner = remaining[0]
            
            print(f"* 勝者 プレイヤー {winner} 番")
            break

        print(f"------------ ターン {turn} (Player {current_player}) ------------")
        
        pass_flag = 0
        
        # 行動の取得
        if current_player == MY_PLAYER_NUM:
            action, pass_flag = my_AI(state)
        else:
            action = random_action(state)
        
        # 出したカードの表示
        if state.my_actions() == [] or pass_flag == 1:
            print("パス")
            if state.pass_count[current_player] >= 3:
                print(f"\n* プレイヤー {current_player} 番 バースト")
        else:
            print(action)
        
        # 次の状態の取得
        if pass_flag == 1:
            state = state.next(action, pass_flag)
        else:
            state = state.next(action)
