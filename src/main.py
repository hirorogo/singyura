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
SIMULATION_COUNT = 30 # 1手につき何回シミュレーションするか（多いほど強いが遅い）
SIMULATION_DEPTH = 100 # どこまで先読みするか

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

    def clone(self):
        """シミュレーション用に状態の深いコピーを作成"""
        # オブジェクトのディープコピーは重いので手動で行う
        new_players_cards = [Hand(list(h)) for h in self.players_cards]
        new_field_cards = self.field_cards.copy()
        new_pass_count = list(self.pass_count)
        new_out_player = list(self.out_player)
        
        return State(
            players_num=self.players_num,
            field_cards=new_field_cards,
            players_cards=new_players_cards,
            turn_player=self.turn_player,
            pass_count=new_pass_count,
            out_player=new_out_player
        )

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


# --- 最強AI実装 (Hybrid: Rule-Based + PIMC) ---

class HybridStrongestAI:
    def __init__(self, my_player_num, simulation_count=50):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count

    def get_action(self, state):
        my_actions = state.my_actions()
        
        # 選択肢がない場合（パス確定）
        if not my_actions:
            return None, 1
        
        # --- 戦略的フィルタリング (God-Lock) ---
        # 「安全な手（Safe）」と「危険な手（Risky）」に分類する
        # Safe: 出しても自分がその次のカード（内側への繋がり）を持っている。主導権を維持できる。
        # Risky: 出すと次のカードを持っていない。他プレイヤーに手番を渡す可能性がある（ロック解除）。
        
        safe_moves = []
        risky_moves = []
        
        hand_card_strs = [str(c) for c in state.players_cards[self.my_player_num]]
        
        for action in my_actions:
            if self._is_safe_move(action, hand_card_strs):
                safe_moves.append(action)
            else:
                risky_moves.append(action)
                
        # 候補手の決定
        candidates = []
        
        # 戦略： 安全な手があるなら、危険な手は考慮せず安全な手を優先（ロック維持）
        if safe_moves:
            candidates = safe_moves
            # 安全な手の中でも、より良いものをPIMCで選ぶ
            # (例: 他の人をより苦しめる方など。ただしSafeなら基本どれでもOKなので全候補でよい)
        else:
            # 安全な手がない場合、仕方なく危険な手を検討する
            candidates = risky_moves
            
            # 【重要】もしパスが可能なら、あえてパスをしてロックを維持する選択肢を追加
            if state.pass_count[self.my_player_num] < 3:
                candidates.append(None) # None はパスを表す

        # 唯一の候補なら即決 (パスのみ、あるいは1枚のみ)
        if len(candidates) == 1:
            if candidates[0] is None:
                return None, 1 # 戦略的パス
            return candidates[0], 0

        # --- PIMC (Perfect Information Monte Carlo) ---
        # 候補手の中からシミュレーションで最善手を選ぶ
        
        action_scores = {action: 0 for action in candidates}
        
        # 1. 未知のカードを特定
        unknown_cards = self._get_unknown_cards(state)
        
        # 2. シミュレーション実行
        for _ in range(self.simulation_count):
            # 決定化
            determinized_state = self._create_determinized_state(state, unknown_cards)
            
            for first_action in candidates:
                sim_state = determinized_state.clone()
                
                # 自分の一手
                if first_action is None:
                    # パスを行う
                    sim_state.next(None, 1)
                else:
                    sim_state.next(first_action, 0)
                
                # プレイアウト
                winner = self._playout(sim_state)
                
                if winner == self.my_player_num:
                    action_scores[first_action] += 1
                elif winner != -1: # 他のプレイヤーの勝ち
                    action_scores[first_action] -= 1
                    
        # スコア最大の行動を選択
        # None(パス)がキーに含まれる可能性があるので注意
        best_action = max(action_scores, key=action_scores.get)
        
        print(f"AI Thought: Safe={len(safe_moves)}, Candidates={[str(c) if c else 'PASS' for c in candidates]}")
        # print(f"Scores: { {str(k) if k else 'PASS': v for k, v in action_scores.items()} }")

        if best_action is None:
            return None, 1
        else:
            return best_action, 0

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
        elif val > 7:
            next_target_val = val + 1
            
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
        for _ in range(SIMULATION_DEPTH):
            if state.is_done():
                break
            p_idx = state.turn_player
            actions = state.my_actions()
            
            if not actions:
                state.next(None, 1)
            else:
                # プレイアウト中の他プレイヤーも、賢い動き（パスしない）をすると仮定
                # ここをランダムのままにするか、ルールベースを入れるかで強さが変わる
                # PIMCの標準では「相手も最適に行動する」が理想だが、重くなるのでランダムで妥協
                action = random.choice(actions)
                state.next(action, 0)
        
        # 勝者判定
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
            state.next(None, 1) # パス
        else:
            print(f"Player {current_player}: Play {action}")
            state.next(action, 0) # プレイ
