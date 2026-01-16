import time
from main import State, HybridStrongestAI, MY_PLAYER_NUM, random_action

def run_quick_test(game_count=10):
    wins = [0] * 3
    ai_pos = 0  # AI is Player 0
    
    # Initialize AI with LOW simulation count for faster testing
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=30)

    start_time = time.time()
    
    for i in range(game_count):
        print(f"Game {i + 1}/{game_count} started...")
        state = State()
        turn_count = 0
        
        while not state.is_done():
            turn_count += 1
            current_player = state.turn_player
            
            if current_player == ai_pos:
                action, pass_flag = my_ai.get_action(state)
                if turn_count % 25 == 0:
                    print(f"  Turn {turn_count}: AI still playing...")
            else:
                action = random_action(state)
                pass_flag = 0
                if action is None or isinstance(action, list):
                    pass_flag = 1
            
            state.next(action, pass_flag)
            
            # Safety: prevent infinite loops
            if turn_count > 200:
                print(f"  Game {i+1} timeout (200 turns)")
                break

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
            
        print(f"  Game {i + 1} finished. Winner: Player {winner}. Turns: {turn_count}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("="*50)
    print(f"Quick Test Result ({game_count} games)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    print(f"AI Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    
    win_percentages = [f"P{i}: {w}/{game_count} ({w/game_count*100:.1f}%)" for i, w in enumerate(wins)]
    print(f"Details: {', '.join(win_percentages)}")
    
    total_wins = sum(wins)
    draws = game_count - total_wins
    if draws > 0:
        print(f"Draws: {draws}/{game_count} ({draws/game_count*100:.1f}%)")
    print("="*50)

if __name__ == "__main__":
    run_quick_test(10)
