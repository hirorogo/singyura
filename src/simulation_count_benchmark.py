"""
シミュレーション回数の最適化ベンチマーク

異なるSIMULATION_COUNT値でベンチマークを実行し、
勝率と処理時間のトレードオフを評価する。
"""
import time
import sys
import importlib

def run_benchmark_with_count(simulation_count, game_count=30):
    """指定されたSIMULATION_COUNTでベンチマークを実行"""
    
    # main_improvedモジュールを動的にリロードしてSIMULATION_COUNTを変更
    import main_improved
    
    # SIMULATION_COUNTを上書き
    main_improved.SIMULATION_COUNT = simulation_count
    
    State = main_improved.State
    ImprovedHybridAI = main_improved.ImprovedHybridAI
    random_action = main_improved.random_action
    
    wins = [0] * 3
    ai_pos = 0  # AI is Player 0
    
    # Initialize AI with specified simulation count
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=simulation_count)
    
    print(f"\n{'='*60}")
    print(f"SIMULATION_COUNT: {simulation_count}")
    print(f"ゲーム数: {game_count}")
    print(f"{'='*60}")

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

        # Determine winner
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
            print(f"  {i + 1}ゲーム完了 - 現在の勝率: {current_wr:.1f}%")

    end_time = time.time()
    duration = end_time - start_time
    
    win_rate = wins[ai_pos] / game_count
    time_per_game = duration / game_count
    
    print(f"\n結果:")
    print(f"  勝率: {wins[ai_pos]}/{game_count} ({win_rate*100:.1f}%)")
    print(f"  合計時間: {duration:.2f}秒")
    print(f"  1ゲームあたりの時間: {time_per_game:.3f}秒")
    print(f"{'='*60}")
    
    return {
        'simulation_count': simulation_count,
        'win_rate': win_rate,
        'time_per_game': time_per_game,
        'total_time': duration,
        'wins': wins
    }

def main():
    """複数のSIMULATION_COUNT値でベンチマークを実行"""
    
    # テストするシミュレーション回数
    simulation_counts = [200, 300, 500, 1000]
    
    # ゲーム数（30ゲームで十分な統計を取る）
    game_count = 30
    
    print("="*60)
    print("シミュレーション回数最適化ベンチマーク")
    print("="*60)
    print(f"各設定で{game_count}ゲームを実行します")
    print("対戦相手: ランダムAI x 2")
    print("="*60)
    
    results = []
    
    for count in simulation_counts:
        result = run_benchmark_with_count(count, game_count)
        results.append(result)
        
        # 少し休憩
        time.sleep(1)
    
    # 結果のサマリー
    print("\n" + "="*60)
    print("総合結果")
    print("="*60)
    print(f"{'回数':<10} {'勝率':<10} {'時間/ゲーム':<15} {'効率スコア':<15}")
    print("-"*60)
    
    for r in results:
        # 効率スコア = 勝率 / (時間/ゲーム) - 勝率が高くて時間が短いほど良い
        efficiency = r['win_rate'] / r['time_per_game']
        print(f"{r['simulation_count']:<10} {r['win_rate']*100:<10.1f}% {r['time_per_game']:<15.3f}秒 {efficiency:<15.3f}")
    
    print("="*60)
    
    # 推奨値の提示
    best_win_rate = max(results, key=lambda x: x['win_rate'])
    best_efficiency = max(results, key=lambda x: x['win_rate'] / x['time_per_game'])
    
    print("\n推奨事項:")
    print(f"  最高勝率: SIMULATION_COUNT={best_win_rate['simulation_count']} (勝率{best_win_rate['win_rate']*100:.1f}%)")
    print(f"  最高効率: SIMULATION_COUNT={best_efficiency['simulation_count']} (効率スコア{best_efficiency['win_rate']/best_efficiency['time_per_game']:.3f})")
    
    # 時間制約を考慮した推奨
    print("\n時間制約別推奨:")
    for r in results:
        if r['time_per_game'] <= 0.5:
            constraint = "高速（<0.5秒/ゲーム）"
            print(f"  {constraint}: SIMULATION_COUNT={r['simulation_count']} (勝率{r['win_rate']*100:.1f}%, {r['time_per_game']:.3f}秒/ゲーム)")
            break
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
