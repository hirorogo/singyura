import sys
import random
import time
from main import State, HybridStrongestAI, random_action

MY_PLAYER_NUM = 0
GAMES = 100
SIMULATION_COUNT = 300  # フルパワー版

def play_one_game():
    """1ゲームをプレイ"""
    state = State(players_num=3)
    ai = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)
    
    while not state.is_done():
        if state.turn_player == MY_PLAYER_NUM:
            action, pass_flag = ai.get_action(state)
        else:
            action = random_action(state)
            pass_flag = 0 if action else 1
        state.next(action, pass_flag)
    
    # 勝者判定
    for i, hand in enumerate(state.players_cards):
        if len(hand) == 0 and i not in state.out_player:
            return 1 if i == MY_PLAYER_NUM else 0
    return 0

print(f"=== フルベンチマーク開始 ===")
print(f"ゲーム数: {GAMES}")
print(f"シミュレーション回数: {SIMULATION_COUNT}")
print()

start = time.time()
wins = 0
for i in range(GAMES):
    if (i + 1) % 10 == 0:
        print(f'Progress: {i+1}/{GAMES} (現在の勝率: {wins/(i+1)*100:.1f}%)', end='\r')
    wins += play_one_game()

elapsed = time.time() - start

print(f'\n\n=== 最終結果 ===')
print(f"勝利数: {wins}/{GAMES}")
print(f"勝率: {wins/GAMES*100:.1f}%")
print(f"実行時間: {elapsed:.1f}秒")
print(f"平均: {elapsed/GAMES:.2f}秒/ゲーム")
