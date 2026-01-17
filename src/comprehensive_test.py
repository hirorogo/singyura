"""
包括的テスト - より多くのゲームで統計的に有意な結果を得る
"""
import time
import random

from main_improved import State, ImprovedHybridAI, random_action

def run_comprehensive_test(simulation_count, game_count=100, seed=None):
    """包括的なテスト"""
    
    if seed is not None:
        random.seed(seed)
    
    wins = [0] * 3
    ai_pos = 0
    
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=simulation_count)
    
    start_time = time.time()
    
    for i in range(game_count):
        state = State()
        
        while not state.is_done():
            current_player = state.turn_player
            
            if current_player == ai_pos:
                action, pass_flag = my_ai.get_action(state)
            else:
                action = random_action(state)
                pass_flag = 0
                if action is None:
                    pass_flag = 1
            
            state.next(action, pass_flag)

        winner = -1
        for p, hand in enumerate(state.players_cards):
            if len(hand) == 0 and p not in state.out_player:
                winner = p
                break
        
        if winner == -1:
            survivors = [p for p in range(state.players_num) if p not in state.out_player]
            if len(survivors) == 1:
                winner = survivors[0]

        if winner != -1:
            wins[winner] += 1

    end_time = time.time()
    duration = end_time - start_time
    
    win_rate = wins[ai_pos] / game_count
    time_per_game = duration / game_count
    
    return win_rate, time_per_game, wins

# 異なるシード値で複数回テスト
print("="*70)
print("包括的テスト - 複数のシードで評価")
print("="*70)

test_configs = [
    (200, "従来版"),
    (500, "改善版"),
]

for sim_count, label in test_configs:
    print(f"\n{label} (SIMULATION_COUNT={sim_count})")
    print("-"*70)
    
    all_win_rates = []
    all_times = []
    
    # 3つの異なるシードでテスト
    for seed_val in [42, 123, 456]:
        wr, tpg, wins = run_comprehensive_test(sim_count, 100, seed=seed_val)
        all_win_rates.append(wr)
        all_times.append(tpg)
        print(f"  Seed {seed_val}: 勝率{wr*100:.1f}%, 時間{tpg:.3f}秒/ゲーム")
    
    avg_wr = sum(all_win_rates) / len(all_win_rates)
    avg_time = sum(all_times) / len(all_times)
    
    print(f"\n  平均勝率: {avg_wr*100:.1f}%")
    print(f"  平均時間: {avg_time:.3f}秒/ゲーム")

print("\n" + "="*70)
print("結論")
print("="*70)
