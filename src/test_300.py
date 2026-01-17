import random
from main_improved import State, ImprovedHybridAI, random_action

def quick_test(sim_count, games=100):
    random.seed(42)
    wins = [0] * 3
    my_ai = ImprovedHybridAI(my_player_num=0, simulation_count=sim_count)
    
    for i in range(games):
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
    
    return wins[0] / games

print("Testing different SIMULATION_COUNT values (100 games, seed=42):")
for count in [200, 300, 400]:
    wr = quick_test(count, 100)
    print(f"  {count}: {wr*100:.1f}%")
