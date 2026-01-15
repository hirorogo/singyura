
import time
from main import State, HybridStrongestAI, MY_PLAYER_NUM

def run_benchmark(game_count=100):
    wins = [0] * 3
    ai_pos = 0 # AI is Player 0
    
    # Initialize AI
    # Simulation count 100 for better accuracy during benchmark
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=50)

    start_time = time.time()
    
    for i in range(game_count):
        state = State()
        # Randomize start player? State() logic determines start player by Diamond 7.
        # But players_cards are shuffled in State().
        
        while not state.is_done():
            current_player = state.turn_player
            
            if current_player == ai_pos:
                action, pass_flag = my_ai.get_action(state)
            else:
                action = RandomAI(state)
                pass_flag = 0
                if action is None:
                    pass_flag = 1 # Force pass if no action returned
            
            state.next(action, pass_flag)

        # Determine winner
        winner = -1
        # 1. Check for empty hand
        for p, hand in enumerate(state.players_cards):
             if len(hand) == 0 and p not in state.out_player:
                 winner = p
                 break
        
        # 2. If no empty hand (all burst except one), find survivor
        if winner == -1:
            survivors = [p for p in range(state.players_num) if p not in state.out_player]
            if len(survivors) == 1:
                winner = survivors[0]
        
        if winner != -1:
            wins[winner] += 1
            
        if (i + 1) % 10 == 0:
            print(f"Game {i + 1}/{game_count} finished. Current Stats: {wins}")

    end_time = time.time()
    duration = end_time - start_time
    
    print("="*30)
    print(f"Benchmark Result ({game_count} games)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    print(f"AI Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    print(f"Other Players: {wins}")
    print("="*30)

if __name__ == "__main__":
    # We need to expose RandomAI or helper from main.py if not available
    # Actually main.py has random_action function, not class.
    
    # Let's fix the import by monkey-patching or just redefining helper here to be safe
    import random
    
    def RandomAI(state):
        my_actions = state.my_actions()
        if my_actions:
            return random.choice(my_actions)
        else:
            return None

    run_benchmark(100)
