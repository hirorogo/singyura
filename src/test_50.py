import time
from main import State, HybridStrongestAI, MY_PLAYER_NUM, random_action

def run_test(game_count=50):
    wins = [0] * 3
    ai_pos = 0
    
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=300)
    start_time = time.time()
    
    for i in range(game_count):
        if (i + 1) % 10 == 0:
            print(f"Game {i + 1}/{game_count}...")
        state = State()
        turn_count = 0
        
        while not state.is_done():
            turn_count += 1
            current_player = state.turn_player
            
            if current_player == ai_pos:
                action, pass_flag = my_ai.get_action(state)
            else:
                action = random_action(state)
                pass_flag = 0
                if action is None or isinstance(action, list):
                    pass_flag = 1
            
            state.next(action, pass_flag)
            
            if turn_count > 200:
                break

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
    
    print("="*50)
    print(f"Test Result ({game_count} games)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    print(f"AI Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    print(f"Details: P0: {wins[0]}, P1: {wins[1]}, P2: {wins[2]}")
    print("="*50)

if __name__ == "__main__":
    run_test(50)
