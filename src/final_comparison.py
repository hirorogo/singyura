"""
最終比較 - 200 vs 300 vs 400
"""
import random
import time

def test_simulation_count(sim_count, game_count=100):
    """指定されたシミュレーション回数でテスト"""
    import main_improved
    main_improved.SIMULATION_COUNT = sim_count
    
    from main_improved import State, ImprovedHybridAI, random_action
    
    results = []
    
    for seed_val in [42, 100, 200, 300, 500]:
        random.seed(seed_val)
        wins = [0] * 3
        my_ai = ImprovedHybridAI(my_player_num=0, simulation_count=sim_count)
        
        start = time.time()
        
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
        
        duration = time.time() - start
        wr = wins[0] / game_count
        tpg = duration / game_count
        results.append((wr, tpg))
    
    avg_wr = sum(r[0] for r in results) / len(results)
    avg_tpg = sum(r[1] for r in results) / len(results)
    
    return avg_wr, avg_tpg

print("="*70)
print("最終比較テスト")
print("="*70)
print("各設定で5つの異なるシード、100ゲームずつテスト")
print("="*70)

configs = [200, 300, 400]
results = {}

for count in configs:
    print(f"\nSIMULATION_COUNT={count}をテスト中...")
    wr, tpg = test_simulation_count(count, 100)
    results[count] = (wr, tpg)
    print(f"  完了: 勝率{wr*100:.1f}%, 時間{tpg:.3f}秒/ゲーム")

print("\n" + "="*70)
print("最終結果")
print("="*70)
print(f"{'回数':<15} {'勝率':<15} {'時間/ゲーム':<20} {'改善率':<15}")
print("-"*70)

baseline_wr = results[200][0]

for count in configs:
    wr, tpg = results[count]
    improvement = (wr - baseline_wr) * 100
    print(f"{count:<15} {wr*100:<15.1f}% {tpg:<20.3f}秒 {improvement:+.1f}%")

print("="*70)

# 最適値を推奨
best_count = max(results.keys(), key=lambda k: results[k][0])
print(f"\n推奨: SIMULATION_COUNT={best_count}")
print(f"  勝率: {results[best_count][0]*100:.1f}%")
print(f"  時間: {results[best_count][1]:.3f}秒/ゲーム")
print(f"  改善: +{(results[best_count][0]-baseline_wr)*100:.1f}%ポイント")

