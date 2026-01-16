import time
from main import State, HybridStrongestAI, MY_PLAYER_NUM, random_action

def run_test(game_count=20):
    wins = [0] * 3
    ai_pos = 0
    
    # Use the configured SIMULATION_COUNT from main.py (1000)
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=1000)
    start_time = time.time()
    
    for i in range(game_count):
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
                print(f"  Timeout at turn {turn_count}")
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
            
        print(f"  Winner: Player {winner}, Turns: {turn_count}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("="*60)
    print(f"FINAL TEST RESULT ({game_count} games, 1000 simulations/move)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    print(f"AI (Player 0) Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    print(f"Details: P0={wins[0]} wins, P1={wins[1]} wins, P2={wins[2]} wins")
    total_wins = sum(wins)
    draws = game_count - total_wins
    if draws > 0:
        print(f"Draws: {draws}")
    print("="*60)

if __name__ == "__main__":
    run_test(20)
