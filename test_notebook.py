#!/usr/bin/env python3
"""
提出用/XQ課題.ipynb の動作確認スクリプト
notebookの各セルをPythonコードとして実行し、エラーがないか確認する
"""

import json
import sys

def test_notebook():
    """notebookのコードを実行してテスト"""
    print("=" * 70)
    print("Notebook 動作確認テスト")
    print("=" * 70)
    
    # notebookを読み込み
    with open('提出用/XQ課題.ipynb', 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    print(f"\nTotal cells: {len(notebook['cells'])}")
    
    # グローバル名前空間（実行環境）
    global_ns = {}
    
    # テストするセル（Cell 0-6: ゲームエンジン + AI + 評価関数まで）
    test_cells = [0, 1, 2, 3, 5, 7]  # Cell 4, 6はmarkdownなのでスキップ
    
    for cell_idx in test_cells:
        cell = notebook['cells'][cell_idx]
        
        if cell['cell_type'] != 'code':
            continue
        
        source = ''.join(cell['source'])
        
        # @title を削除（Colab固有）
        source = source.replace('# @title', '')
        
        print(f"\n{'='*70}")
        print(f"Testing Cell {cell_idx}...")
        print(f"{'='*70}")
        
        # コードの最初の100文字を表示
        preview = source[:100].replace('\n', ' ')
        print(f"Preview: {preview}...")
        
        try:
            exec(source, global_ns)
            print(f"✓ Cell {cell_idx} executed successfully")
            
            # Cell 5 の後で my_AI と ai_instance が定義されているか確認
            if cell_idx == 5:
                if 'my_AI' in global_ns:
                    print("  ✓ my_AI function is defined")
                else:
                    print("  ✗ my_AI function NOT defined!")
                    
                if 'ai_instance' in global_ns:
                    print("  ✓ ai_instance is defined")
                    print(f"    Type: {type(global_ns['ai_instance'])}")
                else:
                    print("  ✗ ai_instance NOT defined!")
                    
        except Exception as e:
            print(f"✗ Cell {cell_idx} FAILED with error:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 簡単な動作テスト
    print("\n" + "=" * 70)
    print("簡単な動作テスト")
    print("=" * 70)
    
    try:
        # Stateインスタンスの作成
        State = global_ns['State']
        state = State()
        print("✓ State instance created")
        
        # my_AI関数の呼び出し
        my_AI = global_ns['my_AI']
        action, pass_flag = my_AI(state)
        print(f"✓ my_AI called successfully")
        print(f"  Action: {action}")
        print(f"  Pass flag: {pass_flag}")
        
        # アクションの型チェック
        Card = global_ns['Card']
        if isinstance(action, Card):
            print(f"✓ Action is a Card: {action}")
        else:
            print(f"⚠ Action type: {type(action)}")
        
        # パスフラグのチェック
        if isinstance(pass_flag, int) and pass_flag in [0, 1]:
            print(f"✓ Pass flag is valid: {pass_flag}")
        else:
            print(f"⚠ Pass flag type/value: {type(pass_flag)}, {pass_flag}")
            
    except Exception as e:
        print(f"✗ 動作テスト FAILED:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 全てのテストが成功しました！")
    print("=" * 70)
    print("\nNotebookは正常に動作します。")
    print("Google Colab または Jupyter Notebook で実行可能です。")
    
    return True

if __name__ == '__main__':
    success = test_notebook()
    sys.exit(0 if success else 1)
