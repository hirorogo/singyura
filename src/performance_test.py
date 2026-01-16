#!/usr/bin/env python3
"""
パフォーマンス測定スクリプト

CPU/GPU、シミュレーション数の比較
"""
import time
import sys
from main import State, HybridStrongestAI, random_action, GPU_AVAILABLE, SIMULATION_COUNT

def quick_benchmark(ai_sim_count=50, game_count=10, show_progress=True):
    """
    クイックベンチマーク
    
    Args:
        ai_sim_count: AIのシミュレーション回数
        game_count: テストゲーム数
        show_progress: 進捗表示
    
    Returns:
        (win_rate, avg_time_per_game)
    """
    wins = 0
    ai_pos = 0
    
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=ai_sim_count)
    
    start_time = time.time()
    
    for i in range(game_count):
        state = State()
        
        while not state.is_done():
            current_player = state.turn_player
            
            if current_player == ai_pos:
                action, pass_flag = my_ai.get_action(state)
            else:
                action = random_action(state)
                pass_flag = 0 if action is not None else 1
            
            state.next(action, pass_flag)
        
        # 勝者判定
        for p, hand in enumerate(state.players_cards):
            if len(hand) == 0 and p not in state.out_player:
                if p == ai_pos:
                    wins += 1
                break
        
        if show_progress and (i + 1) % max(1, game_count // 10) == 0:
            elapsed = time.time() - start_time
            print(f"  {i + 1}/{game_count} games, {elapsed:.1f}s elapsed")
    
    total_time = time.time() - start_time
    win_rate = wins / game_count * 100
    avg_time = total_time / game_count
    
    return win_rate, avg_time

def main():
    print("=" * 60)
    print("七並べAI パフォーマンス測定")
    print("=" * 60)
    print(f"GPU: {'有効' if GPU_AVAILABLE else '無効'}")
    print(f"デフォルトシミュレーション数: {SIMULATION_COUNT}")
    print()
    
    # テスト設定
    test_configs = [
        (10, 10, "極軽量テスト"),
        (50, 10, "軽量テスト"),
        (100, 10, "標準テスト"),
        (200, 5, "高精度テスト（CPU）"),
    ]
    
    if GPU_AVAILABLE:
        test_configs.append((500, 5, "高精度テスト（GPU）"))
        test_configs.append((1000, 3, "最高精度テスト（GPU）"))
    
    results = []
    
    for sim_count, game_count, description in test_configs:
        print(f"\n{description}")
        print(f"シミュレーション数: {sim_count}, ゲーム数: {game_count}")
        print("-" * 60)
        
        win_rate, avg_time = quick_benchmark(sim_count, game_count, show_progress=True)
        
        results.append({
            'sim_count': sim_count,
            'game_count': game_count,
            'description': description,
            'win_rate': win_rate,
            'avg_time': avg_time
        })
        
        print(f"勝率: {win_rate:.1f}% ({win_rate * game_count / 100:.0f}/{game_count})")
        print(f"平均時間/ゲーム: {avg_time:.3f}s")
    
    # サマリー
    print("\n" + "=" * 60)
    print("結果サマリー")
    print("=" * 60)
    print(f"{'設定':<20} {'シミュレーション':<15} {'勝率':<10} {'時間/ゲーム':<15}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['description']:<20} {r['sim_count']:<15} {r['win_rate']:>6.1f}% {r['avg_time']:>12.3f}s")
    
    print("=" * 60)
    
    # 推奨設定
    print("\n推奨設定:")
    if GPU_AVAILABLE:
        print("  GPU有効: SIMULATION_COUNT=1000-2000 で最高精度")
    else:
        print("  CPU: SIMULATION_COUNT=200-500 でバランス")
        print("  リアルタイム対戦: SIMULATION_COUNT=50-100 で十分")

if __name__ == "__main__":
    main()
