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
# コンテスト用: 推論時間制限なしのため増加
SIMULATION_COUNT = 300  # 1手につき何回シミュレーションするか (精度と速度のバランス)
SIMULATION_DEPTH = 300  # どこまで先読みするか
ENDGAME_THRESHOLD = 10  # この枚数以下になったら精密な探索に切り替え
ENDGAME_SIMULATION_COUNT = 1000  # 終盤の精密探索回数

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
    """不完全情報(相手手札)の推論器（確率版）。

    目的: design_strongest.md の Phase1 を満たす。
    - 自分の手札/場に出た札は確定
    - あるプレイヤーが「パス」したとき、その時点で出せた候補札は所持不可能とする
    - 確率分布を持ち、より精密な推論を行う

    実装方針:
    - possible[p][card] = probability (0.0~1.0の確率分布)
    - パス情報やプレイ情報で確率を更新
    - 決定化で確率に応じた重み付きサンプリングを行う
    """

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num

        # 全カード集合
        self.all_cards = [Card(s, n) for s in Suit for n in Number]

        # possible[p][card] = probability (0.0 ~ 1.0)
        # 辞書形式で確率を保持
        self.possible = [{card: 0.0 for card in self.all_cards} for _ in range(self.players_num)]

        # 初期化: 自分以外のカードは均等確率で分配
        unknown_cards = list(self.all_cards)
        
        # 場に出たカードは除外
        for s_idx, s in enumerate(Suit):
            for n_idx, n in enumerate(Number):
                if state.field_cards[s_idx][n_idx] == 1:
                    card = Card(s, n)
                    unknown_cards.remove(card)
        
        # 自分の手札は除外
        my_hand = set(state.players_cards[my_player_num])
        for card in my_hand:
            if card in unknown_cards:
                unknown_cards.remove(card)
        
        # 自分の手札は確率1.0
        for card in my_hand:
            self.possible[my_player_num][card] = 1.0
        
        # 未知のカードは他プレイヤーで均等分配（初期確率）
        other_players = [p for p in range(self.players_num) if p != my_player_num]
        if other_players and unknown_cards:
            init_prob = 1.0 / len(other_players)
            for card in unknown_cards:
                for p in other_players:
                    self.possible[p][card] = init_prob
        
        # すでにアウト(burst)しているプレイヤーは手札0として扱い、推論対象外
        self.out_player = set(state.out_player)
        for p in self.out_player:
            for card in self.all_cards:
                self.possible[p][card] = 0.0

    def clone(self):
        c = object.__new__(CardTracker)
        c.players_num = self.players_num
        c.my_player_num = self.my_player_num
        c.all_cards = self.all_cards
        c.possible = [{card: prob for card, prob in p.items()} for p in self.possible]
        c.out_player = set(self.out_player)
        return c

    def normalize(self, player):
        """確率分布を正規化"""
        total = sum(self.possible[player].values())
        if total > 0:
            for card in self.possible[player]:
                self.possible[player][card] /= total

    def observe_action(self, state, player, action, is_pass):
        """行動観測で確率を更新（ベイズ的更新）。

        - actionを出したなら、そのカードは全員が持たない（確率0）
        - passしたなら、その時点の legal_actions のカードを持つ確率を0にする
        """
        if player in self.out_player:
            return

        if is_pass:
            legal = state.legal_actions()
            # パスしたということは、合法手のどのカードも持っていない
            for c in legal:
                self.possible[player][c] = 0.0
            # 正規化して他のカードの確率を再分配
            self.normalize(player)
            return

        if action is not None and not isinstance(action, list):
            # そのカードを出したので、全プレイヤーが持たない
            for p in range(self.players_num):
                self.possible[p][action] = 0.0
            # 各プレイヤーで正規化
            for p in range(self.players_num):
                if p not in self.out_player:
                    self.normalize(p)

    def mark_out(self, player):
        self.out_player.add(player)
        for card in self.all_cards:
            self.possible[player][card] = 0.0


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
        - 7を基準に、A側(1-6)とK側(8-13)がある
        - 通常: 7から両側に伸ばせる
        - Aが出たら: そのスートはK側(8→K)のみ伸ばせる（A側は封鎖）
        - Kが出たら: そのスートはA側(A→6)のみ伸ばせる（K側は封鎖）
        - 両方出たら: 完全に封鎖（もう伸ばせない）
        """
        actions = []
        for suit, n in zip(Suit, range(4)):
            # 7が出ているか確認（index 6 = 7）
            is_seven_out = self.field_cards[n][6] == 1
            
            if not is_seven_out:
                # 7がまだ出ていない場合、このスートでは何も出せない
                continue
            
            # Aが出ている (index 0) / Kが出ている (index 12)
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            # 両方出ていたら、このスートは完全に封鎖されている
            if is_ace_out and is_king_out:
                continue

            # --- 7より小さい側 (6→A) ---
            # Kが出ていない場合のみ、この側を伸ばせる
            if not is_king_out:
                small_side = self.field_cards[n][0:6]  # A..6 (indices 0-5)
                # 7(index 6)の隣は6(index 5)
                for i in range(5, -1, -1):
                    if small_side[i] == 0:
                        # まだ出ていないカードが見つかったので、これが出せる
                        actions.append(Card(suit, self.num_to_Enum(i + 1)))
                        break

            # --- 7より大きい側 (8→K) ---
            # Aが出ていない場合のみ、この側を伸ばせる
            if not is_ace_out:
                # 7(index 6)の隣は8(index 7)
                for i in range(7, 13):
                    if self.field_cards[n][i] == 0:
                        # まだ出ていないカードが見つかったので、これが出せる
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
        for (p, a, pf) in state.history[-10:]:  # 履歴を10手まで見るように拡張
            self._opponent_model.observe(state, p, a, pf)

        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # 候補手の戦略的フィルタリング（コンテストモード: PASSは含めない）
        candidates = list(my_actions)
        
        # 合法手がある場合はPASSを候補に入れない（探索分散を防ぐ）
        # パス回数が3未満でも、合法手があればPASSしない戦略
        
        if len(candidates) == 1:
            return candidates[0], 0

        # 終盤判定: 手札が少ない場合は精密な探索
        total_cards = sum(len(hand) for hand in state.players_cards)
        is_endgame = total_cards <= ENDGAME_THRESHOLD
        
        # 終盤用のシミュレーション回数
        sim_count = ENDGAME_SIMULATION_COUNT if is_endgame else self.simulation_count

        tracker = self._build_tracker_from_history(state)

        # 戦略的評価を追加
        action_scores = {action: 0 for action in candidates}
        action_strategic_bonus = {action: 0 for action in candidates}
        
        # トンネルロック戦略の評価
        tunnel_lock_cards = self._evaluate_tunnel_lock(state, tracker)
        for card in tunnel_lock_cards:
            if card in action_strategic_bonus:
                action_strategic_bonus[card] += 100  # ロックカードにボーナス

        # バースト誘導戦略の評価
        burst_force_cards = self._evaluate_burst_force(state, tracker)
        for card in burst_force_cards:
            if card in action_strategic_bonus:
                action_strategic_bonus[card] += 50  # バースト誘導カードにボーナス

        for _ in range(sim_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            for first_action in candidates:
                sim_state = determinized_state.clone()

                sim_state.next(first_action, 0)

                winner = self._playout(sim_state)

                if winner == self.my_player_num:
                    action_scores[first_action] += 1
                elif winner != -1:
                    action_scores[first_action] -= 1

        # 戦略ボーナスを加算（勝率とのハイブリッド）
        combined_scores = {
            action: action_scores[action] + action_strategic_bonus[action] 
            for action in candidates
        }

        best_action = max(combined_scores, key=combined_scores.get)

        return best_action, 0

    def _evaluate_tunnel_lock(self, state, tracker):
        """トンネルロック戦略: 相手がトンネルを開けた時、逆側を封鎖する価値の高いカードを返す"""
        lock_cards = []
        
        for suit_idx, suit in enumerate(Suit):
            is_ace_out = state.field_cards[suit_idx][0] == 1
            is_king_out = state.field_cards[suit_idx][12] == 1
            
            # Aが出ている場合、K, Q, J を持っているなら出さない（保持する価値が高い）
            if is_ace_out:
                for num, val in [(Number.KING, 13), (Number.QUEEN, 12), (Number.JACK, 11)]:
                    card = Card(suit, num)
                    if card in state.players_cards[self.my_player_num]:
                        # 出さずに保持すべきカードなので、候補から除外したい
                        # しかし、ここでは「価値が高い」カードをマークする
                        # 実際には逆: これらを避けたいので、ロックリストには入れない
                        pass
            
            # Kが出ている場合、A, 2, 3 を持っているなら出さない
            if is_king_out:
                for num, val in [(Number.ACE, 1), (Number.TWO, 2), (Number.THREE, 3)]:
                    card = Card(suit, num)
                    if card in state.players_cards[self.my_player_num]:
                        pass
        
        # 別のアプローチ: 相手の手札を推測し、相手がトンネルで困るカードを出す
        # 端のカード(A/K)は優先的に出す（トンネルを開く）
        for suit in Suit:
            for num in [Number.ACE, Number.KING]:
                card = Card(suit, num)
                if card in state.players_cards[self.my_player_num]:
                    lock_cards.append(card)
        
        return lock_cards

    def _evaluate_burst_force(self, state, tracker):
        """バースト誘導戦略: パスが多いプレイヤーが持っていないスートを急速に進める"""
        force_cards = []
        
        # 各プレイヤーのパス回数をチェック
        for p in range(state.players_num):
            if p == self.my_player_num or p in state.out_player:
                continue
            
            if state.pass_count[p] >= 2:  # パスが2回以上
                # このプレイヤーが持っていない可能性が高いスートを推定
                weak_suits = []
                for suit_idx, suit in enumerate(Suit):
                    # そのスートのカードを持つ確率の合計が低い場合
                    suit_prob_sum = sum(
                        tracker.possible[p][Card(suit, num)]
                        for num in Number
                    )
                    if suit_prob_sum < 0.3:  # 閾値
                        weak_suits.append(suit)
                
                # 弱いスートのカードを優先して出す
                for suit in weak_suits:
                    for card in state.my_actions():
                        if card.suit == suit:
                            force_cards.append(card)
        
        return force_cards

    def _rollout_policy_action(self, state):
        """プレイアウト用の強化ポリシー（再帰禁止）。"""
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # ロールアウトでは基本PASSしない（探索の分散を避ける）
        
        # 戦略1: 終盤（手札が少ない）なら、連続カードを優先
        hand = state.players_cards[state.turn_player]
        if len(hand) <= 5:
            # 連続するカードを探す
            for card in my_actions:
                suit = card.suit
                val = card.number.val
                # 次のカードを自分が持っているか
                if val < 7:
                    next_val = val - 1
                else:
                    next_val = val + 1
                
                if next_val >= 1 and next_val <= 13:
                    for c in hand:
                        if c.suit == suit and c.number.val == next_val:
                            # 連続している！優先
                            return card, 0
        
        # 戦略2: 端のカード(A/K)を優先（トンネルを作る）
        ends = [a for a in my_actions if a.number in (Number.ACE, Number.KING)]
        if ends:
            return random.choice(ends), 0
        
        # 戦略3: 次のカードを持っている「安全な」カードを優先
        hand_strs = [str(c) for c in state.players_cards[state.turn_player]]
        safe = [a for a in my_actions if self._is_safe_move(a, hand_strs)]
        if safe:
            return random.choice(safe), 0
        
        # 戦略4: 中央のカード(6,8)を優先（選択肢を広げる）
        center = [a for a in my_actions if a.number in (Number.SIX, Number.EIGHT)]
        if center:
            return random.choice(center), 0

        # それ以外はランダム
        return random.choice(my_actions), 0

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
        """推論制約(possible)を満たすように相手手札を生成（確率的サンプリング版）。

        確率分布に基づいて重み付きサンプリングを行う。
        """
        base = original_state.clone()

        # 相手に配るべきカードプール: 自分以外の手札を全部集める
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

        # 確率的割り当て（リトライ付き）
        for attempt in range(50):
            # 作業用
            remain = list(pool)
            hands = {p: [] for p in need.keys()}

            ok = True
            # 各プレイヤーに確率に基づいてカードを割り当て
            for p in need.keys():
                k = need[p]
                if k == 0:
                    continue

                # そのプレイヤーが持ちうるカードとその確率
                candidate_probs = [(c, tracker.possible[p][c]) for c in remain if tracker.possible[p][c] > 0]
                
                if not candidate_probs:
                    # 確率が0のカードしかない場合、フォールバック
                    ok = False
                    break
                
                if len(candidate_probs) < k:
                    # 候補カードが足りない場合、フォールバック
                    ok = False
                    break

                # 確率に基づく重み付きサンプリング
                cards, probs = zip(*candidate_probs)
                total_prob = sum(probs)
                if total_prob == 0:
                    ok = False
                    break
                
                normalized_probs = [p / total_prob for p in probs]
                
                # 重複なしでk枚選択
                try:
                    chosen = []
                    temp_cards = list(cards)
                    temp_probs = list(normalized_probs)
                    
                    for _ in range(k):
                        if not temp_cards:
                            break
                        # 確率に基づいて1枚選択
                        selected_card = random.choices(temp_cards, weights=temp_probs, k=1)[0]
                        chosen.append(selected_card)
                        # 選択したカードを除外
                        idx = temp_cards.index(selected_card)
                        temp_cards.pop(idx)
                        temp_probs.pop(idx)
                        # 確率を再正規化
                        if temp_probs:
                            total = sum(temp_probs)
                            temp_probs = [p / total for p in temp_probs]
                    
                    if len(chosen) < k:
                        ok = False
                        break
                    
                    hands[p].extend(chosen)
                    # remove chosen from remain
                    for c in chosen:
                        remain.remove(c)
                except Exception:
                    ok = False
                    break

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
        else:
            next_target_val = val + 1
            
        # 次のカードを持っているかチェック
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
    if my_actions != []:
        return my_actions[random.randint(0, len(my_actions)-1)]
    else:
        my_actions = []
        return my_actions

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
