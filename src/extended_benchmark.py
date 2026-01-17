"""
拡張ベンチマーク - より多くのゲームで正確な評価
"""
import time
import sys
import importlib

def run_benchmark_with_count(simulation_count, game_count=50):
    """指定されたSIMULATION_COUNTでベンチマークを実行"""
    
    # main_improvedモジュールを動的にリロード
    import main_improved
    main_improved.SIMULATION_COUNT = simulation_count
    
    State = main_improved.State
    ImprovedHybridAI = main_improved.ImprovedHybridAI
    random_action = main_improved.random_action
    
    wins = [0] * 3
    ai_pos = 0
    
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=simulation_count)
    
    print(f"\nSIMULATION_COUNT: {simulation_count} - {game_count}ゲーム実行中...")

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
    
    print(f"  完了: 勝率{win_rate*100:.1f}%, {time_per_game:.3f}秒/ゲーム")
    
    return {
        'simulation_count': simulation_count,
        'win_rate': win_rate,
        'time_per_game': time_per_game,
        'total_time': duration,
        'wins': wins
    }

def main():
    # より細かい間隔でテスト
    simulation_counts = [200, 400, 600, 800, 1000]
    game_count = 50
    
    print("="*60)
    print("拡張ベンチマーク - シミュレーション回数の最適化")
    print("="*60)
    print(f"各設定で{game_count}ゲームを実行")
    print("="*60)
    
    results = []
    
    for count in simulation_counts:
        result = run_benchmark_with_count(count, game_count)
        results.append(result)
        time.sleep(0.5)
    
    # 結果のサマリー
    print("\n" + "="*60)
    print("総合結果")
    print("="*60)
    print(f"{'回数':<10} {'勝率':<12} {'時間/ゲーム':<15} {'総時間':<12}")
    print("-"*60)
    
    for r in results:
        print(f"{r['simulation_count']:<10} {r['win_rate']*100:<12.1f}% {r['time_per_game']:<15.3f}秒 {r['total_time']:<12.1f}秒")
    
    print("="*60)
    
    # 最適値の分析
    best_win_rate = max(results, key=lambda x: x['win_rate'])
    
    print(f"\n最高勝率: SIMULATION_COUNT={best_win_rate['simulation_count']}")
    print(f"  勝率: {best_win_rate['win_rate']*100:.1f}%")
    print(f"  時間/ゲーム: {best_win_rate['time_per_game']:.3f}秒")
    
    # 勝率の改善を確認
    baseline = next((r for r in results if r['simulation_count'] == 200), None)
    if baseline:
        print(f"\nベースライン(200回)との比較:")
        for r in results:
            if r['simulation_count'] != 200:
                diff = (r['win_rate'] - baseline['win_rate']) * 100
                time_ratio = r['time_per_game'] / baseline['time_per_game']
                print(f"  {r['simulation_count']}回: 勝率{diff:+.1f}%, 時間x{time_ratio:.2f}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
