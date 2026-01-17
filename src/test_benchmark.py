import time
import sys

from main_improved import State, ImprovedHybridAI, MY_PLAYER_NUM, random_action, SIMULATION_COUNT

def run_quick_benchmark(game_count=10):
    wins = [0] * 3
    ai_pos = 0  # AI is Player 0
    
    # Initialize AI
    my_ai = ImprovedHybridAI(my_player_num=ai_pos, simulation_count=SIMULATION_COUNT)
    
    print(f"Running quick benchmark with {game_count} games")
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
                    pass_flag = 1
            
            state.next(action, pass_flag)

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
            
        print(f"Game {i + 1}/{game_count} finished")

    end_time = time.time()
    duration = end_time - start_time
    
    print("="*50)
    print(f"Benchmark Result ({game_count} games)")
    print(f"Time: {duration:.2f} seconds ({duration/game_count:.2f} s/game)")
    print(f"AI Win Rate: {wins[ai_pos]}/{game_count} ({wins[ai_pos]/game_count*100:.1f}%)")
    print("="*50)
    
    return wins[ai_pos] / game_count, duration / game_count

if __name__ == "__main__":
    win_rate, time_per_game = run_quick_benchmark(10)
    print(f"\n勝率: {win_rate*100:.1f}%")
    print(f"1ゲームあたりの時間: {time_per_game:.2f}秒")
