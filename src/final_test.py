"""
最終テスト - より大きなサンプルサイズで安定した結果を得る
"""
import time
import random

# 固定シードを設定して再現性を確保
random.seed(42)

from main_improved import State, ImprovedHybridAI, random_action

def run_test(simulation_count, game_count=100):
    """指定されたSIMULATION_COUNTでテストを実行"""
    
    wins = [0] * 3
    ai_pos = 0
    
    # AIを指定されたシミュレーション回数で初期化
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=simulation_count)
    
    print(f"\nSIMULATION_COUNT={simulation_count}でテスト中（{game_count}ゲーム）...")

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
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}ゲーム完了...")

    end_time = time.time()
    duration = end_time - start_time
    
    win_rate = wins[ai_pos] / game_count
    time_per_game = duration / game_count
    
    print(f"完了: 勝率{win_rate*100:.1f}%, 時間{time_per_game:.3f}秒/ゲーム")
    
    return win_rate, time_per_game

# テスト実行
print("="*70)
print("シミュレーション回数の最適化テスト（100ゲーム）")
print("="*70)

test_counts = [200, 500, 800]

results = []
for count in test_counts:
    wr, tpg = run_test(count, 100)
    results.append((count, wr, tpg))

print("\n" + "="*70)
print("結果サマリー")
print("="*70)
print(f"{'回数':<15} {'勝率':<15} {'時間/ゲーム':<20}")
print("-"*70)

for count, wr, tpg in results:
    print(f"{count:<15} {wr*100:<15.1f}% {tpg:<20.3f}秒")

print("="*70)

# 現在のベースライン（200）と比較
baseline_wr = results[0][1]
print(f"\nベースライン勝率（200回）: {baseline_wr*100:.1f}%")
print("改善幅:")
for count, wr, tpg in results[1:]:
    diff = (wr - baseline_wr) * 100
    print(f"  {count}回: {diff:+.1f}% (時間: {tpg:.3f}秒/ゲーム)")
