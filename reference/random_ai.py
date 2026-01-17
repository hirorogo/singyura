"""
ランダムAI実装
大会で提供された基本的なAI（ベンチマーク用）
"""

import random
from reference.base_game_engine import State


def random_action(state):
    """
    ランダムに行動を選択するAI
    
    Args:
        state: ゲームの状態
        
    Returns:
        Card: 出すカード（出せない場合は空リスト）
    """
    my_actions = state.my_actions()
    if my_actions != []:
        return my_actions[random.randint(0, len(my_actions) - 1)]
    else:
        return []


# 大会提出フォーマット用のサンプル
MY_PLAYER_NUM = 0


def my_AI(state):
    """
    大会提出用のAI関数のサンプル
    
    Args:
        state: ゲームの状態
        
    Returns:
        tuple: (出すカード, パスフラグ)
            - 出すカード: Cardオブジェクト
            - パスフラグ: 0 or 1 (1の場合は意図的なパス)
    """
    return random_action(state), 0
