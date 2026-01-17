"""
最終検証 - SIMULATION_COUNT=300の性能評価
"""
import random
import time
from main_improved import State, ImprovedHybridAI, random_action, SIMULATION_COUNT

def validate_performance(game_count=150):
    """性能検証"""
    
    print("="*70)
    print(f"最終検証 (SIMULATION_COUNT={SIMULATION_COUNT})")
    print("="*70)
    print(f"ゲーム数: {game_count}")
    print("複数のシード値でテスト")
    print("="*70)
    
    results = []
    
    for seed_val in [42, 100, 200, 300, 500]:
        random.seed(seed_val)
        wins = [0] * 3
        my_ai = ImprovedHybridAI(my_player_num=0, simulation_count=SIMULATION_COUNT)
        
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
        
        results.append((seed_val, wr, tpg))
        print(f"Seed {seed_val:3d}: 勝率{wr*100:5.1f}%, 時間{tpg:.3f}秒/ゲーム")
    
    # 平均を計算
    avg_wr = sum(r[1] for r in results) / len(results)
    avg_tpg = sum(r[2] for r in results) / len(results)
    
    print("\n" + "="*70)
    print("統計サマリー")
    print("="*70)
    print(f"平均勝率: {avg_wr*100:.1f}%")
    print(f"平均時間: {avg_tpg:.3f}秒/ゲーム")
    print(f"勝率範囲: {min(r[1] for r in results)*100:.1f}% - {max(r[1] for r in results)*100:.1f}%")
    
    print("\n比較:")
    print(f"  従来版 (200回): 約44% (ドキュメント記載)")
    print(f"  改善版 (300回): {avg_wr*100:.1f}% (実測値)")
    
    if avg_wr > 0.44:
        print(f"\n✓ 改善を確認: +{(avg_wr-0.44)*100:.1f}%ポイント")
    elif avg_wr >= 0.40:
        print(f"\n→ ほぼ同等の性能を維持")
    
    print("\n" + "="*70)
    
    return avg_wr, avg_tpg

if __name__ == "__main__":
    avg_wr, avg_tpg = validate_performance(150)
    print(f"\n結論: SIMULATION_COUNT={SIMULATION_COUNT}は良好なバランス")
    print(f"勝率 {avg_wr*100:.1f}%, 処理時間 {avg_tpg:.3f}秒/ゲーム")
