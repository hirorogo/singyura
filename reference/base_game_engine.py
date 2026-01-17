"""
七並べゲームエンジン - 基本実装
Singularityバトルクエスト大会で提供された基本フォーマット

このファイルはdoc/misc/colab_notebook.mdから抽出された参考実装です。
"""

from enum import Enum
from random import shuffle
import numpy as np


class Suit(Enum):
    """カードのスート（マーク）"""
    SPADE = '♠'
    CLUB = '♣'
    HEART = '♡'
    DIAMOND = '♢'
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f"Suit.{self.name}"


class Number(Enum):
    """カードの数字"""
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
    """カードを表すクラス"""
    def __init__(self, suit, number):
        if not (isinstance(suit, Suit) and isinstance(number, Number)):
            raise ValueError  # Enum じゃないとエラー
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
    """手札を表すクラス（リストを継承）"""
    def __init__(self, card_list):
        super().__init__(i for i in card_list)

    def check_number(self):
        """手札の数字のリストを返す"""
        number_list = [i.number.val for i in self]
        return number_list

    def check_suit(self):
        """手札のスートのリストを返す"""
        suit_list = [str(i.suit) for i in self]
        return suit_list

    def choice(self, card):
        """指定したカードを手札から取り出す"""
        if card in self:
            self.remove(card)
            return card
        else:
            raise ValueError

    def check(self, card):
        """指定したカードが手札にあるか確認"""
        return card in self


class Deck(list):
    """デッキ（山札）を表すクラス"""
    def __init__(self):
        super().__init__(
            Card(suit, number) for suit in Suit for number in Number
        )
        self.shuffle()

    def shuffle(self):
        """デッキをシャッフル"""
        shuffle(self)

    def draw(self):
        """カードを1枚引く"""
        return self.pop()

    def deal(self, players_num):
        """プレイヤーに均等にカードを配る"""
        cards = [Hand(i) for i in np.array_split(self, players_num)]
        self.clear()
        return cards


class State:
    """ゲームの状態を管理するクラス"""
    
    def __init__(self, players_num=3, field_cards=None, players_cards=None,
                 turn_player=None, pass_count=None, out_player=None,
                 all_actions=None, all_players=None):
        if players_cards is None:
            # 新規ゲームの初期化
            deck = Deck()
            self.players_cards = deck.deal(players_num)
            self.players_num = players_num
            self.field_cards = np.zeros((4, 13), dtype='int64')
            self.start_flags = [0] * self.players_num
            self.pass_count = [0] * self.players_num
            self.out_player = []
            self.all_actions = []
            self.all_players = []
            self.all_cards = [[str(Card(suit, number)) for number in Number] for suit in Suit]
            
            # 7を自動的に出す
            for players_number in range(players_num):
                self.start_flags[players_number] = self.choice_seven(
                    hand=self.players_cards[players_number]
                )
            self.turn_player = self.start_flags.index(1)
        else:
            # 既存のゲーム状態をコピー
            self.players_cards = players_cards
            self.field_cards = field_cards
            self.players_num = players_num
            self.turn_player = turn_player
            self.pass_count = pass_count
            self.out_player = out_player
            self.all_actions = all_actions
            self.all_players = all_players
            self.all_cards = [[str(Card(suit, number)) for number in Number] for suit in Suit]

    def choice_seven(self, hand):
        """7のカードを場に出す（初期配置）"""
        start_flag = 0
        for card in [Card(suit, Number.SEVEN) for suit in Suit]:
            if hand.check(Card(Suit.DIAMOND, Number.SEVEN)):
                start_flag = 1
            if hand.check(card):
                self.put_card(hand.choice(card))
        return start_flag

    def choice_card(self, hand, card):
        """手札からカードを選ぶ"""
        hand.choice(card)

    def put_card(self, card):
        """カードを場に出す"""
        num = 10
        for s, i in zip(Suit, range(4)):
            if card.suit == s:
                num = i
        self.field_cards[num][card.number.val - 1] = int(1)

    def legal_actions(self):
        """場で出せるカードのリストを取得（トンネルルール対応）"""
        actions = []
        for suit, n in zip(Suit, range(4)):
            small_side = self.field_cards[n][0:6][::-1].tolist()
            large_side = self.field_cards[n][7:13].tolist()

            # カードの場の状態をチェック
            is_ace_out = self.field_cards[n][0] == 1    # Aが出ている
            is_king_out = self.field_cards[n][12] == 1  # Kが出ている

            # 7より小さい側 (A-6) の最も外側に出せるカード
            if small_side.count(1) != 6:
                card_num_val = 6 - small_side.index(0)

                if card_num_val != 1:
                    actions.append(Card(suit, self.num_to_Enum(card_num_val)))
                elif self.field_cards[n][1] == 1 and not is_ace_out:
                    actions.append(Card(suit, Number.ACE))

            # 7より大きい側 (8-K) の最も外側に出せるカード
            if large_side.count(1) != 6:
                card_num_val = 8 + large_side.index(0)

                if card_num_val != 13:
                    actions.append(Card(suit, self.num_to_Enum(card_num_val)))
                elif self.field_cards[n][11] == 1 and not is_king_out:
                    actions.append(Card(suit, Number.KING))

            # トンネルルール
            if is_ace_out and not is_king_out:
                actions.append(Card(suit, Number.KING))
            elif is_king_out and not is_ace_out:
                actions.append(Card(suit, Number.ACE))

        return list(set(actions))

    def my_actions(self):
        """自分が出せるカードのリストを取得"""
        actions = []
        for legal in self.legal_actions():
            if self.players_cards[self.turn_player].check(legal):
                actions.append(legal)
        return actions

    def my_actions_str(self):
        """自分が出せるカードを文字列リストで取得"""
        actions = []
        for legal in self.legal_actions():
            if self.players_cards[self.turn_player].check(legal):
                actions.append(legal)
        return [str(i) for i in actions]

    def my_hands(self):
        """自分の手札を取得"""
        return self.players_cards[self.turn_player]

    def my_hands_str(self):
        """自分の手札を文字列リストで取得"""
        return [str(i) for i in self.players_cards[self.turn_player]]

    def num_to_Enum(self, num):
        """数字をNumberEnumに変換"""
        enum_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                     Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                     Number.NINE, Number.TEN, Number.JACK, Number.QUEEN,
                     Number.KING]
        return enum_list[num - 1]

    def next(self, action, pass_flag=0):
        """次の状態を取得（行動を実行）"""
        if self.my_actions() == []:
            # 出せるカードがない場合は強制パス
            self.pass_count[self.turn_player] += 1
            self.pass_check()
        elif pass_flag == 1:
            # 意図的なパス
            self.pass_count[self.turn_player] += 1
            self.pass_check()
        else:
            # カードを出す
            self.players_cards[self.turn_player].remove(action)
            self.put_card(action)
            self.all_actions.append(action)
            self.all_players.append(self.turn_player)

        # 次のプレイヤーへ
        self.next_player()
        return State(
            players_num=self.players_num,
            field_cards=self.field_cards,
            players_cards=self.players_cards,
            turn_player=self.turn_player,
            pass_count=self.pass_count,
            out_player=self.out_player,
            all_actions=self.all_actions,
            all_players=self.all_players
        )

    def next_player(self):
        """次のプレイヤーを取得（失格者はスキップ）"""
        flag = 0
        while flag == 0:
            self.turn_player = (self.turn_player + 1) % self.players_num
            if self.turn_player not in self.out_player:
                flag = 1

    def pass_check(self):
        """パス回数のチェック（4回目で失格）"""
        out_list = self.out_player
        if self.pass_count[self.turn_player] > 3:
            # バースト：手札を全て場に出す
            for card in self.my_hands():
                self.put_card(card)
                self.all_actions.append(card)
                self.all_players.append(self.turn_player)
            out_list.append(self.turn_player)
            self.out_player = out_list

    def to_str(self, num):
        """数値を文字列に変換"""
        return str(num)

    def is_done(self):
        """ゲーム終了判定（手札が0枚）"""
        return len(self.my_hands()) == 0

    def __str__(self):
        """ゲーム状態の文字列表現"""
        str_output = ''
        field_cards = self.field_cards.tolist()
        from operator import mul
        out_list = [list(map(mul, self.all_cards[i], field_cards[i])) for i in range(4)]
        str_output += "場のカード\n\n"
        for i in range(len(out_list)):
            minilist = out_list[i]
            for j in range(len(minilist)):
                if minilist[j] == "":
                    str_output += " -- "
                else:
                    str_output += " " + minilist[j] + " "
            str_output += '\n'
        num = self.to_str(self.turn_player)
        pass_cnt = self.to_str(self.pass_count[self.turn_player])
        str_output += "\nプレイヤー" + num + "番　　パス回数" + pass_cnt + "\n"
        str_output += "\nあなたの手札\n"

        out_list = self.my_hands_str()
        for i in range(len(out_list)):
            str_output += out_list[i]
            str_output += " "

        str_output += "\n\n出せるカード\n"

        out_list = self.my_actions_str()
        for i in range(len(out_list)):
            str_output += out_list[i]
            str_output += " "

        str_output += "\n"

        return str_output


def num_to_Card(number, suit):
    """数字とスートからCardオブジェクトを生成"""
    number_list = [Number.ACE, Number.TWO, Number.THREE, Number.FOUR,
                   Number.FIVE, Number.SIX, Number.SEVEN, Number.EIGHT,
                   Number.NINE, Number.TEN, Number.JACK, Number.QUEEN,
                   Number.KING]
    suit_list = [Suit.SPADE, Suit.CLUB, Suit.HEART, Suit.DIAMOND]
    return Card(suit_list[suit], number_list[number - 1])
