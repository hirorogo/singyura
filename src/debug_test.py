from main import State, random_action

# Simple debug test
state = State()
print("Initial state after 7s placed:")
print(f"Field cards:\n{state.field_cards}")
print(f"Player 0 hand ({len(state.players_cards[0])} cards): {[str(c) for c in state.players_cards[0][:5]]}")
print(f"Player 1 hand ({len(state.players_cards[1])} cards): {[str(c) for c in state.players_cards[1][:5]]}")
print(f"Player 2 hand ({len(state.players_cards[2])} cards): {[str(c) for c in state.players_cards[2][:5]]}")

# Test legal actions
print(f"\nLegal actions: {[str(c) for c in state.legal_actions()]}")
print(f"Player {state.turn_player} can play: {[str(c) for c in state.my_actions()]}")

# Play a few turns
for turn in range(10):
    print(f"\n--- Turn {turn + 1}, Player {state.turn_player} ---")
    
    legal = state.my_actions()
    print(f"Legal moves: {[str(c) for c in legal]}")
    
    if legal:
        action = random_action(state)
        print(f"Playing: {action}")
        state.next(action, 0)
    else:
        print("No legal moves, passing")
        state.next(None, 1)
    
    print(f"Pass counts: {state.pass_count}")
    print(f"Out players: {state.out_player}")
    
    if state.is_done():
        print("\nGame ended!")
        break
