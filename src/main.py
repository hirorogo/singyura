
import random
from enum import Enum
from random import shuffle
import numpy as np

# --- 定数・設定 ---
EP_GAME_COUNT = 1000  # 評価用の対戦回数
MY_PLAYER_NUM = 0     # 自分のプレイヤー番号

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
        if not (isinstance(suit, Suit) and isinstance(number, Number)):
            raise ValueError
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


# --- ゲームエンジン ---

class State:
    def __init__(self, players_num=3, field_cards=None, players_cards=None, turn_player=None, pass_count=None, out_player=None):
        if players_cards is None:
            deck = Deck()
            self.players_cards = deck.deal(players_num)
            self.players_num = players_num
            # 4スート x 13の数字 (0-12 index)
            self.field_cards = np.zeros((4, 13), dtype='int64')
            self.pass_count = [0] * self.players_num
            self.out_player = [] # バーストまたは上がりで抜けたプレイヤー
            
            # 手札にある7を自動的に場に出す処理
            start_flags = [0] * self.players_num
            for players_number in range(players_num):
                 # choice_seven は内部で put_card も行う
                start_flags[players_number] = self.choice_seven(hand=self.players_cards[players_number])
            
            # ダイヤの7を持っていた人がスタート
            if 1 in start_flags:
                self.turn_player = start_flags.index(1)
            else:
                self.turn_player = 0 # フォールバック

        else:
            self.players_cards = players_cards
            self.field_cards = field_cards
            self.players_num = players_num
            self.turn_player = turn_player
            self.pass_count = pass_count
            self.out_player = out_player

    def choice_seven(self, hand):
        """手札の7を場に出す。ダイヤの7があれば1を返す"""
        is_start_player = 0
        sevens = [Card(suit, Number.SEVEN) for suit in Suit]
        
        # まずダイヤの7チェック
        if hand.check(Card(Suit.DIAMOND, Number.SEVEN)):
            is_start_player = 1
            
        # 手札にある7を全て場に出す
        for card in sevens:
            if hand.check(card):
                hand.choice(card) # 手札から削除
                self.put_card(card) # 場に出す
                
        return is_start_player

    def put_card(self, card):
        """場にカードを置く（記録する）"""
        suit_index = 0
        for i, s in enumerate(Suit):
            if card.suit == s:
                suit_index = i
                break
        self.field_cards[suit_index][card.number.val - 1] = 1

    def legal_actions(self):
        """場で出せるカードのリストを返す"""
        actions = []
        for suit, n in zip(Suit, range(4)):
            # 0〜5 (A〜6) と 7〜12 (8〜K)。 6 (7) は常に出ている前提
            
            # Aが出ている (index 0) / Kが出ている (index 12)
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            # --- 7より小さい側 (A-6) ---
            # 7(index 6) は出ている。6(index 5) ... 1(index 0) へと探索
            # 出ていないカードで、その隣が出ているものを探す
            # 簡易実装: field_cards[n][0:6] は A,2,3,4,5,6
            # 逆順にして [6, 5, 4, 3, 2, A]
            small_side = self.field_cards[n][0:6]

            # 6が出ているか？
            if small_side[5] == 0:
                actions.append(Card(suit, Number.SIX))
            else:
                # 6が出ているなら、5, 4... と見ていく
                for i in range(5, -1, -1): # 5,4,3,2,0
                    if small_side[i] == 0:
                        # まだ出ていないカード。これの隣(i+1)は出ている(ループで確認済み or 7)
                        # つまりこれが出せる
                        actions.append(Card(suit, self.num_to_Enum(i + 1)))
                        break
            
            # --- 7より大きい側 (8-K) ---
            # field_cards[n][7:13] は 8,9,10,J,Q,K
            large_side = self.field_cards[n][7:13]
            
            # 8が出ているか？ (index 7)
            if self.field_cards[n][7] == 0:
                actions.append(Card(suit, Number.EIGHT))
            else:
                for i in range(7, 13):
                    if self.field_cards[n][i] == 0:
                        actions.append(Card(suit, self.num_to_Enum(i + 1)))
                        break
            
            # トンネルルールの考慮（Aが出たらKが出せる等）はreadmeのロジックを参考に含める
            # readmeのlegal_actionsはかなり複雑な記述があったが、基本的な7並べならこれだけで十分動く
            # ここではシンプルな隣接ルールのみとする（トンネル対応が必要なら後で追加）
            
        return list(set(actions)) # 重複排除

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
        for hand in self.players_cards:
            if len(hand) == 0:
                return True
        
        # バースト等で残り1人になったら終了
        active_count = self.players_num - len(self.out_player)
        return active_count <= 1

    def next(self, action, pass_flag=0):
        """状態更新"""
        # 現在のプレイヤー
        p_idx = self.turn_player

        if pass_flag == 1 or self.my_actions() == []:
            # パス処理
            self.pass_count[p_idx] += 1
            if self.pass_count[p_idx] >= 3:
                # バースト処理
                # 手札をすべて場に出す
                hand = self.players_cards[p_idx]
                for card in list(hand):
                    self.put_card(card)
                hand.clear() # 手札消滅
                self.out_player.append(p_idx)
                print(f"Player {p_idx} BURST!")
        else:
            # カードを出す
            if action:
                try:
                    self.players_cards[p_idx].choice(action) # 手札から削除
                    self.put_card(action) # 場に出す
                except ValueError:
                    print(f"Error: Player {p_idx} tried to play {action} but didn't have it.")

        # 勝利判定チェック（手札が0になったら）
        if len(self.players_cards[p_idx]) == 0 and p_idx not in self.out_player:
            # 上がり！
            # ここではターンを渡さずに終了状態にする（is_doneで判定させるため）
            # または、out_playerに追加してゲームから除外するか。
            # 今回は「1位が決まったら終了」なので、ここでリターンしてループ側でキャッチする
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


# --- AI実装 ---

def random_action(state):
    """ランダムAI"""
    my_actions = state.my_actions()
    if my_actions:
        return my_actions[random.randint(0, len(my_actions)-1)]
    else:
        return None

# 適応型ルールベースAI（雛形）
def my_AI(state):
    """
    ルールベースAI
    1. パスチェック: 出せるカードがないならパス
    2. 戦略的選択: 出せるカードの中で最も有利なものを選ぶ
    """
    my_actions = state.my_actions()
    
    # 出せるカードがない場合 -> パス
    if not my_actions:
         return None, 1 # action=None, pass_flag=1
    
    # --- 戦略ロジック実装予定地 ---
    
    # 現状はランダム（ここを改良する）
    best_action = random.choice(my_actions)
    
    return best_action, 0 


# --- メイン実行ループ ---

if __name__ == "__main__":
    print(f"MY_PLAYER_NUM: {MY_PLAYER_NUM}")
    
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
        action = None
        
        if current_player == MY_PLAYER_NUM:
            action, pass_flag = my_AI(state)
        else:
            action = random_action(state)
            if action is None:
                pass_flag = 1
        
        # アクションの表示
        if pass_flag == 1:
            print(f"Player {current_player}: PASS ({state.pass_count[current_player] + 1}回目)")
        else:
            print(f"Player {current_player}: Play {action}")
        
        # 状態更新
        state.next(action, pass_flag)
