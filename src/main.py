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
# 大会モード: 処理時間を気にせず最強を目指す（実証済み最適値＋参考コード統合による強化）
SIMULATION_COUNT = 1000  # 1手につき何回シミュレーションするか（超強化版：700→1000, 最高精度）
SIMULATION_DEPTH = 350  # どこまで先読みするか（強化版：300→350）

# Phase 2改善フラグ
ENABLE_TUNNEL_LOCK = True  # トンネルロック戦略
ENABLE_BURST_FORCE = True  # バースト誘導戦略

# 確率的推論の設定
BELIEF_STATE_DECAY_FACTOR = 0.05  # パス観測時の確率減衰率（実証済み）
DETERMINIZATION_ATTEMPTS = 120  # 確定化のリトライ回数（強化版：100→120）

# 戦略重み付け係数（強化版：戦略ボーナスの影響を増強、参考コード統合により最適化）
STRATEGY_WEIGHT_MULTIPLIER = 1.5  # 戦略ボーナスの影響度（超強化：1.2→1.5）
TUNNEL_LOCK_WEIGHT = 3.5  # トンネルロック戦略の重み（超強化：3.0→3.5）
BURST_FORCE_WEIGHT = 3.5  # バースト誘導戦略の重み（超強化：3.0→3.5）

# 新規追加：適応的戦略パラメータ
AGGRESSIVE_MODE_THRESHOLD = 0.6  # 積極的モードに切り替える手札割合（残り40%以下で攻撃的に）
DEFENSIVE_MODE_THRESHOLD = 0.8  # 防御的モードに切り替える手札割合（残り80%以上で慎重に）
AGGRESSIVENESS_MULTIPLIER = 0.3  # 攻撃度による重み調整の係数
URGENCY_MULTIPLIER = 0.5  # 緊急度による終盤戦略の補正係数

# ヒューリスティック戦略の詳細パラメータ（参考コード統合による最適化）
ACE_KING_BASE_BONUS = 10  # A/K基本ボーナス（超強化：8→10）
TUNNEL_COMPLETE_BONUS = 10  # トンネル完成ボーナス
ADJACENT_CARD_BONUS = 6  # 隣接カードが場にある場合のボーナス
ADJACENT_CARD_PENALTY = 6  # 相手に道を開く可能性のペナルティ
SAFE_MOVE_BONUS = 20  # 次のカードを自分が持つ場合のボーナス（完全制御可能、強化）
SUIT_CONCENTRATION_MULTIPLIER = 2.5  # スート集中戦略の倍率（参考コードの*0.5から5倍に）
HAND_REDUCTION_BONUS = 0.15  # 手札削減インセンティブ
CHAIN_POTENTIAL_MULTIPLIER = 15  # 連鎖可能性の倍率（超強化：12→15）

# ロールアウトポリシーのパラメータ
ROLLOUT_ACE_KING_BONUS = 10  # ロールアウト時のA/Kボーナス（強化：8→10）
ROLLOUT_ADJACENT_BONUS = 6  # ロールアウト時の隣接カードボーナス（強化：4→6）
ROLLOUT_ADJACENT_PENALTY = 6  # ロールアウト時の隣接カードペナルティ（強化：4→6）
ROLLOUT_SAFE_BONUS = 12  # ロールアウト時のSafe判定ボーナス（強化：8→12）
ROLLOUT_SUIT_MULTIPLIER = 2.0  # ロールアウト時のスート集中倍率（強化：1.5→2.0）
ROLLOUT_HAND_REDUCTION = 0.3  # ロールアウト時の手札削減インセンティブ（強化：0.2→0.3）
ROLLOUT_CHAIN_MULTIPLIER = 8  # ロールアウト時の連鎖可能性倍率（強化：6→8）

# 参考コード由来の高度なヒューリスティックパラメータ（戦略を尖らせるための重み）
ADVANCED_HEURISTIC_PARAMS = {
    'W_CIRCULAR_DIST': 22,    # 7からの距離（端に近いほど出しにくい）
    'W_MY_PATH': 112,         # 自分の次の手に繋がるボーナス
    'W_OTHERS_RISK': -127,    # 他人に塩を送るリスク（深度1あたりの減点）
    'W_SUIT_DOM': 84,         # スート支配力の重み
    'W_WIN_DASH': 41,         # 勝ち圏内の放出意欲
    'P_THRESHOLD_BASE': 200,  # 基本のパスしきい値（超高値により、PASSをほぼ禁止）
    'P_KILL_ZONE': 300,       # 相手をハメる時のパスしきい値（超高値で極めて慎重な判断）
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
    """パス履歴から相手の手札可能性を推論
    
    参考用実装からの完全コピー版（doc/misc/colab_notebook.md）
    - シンプルなset-basedアプローチ
    - パス観測時にlegal_actionsを完全に除外（より決定的）
    - 確率計算なし（実行速度重視）
    """

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

        トンネルルール（正しい理解）:
        - 初期状態（AもKも出ていない）: 7から6と8を出せる（通常の7並べ）
        - カードがAまで出た場合 → そのスートはKからしか出せない（トンネル発動）
        - Kが出た時 → そのスートはAからしか出せない（トンネル発動）
        - AとKの両方が出ている → 両側から伸ばせる（列完成に向かう）
        """
        actions = []
        for suit, n in zip(Suit, range(4)):
            # Aが出ている (index 0) / Kが出ている (index 12)
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            # --- 7より小さい側 (A-6) ---
            # 条件: Kが出ている OR (AもKも出ていない = 初期状態)
            if is_king_out or (not is_ace_out and not is_king_out):
                small_side = self.field_cards[n][0:6]  # A..6
                if small_side[5] == 0:
                    actions.append(Card(suit, Number.SIX))
                else:
                    for i in range(5, -1, -1):
                        if small_side[i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

            # --- 7より大きい側 (8-K) ---
            # 条件: Aが出ている OR (AもKも出ていない = 初期状態)
            if is_ace_out or (not is_ace_out and not is_king_out):
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
    """strategy.md の相手タイプ推定（強化版）。
    
    各プレイヤーの行動パターンを分析し、戦略モードを判定する。
    - Aggressive（トンネル活用型）: A/Kなどの端を積極的に出す
    - Blocker（遅延・ハメ型）: パスを多用、中央付近を止める
    """

    def __init__(self, players_num):
        self.players_num = players_num
        # 各プレイヤーの特徴フラグ
        self.flags = {p: {
            "aggressive": 0,
            "blocker": 0,
            "tunnel_usage": 0,  # トンネルを開けた回数
            "pass_count": 0,     # パス回数
            "end_cards": 0,      # 端カード（A/K）を出した回数
            "middle_cards": 0,   # 中央カード（6/8）を出した回数
        } for p in range(players_num)}
        
        # ゲーム進行度（ターン数）
        self.turn_count = 0

    def observe(self, state, player, action, pass_flag):
        """行動観測で相手タイプを更新"""
        self.turn_count += 1
        
        if pass_flag == 1:
            self.flags[player]["pass_count"] += 1
            self.flags[player]["blocker"] += 1
            return

        if action is None or isinstance(action, list):
            return

        # A/K を出した → aggressive, トンネル活用
        if action.number in (Number.ACE, Number.KING):
            self.flags[player]["aggressive"] += 2
            self.flags[player]["end_cards"] += 1
            
            # トンネルを開ける行動かチェック
            suit_idx = list(Suit).index(action.suit)
            if action.number == Number.ACE:
                # Aを出した → K側のトンネルを開ける
                if state.field_cards[suit_idx][12] == 0:  # Kがまだ出ていない
                    self.flags[player]["tunnel_usage"] += 1
            elif action.number == Number.KING:
                # Kを出した → A側のトンネルを開ける
                if state.field_cards[suit_idx][0] == 0:  # Aがまだ出ていない
                    self.flags[player]["tunnel_usage"] += 1

        # 中央(6/8)を出した → 両方向に展開、やや blocker
        if action.number in (Number.SIX, Number.EIGHT):
            self.flags[player]["middle_cards"] += 1
            self.flags[player]["blocker"] += 0.5

        # J/Qあたりを出した → blocker 傾向
        if action.number in (Number.JACK, Number.QUEEN):
            self.flags[player]["blocker"] += 1

    def mode(self, player):
        """プレイヤーの戦略モードを判定
        
        Returns:
            - "tunnel_lock": トンネル活用型（A/Kを積極的に使う）→ トンネルロックで対抗
            - "burst_force": パス多用型（詰まりやすい）→ バースト誘導で対抗
            - "neutral": 中立型
        """
        flags = self.flags[player]
        a = flags["aggressive"]
        b = flags["blocker"]
        pass_count = flags["pass_count"]
        tunnel_usage = flags["tunnel_usage"]
        
        # パス回数が多い（2回以上）→ バースト誘導が有効
        if pass_count >= 2:
            return "burst_force"
        
        # トンネルを積極的に使っている → トンネルロックで封鎖
        if tunnel_usage >= 2 or a >= b + 3:
            return "tunnel_lock"
        
        # Blocker傾向が強い
        if b >= a + 2:
            return "burst_force"
        
        return "neutral"
    
    def get_threat_level(self, player):
        """プレイヤーの脅威度を計算（0.0～1.0）
        
        高いほど優先的に対策すべき相手
        """
        flags = self.flags[player]
        
        # 基本脅威度
        threat = 0.5
        
        # Aggressive型は脅威度高め
        threat += flags["aggressive"] * 0.05
        
        # トンネル活用は大きな脅威
        threat += flags["tunnel_usage"] * 0.1
        
        # パスが多い相手は脅威度低め（詰まりやすい）
        threat -= flags["pass_count"] * 0.1
        
        return max(0.0, min(1.0, threat))


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
        
        # 新機能：ゲーム状態を評価して適応的に戦略を調整
        game_state_info = self._evaluate_game_state(state)
        
        # Phase 2改善: 戦略的評価を適用
        strategic_bonus = self._evaluate_strategic_actions(state, tracker, my_actions, game_state_info)

        action_scores = {action: 0 for action in candidates}

        # 動的シミュレーション回数: 候補が少ない場合はより深く探索
        actual_sim_count = self.simulation_count
        if len(candidates) <= 2:
            actual_sim_count = int(self.simulation_count * 2.0)  # 2倍に増強
        elif len(candidates) <= 3:
            actual_sim_count = int(self.simulation_count * 1.5)
        elif len(candidates) <= 5:
            actual_sim_count = int(self.simulation_count * 1.2)

        for _ in range(actual_sim_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)

            for first_action in candidates:
                sim_state = determinized_state.clone()

                if first_action is None:
                    sim_state.next(None, 1)
                else:
                    sim_state.next(first_action, 0)

                winner = self._playout(sim_state)

                # より詳細なスコアリング
                if winner == self.my_player_num:
                    action_scores[first_action] += 2  # 勝利は+2点
                elif winner == -1:
                    # 引き分け（全員バースト）は0点
                    pass
                else:
                    action_scores[first_action] -= 1  # 負けは-1点
                    
                    # 手札枚数による追加評価（終了時点での手札が少ないほど良い）
                    my_remaining = len(sim_state.players_cards[self.my_player_num])
                    winner_remaining = len(sim_state.players_cards[winner])
                    
                    # 手札差に応じた細かいスコア調整
                    if my_remaining < winner_remaining:
                        action_scores[first_action] += 0.3  # 惜しい負けは少しプラス
                    elif my_remaining - winner_remaining >= 3:
                        action_scores[first_action] -= 0.3  # 大差の負けは少しマイナス
        
        # Phase 2改善: 戦略ボーナスを加算（重要度を高める）
        for action in candidates:
            if action in strategic_bonus:
                # 戦略ボーナスの影響を調整
                action_scores[action] += strategic_bonus[action] * STRATEGY_WEIGHT_MULTIPLIER

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
            # ただし、best_scoreはシミュレーションスコア+戦略ボーナスなので、
            # 戦略ボーナス部分のみを比較対象とする
            if best_action in strategic_bonus:
                strategic_score_only = strategic_bonus[best_action]
                if strategic_score_only < pass_threshold and my_pass_count < 3:
                    return None, 1

        if best_action is None:
            return None, 1
        return best_action, 0

    def _rollout_policy_action(self, state):
        """プレイアウト用の軽量ポリシー（再帰禁止）。
        
        参考用コード（xq-kessyou-main）の戦略を統合した強化版。
        スコアリングベースの判断で、より精密な選択を行う。
        """
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        my_hand = state.players_cards[state.turn_player]
        
        # スコアリングベースで最適なアクションを選択（参考コードの手法）
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        action_scores = {}
        
        # 各スートのカード枚数をカウント
        suit_counts = {suit: 0 for suit in Suit}
        for card in my_hand:
            suit_counts[card.suit] += 1
        
        for action in my_actions:
            score = 0
            suit_idx = suit_to_index[action.suit]
            num_idx = action.number.val - 1
            
            # 1. A/K優先
            if num_idx == 0 or num_idx == 12:
                score += ROLLOUT_ACE_KING_BONUS
            
            # 2. 隣接カード分析
            next_indices = []
            if num_idx < 6:
                next_indices.append(num_idx - 1)
            elif num_idx > 6:
                next_indices.append(num_idx + 1)
            
            for next_idx in next_indices:
                if 0 <= next_idx <= 12:
                    if state.field_cards[suit_idx][next_idx] == 1:
                        # 次のカードが既に場にある
                        score += ROLLOUT_ADJACENT_BONUS
                    else:
                        # 次のカードが場にない
                        score -= ROLLOUT_ADJACENT_PENALTY
                        # 自分が持っているかチェック
                        next_num = self._index_to_number(next_idx)
                        if next_num:
                            next_card = Card(action.suit, next_num)
                            if next_card in my_hand:
                                score += ROLLOUT_SAFE_BONUS
            
            # 3. スート集中戦略
            score += suit_counts[action.suit] * ROLLOUT_SUIT_MULTIPLIER
            
            # 4. 手札削減インセンティブ
            score += (len(my_hand) - 1) * ROLLOUT_HAND_REDUCTION
            
            # 5. 連鎖可能性
            potential_new_moves = 0
            for c in my_hand:
                if c.suit == action.suit:
                    c_idx = c.number.val - 1
                    if (num_idx < 6 and c_idx == num_idx - 1) or \
                       (num_idx > 6 and c_idx == num_idx + 1):
                        potential_new_moves += 1
            score += potential_new_moves * ROLLOUT_CHAIN_MULTIPLIER
            
            action_scores[action] = score
        
        # 最高スコアのアクションを選択（同点の場合はランダム）
        max_score = max(action_scores.values())
        best_actions = [a for a, s in action_scores.items() if s == max_score]
        
        return random.choice(best_actions), 0
    
    def _evaluate_game_state(self, state):
        """ゲームの現在の状態を評価し、戦略調整のための情報を返す
        
        Returns:
            dict: ゲーム状態情報
                - 'phase': 'early'/'middle'/'late' - ゲームフェーズ
                - 'my_position': 'leading'/'middle'/'behind' - 自分の位置
                - 'urgency': 0.0~1.0 - 緊急度（バースト危機）
                - 'aggressiveness': 0.0~1.0 - 推奨攻撃度
        """
        my_hand_size = len(state.players_cards[self.my_player_num])
        
        # 他プレイヤーの手札サイズを取得
        opponent_hand_sizes = []
        for p in range(state.players_num):
            if p != self.my_player_num and p not in state.out_player:
                opponent_hand_sizes.append(len(state.players_cards[p]))
        
        # ゲームフェーズの判定（残り手札の割合で判断）
        # 初期手札数の推定（52枚を均等に配布）
        initial_hand_size = 52 // state.players_num
        hand_ratio = my_hand_size / max(1, initial_hand_size)
        
        if hand_ratio > DEFENSIVE_MODE_THRESHOLD:
            phase = 'early'
        elif hand_ratio > AGGRESSIVE_MODE_THRESHOLD:
            phase = 'middle'
        else:
            phase = 'late'
        
        # 自分の相対位置（手札サイズの比較）
        if not opponent_hand_sizes:
            my_position = 'leading'
        else:
            avg_opponent_size = sum(opponent_hand_sizes) / len(opponent_hand_sizes)
            if my_hand_size < avg_opponent_size - 2:
                my_position = 'leading'
            elif my_hand_size > avg_opponent_size + 2:
                my_position = 'behind'
            else:
                my_position = 'middle'
        
        # 緊急度（パス回数に基づく）
        my_pass_count = state.pass_count[self.my_player_num]
        urgency = min(1.0, my_pass_count / 3.0)
        
        # 推奨攻撃度の計算
        aggressiveness = 0.5  # ベースライン
        
        if phase == 'late':
            aggressiveness += 0.3  # 終盤は積極的に
        elif phase == 'early':
            aggressiveness -= 0.1  # 序盤は慎重に
        
        if my_position == 'leading':
            aggressiveness += 0.2  # リードしている場合は攻撃的に
        elif my_position == 'behind':
            aggressiveness -= 0.1  # 遅れている場合はやや慎重に
        
        if urgency > 0.6:
            aggressiveness += 0.2  # バースト危機は積極的にカードを出す
        
        aggressiveness = max(0.0, min(1.0, aggressiveness))
        
        return {
            'phase': phase,
            'my_position': my_position,
            'urgency': urgency,
            'aggressiveness': aggressiveness,
            'my_hand_size': my_hand_size,
            'opponent_hand_sizes': opponent_hand_sizes
        }
    
    def _count_run_length(self, action, my_hand):
        """連続して出せるカードの長さを数える"""
        num_idx = action.number.val - 1
        suit = action.suit
        run_length = 0
        
        if num_idx < 6:  # 7より小さい側
            check_idx = num_idx - 1
            while check_idx >= 0:
                next_card = Card(suit, self._index_to_number(check_idx))
                if next_card in my_hand:
                    run_length += 1
                    check_idx -= 1
                else:
                    break
        elif num_idx > 6:  # 7より大きい側
            check_idx = num_idx + 1
            while check_idx <= 12:
                next_card = Card(suit, self._index_to_number(check_idx))
                if next_card in my_hand:
                    run_length += 1
                    check_idx += 1
                else:
                    break
        
        return run_length
    
    def _evaluate_strategic_actions(self, state, tracker, my_actions, game_state_info):
        """Phase 2改善: 戦略的評価（強化版）
        
        OpponentModelに基づいて動的に戦略重み付けを変更
        - Tunnel Lock モード: トンネル封鎖戦略を強化
        - Burst Force モード: バースト誘導戦略を強化
        - Neutral モード: バランス型
        
        さらにゲーム状態に応じて適応的に重みを調整
        """
        bonus = {}
        my_hand = state.players_cards[self.my_player_num]
        
        # 相手モードの取得と重み係数の設定
        mode_weights = {"tunnel_lock": 1.0, "burst_force": 1.0, "heuristic": 1.0}
        
        # ゲーム状態に応じた重み調整
        aggressiveness = game_state_info['aggressiveness']
        phase = game_state_info['phase']
        
        if self._opponent_model:
            # 各相手のモードを判定し、最も脅威度の高い相手に合わせて戦略を調整
            opponent_modes = []
            threat_levels = []
            
            for p in range(state.players_num):
                if p != self.my_player_num and p not in state.out_player:
                    mode = self._opponent_model.mode(p)
                    threat = self._opponent_model.get_threat_level(p)
                    opponent_modes.append(mode)
                    threat_levels.append((p, mode, threat))
            
            # 最も脅威度の高い相手に合わせて重み調整
            if threat_levels:
                threat_levels.sort(key=lambda x: x[2], reverse=True)
                primary_opponent_mode = threat_levels[0][1]
                
                if primary_opponent_mode == "tunnel_lock":
                    # トンネル活用型の相手 → トンネルロック戦略を強化
                    mode_weights["tunnel_lock"] = TUNNEL_LOCK_WEIGHT * (1.0 + aggressiveness * AGGRESSIVENESS_MULTIPLIER)
                    mode_weights["burst_force"] = 0.8
                elif primary_opponent_mode == "burst_force":
                    # パス多用型の相手 → バースト誘導戦略を強化
                    mode_weights["burst_force"] = BURST_FORCE_WEIGHT * (1.0 + aggressiveness * AGGRESSIVENESS_MULTIPLIER)
                    mode_weights["tunnel_lock"] = 0.8
        
        # フェーズに応じた戦略調整
        if phase == 'late':
            # 終盤は確実性重視
            mode_weights["heuristic"] = 1.5
        elif phase == 'early':
            # 序盤はバランス重視
            mode_weights["tunnel_lock"] *= 0.8
            mode_weights["burst_force"] *= 0.8
        
        # トンネルロック戦略
        if ENABLE_TUNNEL_LOCK:
            tunnel_bonus = self._evaluate_tunnel_lock_advanced(state, tracker, my_hand, my_actions)
            for action, score in tunnel_bonus.items():
                bonus[action] = bonus.get(action, 0) + (score * mode_weights["tunnel_lock"])
        
        # バースト誘導戦略
        if ENABLE_BURST_FORCE:
            burst_bonus = self._evaluate_burst_force_advanced(state, tracker, my_actions)
            for action, score in burst_bonus.items():
                bonus[action] = bonus.get(action, 0) + (score * mode_weights["burst_force"])
        
        # 参考用コードからのヒューリスティック戦略を適用
        heuristic_bonus = self._evaluate_heuristic_strategy(state, my_hand, my_actions)
        for action, score in heuristic_bonus.items():
            bonus[action] = bonus.get(action, 0) + (score * mode_weights["heuristic"])
        
        # 連続カード（ラン）戦略
        run_bonus = self._evaluate_run_strategy(state, my_hand, my_actions)
        for action, score in run_bonus.items():
            bonus[action] = bonus.get(action, 0) + (score * (1.0 + aggressiveness * 0.2))
        
        # ゲーム終盤戦略（残り手札が少ない場合）
        if len(my_hand) <= 5 or phase == 'late':
            endgame_bonus = self._evaluate_endgame_strategy(state, my_hand, my_actions, game_state_info)
            for action, score in endgame_bonus.items():
                bonus[action] = bonus.get(action, 0) + score
        
        # ブロック戦略（相手を詰まらせる）
        block_bonus = self._evaluate_block_strategy(state, tracker, my_actions)
        for action, score in block_bonus.items():
            bonus[action] = bonus.get(action, 0) + (score * (1.0 - aggressiveness * AGGRESSIVENESS_MULTIPLIER))
        
        # 新機能：カードカウンティング戦略
        counting_bonus = self._evaluate_card_counting_strategy(state, tracker, my_hand, my_actions)
        for action, score in counting_bonus.items():
            bonus[action] = bonus.get(action, 0) + score
        
        # 新機能：参考コード由来の高度なヒューリスティック戦略
        advanced_heuristic_bonus = self._evaluate_advanced_heuristic_strategy(state, my_hand, my_actions)
        for action, score in advanced_heuristic_bonus.items():
            bonus[action] = bonus.get(action, 0) + (score * ADVANCED_HEURISTIC_WEIGHT)
        
        return bonus
    
    def _evaluate_heuristic_strategy(self, state, my_hand, my_actions):
        """参考用コード（xq-kessyou-main/7narabe_answer.ipynb）のヒューリスティック戦略（強化版）
        
        トンネルルール対応版:
        - 次のカードを自分が持っている場合にボーナス
        - 同じスートのカード数によるボーナス
        - 自分の新たなアクションを開くカードへのボーナス
        - 隣接カードが場にあるかチェック
        - A/K優先度の動的調整（参考コードの戦略を統合）
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
            
            # 参考コードからの改善1: A/Kの基本優先度を上げる
            # A/Kは両端なので、相手への道を開かないため基本的に有利
            if number_index == 0 or number_index == 12:
                score += ACE_KING_BASE_BONUS
            
            # トンネルルール対応：A/Kの扱いをさらに精密化
            is_ace_out = state.field_cards[suit_index][0] == 1
            is_king_out = state.field_cards[suit_index][12] == 1
            
            # トンネルが形成されている場合の追加ボーナス
            if number_index == 0:  # A
                if is_king_out:
                    # Kが出ている場合、Aを出すとトンネルが完成 → より有利
                    score += TUNNEL_COMPLETE_BONUS
                else:
                    # Kが出ていない場合でも、A側を進めることは重要
                    score += 3  # 控えめなボーナス
            elif number_index == 12:  # K
                if is_ace_out:
                    # Aが出ている場合、Kを出すとトンネルが完成 → より有利
                    score += TUNNEL_COMPLETE_BONUS
                else:
                    # Aが出ていない場合でも、K側を進めることは重要
                    score += 3  # 控えめなボーナス
            
            # 参考コードからの改善2: 隣接カードのチェックを強化
            next_indices = []
            if number_index < 6:  # 7より小さい側
                next_indices.append(number_index - 1)
            elif number_index > 6:  # 7より大きい側
                next_indices.append(number_index + 1)
            
            for next_number_index in next_indices:
                if 0 <= next_number_index <= 12:
                    if state.field_cards[suit_index][next_number_index] == 1:
                        # 次のカードがすでに場にある → 良い
                        score += ADJACENT_CARD_BONUS
                    else:
                        # 次のカードが場にない → 相手に道を開く可能性
                        score -= ADJACENT_CARD_PENALTY
                        
                        # ただし、次のカードを自分が持っていれば軽減（Safe判定）
                        next_number = self._index_to_number(next_number_index)
                        if next_number:
                            next_card = Card(suit, next_number)
                            if next_card in my_hand:
                                score += SAFE_MOVE_BONUS  # 次のカードを自分が持っている → 完全に制御可能
            
            # 参考コードからの改善3: 同じスートのカード数が多いほどボーナス
            # 自分が多く持っているスートを積極的に進めることで、連鎖的に出せる
            score += suit_counts[suit] * SUIT_CONCENTRATION_MULTIPLIER
            
            # 参考コードからの改善4: 手札を減らすインセンティブ
            # 全体的に手札を減らす方向にインセンティブ
            score += (len(my_hand) - 1) * HAND_REDUCTION_BONUS
            
            # 参考コードからの改善5: 自分の新たなアクションを開くカードへの高いボーナス
            potential_new_moves = 0
            for c in my_hand:
                if c.suit == suit:
                    c_index = c.number.val - 1
                    # このカードを出すことで次に出せるようになるカードがあるか
                    if (number_index < 6 and c_index == number_index - 1) or \
                       (number_index > 6 and c_index == number_index + 1):
                        potential_new_moves += 1
            score += potential_new_moves * CHAIN_POTENTIAL_MULTIPLIER
            
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
    
    def _evaluate_tunnel_lock_advanced(self, state, tracker, my_hand, my_actions):
        """トンネルロック戦略（強化版）
        
        確率的推論を活用した高度なトンネル封鎖戦略:
        - 相手の手札確率分布を考慮
        - トンネル状態の詳細分析
        - 複数の相手を同時に考慮
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        for suit_idx, suit in enumerate(Suit):
            is_ace_out = state.field_cards[suit_idx][0] == 1
            is_king_out = state.field_cards[suit_idx][12] == 1
            
            # 自分がこのスートで持っているカードの方向性を詳細に分析
            my_high_cards = []  # 8-K側のカード
            my_low_cards = []   # A-6側のカード
            for card in my_hand:
                if card.suit == suit:
                    if card.number.val >= 8:
                        my_high_cards.append(card)
                    elif card.number.val <= 6:
                        my_low_cards.append(card)
            
            # 相手がこの方向に持っている可能性を計算
            for action in my_actions:
                if action.suit != suit:
                    continue
                
                action_val = action.number.val
                
                # Aが出ている場合（K側のみ伸ばせる）
                if is_ace_out and not is_king_out and action_val == 13:
                    # K を出すかどうかの判断
                    
                    # 相手がK側（8-K）に持っている期待枚数を計算
                    opponent_high_expectation = 0
                    for p in range(state.players_num):
                        if p != self.my_player_num and p not in state.out_player:
                            for num_val in range(8, 14):
                                num = self._index_to_number(num_val - 1)
                                if num:
                                    check_card = Card(suit, num)
                                    # set-based: カードが possible[p] に含まれるかチェック
                                    if check_card in tracker.possible[p]:
                                        opponent_high_expectation += 1
                    
                    # 自分が多く持っている場合は出す、少ない場合は温存
                    if len(my_high_cards) >= 4:
                        # 自分が支配的 → 出してトンネルを完成させる
                        bonus[action] = 15
                    elif len(my_high_cards) <= 2 and opponent_high_expectation > 1.5:
                        # 相手が多く持っている可能性 → 温存して封鎖
                        bonus[action] = -20
                    else:
                        # 中間的 → やや温存
                        bonus[action] = -5
                
                # Kが出ている場合（A側のみ伸ばせる）
                elif is_king_out and not is_ace_out and action_val == 1:
                    # A を出すかどうかの判断
                    
                    # 相手がA側（A-6）に持っている期待枚数を計算
                    opponent_low_expectation = 0
                    for p in range(state.players_num):
                        if p != self.my_player_num and p not in state.out_player:
                            for num_val in range(1, 7):
                                num = self._index_to_number(num_val - 1)
                                if num:
                                    check_card = Card(suit, num)
                                    # set-based: カードが possible[p] に含まれるかチェック
                                    if check_card in tracker.possible[p]:
                                        opponent_low_expectation += 1
                    
                    # 自分が多く持っている場合は出す、少ない場合は温存
                    if len(my_low_cards) >= 4:
                        # 自分が支配的 → 出してトンネルを完成させる
                        bonus[action] = 15
                    elif len(my_low_cards) <= 2 and opponent_low_expectation > 1.5:
                        # 相手が多く持っている可能性 → 温存して封鎖
                        bonus[action] = -20
                    else:
                        # 中間的 → やや温存
                        bonus[action] = -5
                
                # トンネルを開ける行動（AまたはKを先に出す）
                elif not is_ace_out and not is_king_out:
                    if action_val == 1:  # Aを出す → K側を開放
                        # 自分がK側に多く持っているなら有利
                        if len(my_high_cards) >= len(my_low_cards) + 2:
                            bonus[action] = 10
                        else:
                            bonus[action] = -5  # 相手に有利になる可能性
                    elif action_val == 13:  # Kを出す → A側を開放
                        # 自分がA側に多く持っているなら有利
                        if len(my_low_cards) >= len(my_high_cards) + 2:
                            bonus[action] = 10
                        else:
                            bonus[action] = -5  # 相手に有利になる可能性
        
        return bonus
    
    def _evaluate_burst_force_advanced(self, state, tracker, my_actions):
        """バースト誘導戦略（強化版）
        
        確率的推論を活用した高度なバースト誘導:
        - 各相手のパス回数と確率分布から脆弱性を特定
        - 最も詰まりやすい相手を狙い撃ち
        - 複数スートの同時攻撃
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        # 各プレイヤーの脆弱性スコアを計算
        vulnerability = {}
        for player in range(state.players_num):
            if player == self.my_player_num or player in state.out_player:
                continue
            
            pass_count = state.pass_count[player]
            
            # パス回数が多いほど脆弱
            vuln_score = pass_count * 10
            
            # 期待手札枚数が多いほど危険（まだ余裕がある）
            # set-based: possible[player]のサイズで推定
            expected_hand_size = len(tracker.possible[player])
            vuln_score += max(0, 10 - expected_hand_size) * 3
            
            # 各スートの所持確率を分析
            suit_vulnerabilities = {}
            for suit in Suit:
                suit_card_count = 0
                for num in Number:
                    card = Card(suit, num)
                    # set-based: カードが possible[player] に含まれるかチェック
                    if card in tracker.possible[player]:
                        suit_card_count += 1
                
                # 所持可能性が低いスートほど脆弱
                suit_vulnerabilities[suit] = max(0, 5 - suit_card_count)
            
            vulnerability[player] = {
                'total': vuln_score,
                'suits': suit_vulnerabilities
            }
        
        # 最も脆弱な相手を特定
        if not vulnerability:
            return bonus
        
        most_vulnerable_player = max(vulnerability.keys(), key=lambda p: vulnerability[p]['total'])
        
        # アクションにボーナスを付与
        for action in my_actions:
            action_bonus = 0
            
            # 最も脆弱な相手に対して
            if most_vulnerable_player in vulnerability:
                player_vuln = vulnerability[most_vulnerable_player]
                suit_vuln = player_vuln['suits'].get(action.suit, 0)
                
                # パス回数に応じた基本ボーナス
                pass_count = state.pass_count[most_vulnerable_player]
                if pass_count >= 3:
                    action_bonus += 25  # あと1回でバースト
                elif pass_count >= 2:
                    action_bonus += 15
                elif pass_count >= 1:
                    action_bonus += 8
                
                # スート脆弱性ボーナス
                action_bonus += suit_vuln * 3
                
                # そのスートの進行度をチェック
                suit_idx = suit_to_index[action.suit]
                cards_played = np.sum(state.field_cards[suit_idx])
                progress = cards_played / 13.0
                
                # 進行度が高いほど相手が詰まりやすい
                action_bonus += progress * 10
            
            # 複数の脆弱な相手がいる場合、累積ボーナス
            for player, vuln_data in vulnerability.items():
                if player != most_vulnerable_player:
                    suit_vuln = vuln_data['suits'].get(action.suit, 0)
                    if suit_vuln > 2:  # そこそこ脆弱
                        action_bonus += suit_vuln * 1.5
            
            if action_bonus > 0:
                bonus[action] = bonus.get(action, 0) + action_bonus
        
        return bonus
    
    def _evaluate_burst_force(self, state, tracker, my_actions):
        """バースト誘導戦略（旧版・互換性のため残す）
        
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
    
    def _evaluate_run_strategy(self, state, my_hand, my_actions):
        """連続カード（ラン）戦略
        
        連続して出せるカードがある場合、その起点となるカードに高いボーナスを与える
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        for action in my_actions:
            suit = action.suit
            suit_idx = suit_to_index[suit]
            num_idx = action.number.val - 1
            
            # このカードを出した後、連続して出せるカードを数える
            run_length = 0
            
            if num_idx < 6:  # 7より小さい側
                # 下方向に連続して出せるか
                check_idx = num_idx - 1
                while check_idx >= 0:
                    next_card = Card(suit, self._index_to_number(check_idx))
                    if next_card in my_hand:
                        run_length += 1
                        check_idx -= 1
                    else:
                        break
            elif num_idx > 6:  # 7より大きい側
                # 上方向に連続して出せるか
                check_idx = num_idx + 1
                while check_idx <= 12:
                    next_card = Card(suit, self._index_to_number(check_idx))
                    if next_card in my_hand:
                        run_length += 1
                        check_idx += 1
                    else:
                        break
            
            # 連続カードが長いほど大きなボーナス
            if run_length >= 1:
                bonus[action] = run_length * 8
        
        return bonus
    
    def _evaluate_endgame_strategy(self, state, my_hand, my_actions, game_state_info):
        """ゲーム終盤戦略（強化版）
        
        残り手札が少ない場合は、確実に出せるカードを優先する
        ゲーム状態に応じて動的に調整
        """
        bonus = {}
        
        # 手札枚数とゲームフェーズに応じたボーナス倍率
        hand_size = len(my_hand)
        phase = game_state_info['phase']
        urgency = game_state_info['urgency']
        
        # 基本倍率
        if phase == 'late':
            multiplier = max(1, 8 - hand_size)  # 終盤は強力に
        else:
            multiplier = max(1, 6 - hand_size)
        
        # 緊急度による調整
        multiplier = multiplier * (1.0 + urgency * URGENCY_MULTIPLIER)
        
        for action in my_actions:
            score = 0
            
            # 出した後に確実に次のカードも出せる場合（連鎖可能）
            val = action.number.val
            if val == 1 or val == 13:
                # 端カードは確実に出せるので高評価
                score += 15 * multiplier
            else:
                # 次のカードを持っているか確認
                if val < 7:
                    next_val = val - 1
                else:
                    next_val = val + 1
                
                if 1 <= next_val <= 13:
                    next_card = Card(action.suit, self._index_to_number(next_val - 1))
                    if next_card in my_hand:
                        score += 12 * multiplier
            
            if score > 0:
                bonus[action] = score
        
        return bonus
    
    def _evaluate_card_counting_strategy(self, state, tracker, my_hand, my_actions):
        """カードカウンティング戦略
        
        場に出たカードと自分の手札から、残りのカードを推定し、
        より有利な判断を行う
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        # 各スートについて分析
        for suit in Suit:
            suit_idx = suit_to_index[suit]
            
            # このスートで場に出ているカードを数える
            cards_on_field = sum(state.field_cards[suit_idx])
            
            # 自分が持っているこのスートのカード
            my_cards_in_suit = [c for c in my_hand if c.suit == suit]
            
            # 残りのカード数（相手が持っている可能性のあるカード）
            # 全13枚 - 場のカード - 自分のカード
            remaining_cards = 13 - cards_on_field - len(my_cards_in_suit)
            
            # このスートで出せるアクションを評価
            for action in my_actions:
                if action.suit != suit:
                    continue
                
                score = 0
                num_idx = action.number.val - 1
                
                # 場の進行状況を分析
                # 7から両側にどれだけ進んでいるか
                low_progress = 0  # 7→1方向の進行度
                # 7より小さい側で最も進んだ位置を探す
                for i in range(6, -1, -1):
                    if state.field_cards[suit_idx][i] == 1:
                        low_progress = 6 - i
                        break
                
                high_progress = 0  # 7→13方向の進行度
                # 7より大きい側で最も進んだ位置を探す
                for i in range(6, 13):
                    if state.field_cards[suit_idx][i] == 1:
                        high_progress = i - 6
                        break
                
                # このカードを出すことで進行する方向の評価
                if num_idx < 6:  # 低い方向
                    # このスートの低い側がまだ進んでいない場合、リスク
                    if low_progress < 2 and remaining_cards > 3:
                        score -= 5  # 相手に道を開く可能性
                    elif low_progress >= 4:
                        score += 8  # もう進んでいるので安全
                elif num_idx > 6:  # 高い方向
                    # このスートの高い側がまだ進んでいない場合、リスク
                    if high_progress < 2 and remaining_cards > 3:
                        score -= 5
                    elif high_progress >= 4:
                        score += 8
                
                # 相手が持っているカードが少ない場合は攻撃的に
                if remaining_cards <= 2:
                    score += 10  # ほぼ支配している
                elif remaining_cards <= 4:
                    score += 5  # やや有利
                
                # このカードを出すことで次に出せるカードが増えるか
                potential_next_cards = 0
                for c in my_cards_in_suit:
                    c_idx = c.number.val - 1
                    if num_idx < 6 and c_idx == num_idx - 1:
                        potential_next_cards += 1
                    elif num_idx > 6 and c_idx == num_idx + 1:
                        potential_next_cards += 1
                
                score += potential_next_cards * 6
                
                if score != 0:
                    bonus[action] = score
        
        return bonus
    
    def _evaluate_advanced_heuristic_strategy(self, state, my_hand, my_actions):
        """参考コード由来の高度なヒューリスティック戦略
        
        提供された参考コードからの戦略を統合:
        - 円環距離（7からの距離）評価
        - 深度ベースの開放リスク評価（get_chain_risk）
        - スート支配力の評価
        - トンネル端（A/K）の特別処理を強化
        - 戦略的パス判断（別途実装）
        
        参考: 問題文で提供されたmy_AI関数のパラメータ駆動戦略
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
                    # ただし、相手の手札は完全には分からないので、推論ベースで評価
                    
                    # 簡易実装：相手がバーストしそうな時は、
                    # 場に繋がるカード（legal_actions）の価値を上げる
                    # なぜなら、相手がバースト後に場が広がる可能性が高いから
                    for card in my_actions:
                        # このカードを出すことで、新たに出せるようになるカードがあるか
                        # （つまり、場を広げる行動）
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
    
    def _evaluate_block_strategy(self, state, tracker, my_actions):
        """ブロック戦略
        
        相手が出そうとしているスートを先に進めて、相手のカードを出せなくする
        """
        bonus = {}
        suit_to_index = {Suit.SPADE: 0, Suit.CLUB: 1, Suit.HEART: 2, Suit.DIAMOND: 3}
        
        for player in range(state.players_num):
            if player == self.my_player_num or player in state.out_player:
                continue
            
            # このプレイヤーが出せそうなカードを推論
            for action in my_actions:
                suit = action.suit
                suit_idx = suit_to_index[suit]
                num_idx = action.number.val - 1
                
                # 次のカードを相手が持っている可能性が高い場合、
                # このカードを出すことで相手を助けてしまう
                # 逆に、相手が持っていない可能性が高い場合はボーナス
                
                next_indices = []
                if num_idx < 6:
                    next_indices.append(num_idx - 1)
                elif num_idx > 6:
                    next_indices.append(num_idx + 1)
                
                for next_idx in next_indices:
                    if 0 <= next_idx <= 12:
                        next_card = Card(suit, self._index_to_number(next_idx))
                        
                        # 相手がこのカードを持っていない可能性が高い場合
                        if next_card not in tracker.possible[player]:
                            # 相手が出せないので、この方向を進めるのは良い
                            bonus[action] = bonus.get(action, 0) + 3
                        elif next_card in tracker.possible[player]:
                            # 相手が持っている可能性がある → やや不利
                            bonus[action] = bonus.get(action, 0) - 2
        
        return bonus

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
                    # カードを場に置く（エラーは無視 - すでに置かれている場合など）
                    replay_state.put_card(a)

            # 3) 次手番へ（out_player をスキップ）
            original = replay_state.turn_player
            for i in range(1, replay_state.players_num + 1):
                np_ = (original + i) % replay_state.players_num
                if np_ not in replay_state.out_player:
                    replay_state.turn_player = np_
                    break

        return tracker

    def _create_determinized_state_with_constraints(self, original_state, tracker: CardTracker):
        """重み付け確定化: 推論制約を満たすように相手手札を生成
        
        参考用実装ベース（doc/misc/colab_notebook.md 689-748行目）
        """
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

        # 確定化を複数回リトライ（値は DETERMINIZATION_ATTEMPTS で管理）
        # 制約を満たす割り当てを試行（過去の検証でこの回数で十分収束）
        for _ in range(30):  # 参考用実装の値（30回）
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
