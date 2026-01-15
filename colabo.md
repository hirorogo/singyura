{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "codemirror_mode": {
        "name": "ipython",
        "version": 3
      },
      "file_extension": ".py",
      "mimetype": "text/x-python",
      "name": "python",
      "nbconvert_exporter": "python",
      "pygments_lexer": "ipython3",
      "version": "3.7.4"
    },
    "colab": {
      "provenance": [],
      "collapsed_sections": [
        "w9NrcC2eX2rz",
        "q9izlUugX2r1",
        "ryk0xBKDX2r2",
        "GNGpCtcKX2r3",
        "qUkKLp7YX2r3",
        "ynw4st_SX2r3",
        "kje5JkeXX2r4",
        "S2KVM9v3X2r4",
        "DcPIw4roX2r4",
        "OCyEEe9xX2r5",
        "jpC0h8JmX2r5",
        "-BCcjsiGX2r6",
        "0PbemkfyX2r8"
      ],
      "include_colab_link": true
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/hirorogo/singyura/blob/main/main\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "ISHogYPkX2rm",
        "cellView": "form"
      },
      "source": [
        "# @title\n",
        "from enum import Enum\n",
        "from random import shuffle\n",
        "import numpy as np\n",
        "from operator import mul\n",
        "import random\n",
        "import termcolor\n",
        "\n",
        "class Suit(Enum):\n",
        "    SPADE = '♠'\n",
        "    CLUB = '♣'\n",
        "    HEART = '♡'\n",
        "    DIAMOND = '♢'\n",
        "    def __str__(self):\n",
        "        return self.value\n",
        "    def __repr__(self):\n",
        "        return f\"Suit.{self.name}\"\n",
        "\n",
        "\n",
        "class Number(Enum):\n",
        "    ACE = (1, 'A')\n",
        "    TWO = (2, '2')\n",
        "    THREE = (3, '3')\n",
        "    FOUR = (4, '4')\n",
        "    FIVE = (5, '5')\n",
        "    SIX = (6, '6')\n",
        "    SEVEN = (7, '7')\n",
        "    EIGHT = (8, '8')\n",
        "    NINE = (9, '9')\n",
        "    TEN = (10, '10')\n",
        "    JACK = (11, 'J')\n",
        "    QUEEN = (12, 'Q')\n",
        "    KING = (13, 'K')\n",
        "\n",
        "    def __init__(self, val, string):\n",
        "        self.val = val\n",
        "        self.string = string\n",
        "\n",
        "    def __str__(self):\n",
        "        return self.string\n",
        "\n",
        "    def __repr__(self):\n",
        "        return f\"Number.{self.name}\"\n",
        "\n",
        "class Card:\n",
        "    def __init__(self, suit, number):\n",
        "        if not (isinstance(suit, Suit) and isinstance(number, Number)):\n",
        "            raise ValueError  # Enum じゃないとエラー\n",
        "        self.suit = suit\n",
        "        self.number = number\n",
        "\n",
        "    def __str__(self):\n",
        "        return str(self.suit) + str(self.number)\n",
        "\n",
        "    def __repr__(self):\n",
        "        return f\"Card({self.__str__()})\"\n",
        "\n",
        "    def __eq__(self, other):\n",
        "        return (self.suit, self.number) == (other.suit, other.number)\n",
        "\n",
        "    def __hash__(self):\n",
        "        return hash((self.suit, self.number))\n",
        "\n",
        "\n",
        "class Hand(list):\n",
        "    def __init__(self,card_list):\n",
        "        super().__init__(\n",
        "            i for i in card_list\n",
        "        )\n",
        "\n",
        "    def check_number(self):\n",
        "        number_list=[i.number.val for i in self]\n",
        "        return number_list\n",
        "\n",
        "    def check_suit(self):\n",
        "        suit_list=[str(i.suit) for i in self]\n",
        "        return suit_list\n",
        "\n",
        "    def choice(self,card):\n",
        "        #Card(Suit.SPADE, Number.ACE)\n",
        "        if card in self:\n",
        "            self.remove(card)\n",
        "            return card\n",
        "        else:\n",
        "            raise ValueError\n",
        "\n",
        "    def check(self,card):\n",
        "        return card in self\n",
        "\n",
        "\n",
        "class Deck(list):\n",
        "    def __init__(self):\n",
        "        super().__init__(\n",
        "            Card(suit, number) for suit in Suit for number in Number\n",
        "        )  # list の初期化を呼び出す\n",
        "        self.shuffle()  # 最初にシャッフル\n",
        "    def shuffle(self):\n",
        "        shuffle(self)\n",
        "    def draw(self):\n",
        "        return self.pop()\n",
        "    def deal(self, players_num):\n",
        "        cards=[Hand(i) for i in np.array_split(self,players_num)]\n",
        "        self.clear()\n",
        "        return cards"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {
        "id": "1tSkVx3rjMti",
        "cellView": "form"
      },
      "outputs": [],
      "source": [
        "# @title\n",
        "# ゲームの状態\n",
        "class State:\n",
        "    # 初期化\n",
        "    def __init__(self, players_num=3,field_cards=None, players_cards=None,turn_player=None,pass_count=None,out_player=None,all_actions=None,all_players=None):\n",
        "        if players_cards==None:\n",
        "            deck = Deck()\n",
        "            self.players_cards=deck.deal(players_num)\n",
        "            self.players_num=players_num\n",
        "            self.field_cards=np.zeros((4,13), dtype='int64')\n",
        "            self.start_flags=[0]*self.players_num\n",
        "            self.pass_count=[0]*self.players_num\n",
        "            self.out_player=[]\n",
        "            self.all_actions = []\n",
        "            self.all_players = []\n",
        "            self.all_cards=[[str(Card(suit, number))  for number in Number] for suit in Suit]\n",
        "            for players_number in range(players_num):\n",
        "                self.start_flags[players_number]=self.choice_seven(hand=self.players_cards[players_number])\n",
        "            self.turn_player=self.start_flags.index(1)\n",
        "        else:\n",
        "            self.players_cards=players_cards\n",
        "            self.field_cards=field_cards\n",
        "            self.players_num=players_num\n",
        "            self.turn_player=turn_player\n",
        "            self.pass_count=pass_count\n",
        "            self.out_player=out_player\n",
        "            self.all_actions=all_actions\n",
        "            self.all_players =all_players\n",
        "            self.all_cards=[[str(Card(suit, number))  for number in Number] for suit in Suit]\n",
        "\n",
        "\n",
        "    #7のカードを出す\n",
        "    def choice_seven(self,hand):\n",
        "        start_flag=0\n",
        "        for card in [Card(suit,Number.SEVEN) for suit in Suit]:\n",
        "            if hand.check(Card(Suit.DIAMOND,Number.SEVEN))==True:\n",
        "                start_flag=1\n",
        "            if hand.check(card)==True:\n",
        "                self.put_card(hand.choice(card))\n",
        "        return start_flag\n",
        "\n",
        "    def choice_card(self,hand,card):\n",
        "        hand.choice(card)\n",
        "\n",
        "    #場にカードを出す\n",
        "    def put_card(self,card):\n",
        "        num=10\n",
        "        for s,i in zip(Suit,range(4)):\n",
        "            if card.suit==s:\n",
        "                num=i\n",
        "        #state.my_hands().remove(card)\n",
        "        self.field_cards[num][card.number.val-1]=int(1)\n",
        "\n",
        "\n",
        "    # 場で出せる手のリスト取得\n",
        "    def legal_actions(self):\n",
        "        actions = []\n",
        "        for suit, n in zip(Suit, range(4)):\n",
        "            small_side = self.field_cards[n][0:6][::-1].tolist()\n",
        "            large_side = self.field_cards[n][7:13].tolist()\n",
        "\n",
        "            # カードの場の状態をチェック\n",
        "            is_ace_out = self.field_cards[n][0] == 1    # Aが出ている (インデックス 0)\n",
        "            is_king_out = self.field_cards[n][12] == 1  # Kが出ている (インデックス 12)\n",
        "\n",
        "            # --- 1. 通常の隣接カード判定 ---\n",
        "\n",
        "            # 7より小さい側 (A-6) の最も外側に出せるカード\n",
        "            if small_side.count(1) != 6:\n",
        "                card_num_val = 6 - small_side.index(0)\n",
        "\n",
        "                if card_num_val != 1:\n",
        "                    actions.append(Card(suit, self.num_to_Enum(card_num_val)))\n",
        "\n",
        "                elif self.field_cards[n][1] == 1 and not is_ace_out:\n",
        "                    actions.append(Card(suit, Number.ACE))\n",
        "\n",
        "            # 7より大きい側 (8-K) の最も外側に出せるカード\n",
        "            if large_side.count(1) != 6:\n",
        "                card_num_val = 8 + large_side.index(0)\n",
        "\n",
        "                if card_num_val != 13:\n",
        "                    actions.append(Card(suit, self.num_to_Enum(card_num_val)))\n",
        "\n",
        "                elif self.field_cards[n][11] == 1 and not is_king_out:\n",
        "                    actions.append(Card(suit, Number.KING))\n",
        "\n",
        "            if is_ace_out and not is_king_out:\n",
        "                actions.append(Card(suit, Number.KING))\n",
        "\n",
        "            elif is_king_out and not is_ace_out:\n",
        "                actions.append(Card(suit, Number.ACE))\n",
        "\n",
        "        return list(set(actions))\n",
        "\n",
        "\n",
        "    # 自分が出せる手のリスト取得\n",
        "    def my_actions(self):\n",
        "        actions = []\n",
        "        for legal in self.legal_actions():\n",
        "            if self.players_cards[self.turn_player].check(legal)==True:\n",
        "                actions.append(legal)\n",
        "        return actions\n",
        "    def my_actions_str(self):\n",
        "        actions = []\n",
        "        for legal in self.legal_actions():\n",
        "            if self.players_cards[self.turn_player].check(legal)==True:\n",
        "                actions.append(legal)\n",
        "        return [str(i) for i in actions]\n",
        "\n",
        "    # 自分の手札取得\n",
        "    def my_hands(self):\n",
        "        return self.players_cards[self.turn_player]\n",
        "    def my_hands_str(self):\n",
        "        return [str(i) for i in self.players_cards[self.turn_player]]\n",
        "\n",
        "\n",
        "    def num_to_Enum(self,num):\n",
        "        enum_list=[Number.ACE,Number.TWO,Number.THREE,Number.FOUR,\n",
        "                   Number.FIVE,Number.SIX,Number.SEVEN,Number.EIGHT,\n",
        "                   Number.NINE,Number.TEN,Number.JACK,Number.QUEEN,\n",
        "                   Number.KING]\n",
        "        return enum_list[num-1]\n",
        "\n",
        "\n",
        "    # 次の状態の取得\n",
        "    def next(self,action,pass_flag = 0):\n",
        "        if self.my_actions()==[]:\n",
        "            self.pass_count[self.turn_player]+=1\n",
        "            self.pass_check()\n",
        "        elif pass_flag == 1:\n",
        "            self.pass_count[self.turn_player]+=1\n",
        "            self.pass_check()\n",
        "        else:\n",
        "            self.players_cards[self.turn_player].remove(action)\n",
        "            self.put_card(action)\n",
        "            self.all_actions.append(action)\n",
        "            self.all_players.append(self.turn_player)\n",
        "\n",
        "        #次のプレイヤーに\n",
        "        self.next_player()\n",
        "        return State(players_num=self.players_num,field_cards=self.field_cards, players_cards=self.players_cards,turn_player=self.turn_player,pass_count=self.pass_count,out_player=self.out_player,all_actions=self.all_actions,all_players=self.all_players)\n",
        "\n",
        "    #次のプレイヤーの取得\n",
        "    def next_player(self):\n",
        "        flag=0\n",
        "        while flag==0:\n",
        "            self.turn_player = (self.turn_player + 1) % self.players_num\n",
        "\n",
        "            if self.turn_player not in self.out_player:\n",
        "                flag=1\n",
        "\n",
        "    #パスの上限判定\n",
        "    def pass_check(self):\n",
        "        out_list=self.out_player\n",
        "        if self.pass_count[self.turn_player]>3:\n",
        "            for card in self.my_hands():\n",
        "                self.put_card(card)\n",
        "                self.all_actions.append(card)\n",
        "                self.all_players.append(self.turn_player)\n",
        "\n",
        "            out_list.append(self.turn_player)\n",
        "\n",
        "            self.out_player=out_list\n",
        "\n",
        "    def to_str(self,num):\n",
        "        return str(num)\n",
        "\n",
        "    #勝ち負け判定\n",
        "    def is_done(self):\n",
        "        return len(self.my_hands())==0\n",
        "\n",
        "\n",
        "    # 状態表示\n",
        "    def __str__(self):\n",
        "        str = ''\n",
        "        field_cards=self.field_cards.tolist()\n",
        "        out_list=[list(map(mul,self.all_cards[i],field_cards[i])) for i in range(4)]\n",
        "        str += \"場のカード\\n\\n\"\n",
        "        for i in range(len(out_list)):\n",
        "            minilist=out_list[i]\n",
        "            for j in range(len(minilist)):\n",
        "                if minilist[j] == \"\":\n",
        "                    str += \" -- \"\n",
        "                else:\n",
        "                    str +=\" \"+minilist[j]+\" \"\n",
        "            str += '\\n'\n",
        "        num=self.to_str(self.turn_player)\n",
        "        pass_cnt=self.to_str(self.pass_count[self.turn_player])\n",
        "        str+=\"\\nプレイヤー\"+num+\"番　　パス回数\"+pass_cnt+\"\\n\"\n",
        "        str += \"\\nあなたの手札\\n\"\n",
        "\n",
        "        out_list=self.my_hands_str()\n",
        "        for i in range(len(out_list)):\n",
        "            str+=out_list[i]\n",
        "            str+=\" \"\n",
        "\n",
        "        str += \"\\n\\n出せるカード\\n\"\n",
        "\n",
        "        out_list=self.my_actions_str()\n",
        "        for i in range(len(out_list)):\n",
        "            str+=out_list[i]\n",
        "            str+=\" \"\n",
        "\n",
        "        str += \"\\n\"\n",
        "\n",
        "        return str"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "h2Hahk8vX2ru",
        "cellView": "form"
      },
      "source": [
        "# @title\n",
        "def num_to_Card(number,suit):\n",
        "    number_list=[Number.ACE,Number.TWO,Number.THREE,Number.FOUR,\n",
        "                Number.FIVE,Number.SIX,Number.SEVEN,Number.EIGHT,\n",
        "                Number.NINE,Number.TEN,Number.JACK,Number.QUEEN,\n",
        "                Number.KING]\n",
        "    suit_list=[Suit.SPADE,Suit.CLUB,Suit.HEART,Suit.DIAMOND]\n",
        "    return Card(suit_list[suit],number_list[number-1])"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "VPV1gI_XX2ru"
      },
      "source": [
        "# ランダム行動 AI\n",
        "def random_action(state):\n",
        "    my_actions = state.my_actions()\n",
        "    if my_actions != []:\n",
        "        return my_actions[random.randint(0, len(my_actions)-1)]\n",
        "    else:\n",
        "        my_actions=[]\n",
        "    return my_actions"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "source": [
        "# **※課題 my_AIの作成**\n",
        "\n",
        "`return (出したいカード),(パスを行うか)`を行うAIを作成してください"
      ],
      "metadata": {
        "id": "3dAOfxAl-mww"
      }
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "ftYdPQgltvYk"
      },
      "source": [
        "MY_PLAYER_NUM = 0\n",
        "\n",
        "def my_AI(state):\n",
        "  return random_action(state),0"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "source": [
        "**ランダムAIとの勝率チェック**\n"
      ],
      "metadata": {
        "id": "4AAzP2yVF8PJ"
      }
    },
    {
      "cell_type": "code",
      "source": [
        "# パラメータ\n",
        "EP_GAME_COUNT = 1000  # 1評価あたりのゲーム数\n",
        "\n",
        "def player_point(ended_state):\n",
        "    if ended_state.turn_player == MY_PLAYER_NUM:\n",
        "        return 1\n",
        "    return 0\n",
        "\n",
        "def play(next_actions):\n",
        "    state = State()\n",
        "    while True:\n",
        "        if state.is_done():\n",
        "            break\n",
        "        pass_flag=0\n",
        "        if state.turn_player == MY_PLAYER_NUM:\n",
        "            action,pass_flag = my_AI(state)\n",
        "        else:\n",
        "            action = random_action(state)\n",
        "        # 次の状態の取得\n",
        "        if pass_flag == 1:\n",
        "            state = state.next(action,pass_flag)\n",
        "        else:\n",
        "            state = state.next(action)\n",
        "    return player_point(state)\n",
        "\n",
        "# 任意のアルゴリズムの評価\n",
        "def evaluate_algorithm_of(label, next_actions):\n",
        "    # 複数回の対戦を繰り返す\n",
        "    total_point = 0\n",
        "    for i in range(EP_GAME_COUNT):\n",
        "        total_point += play(next_actions)\n",
        "        print('\\rEvaluate {}/{}'.format(i + 1, EP_GAME_COUNT), end='')\n",
        "    print('')\n",
        "\n",
        "    # 平均ポイントの計算\n",
        "    average_point = total_point / EP_GAME_COUNT\n",
        "    print(label.format(average_point))\n",
        "\n",
        "# VSランダム\n",
        "next_actions = (random_action, random_action)\n",
        "evaluate_algorithm_of('VS_Random {:.3f}', next_actions)"
      ],
      "metadata": {
        "id": "nhqO3oWYSmY8"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "source": [
        "# ランダムAIと対戦\n",
        "state = State()\n",
        "turn = 0\n",
        "\n",
        "print(\"----------- ゲーム開始 -----------\\nmy_AI :プレイヤー\"+str(MY_PLAYER_NUM)+\"番\")\n",
        "\n",
        "# ゲーム終了までのループ\n",
        "while True:\n",
        "    turn += 1\n",
        "    num = state.turn_player\n",
        "\n",
        "    # ゲーム終了時\n",
        "    if state.is_done():\n",
        "        print(\"------- ゲーム終了　ターン\",turn,\"-------\")\n",
        "        print(\"* 勝者 プレイヤー\"+str(num)+\"番\")\n",
        "        break;\n",
        "    else:\n",
        "        print(\"------------ ターン\",turn,\"------------\")\n",
        "\n",
        "    pass_flag = 0\n",
        "    # 行動の取得\n",
        "    if num == MY_PLAYER_NUM:\n",
        "        action,pass_flag = my_AI(state)\n",
        "        print(termcolor.colored(state, 'red'))\n",
        "    else:\n",
        "        action = random_action(state)\n",
        "        print(state)\n",
        "\n",
        "    print(\"出したカード\")\n",
        "    if state.my_actions() == [] or pass_flag == 1:\n",
        "        print(\"パス\")\n",
        "        if state.pass_count[num] >= 3:\n",
        "          print(\"\\n* プレイヤー\"+str(num)+\"番 バースト\")\n",
        "    else:\n",
        "        print(action)\n",
        "\n",
        "    # 次の状態の取得\n",
        "    if pass_flag == 1:\n",
        "        state = state.next(action,pass_flag)\n",
        "    else:\n",
        "        state = state.next(action)"
      ],
      "metadata": {
        "id": "CGbaK1GK9e9x"
      },
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "w9NrcC2eX2rz"
      },
      "source": [
        "### 1.手札に関する関数"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "sY71kXQxX2r0"
      },
      "source": [
        " #リストで手札を表示する\n",
        "state.my_hands()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "NPPVEELbX2r0"
      },
      "source": [
        "#リストで手札の数字を表示する\n",
        "state.my_hands().check_number()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "km52OeTSX2r0"
      },
      "source": [
        "#リストで手札のマークを表示する\n",
        "state.my_hands().check_suit()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "ZzK-zoa7X2r1"
      },
      "source": [
        "#リストで自分が出せるカードを表示する\n",
        "state.my_actions()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "-byPQ6tZX2r1"
      },
      "source": [
        "#リストで自分が出せるカードの数字を表示する\n",
        "Hand(state.my_actions()).check_number()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "cUciN2QWX2r1"
      },
      "source": [
        "#リストで自分が出せるカードの記号を表示する\n",
        "Hand(state.my_actions()).check_suit()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "q9izlUugX2r1"
      },
      "source": [
        "### 2.場の札に関する関数"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "0LQ91aJ5X2r1"
      },
      "source": [
        "#場のカードを表示する\n",
        "state.field_cards"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "dwoBNEeLX2r2"
      },
      "source": [
        "#場で出せるカードをリストで取得する\n",
        "state.legal_actions()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "EpvIoacAX2r2"
      },
      "source": [
        "#場で出せるカードの数字をリストで取得する\n",
        "Hand(state.legal_actions()).check_number()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "wfcqNxwgX2r2"
      },
      "source": [
        "#場で出せるカードの記号をリストで取得する\n",
        "Hand(state.legal_actions()).check_suit()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "ryk0xBKDX2r2"
      },
      "source": [
        " ### 3.状態に関する関数"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "sTKB-jhrX2r2"
      },
      "source": [
        "#今のプレイヤーの番号を表示する\n",
        "state.turn_player"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "ssOtTxgwX2r3"
      },
      "source": [
        "#3回パスをしてしまったプレイヤーを表示する\n",
        "state.out_player"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "GNGpCtcKX2r3"
      },
      "source": [
        "### 4.pythonプログラミングの基礎"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "qUkKLp7YX2r3"
      },
      "source": [
        "#### print"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "EzhNRJxxX2r3"
      },
      "source": [
        "何かを表示するときはprintというものを使います。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "7QmCTgKHX2r3"
      },
      "source": [
        "print(\"Hello World\")\n",
        "print(5)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "ynw4st_SX2r3"
      },
      "source": [
        "#### 計算式"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "HN3vwH0cX2r3"
      },
      "source": [
        "四則演算ができます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "DSp417xWX2r3"
      },
      "source": [
        "print(5+4)  #足し算\n",
        "print(5-4)  #引き算\n",
        "print(5*4)  #掛け算\n",
        "print(5/4)  #割り算\n",
        "print(5%4)  #割った余りを求める"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "kje5JkeXX2r4"
      },
      "source": [
        "#### 変数"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "gTubItztX2r4"
      },
      "source": [
        "数学の文字と同じで数字を代入することができます。文章も代入できます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "XZkFveThX2r4"
      },
      "source": [
        "a = 3\n",
        "b = 1+3  #計算式の形で代入ができます\n",
        "c = \"こんにちは\"  #文字列も代入できます\n",
        "aisatsu = \"こんばんは\"  #変数名は何文字でもいいです\n",
        "print(a)\n",
        "print(b)\n",
        "print(c)\n",
        "print(aisatsu)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "S2KVM9v3X2r4"
      },
      "source": [
        "#### リスト"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "w324hbHHX2r4"
      },
      "source": [
        "リストを使うとたくさんの数字や文字をまとめることができます。数学の添字と同じです。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "cpQ5cFotX2r4"
      },
      "source": [
        "l = [1,2,3,4,5]\n",
        "print(l[3])  #0番目から数えて3番目の要素を返します\n",
        "\n",
        "l.append(100)  #末尾に100を追加します\n",
        "print(l)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "DcPIw4roX2r4"
      },
      "source": [
        "#### if文"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "ZxEUKpMhX2r4"
      },
      "source": [
        "if文を使うことで条件分岐をすることができます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "r9QzETTlX2r4"
      },
      "source": [
        "a = int(input())  #変数に数字を代入するコード\n",
        "\n",
        "#:とインデントを忘れないようにしてください\n",
        "if(a>50):\n",
        "    print(\"50より大きいです\")\n",
        "else:\n",
        "    print(\"50より小さいです\")"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "OCyEEe9xX2r5"
      },
      "source": [
        "#### for文"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "lcOTyZX6X2r5"
      },
      "source": [
        "for文を使うことで繰り返し処理をすることができます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "M6dvYG3mX2r5"
      },
      "source": [
        "#:とインデントを忘れないようにしてください。\n",
        "for i in range(5):\n",
        "    print(\"Hello World.\")"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "pSKzbfeDX2r5"
      },
      "source": [
        "こんな使い方もあります。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "-Kt-d6BNX2r5"
      },
      "source": [
        "for item in [\"Apple\", \"Orange\", \"Banana\", \"Melon\"]:\n",
        "    print(item)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "jpC0h8JmX2r5"
      },
      "source": [
        "#### 関数"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "GUxqtfZUX2r5"
      },
      "source": [
        "関数というものを使うと何度も使う機能を少ないコーディングで書くことができます。数学の関数と同じで値を入力すると値を計算して返します。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "nt3iJQACX2r5"
      },
      "source": [
        "#:とインデントを忘れないようにしてください。\n",
        "#引数を3乗する関数\n",
        "def testfunc(hikisu):\n",
        "    cube = hikisu*hikisu*hikisu\n",
        "    return cube"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "getuqW56X2r6"
      },
      "source": [
        "print(testfunc(3))"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "-BCcjsiGX2r6"
      },
      "source": [
        "### 4.便利な関数"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "a0UjdWi1X2r6"
      },
      "source": [
        "#リストを定義する\n",
        "l = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "iBQ9yH2rX2r6"
      },
      "source": [
        "#最大値を求める関数\n",
        "max(l)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "VKZq8YHkX2r6"
      },
      "source": [
        "#最小値を求める関数\n",
        "min(l)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "Ge3cdmT-X2r7"
      },
      "source": [
        "#昇順に並び替える関数\n",
        "sorted(l)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "TQi9dmeBX2r8"
      },
      "source": [
        "#降順に並び替えるときはreverse = Trueをつける\n",
        "sorted(l, reverse = True)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "PwSNMFzSX2r8"
      },
      "source": [
        "#7からの距離を求める関数\n",
        "def DistFrom7(num):\n",
        "    return abs(num-7)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "KJb5gcpdX2r8"
      },
      "source": [
        "#keyを使うと7からの距離で最大最小並び替えができる\n",
        "print(max(l, key = DistFrom7))\n",
        "print(min(l, key = DistFrom7))\n",
        "print(sorted(l, key = DistFrom7))"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "ukxPmT0dX2r8"
      },
      "source": [
        "#使用例\n",
        "#手札を7から近い順に並び替える\n",
        "def DistFrom7(hand):\n",
        "    return abs(hand.number.val-7)\n",
        "\n",
        "\n",
        "hands_sorted = sorted(state.my_hands(), key = DistFrom7, reverse = False)\n",
        "print(state.my_hands())\n",
        "print(hands_sorted)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "0PbemkfyX2r8"
      },
      "source": [
        "### 5.Classの説明\n",
        "この7ならべプログラムではclassと呼ばれる概念が使われています。classを使うと「もの」をわかりやすく記述することができます。"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "YHlJBaWIX2r8"
      },
      "source": [
        "たとえば、身長と好きな色がある「人」というクラスを作ってみます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "jiTCXnBEX2r8"
      },
      "source": [
        "class person:\n",
        "    height = 0\n",
        "    favcolor = \"hoge\""
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "DU5mD7SJX2r8"
      },
      "source": [
        "これで「人」が定義できました。それでは田中さんを作ってみます。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "XiWasNZyX2r9"
      },
      "source": [
        "tanaka = person()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "Jehdq2A6X2r9"
      },
      "source": [
        "tanaka.heightとすると身長が、tanaka.colorとすると好きな色が表示できます。しかし田中さんの身長と好きな色はまだ初期のままです。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "TRDlrcNXX2r9"
      },
      "source": [
        "print(tanaka.height)\n",
        "print(tanaka.favcolor)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "VsiwmnxaX2r9"
      },
      "source": [
        "田中さんの身長と好きな色を代入してみましょう"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "MQjKnFuIX2r9"
      },
      "source": [
        "tanaka.height=150\n",
        "tanaka.favcolor=\"blue\""
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "_9V3EjCQX2r9"
      },
      "source": [
        "print(tanaka.height)\n",
        "print(tanaka.favcolor)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "HTxblvHPX2r9"
      },
      "source": [
        "classの中には関数を入れることもできます。ためしに身長と好きな色を表示する関数を作ってみます。<br>関数内で変数を扱うときは「そのクラス自身の変数」であることをいうためにself.heightのようにします。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "vtzhIwk4X2r9"
      },
      "source": [
        "class person:\n",
        "    height = 0\n",
        "    favcolor = \"hoge\"\n",
        "\n",
        "    def explain(self):\n",
        "        print(\"身長は\"+str(self.height)+\"、好きな色は\"+self.favcolor)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "FUVRKyNyX2r9"
      },
      "source": [
        "okada = person()\n",
        "okada.height = 160\n",
        "okada.favcolor = \"pink\""
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "Y7azgKzlX2r9"
      },
      "source": [
        "okada.explain()"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "ZsP9BlsUX2r-"
      },
      "source": [
        "\\_\\_init\\_\\_という関数はclassを代入したときに自動的に動く関数です。これを使うと最初に変数を代入するときなどに便利です。"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "Kt3zKYhpX2r-"
      },
      "source": [
        "class person:\n",
        "    def __init__(self, height, favcolor):\n",
        "        self.height = height\n",
        "        self.favcolor = favcolor\n",
        "\n",
        "    def explain(self):\n",
        "        print(\"身長は\"+str(self.height)+\"、色は\"+self.favcolor)"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "kaWdJCB5X2r-"
      },
      "source": [
        "suzuki = person(170, \"yellow\")"
      ],
      "execution_count": null,
      "outputs": []
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "H9abIYEYX2r-"
      },
      "source": [
        "suzuki.explain()"
      ],
      "execution_count": null,
      "outputs": []
    }
  ]
}