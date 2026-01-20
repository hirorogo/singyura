from main import State

state = State(players_num=3)

print("=== 初期状態 ===")
print(f"Turn player: {state.turn_player}")
print(f"Player 0 hand size: {len(state.players_cards[0])}")
print(f"Player 1 hand size: {len(state.players_cards[1])}")
print(f"Player 2 hand size: {len(state.players_cards[2])}")

print("\n=== Field cards (4x13) ===")
import numpy as np
for i, suit_name in enumerate(['♠', '♣', '♡', '♢']):
    row = state.field_cards[i]
    print(f"{suit_name}: {row}")

print("\n=== Legal actions ===")
legal = state.legal_actions()
print(f"Legal actions count: {len(legal)}")
if legal:
    print(f"Examples: {legal[:5]}")

# 各プレイヤーのmy_actions
for p in range(3):
    state.turn_player = p
    my_acts = state.my_actions()
    print(f"\nPlayer {p} my_actions: {len(my_acts)}")
    if my_acts:
        print(f"  Examples: {my_acts[:3]}")
