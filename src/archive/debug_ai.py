from main import State, HybridStrongestAI, random_action
import traceback

MY_PLAYER_NUM = 0
ai = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=10)

state = State(players_num=3)
turn = 0

print("=== AIデバッグ実行 ===")
while not state.is_done() and turn < 50:
    turn += 1
    print(f"\nTurn {turn}, Player {state.turn_player}")
    
    try:
        if state.turn_player == MY_PLAYER_NUM:
            my_actions = state.my_actions()
            print(f"  利用可能な手: {len(my_actions)}")
            if my_actions:
                print(f"  手の例: {my_actions[0]}")
            
            action, pass_flag = ai.get_action(state)
            print(f"  AIの選択: {action}, pass={pass_flag}")
        else:
            action = random_action(state)
            pass_flag = 0 if action else 1
            print(f"  ランダム選択: {action}, pass={pass_flag}")
        
        state.next(action, pass_flag)
    except Exception as e:
        print(f"エラー発生: {e}")
        traceback.print_exc()
        break

# 勝者判定
for i, hand in enumerate(state.players_cards):
    if len(hand) == 0 and i not in state.out_player:
        print(f"\n勝者: Player {i}")
        break
