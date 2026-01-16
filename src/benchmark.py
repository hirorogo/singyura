import time
from main import State, HybridStrongestAI, MY_PLAYER_NUM, random_action, GPU_AVAILABLE, SIMULATION_COUNT

def run_benchmark(game_count=100):
    wins = [0] * 3
    ai_pos = 0 # AI is Player 0
    
    # Initialize AI
    # Use default SIMULATION_COUNT which adapts to GPU availability
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=SIMULATION_COUNT)
    
    print(f"Running benchmark with {game_count} games")
    print(f"GPU: {'Enabled' if GPU_AVAILABLE else 'Disabled'}")
    print(f"Simulation count: {SIMULATION_COUNT}")

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
                    pass_flag = 1 # Force pass if no action returned
            
            state.next(action, pass_flag)

        # Determine winner
        winner = -1
        # 1. Check for empty hand AND valid player (not burst)
        for p, hand in enumerate(state.players_cards):
             if len(hand) == 0 and p not in state.out_player:
                 winner = p
                 break
        
        # 2. If no empty hand (all burst except one), find survivor
        if winner == -1:
            survivors = [p for p in range(state.players_num) if p not in state.out_player]
            if len(survivors) == 1:
                winner = survivors[0]
            # If multiple survivors exist, game shouldn't have ended unless one has empty hand (covered above).
            # But wait, is_done() returns True if ANYONE has empty hand.
            # If a player bursts, their hand becomes empty. 
            # We need to distinguish between empty hand due to winning vs bursting.
            # In State.next(), when burst happens, hand.clear() is called.
            # So len(hand) == 0 is true for burst players too.
            # Handled by `p not in state.out_player` check above.

            elif len(survivors) == 0:
                # All players burst - DRAW
                pass

        if winner != -1:
            wins[winner] += 1
        else:
             survivors = [p for p in range(state.players_num) if p not in state.out_player]
             if len(survivors) > 1:
                 # This case "No winner found but survivors exist" happens if is_done() returns True
                 # BUT no one has strictly won and more than 1 are active.
                 # Why would is_done() return true?
                 # Only if:
                 # 1. Someone has empty hand (could be a burst player if not carefully checked)
                 # 2. active_count <= 1
                 
                 # Let's debug specifically which condition triggered end
                 empty_hands = [p for p, h in enumerate(state.players_cards) if len(h) == 0]
                 # print(f"DEBUG: Game End. Survivors: {survivors}, EmptyHands: {empty_hands}, Out: {state.out_player}")
                 pass
            
        if (i + 1) % 10 == 0:
            print(f"Game {i + 1}/{game_count} finished. Current Stats: {wins}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("="*30)
    print(f"Benchmark Result ({game_count} games)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    # AI is Player 0
    print(f"AI Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    
    # Calculate win rates for each player
    win_percentages = [f"P{i}: {w}/{game_count} ({w/game_count*100:.1f}%)" for i, w in enumerate(wins)]
    
    # If the sum of wins < game_count, some games ended in a draw (everyone burst)
    total_wins = sum(wins)
    draws = game_count - total_wins
    
    print(f"Details: {', '.join(win_percentages)}")
    if draws > 0:
        print(f"Draws (All Burst): {draws}/{game_count} ({draws/game_count*100:.1f}%)")
        
    print("="*30)

if __name__ == "__main__":
    run_benchmark(100)
