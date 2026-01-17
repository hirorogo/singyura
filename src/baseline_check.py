"""
ベースライン確認 - 200回で本当に44%なのか？
"""
import random
import time

# Temporarily set SIMULATION_COUNT back to 200
import main_improved
main_improved.SIMULATION_COUNT = 200

from main_improved import State, ImprovedHybridAI, random_action

def check_baseline(game_count=200):
    """ベースライン性能を確認"""
    
    print("="*70)
    print("ベースライン確認 (SIMULATION_COUNT=200)")
    print("="*70)
    print(f"ゲーム数: {game_count}")
    print("="*70)
    
    results = []
    
    for seed_val in [42, 100, 200, 300, 500]:
        random.seed(seed_val)
        wins = [0] * 3
        my_ai = ImprovedHybridAI(my_player_num=0, simulation_count=200)
        
        for i in range(game_count):
            state = State()
            while not state.is_done():
                if state.turn_player == 0:
                    action, pass_flag = my_ai.get_action(state)
                else:
                    action = random_action(state)
                    pass_flag = 0 if action else 1
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
        
        wr = wins[0] / game_count
        results.append(wr)
        print(f"Seed {seed_val:3d}: 勝率{wr*100:5.1f}%")
    
    avg_wr = sum(results) / len(results)
    
    print("\n" + "="*70)
    print(f"ベースライン平均勝率 (200回): {avg_wr*100:.1f}%")
    print("="*70)
    
    return avg_wr

if __name__ == "__main__":
    baseline = check_baseline(200)
