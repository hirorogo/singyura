"""
改善の検証 - 500回のシミュレーションでベンチマーク
"""
import time
import random

# 固定シード
random.seed(42)

from main_improved import State, ImprovedHybridAI, random_action, SIMULATION_COUNT

def run_verification_benchmark(game_count=50):
    """改善後のベンチマーク"""
    
    wins = [0] * 3
    ai_pos = 0
    
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=SIMULATION_COUNT)
    
    print("="*70)
    print(f"改善版ベンチマーク（SIMULATION_COUNT={SIMULATION_COUNT}）")
    print("="*70)
    print(f"ゲーム数: {game_count}")
    print("対戦相手: ランダムAI x 2")
    print("="*70)

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
        
        if (i + 1) % 10 == 0:
            current_wr = wins[ai_pos] / (i + 1) * 100
            print(f"  {i+1}ゲーム完了 - 現在の勝率: {current_wr:.1f}%")

    end_time = time.time()
    duration = end_time - start_time
    
    win_rate = wins[ai_pos] / game_count
    time_per_game = duration / game_count
    
    print("\n" + "="*70)
    print("最終結果")
    print("="*70)
    print(f"SIMULATION_COUNT: {SIMULATION_COUNT}")
    print(f"勝率: {wins[ai_pos]}/{game_count} ({win_rate*100:.1f}%)")
    print(f"合計時間: {duration:.2f}秒")
    print(f"1ゲームあたりの時間: {time_per_game:.3f}秒")
    print("="*70)
    
    print("\n比較:")
    print(f"  従来版（200回）: 勝率44%, 時間0.02秒/ゲーム")
    print(f"  改善版（500回）: 勝率{win_rate*100:.1f}%, 時間{time_per_game:.3f}秒/ゲーム")
    
    if win_rate >= 0.44:
        improvement = (win_rate - 0.44) * 100
        print(f"\n✓ 勝率向上: +{improvement:.1f}%ポイント")
    
    print("\n" + "="*70)
    
    return win_rate, time_per_game

if __name__ == "__main__":
    run_verification_benchmark(50)
