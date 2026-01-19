#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプル版AIのベンチマーク

シンプル化したPIMC実装の性能を測定する。
目標: 44%程度の勝率を再現（オリジナル版と同等）
"""

import time
from main_simplified import State, ImprovedHybridAI, MY_PLAYER_NUM, random_action, SIMULATION_COUNT

def benchmark_simplified(num_games=100):
    """シンプル版AIのベンチマークを実行"""
    print("=" * 50)
    print("シンプル版のベンチマーク（ベースライン確立）")
    print("=" * 50)
    print(f"Running benchmark with {num_games} games")
    print(f"Simulation count: {SIMULATION_COUNT}")
    
    ai_instance = ImprovedHybridAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)
    
    wins = [0, 0, 0]
    start_time = time.time()
    
    for game_num in range(1, num_games + 1):
        state = State()
        
        while not state.is_done():
            current_player = state.turn_player
            
            if current_player == MY_PLAYER_NUM:
                action, pass_flag = ai_instance.get_action(state)
            else:
                action = random_action(state)
                pass_flag = 0 if action is not None else 1
            
            if pass_flag == 1 or action is None:
                state.next(None, 1)
            else:
                state.next(action, 0)
        
        # 勝者を判定
        winner = -1
        for i, hand in enumerate(state.players_cards):
            if len(hand) == 0 and i not in state.out_player:
                winner = i
                break
        
        if winner == -1:
            remaining = [i for i in range(state.players_num) if i not in state.out_player]
            if remaining:
                winner = remaining[0]
        
        if winner != -1:
            wins[winner] += 1
        
        if game_num % 10 == 0:
            print(f"Game {game_num}/{num_games} finished. Current Stats: {wins}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("=" * 50)
    print(f"Benchmark Result ({num_games} games)")
    print(f"Time: {total_time:.2f} seconds ({total_time/num_games:.2f} s/game)")
    print(f"AI Win Rate: {wins[MY_PLAYER_NUM]}/{num_games} ({wins[MY_PLAYER_NUM]/num_games*100:.1f}%)")
    print(f"Details: P0: {wins[0]}/{num_games} ({wins[0]/num_games*100:.1f}%), " + 
          f"P1: {wins[1]}/{num_games} ({wins[1]/num_games*100:.1f}%), " + 
          f"P2: {wins[2]}/{num_games} ({wins[2]/num_games*100:.1f}%)")
    print("=" * 50)
    print()
    print(f"最終勝率: {wins[MY_PLAYER_NUM]/num_games*100:.1f}%")
    print(f"目標勝率（ベースライン）: 44%")
    print(f"注：統計的分散が大きいため、より多くのゲーム（1000+）での測定を推奨")
    
    return wins[MY_PLAYER_NUM] / num_games

if __name__ == "__main__":
    win_rate = benchmark_simplified(100)
    
    if win_rate >= 0.44:
        print("\n✅ ベースライン達成！")
    elif win_rate >= 0.40:
        print("\n⚠️ ベースラインに近い（微調整が必要）")
    else:
        print("\n❌ ベースライン未達成（さらなる改善が必要）")
