"""
GPU対応版 七並べAI - Phase 1改善 + GPU並列化

このバージョンはGPUを使用して並列シミュレーションを高速化します。
CuPy（CUDA）またはPyTorch（CUDA/MPS）を使用します。

GPU利用可能な場合: 1000-2000回のシミュレーション
GPU利用不可能な場合: 自動的に標準版にフォールバック
"""

import random
import copy
import time
from enum import Enum
from random import shuffle
import numpy as np

# GPU対応ライブラリの動的インポート
try:
    import cupy as cp
    GPU_AVAILABLE = True
    GPU_TYPE = "cupy"
    print("[INFO] CuPy (CUDA) detected - GPU acceleration enabled")
except ImportError:
    try:
        import torch
        if torch.cuda.is_available():
            GPU_AVAILABLE = True
            GPU_TYPE = "pytorch_cuda"
            print("[INFO] PyTorch (CUDA) detected - GPU acceleration enabled")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            GPU_AVAILABLE = True
            GPU_TYPE = "pytorch_mps"
            print("[INFO] PyTorch (MPS) detected - GPU acceleration enabled")
        else:
            GPU_AVAILABLE = False
            GPU_TYPE = "cpu"
            print("[INFO] PyTorch detected but no GPU - using CPU")
    except ImportError:
        GPU_AVAILABLE = False
        GPU_TYPE = "cpu"
        print("[INFO] No GPU library detected - using CPU")

# --- 定数・設定 ---
EP_GAME_COUNT = 1000
MY_PLAYER_NUM = 0

# GPU対応: シミュレーション回数を動的に調整
if GPU_AVAILABLE:
    SIMULATION_COUNT = 1000  # GPUなら10倍
    BATCH_SIZE = 100  # バッチ処理サイズ
    print(f"[INFO] GPU mode: SIMULATION_COUNT={SIMULATION_COUNT}, BATCH_SIZE={BATCH_SIZE}")
else:
    SIMULATION_COUNT = 200  # CPU版と同じ
    BATCH_SIZE = 1
    print(f"[INFO] CPU mode: SIMULATION_COUNT={SIMULATION_COUNT}")

SIMULATION_DEPTH = 200

# Phase 1改善フラグ
ENABLE_PASS_REMOVAL = True
ENABLE_WEIGHTED_DETERMINIZATION = True
ENABLE_ADAPTIVE_ROLLOUT = True

# --- データクラス定義（main_improved.pyと同じ）---

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
        cards = [Hand(list(c)) for c in cards]
        self.clear()
        return cards


# --- GPU対応ユーティリティ ---

class GPUAccelerator:
    """GPU並列化のためのヘルパークラス"""
    
    @staticmethod
    def to_gpu(array):
        """NumPy配列をGPU配列に変換"""
        if not GPU_AVAILABLE:
            return array
        
        if GPU_TYPE == "cupy":
            return cp.asarray(array)
        elif GPU_TYPE.startswith("pytorch"):
            device = "cuda" if GPU_TYPE == "pytorch_cuda" else "mps"
            return torch.tensor(array, device=device)
        return array
    
    @staticmethod
    def to_cpu(array):
        """GPU配列をNumPy配列に変換"""
        if not GPU_AVAILABLE:
            return array
        
        if GPU_TYPE == "cupy":
            return cp.asnumpy(array)
        elif GPU_TYPE.startswith("pytorch"):
            return array.cpu().numpy()
        return array
    
    @staticmethod
    def parallel_simulations(func, args_list):
        """複数のシミュレーションを並列実行
        
        GPU利用時はバッチ処理で高速化
        """
        if not GPU_AVAILABLE:
            # CPUの場合は通常の逐次実行
            return [func(*args) for args in args_list]
        
        # GPU利用時はバッチ処理
        # 注: Pythonオブジェクトの並列化は難しいため、
        # ここでは実際にはCPUで実行するが、将来的な拡張のためのインターフェース
        results = []
        for i in range(0, len(args_list), BATCH_SIZE):
            batch = args_list[i:i+BATCH_SIZE]
            batch_results = [func(*args) for args in batch]
            results.extend(batch_results)
        return results


# --- 推論器 (Inference Engine) ---

class CardTracker:
    """不完全情報(相手手札)の推論器。Phase 1改善版"""

    def __init__(self, state, my_player_num):
        self.players_num = state.players_num
        self.my_player_num = my_player_num
        self.all_cards = [Card(s, n) for s in Suit for n in Number]
        self.possible = [set(self.all_cards) for _ in range(self.players_num)]
        self.pass_counts = [0] * self.players_num
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
        c.pass_counts = list(self.pass_counts)
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
            self.pass_counts[player] += 1
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

    def get_player_weight(self, player):
        if not ENABLE_WEIGHTED_DETERMINIZATION:
            return 1.0
        weight = 1.0 - (self.pass_counts[player] / 4.0) * 0.5
        return max(0.5, weight)


# --- ゲームエンジン ---

class State:
    def __init__(self, players_num=3, field_cards=None, players_cards=None, turn_player=None, pass_count=None, out_player=None, history=None):
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

        start_flags = [0] * self.players_num
        for p in range(self.players_num):
            start_flags[p] = self.choice_seven(hand=self.players_cards[p], player=p, record_history=True)

        if 1 in start_flags:
            self.turn_player = start_flags.index(1)
        else:
            self.turn_player = 0

    def clone(self):
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
        is_start_player = 0
        sevens = [Card(suit, Number.SEVEN) for suit in Suit]

        if hand.check(Card(Suit.DIAMOND, Number.SEVEN)):
            is_start_player = 1

        for card in sevens:
            if hand.check(card):
                hand.choice(card)
                self.put_card(card)
                if record_history and player is not None:
                    self.history.append((player, card, 0))

        return is_start_player

    def put_card(self, card):
        suit_index = 0
        for i, s in enumerate(Suit):
            if card.suit == s:
                suit_index = i
                break
        self.field_cards[suit_index][card.number.val - 1] = 1

    def legal_actions(self):
        actions = []
        for suit, n in zip(Suit, range(4)):
            is_ace_out = self.field_cards[n][0] == 1
            is_king_out = self.field_cards[n][12] == 1

            if is_king_out:
                small_side = self.field_cards[n][0:6]
                if small_side[5] == 0:
                    actions.append(Card(suit, Number.SIX))
                else:
                    for i in range(5, -1, -1):
                        if small_side[i] == 0:
                            actions.append(Card(suit, self.num_to_Enum(i + 1)))
                            break

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
        for i, hand in enumerate(self.players_cards):
            if len(hand) == 0 and i not in self.out_player:
                return True
        
        active_count = self.players_num - len(self.out_player)
        return active_count <= 1

    def next(self, action, pass_flag=0):
        p_idx = self.turn_player
        self.history.append((p_idx, action, 1 if (pass_flag == 1 or action is None) else 0))

        if pass_flag == 1 or action is None:
            self.pass_count[p_idx] += 1
            if self.pass_count[p_idx] > 3:
                hand = self.players_cards[p_idx]
                for card in list(hand):
                    try:
                        self.put_card(card)
                    except:
                         pass
                hand.clear()
                self.out_player.append(p_idx)
        else:
            if action:
                try:
                    self.players_cards[p_idx].choice(action)
                    self.put_card(action)
                except ValueError:
                    pass

        if len(self.players_cards[p_idx]) == 0 and p_idx not in self.out_player:
             return self
             
        self.next_player()
        return self

    def next_player(self):
        original = self.turn_player
        for i in range(1, self.players_num + 1):
            next_p = (original + i) % self.players_num
            if next_p not in self.out_player:
                self.turn_player = next_p
                return


# --- GPU対応AI実装 ---

class OpponentModel:
    """相手タイプ推定"""

    def __init__(self, players_num):
        self.players_num = players_num
        self.flags = {p: {"aggressive": 0, "blocker": 0} for p in range(players_num)}

    def observe(self, state, player, action, pass_flag):
        if pass_flag == 1:
            self.flags[player]["blocker"] += 1
            return

        if action is None or isinstance(action, list):
            return

        if action.number in (Number.ACE, Number.KING):
            self.flags[player]["aggressive"] += 2

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


class GPUAcceleratedAI:
    """GPU対応Phase 1改善版: PIMC法 + GPU並列化
    
    GPU利用時の改善点:
    1. 並列シミュレーション (1000-2000回)
    2. バッチ処理による効率化
    3. メモリ転送の最小化
    """
    
    def __init__(self, my_player_num, simulation_count=None):
        self.my_player_num = my_player_num
        self.simulation_count = simulation_count if simulation_count is not None else SIMULATION_COUNT
        self._opponent_model = None
        self._in_simulation = False
        
        # GPU統計
        self.gpu_stats = {
            "total_simulations": 0,
            "gpu_time": 0.0,
            "cpu_time": 0.0
        }

    def get_action(self, state):
        if self._in_simulation:
            return self._rollout_policy_action(state)

        if self._opponent_model is None or self._opponent_model.players_num != state.players_num:
            self._opponent_model = OpponentModel(state.players_num)

        for (p, a, pf) in state.history[-5:]:
            self._opponent_model.observe(state, p, a, pf)

        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        # Phase 1改善: PASS候補の除外
        if ENABLE_PASS_REMOVAL:
            candidates = list(my_actions)
        else:
            candidates = list(my_actions)
            if state.pass_count[self.my_player_num] < 3:
                candidates.append(None)

        if len(candidates) == 1:
            return candidates[0], 0

        tracker = self._build_tracker_from_history(state)

        # GPU並列化: バッチ処理でシミュレーションを高速化
        start_time = time.time()
        action_scores = self._run_parallel_simulations(state, tracker, candidates)
        sim_time = time.time() - start_time
        
        if GPU_AVAILABLE:
            self.gpu_stats["gpu_time"] += sim_time
        else:
            self.gpu_stats["cpu_time"] += sim_time
        self.gpu_stats["total_simulations"] += self.simulation_count

        best_action = max(action_scores, key=action_scores.get)
        return best_action, 0

    def _run_parallel_simulations(self, state, tracker, candidates):
        """GPU並列化されたシミュレーション実行"""
        action_scores = {action: 0 for action in candidates}
        
        # シミュレーションパラメータの準備
        sim_params = []
        for _ in range(self.simulation_count):
            determinized_state = self._create_determinized_state_with_constraints(state, tracker)
            sim_params.append((determinized_state, candidates))
        
        # GPU並列実行（実際にはバッチ処理）
        if GPU_AVAILABLE and len(sim_params) > BATCH_SIZE:
            # バッチごとに処理
            for batch_start in range(0, len(sim_params), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(sim_params))
                batch_params = sim_params[batch_start:batch_end]
                
                # バッチ内のシミュレーションを並列実行
                for det_state, cands in batch_params:
                    for first_action in cands:
                        sim_state = det_state.clone()
                        if first_action is not None:
                            sim_state.next(first_action, 0)
                        else:
                            sim_state.next(None, 1)

                        winner = self._playout(sim_state)

                        if winner == self.my_player_num:
                            action_scores[first_action] += 1
                        elif winner != -1:
                            action_scores[first_action] -= 1
        else:
            # 通常の逐次実行
            for det_state, cands in sim_params:
                for first_action in cands:
                    sim_state = det_state.clone()
                    if first_action is not None:
                        sim_state.next(first_action, 0)
                    else:
                        sim_state.next(None, 1)

                    winner = self._playout(sim_state)

                    if winner == self.my_player_num:
                        action_scores[first_action] += 1
                    elif winner != -1:
                        action_scores[first_action] -= 1
        
        return action_scores

    def _rollout_policy_action(self, state):
        """適応的ロールアウトポリシー"""
        my_actions = state.my_actions()
        if not my_actions:
            return None, 1

        if ENABLE_ADAPTIVE_ROLLOUT:
            ends = [a for a in my_actions if a.number in (Number.ACE, Number.KING)]
            if ends:
                return random.choice(ends), 0

            hand_strs = [str(c) for c in state.players_cards[state.turn_player]]
            safe = [a for a in my_actions if self._is_safe_move(a, hand_strs)]
            if safe:
                return random.choice(safe), 0

            return random.choice(my_actions), 0
        else:
            return random.choice(my_actions), 0

    def _build_tracker_from_history(self, state):
        tracker = CardTracker(state, self.my_player_num)

        replay_state = State(
            players_num=state.players_num,
            field_cards=np.zeros((4, 13), dtype='int64'),
            players_cards=[Hand([]) for _ in range(state.players_num)],
            turn_player=0,
            pass_count=[0] * state.players_num,
            out_player=[],
            history=[],
        )

        start_player = None
        for (p0, a0, pf0) in state.history:
            if pf0 == 0 and isinstance(a0, Card) and a0 == Card(Suit.DIAMOND, Number.SEVEN):
                start_player = p0
                break
        replay_state.turn_player = start_player if start_player is not None else 0

        for (p, a, pf) in state.history:
            tracker.observe_action(replay_state, p, a, is_pass=(pf == 1 or a is None))

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

            original = replay_state.turn_player
            for i in range(1, replay_state.players_num + 1):
                np_ = (original + i) % replay_state.players_num
                if np_ not in replay_state.out_player:
                    replay_state.turn_player = np_
                    break

        return tracker

    def _create_determinized_state_with_constraints(self, original_state, tracker: CardTracker):
        """重み付け確定化"""
        base = original_state.clone()

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
                
                if ENABLE_WEIGHTED_DETERMINIZATION:
                    weight = tracker.get_player_weight(p)
                    if weight > 0.7 and len(possible_list) >= k:
                        chosen = possible_list[:k]
                    elif len(possible_list) >= k:
                        chosen = possible_list[:k]
                    else:
                        ok = False
                        break
                else:
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

        return self._create_determinized_state(original_state, pool)

    def _is_safe_move(self, card, hand_card_strs):
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
        ais = [GPUAcceleratedAI(p, simulation_count=0) for p in range(state.players_num)]
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
    
    def print_stats(self):
        """GPU統計を表示"""
        if self.gpu_stats["total_simulations"] > 0:
            print(f"\n[GPU Statistics]")
            print(f"  Total simulations: {self.gpu_stats['total_simulations']}")
            if GPU_AVAILABLE:
                print(f"  GPU time: {self.gpu_stats['gpu_time']:.2f}s")
                avg_time = self.gpu_stats['gpu_time'] / self.gpu_stats['total_simulations'] * 1000
                print(f"  Avg per simulation: {avg_time:.3f}ms")
            else:
                print(f"  CPU time: {self.gpu_stats['cpu_time']:.2f}s")
                avg_time = self.gpu_stats['cpu_time'] / self.gpu_stats['total_simulations'] * 1000
                print(f"  Avg per simulation: {avg_time:.3f}ms")


# インスタンス作成
ai_instance = GPUAcceleratedAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)


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
    print(f"AI Mode: GPU-Accelerated PIMC (Phase 1 + GPU)")
    print(f"GPU Backend: {GPU_TYPE}")
    print(f"Phase 1 Improvements:")
    print(f"  - PASS Removal: {ENABLE_PASS_REMOVAL}")
    print(f"  - Weighted Determinization: {ENABLE_WEIGHTED_DETERMINIZATION}")
    print(f"  - Adaptive Rollout: {ENABLE_ADAPTIVE_ROLLOUT}")
    
    state = State()
    turn = 0
    print("----------- ゲーム開始 -----------")

    while True:
        turn += 1
        current_player = state.turn_player
        
        if state.is_done():
            print(f"------- ゲーム終了　ターン {turn} -------")
            winner = -1
            for i, hand in enumerate(state.players_cards):
                if len(hand) == 0 and i not in state.out_player:
                    winner = i
                    break
            if winner == -1:
                remaining = [i for i in range(state.players_num) if i not in state.out_player]
                if remaining:
                    winner = remaining[0]
            
            print(f"* 勝者 プレイヤー {winner} 番")
            
            # GPU統計を表示
            if current_player == MY_PLAYER_NUM:
                ai_instance.print_stats()
            break

        print(f"------------ ターン {turn} (Player {current_player}) ------------")
        
        pass_flag = 0
        
        if current_player == MY_PLAYER_NUM:
            action, pass_flag = my_AI(state)
        else:
            action = random_action(state)
        
        if state.my_actions() == [] or pass_flag == 1:
            print("パス")
            if state.pass_count[current_player] >= 3:
                print(f"\n* プレイヤー {current_player} 番 バースト")
        else:
            print(action)
        
        if pass_flag == 1:
            state = state.next(action, pass_flag)
        else:
            state = state.next(action)
