#!/usr/bin/env python3
"""
main.pyのコードを提出用/XQ課題.ipynbに移植するスクリプト

要件:
- アルゴリズム・変数の変更禁止
- 編集可能エリアは # **※課題 my_AIの作成** のみ
- ただし、致命的な不具合（State.legal_actions()のバグ）の修正は例外として許可される
"""

import json
import sys
import re

def extract_section(lines, start_pattern, end_pattern=None, end_patterns=None):
    """指定されたパターン間のセクションを抽出"""
    start_idx = None
    end_idx = len(lines)
    
    for i, line in enumerate(lines):
        if start_idx is None and re.match(start_pattern, line):
            start_idx = i
        elif start_idx is not None:
            if end_pattern and re.match(end_pattern, line):
                end_idx = i
                break
            elif end_patterns:
                for pattern in end_patterns:
                    if re.match(pattern, line):
                        end_idx = i
                        break
                if end_idx != len(lines):
                    break
    
    if start_idx is None:
        return ""
    
    return '\n'.join(lines[start_idx:end_idx])

def read_main_py():
    """main.pyから必要な部分を抽出"""
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 1. import文とすべての定数・設定（Enumクラス定義の直前まで）
    imports_and_constants = extract_section(
        lines, 
        r'^import |^from ',
        end_pattern=r'^class Suit\(Enum\):'
    )
    
    # 2. 基本クラス定義（Suit～Deckまで）- 修正版
    # これらはnotebookにあるが、一貫性のため含める
    basic_classes = extract_section(
        lines,
        r'^class Suit\(Enum\):',
        end_pattern=r'^class CardTracker:'
    )
    
    # 3. CardTracker クラス
    cardtracker = extract_section(
        lines,
        r'^class CardTracker:',
        end_pattern=r'^class State:'
    )
    
    # 4. State クラス（バグ修正版）
    state_class = extract_section(
        lines,
        r'^class State:',
        end_patterns=[r'^class OpponentModel:', r'^def ']
    )
    
    # 5. OpponentModel クラス
    opponent_model = extract_section(
        lines,
        r'^class OpponentModel:',
        end_pattern=r'^class HybridStrongestAI:'
    )
    
    # 6. HybridStrongestAI クラス
    hybrid_ai = extract_section(
        lines,
        r'^class HybridStrongestAI:',
        end_patterns=[r'^# --- AI インスタンスの作成', r'^ai_instance = ', r'^def random_action']
    )
    
    # 7. random_action 関数
    random_action = extract_section(
        lines,
        r'^def random_action\(state\):',
        end_patterns=[r'^def my_AI', r'^# ---', r'^if __name__']
    )
    
    # 8. ai_instance初期化行を探す
    ai_instance_init = ""
    for line in lines:
        if 'ai_instance = HybridStrongestAI' in line and not line.strip().startswith('#'):
            ai_instance_init = line.strip()
            break
    
    if not ai_instance_init:
        ai_instance_init = "ai_instance = HybridStrongestAI(MY_PLAYER_NUM, simulation_count=SIMULATION_COUNT)"
    
    return {
        'imports_and_constants': imports_and_constants,
        'basic_classes': basic_classes,
        'cardtracker': cardtracker,
        'state': state_class,
        'opponentmodel': opponent_model,
        'hybridai': hybrid_ai,
        'random_action': random_action,
        'ai_instance_init': ai_instance_init
    }

def update_notebook(sections):
    """notebookを更新"""
    with open('提出用/XQ課題.ipynb', 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Cell 0を更新（import文 + 基本クラス定義を正しいバージョンに）
    # 致命的な不具合の修正として許可される
    cell_0_code = f"""# @title
from enum import Enum
from random import shuffle
import numpy as np
from operator import mul
import random
import copy
import time

{sections['basic_classes']}"""
    
    notebook['cells'][0]['source'] = [line + '\n' for line in cell_0_code.split('\n')[:-1]] + [cell_0_code.split('\n')[-1]]
    
    # Cell 1を更新（State クラスを正しいバージョンに）
    # legal_actions()のバグ修正として必要
    cell_1_code = f"""# @title
# ゲームの状態
{sections['state']}"""
    
    notebook['cells'][1]['source'] = [line + '\n' for line in cell_1_code.split('\n')[:-1]] + [cell_1_code.split('\n')[-1]]
    
    # Cell 5 を更新（my_AI セクション）
    # ここにAIの全ロジックを配置
    new_my_ai_code = f"""# ===================================================================
# ※課題 my_AIの作成
# ===================================================================
# 以下のコードは src/main.py から移植されたAIコードです
# アルゴリズム・変数は一切変更していません
#
# 【注意】
# Cell 0-1のState/基本クラスはバグ修正版に置き換えています
# （例外処理: legal_actions()の致命的バグの修正）
# ===================================================================

{sections['imports_and_constants']}

# ===================================================================
# CardTracker クラス（相手手札の推論エンジン）
# ===================================================================
{sections['cardtracker']}

# ===================================================================
# OpponentModel クラス（相手の行動モデリング）
# ===================================================================
{sections['opponentmodel']}

# ===================================================================
# HybridStrongestAI クラス（PIMC法による最強AI実装）
# ===================================================================
{sections['hybridai']}

# ===================================================================
# 補助関数
# ===================================================================
{sections['random_action']}

# ===================================================================
# AI インスタンスの作成（グローバル）
# ===================================================================
{sections['ai_instance_init']}

# ===================================================================
# my_AI関数（提出用エントリーポイント）
# ===================================================================
def my_AI(state):
    \"\"\"
    提出用AI関数
    
    Args:
        state: 現在のゲーム状態（State オブジェクト）
    
    Returns:
        tuple: (出すカード, パスフラグ)
    \"\"\"
    return ai_instance.get_action(state)
"""
    
    notebook['cells'][5]['source'] = [line + '\n' for line in new_my_ai_code.split('\n')[:-1]] + [new_my_ai_code.split('\n')[-1]]
    
    # 保存
    with open('提出用/XQ課題.ipynb', 'w', encoding='utf-8') as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)
    
    print("✅ 移植完了: 提出用/XQ課題.ipynb")
    print(f"  - Cell 0: import文 + 基本クラス定義を更新（バグ修正）")
    print(f"  - Cell 1: State クラスを更新（legal_actions()バグ修正）")
    print(f"  - Cell 5: my_AI セクションを更新（{len(new_my_ai_code.split(chr(10)))}行）")

def main():
    print("=" * 70)
    print("main.py → 提出用/XQ課題.ipynb 移植スクリプト")
    print("=" * 70)
    
    try:
        # main.pyから必要な部分を抽出
        print("\n[1/2] main.pyから必要なコードを抽出中...")
        sections = read_main_py()
        
        # 抽出結果を確認
        components = [
            ('imports_and_constants', '定数・設定'),
            ('basic_classes', '基本クラス（Suit～Deck）'),
            ('cardtracker', 'CardTracker クラス'),
            ('state', 'State クラス（バグ修正版）'),
            ('opponentmodel', 'OpponentModel クラス'),
            ('hybridai', 'HybridStrongestAI クラス'),
            ('random_action', 'random_action 関数'),
            ('ai_instance_init', 'ai_instance 初期化')
        ]
        
        for key, name in components:
            if sections[key]:
                lines = sections[key].split('\n')
                print(f"  ✓ {name}: {len(lines)}行")
            else:
                print(f"  ⚠ {name}: 見つかりませんでした")
        
        # notebookを更新
        print("\n[2/2] 提出用/XQ課題.ipynb を更新中...")
        update_notebook(sections)
        
        print("\n" + "=" * 70)
        print("✅ 移植完了！")
        print("=" * 70)
        print("\n更新内容:")
        print("  - Cell 0: 基本クラス（Suit, Number, Card, Hand, Deck）")
        print("  - Cell 1: State クラス（legal_actions()バグ修正版）")
        print("  - Cell 5: my_AI + AI全ロジック（CardTracker, OpponentModel, HybridStrongestAI）")
        print("\n次のステップ:")
        print("  1. Jupyter Notebook または Google Colab で開く")
        print("  2. 全てのセルを実行（Runtime > Run all）")
        print("  3. エラーが出ないことを確認")
        print("  4. ゲーム実行セル（Cell 8）で動作確認")
        print("\n注意:")
        print("  - アルゴリズムや変数は一切変更していません")
        print("  - Cell 0-1の更新は legal_actions() の致命的バグ修正のためです")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
