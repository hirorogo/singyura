import random
import copy
import time
from enum import Enum
from random import shuffle
import numpy as np

# --- 定数・設定 ---
EP_GAME_COUNT = 1000  # 評価用の対戦回数
MY_PLAYER_NUM = 0     # 自分のプレイヤー番号

# シミュレーション用設定
# 強さ優先: 探索回数を増やす（遅くなる）
SIMULATION_COUNT = 300  # 1手につき何回シミュレーションするか（最適化済み）
SIMULATION_DEPTH = 200  # どこまで先読みするか

# Phase 2改善フラグ
ENABLE_TUNNEL_LOCK = True  # トンネルロック戦略
ENABLE_BURST_FORCE = True  # バースト誘導戦略

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
        # if not (isinstance(suit, Suit) and isinstance(number, Number)):
        #     raise ValueError
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

    目的: design_strongest.md の Phase1 を満たす。
    - 自分の手札/場に出た札は確定
    - あるプレイヤーが「パス」したとき、その時点で出せた候補札は所持不可能とする

    実装方針(軽量):
    - possible[p][card] = 0/1 の制約集合 (1=持ちうる, 0=持ちえない)
    - 厳密な確率分布までは持たず、決定化で制約を満たす割当を生成する
    """

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num

        # 全カード集合
        self.all_cards = [Card(s, n) for s in Suit for n in Number]

        # possible[p][card] = bool
        self.possible = [set(self.all_cards) for _ in range(self.players_num)]

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

        - actionを出したなら、そのカードは全員が持たない
        - passしたなら、その時点の legal_actions のうち player が出せたはずのカードは所持できない
        """
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
        """ended_state の history を先頭から正しく再生し、各手番時点の盤面で legal_actions を評価できる State を返す。

        注意:
        - determinization で作られた state でも、players_cards / field_cards / pass_count / out_player / turn_player が整合していれば再生できる
        - 初期手札(7抜き)と開始手番は ended_state をそのまま使い、history を適用する
        """
        s = State(
            players_num=ended_state.players_num,
            field_cards=ended_state.field_cards.copy() * 0,
            players_cards=[Hand(list(h)) for h in ended_state.players_cards],
            turn_player=ended_state.turn_player,
            pass_count=[0] * ended_state.players_num,
            out_player=[],
            history=[],
        )

        # まず初期状態として「初期7オープン」を再現する必要がある。
        # ended_state.players_cards は現時点の手札なので、ここでは ended_state.history の先頭にある初期7(記録済み想定)をそのまま適用する。
        # そのため開始盤面は空から作り、history を順に適用する。
        s.players_cards = [Hand([]) for _ in range(ended_state.players_num)]
        # ここは replay 用の盤面だけ再現できればよいので、各プレイヤーの手札は追跡しない(推論用legal_actionsが目的)
        # よって State.next を使わず、field/pass/out/turn のみを更新する。

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
            # その手番の直前が s の状態。
            # 行動適用: pf==1 ならパス、pf==0ならカードを場に置く
            if pf == 1 or a is None:
                s.pass_count[p] += 1
                if s.pass_count[p] > 3:
                    if p not in s.out_player:
                        s.out_player.append(p)
            else:
                # カードを場へ
                try:
                    s.put_card(a)
                except Exception:
                    pass

            # 勝者が出た/残り1人ならそこで止めてもよいが、推論器は最後まで見てOK
            # 次の手番へ
            # out_player を避けて回す
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
        """場で出せるカードのリストを返す (トンネルルール対応)。

        トンネルルール:
        - そのスートでA(1)が出たら、以後はK側(8→…→K)しか伸ばせない
        - そのスートでK(13)が出たら、以後はA側(A→…→6)しか伸ばせない
        """
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
                    except:
                         pass # 既に出ているなどのエラーは無視
                hand.clear() # 手札消滅
                self.out_player.append(p_idx)
                # print(f"Player {p_idx} BURST!")
        else:
            # カードを出す
            if action:
                try:
                    self.players_cards[p_idx].choice(action) # 手札から削除
                    self.put_card(action) # 場に出す
                except ValueError:
                    pass
                    # print(f"Error: Player {p_idx} tried to play {action} but didn't have it.")

        # 勝利判定チェック（手札が0になったら）
        if len(self.players_cards[p_idx]) == 0 and p_idx not in self.out_player:
             # ここではターンを渡さずに終了状態にする（is_doneで判定させるため）
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
        # ここに来るのは全員アウトの場合のみ


# --- 最強AI実装 (Hybrid: Rule-Based + PIMC + Inference) ---

class OpponentModel:
    """strategy.md の相手タイプ推定(簡易)。"""

    def __init__(self, players_num):
        self.players_num = players_num
        self.flags = {p: {"aggressive": 0, "blocker": 0} for p in range(players_num)}

    def observe(self, state, player, action, pass_flag):
        if pass_flag == 1:
            # 出せるのにパスしていたらblockerっぽい、を考えたいが
            # 本コードでは pass は「出せない」場合が多いので弱くカウント
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


class HybridStrongestAI:
    def __init__(self, my_player_num, simulation_count=50):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count

        self._opponent_model = None
        # シミュレーション内で再帰的にPIMCを呼ばないためのガード
        self._in_simulation = False

    def get_action(self, state):
        # シミュレーション中は軽量なロールアウトポリシーで打つ（AI同士前提でも無限再帰を防ぐ）
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
            # Return a default action when no actions are available
            return None, 1

        # PASSは基本的に不利なので候補から除外（シミュレーションの分散を避ける）
        # 出せるカードがある場合は必ず出す方が有利
        candidates = list(my_actions)
        # NOTE: 戦略的PASSは将来の改善で検討可能だが、現在は効果が低いため除外

        if len(candidates) == 1:
            if candidates[0] is None:
                return None, 1
            return candidates[0], 0

        tracker = self._build_tracker_from_history(state)
        
        # Phase 2改善: 戦略的評価を適用
        strategic_bonus = self._evaluate_strategic_actions(state, tracker, my_actions)

        action_scores = {action: 0 for action in candidates}

        for _ in range(self.simulation_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            for first_action in candidates:
                sim_state = determinized_state.clone()

                if first_action is None:
                    sim_state.next(None, 1)
                else:
                    sim_state.next(first_action, 0)

                winner = self._playout(sim_state)

                if winner == self.my_player_num:
                    action_scores[first_action] += 1
                elif winner != -1:
                    action_scores[first_action] -= 1
        
        # Phase 2改善: 戦略ボーナスを加算
        for action in candidates:
            if action in strategic_bonus:
                action_scores[action] += strategic_bonus[action]

        best_action = max(action_scores, key=action_scores.get)

        if best_action is None:
            return None, 1
        return best_action, 0

    def _rollout_policy_action(self, state):
        """プレイアウト用の軽量ポリシー（再帰禁止）。
        
        参考用コードの戦略を取り入れた改善版。
        """
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
            # 次のカードを特定
            if val < 7:
                next_val = val - 1
            elif val > 7:
                next_val = val + 1
            else:
                continue  # 7は初期配置で自動的に出される
            
            # 次のカードを自分が持っているかチェック
            if next_val >= 1 and next_val <= 13:
                next_card = Card(action.suit, self._index_to_number(next_val - 1))
                if next_card and next_card in my_hand:
                    safe_moves.append(action)
        
        if safe_moves:
            return random.choice(safe_moves), 0
        
        # 3. 自分が多く持っているスートを優先
        suit_counts = {}
        for c in my_hand:
            suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
        
        # スートのカード数が最も多いアクションを優先
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
        """Phase 2改善: 戦略的評価
        
        トンネルロック、バースト誘導、参考用コードのヒューリスティック戦略を組み合わせる
        """
        bonus = {}
        my_hand = state.players_cards[self.my_player_num]
        
        # トンネルロック戦略
        if ENABLE_TUNNEL_LOCK:
            tunnel_bonus = self._evaluate_tunnel_lock(state, my_hand, my_actions)
            for action, score in tunnel_bonus.items():
                bonus[action] = bonus.get(action, 0) + score
        
        # バースト誘導戦略
        if ENABLE_BURST_FORCE:
            burst_bonus = self._evaluate_burst_force(state, tracker, my_actions)
            for action, score in burst_bonus.items():
                bonus[action] = bonus.get(action, 0) + score
        
        # 参考用コードからのヒューリスティック戦略を適用
        heuristic_bonus = self._evaluate_heuristic_strategy(state, my_hand, my_actions)
        for action, score in heuristic_bonus.items():
            bonus[action] = bonus.get(action, 0) + score
        
        return bonus
    
    def _evaluate_heuristic_strategy(self, state, my_hand, my_actions):
        """参考用コード（二次試験.ipynb）のヒューリスティック戦略
        
        トンネルルール対応版:
        - 次のカードを自分が持っている場合にボーナス
        - 同じスートのカード数によるボーナス
        - 自分の新たなアクションを開くカードへのボーナス
        - 隣接カードが場にあるかチェック
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        # 各スートのカード枚数をカウント
        suit_counts = {suit: 0 for suit in Suit}
        for card in my_hand:
            suit_counts[card.suit] += 1
        
        for card in my_actions:
            suit = card.suit
            suit_index = suit_to_index[suit]
            number_index = card.number.val - 1  # 0-based index
            score = 0
            
            # トンネルルール対応：A/Kの扱い
            # 両方のトンネルが開いていない場合、A/Kを出すと相手に有利になる可能性がある
            is_ace_out = state.field_cards[suit_index][0] == 1
            is_king_out = state.field_cards[suit_index][12] == 1
            
            if number_index == 0:  # A
                if is_king_out:
                    # Kが出ている場合、Aを出すとトンネルが閉じる → やや有利
                    score += 5
                else:
                    # Kが出ていない場合、Aを温存した方が良い
                    score -= 5
            elif number_index == 12:  # K
                if is_ace_out:
                    # Aが出ている場合、Kを出すとトンネルが閉じる → やや有利
                    score += 5
                else:
                    # Aが出ていない場合、Kを温存した方が良い
                    score -= 5
            
            # 隣接カードのチェック
            next_indices = []
            if number_index < 6:  # 7より小さい側
                next_indices.append(number_index - 1)
            elif number_index > 6:  # 7より大きい側
                next_indices.append(number_index + 1)
            
            for next_number_index in next_indices:
                if 0 <= next_number_index <= 12:
                    if state.field_cards[suit_index][next_number_index] == 1:
                        # 次のカードがすでに場にある → 良い
                        score += 5
                    else:
                        # 次のカードが場にない → 相手に道を開く可能性
                        score -= 5
                        
                        # ただし、次のカードを自分が持っていれば軽減（Safe判定）
                        next_number = self._index_to_number(next_number_index)
                        if next_number:
                            next_card = Card(suit, next_number)
                            if next_card in my_hand:
                                score += 12  # 次のカードを自分が持っている → 制御可能
            
            # 同じスートのカード数が多いほどボーナス
            score += suit_counts[suit] * 2
            
            # 自分の新たなアクションを開くカードへのボーナス
            potential_new_moves = 0
            for c in my_hand:
                if c.suit == suit:
                    c_index = c.number.val - 1
                    # このカードを出すことで次に出せるようになるカードがあるか
                    if (number_index < 6 and c_index == number_index - 1) or \
                       (number_index > 6 and c_index == number_index + 1):
                        potential_new_moves += 1
            score += potential_new_moves * 10
            
            bonus[card] = score
        
        return bonus
    
    def _index_to_number(self, index):
        """0-based indexをNumber Enumに変換"""
        number_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                       Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                       Number.NINE, Number.TEN, Number.JACK, Number.QUEEN, Number.KING]
        if 0 <= index <= 12:
            return number_list[index]
        return None
    
    def _evaluate_tunnel_lock(self, state, my_hand, my_actions):
        """トンネルロック戦略（改善版）
        
        トンネルルール:
        - Aが出た場合、K側（8→...→K）のみ伸ばせる
        - Kが出た場合、A側（A→...→6）のみ伸ばせる
        
        戦略:
        - 相手がトンネルを開けている場合（A or K が出ている）、
          逆側の端カードを温存して封鎖することで相手を詰まらせる
        - ただし、自分がその方向に多くのカードを持っている場合は出した方が良い
        """
        bonus = {}
        
        for suit_idx, suit in enumerate(Suit):
            is_ace_out = state.field_cards[suit_idx][0] == 1
            is_king_out = state.field_cards[suit_idx][12] == 1
            
            # 自分がこのスートで持っているカードの方向性を分析
            my_high_cards = 0  # 8-K側のカード
            my_low_cards = 0   # A-6側のカード
            for card in my_hand:
                if card.suit == suit:
                    if card.number.val >= 8:
                        my_high_cards += 1
                    elif card.number.val <= 6:
                        my_low_cards += 1
            
            # Aが出ている場合（K側のみ伸ばせる）
            if is_ace_out and not is_king_out:
                k_card = Card(suit, Number.KING)
                if k_card in my_hand and k_card in my_actions:
                    # 自分がK側に多くのカードを持っている場合は出した方が良い
                    if my_high_cards >= 3:
                        bonus[k_card] = 8  # Kを出してトンネルを閉じる
                    else:
                        # Kを温存して相手を詰まらせる
                        bonus[k_card] = -10
            
            # Kが出ている場合（A側のみ伸ばせる）
            if is_king_out and not is_ace_out:
                a_card = Card(suit, Number.ACE)
                if a_card in my_hand and a_card in my_actions:
                    # 自分がA側に多くのカードを持っている場合は出した方が良い
                    if my_low_cards >= 3:
                        bonus[a_card] = 8  # Aを出してトンネルを閉じる
                    else:
                        # Aを温存して相手を詰まらせる
                        bonus[a_card] = -10
        
        return bonus
    
    def _evaluate_burst_force(self, state, tracker, my_actions):
        """バースト誘導戦略
        
        パス回数が多い相手が持っていないスートを急速に進める
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
        """相手の弱いスート（持っていないカードが多そうなスート）を推論"""
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
        """推論制約(possible)を満たすように相手手札を生成する。

        失敗しうる(制約が強すぎる)ので、数回リトライしてダメならフォールバック。
        """
        base = original_state.clone()

        # 相手に配るべきカードプール: 自分以外の手札を全部集める(元実装互換)
        # ただし順序はどうでもよい
        pool = []
        for p in range(base.players_num):
            if p != self.my_player_num:
                pool.extend(base.players_cards[p])

        # いったん空にして再配分
        for p in range(base.players_num):
            if p != self.my_player_num:
                base.players_cards[p] = Hand([])

        # 手札枚数(バーストは0)
        need = {p: len(original_state.players_cards[p]) for p in range(base.players_num) if p != self.my_player_num}

        # リトライ
        for _ in range(30):
            random.shuffle(pool)

            # 作業用
            remain = list(pool)
            hands = {p: [] for p in need.keys()}

            ok = True
            # まず各プレイヤーに「可能なカード」を優先して割り当て
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
                # remove chosen from remain
                chosen_set = set(chosen)
                remain = [c for c in remain if c not in chosen_set]

            if not ok:
                continue

            # もし残りがある(理論上ないはず)なら適当に分配
            # (安全のため)
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
        """出したカードの『次』を自分が持っていればSafe（ロック継続）"""
        val = card.number.val
        suit = card.suit
        
        # A(1) や K(13) は端なので、出すとそこで列が終わる＝安全（誰もそれ以上出せない）
        if val == 1 or val == 13:
            return True
            
        # 7より小さい場合 (A...6), 次に出せるのは val - 1
        next_target_val = -1
        if val < 7:
            next_target_val = val - 1
        # 7より大きい場合 (8...K), 次に出せるのは val + 1
            
        # 次のカードを持っているかチェック
        # Cardオブジェクトの生成コストを避けるため文字列比較などを利用（最適化）
        # ここでは簡易に全探索
        
        # 次のカードを表す文字列表現作成
        # Number Enumから探すのは少し手間なので、単純に検索
        # hand_card_strs は呼び出し元で作成済み
        
        # next_target_val に対応する Number を探す（効率悪いが枚数少ないので許容）
        # Enum定義: ACE=(1, 'A')...
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
        # プレイアウト用に各プレイヤーのAIを用意（同等ロジックのロールアウトを使う）
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


# インスタンス作成
ai_instance = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)


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
    print("AI Mode: PIMC (Perfect Information Monte Carlo)")
    
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
