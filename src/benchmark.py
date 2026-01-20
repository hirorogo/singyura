"""
統合ベンチマークスクリプト

すべてのベンチマーク機能を1つのスクリプトに統合しました。
コマンドライン引数で各種オプションを制御できます。

使い方:
    # 標準ベンチマーク（100ゲーム）
    python benchmark_unified.py
    
    # ゲーム数を指定
    python benchmark_unified.py --games 1000
    
    # シミュレーション回数を指定
    python benchmark_unified.py --simulations 500
    
    # GPU使用（CuPyが必要）
    python benchmark_unified.py --gpu
    
    # すべてのオプションを組み合わせ
    python benchmark_unified.py --games 500 --simulations 700 --gpu
"""

import time
import argparse
import sys

def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description='七並べAIの統合ベンチマークツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                              # 標準ベンチマーク（100ゲーム）
  %(prog)s --games 1000                 # 1000ゲーム実行
  %(prog)s --simulations 700            # シミュレーション回数を700に設定
  %(prog)s --gpu                        # GPU使用（CuPy必要）
  %(prog)s --games 500 --simulations 500 --gpu  # すべて指定
        """
    )
    
    parser.add_argument(
        '--games', '-g',
        type=int,
        default=100,
        help='実行するゲーム数（デフォルト: 100）'
    )
    
    parser.add_argument(
        '--simulations', '-s',
        type=int,
        default=None,
        help='シミュレーション回数（デフォルト: main.pyのSIMULATION_COUNTを使用）'
    )
    
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='GPU使用（CuPyが必要）'
    )
    
    parser.add_argument(
        '--progress-interval',
        type=int,
        default=1,
        help='進捗表示の間隔（ゲーム数）（デフォルト: 10）'
    )
    
    return parser.parse_args()

def setup_gpu(use_gpu):
    """GPU環境をセットアップ"""
    if use_gpu:
        try:
            import cupy as xp
            print("✓ CuPy検出: GPU高速化を有効化")
            return True
        except ImportError:
            print("⚠ 警告: CuPyが見つかりません。CPUモードで実行します")
            return False
    return False

def run_benchmark(game_count, simulation_count=None, use_gpu=False, progress_interval=10):
    """
    ベンチマークを実行
    
    Args:
        game_count: 実行するゲーム数
        simulation_count: シミュレーション回数（Noneの場合はmain.pyのデフォルト値）
        use_gpu: GPU使用フラグ
        progress_interval: 進捗表示の間隔
    """
    # GPU設定
    gpu_available = setup_gpu(use_gpu)
    
    # main.pyからインポート
    from main import State, HybridStrongestAI, MY_PLAYER_NUM, random_action, SIMULATION_COUNT
    
    # シミュレーション回数の決定
    sim_count = simulation_count if simulation_count is not None else SIMULATION_COUNT
    
    wins = [0] * 3
    ai_pos = 0  # AI is Player 0
    
    # AI初期化
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=sim_count)
    
    # ベンチマーク情報を表示
    print("="*60)
    print("七並べAI 統合ベンチマーク")
    print("="*60)
    print(f"ゲーム数: {game_count}")
    print(f"シミュレーション回数: {sim_count}")
    print(f"GPU使用: {'はい (CuPy)' if gpu_available else 'いいえ (CPU)'}")
    print(f"進捗表示間隔: {progress_interval}ゲームごと")
    print("="*60)
    print()

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

        # 勝者判定
        winner = -1
        for p, hand in enumerate(state.players_cards):
            if len(hand) == 0 and p not in state.out_player:
                winner = p
                break
        
        # 勝者が見つからない場合、生存者を確認
        if winner == -1:
            survivors = [p for p in range(state.players_num) if p not in state.out_player]
            if len(survivors) == 1:
                winner = survivors[0]

        if winner != -1:
            wins[winner] += 1
            
        # 進捗表示
        if (i + 1) % progress_interval == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / (i + 1)
            current_win_rate = wins[ai_pos] / (i + 1) * 100
            print(f"進捗: {i + 1}/{game_count} ゲーム | "
                  f"現在の勝率: {current_win_rate:.1f}% | "
                  f"平均: {avg_time:.2f}秒/ゲーム")

    end_time = time.time()
    duration = end_time - start_time
    
    # 結果表示
    print()
    print("="*60)
    print("ベンチマーク結果")
    print("="*60)
    print(f"総実行時間: {duration:.2f}秒")
    print(f"平均時間: {duration/game_count:.2f}秒/ゲーム")
    print()
    
    # AI勝率
    ai_wins = wins[ai_pos]
    ai_win_rate = ai_wins / game_count * 100
    print(f"🤖 AI勝率: {ai_wins}/{game_count} ({ai_win_rate:.1f}%)")
    
    # 各プレイヤーの詳細
    print()
    print("詳細:")
    for i, w in enumerate(wins):
        win_rate = w / game_count * 100
        label = "AI" if i == ai_pos else f"Random{i}"
        print(f"  P{i} ({label}): {w}/{game_count} ({win_rate:.1f}%)")
    
    # 引き分け
    total_wins = sum(wins)
    draws = game_count - total_wins
    if draws > 0:
        draw_rate = draws / game_count * 100
        print(f"  引き分け（全員バースト）: {draws}/{game_count} ({draw_rate:.1f}%)")
    
    # 統計情報
    if hasattr(my_ai, 'print_stats'):
        print()
        print("AI統計情報:")
        my_ai.print_stats()
    
    print("="*60)
    
    # 評価コメント
    print()
    print("評価:")
    baseline_rate = 33.3  # 3人対戦のランダム期待値
    if ai_win_rate >= 70:
        print(f"  ✓ 優秀！ベースライン({baseline_rate:.1f}%)を大幅に上回っています")
    elif ai_win_rate >= 50:
        print(f"  ✓ 良好。ベースライン({baseline_rate:.1f}%)を上回っています")
    elif ai_win_rate >= baseline_rate:
        print(f"  △ 及第点。ベースライン({baseline_rate:.1f}%)をわずかに上回っています")
    else:
        print(f"  ✗ 改善が必要。ベースライン({baseline_rate:.1f}%)を下回っています")
    
    return ai_win_rate

def main():
    """メイン処理"""
    args = parse_args()
    
    try:
        win_rate = run_benchmark(
            game_count=args.games,
            simulation_count=args.simulations,
            use_gpu=args.gpu,
            progress_interval=args.progress_interval
        )
        
        print()
        print(f"最終勝率: {win_rate:.1f}%")
        
    except KeyboardInterrupt:
        print("\n\nベンチマークが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
