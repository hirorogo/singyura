#!/usr/bin/env python3
"""
提出用/XQ課題.ipynb の my_AI 関数確認スクリプト

このスクリプトは以下を確認します：
1. my_AI 関数が定義されているか
2. 必要なクラス（CardTracker, OpponentModel, HybridStrongestAI）が定義されているか
3. ai_instance が初期化されているか
4. my_AI が正しく (Card, pass_flag) を返すか
"""

import json
import sys

def verify_notebook():
    print("=" * 70)
    print("提出用/XQ課題.ipynb 検証スクリプト")
    print("=" * 70)
    
    # Load notebook
    try:
        with open('提出用/XQ課題.ipynb', 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        print("\n✓ Notebook loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load notebook: {e}")
        return False
    
    # Check Cell 5
    print("\n" + "=" * 70)
    print("Cell 5 の内容確認")
    print("=" * 70)
    
    cell_5_source = ''.join(notebook['cells'][5]['source'])
    
    checks = [
        ("MY_PLAYER_NUM = 0", "MY_PLAYER_NUM 定数"),
        ("class CardTracker:", "CardTracker クラス"),
        ("class OpponentModel:", "OpponentModel クラス"),
        ("class HybridStrongestAI:", "HybridStrongestAI クラス"),
        ("def get_action(self, state):", "get_action メソッド"),
        ("ai_instance = HybridStrongestAI", "ai_instance 初期化"),
        ("def my_AI(state):", "my_AI 関数定義"),
        ("return ai_instance.get_action(state)", "my_AI の実装"),
    ]
    
    all_ok = True
    for search_str, description in checks:
        if search_str in cell_5_source:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - 見つかりません！")
            all_ok = False
    
    if not all_ok:
        print("\n✗ Cell 5 に必要な要素が不足しています")
        return False
    
    # Execution test
    print("\n" + "=" * 70)
    print("実行テスト")
    print("=" * 70)
    
    try:
        # Ensure numpy is available
        import numpy
        print("  ✓ numpy インストール済み")
    except ImportError:
        print("  ✗ numpy が必要です: pip install numpy")
        return False
    
    global_ns = {}
    
    # Execute cells
    print("\nセルを実行中...")
    for cell_idx in [0, 1, 2, 3, 5]:
        cell = notebook['cells'][cell_idx]
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source']).replace('# @title', '')
        try:
            exec(source, global_ns)
            print(f"  ✓ Cell {cell_idx} 実行成功")
        except Exception as e:
            print(f"  ✗ Cell {cell_idx} 実行失敗: {e}")
            return False
    
    # Test my_AI
    print("\nmy_AI 関数テスト...")
    try:
        State = global_ns['State']
        my_AI = global_ns['my_AI']
        
        state = State()
        result = my_AI(state)
        
        print(f"  my_AI(state) の戻り値: {result}")
        print(f"  型: {type(result)}")
        
        if isinstance(result, tuple) and len(result) == 2:
            action, pass_flag = result
            print(f"  ✓ タプル (Card, pass_flag) を返しています")
            print(f"    - action: {action} (型: {type(action).__name__})")
            print(f"    - pass_flag: {pass_flag} (型: {type(pass_flag).__name__})")
        else:
            print(f"  ✗ タプル (Card, pass_flag) を返していません")
            return False
            
    except Exception as e:
        print(f"  ✗ my_AI 実行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 全ての確認が完了しました！")
    print("=" * 70)
    print("\nmy_AI 関数は正しく定義され、動作しています。")
    print("Google Colab で実行する場合:")
    print("  1. 'Runtime' → 'Run all' を実行")
    print("  2. または Cell 0, 1, 2, 3, 5 を順番に実行")
    
    return True

if __name__ == '__main__':
    success = verify_notebook()
    sys.exit(0 if success else 1)
