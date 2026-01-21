#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6000試合テストスクリプト（Google Colab対応）

このスクリプトは7並べAIの6000試合テストを実行します。
- GPU対応（CuPyがあれば自動的に使用）
- 外部リクエストなし（完全ローカル実行）
- 学習統計の表示
- 最終結果の保存

使い方:
    python colab_6000_game_test.py
"""

import sys
import os

# src/main.pyからインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import time
import random

# GPU検出
try:
    import cupy as cp
    USE_GPU = True
    print("✓ CuPy検出: GPU高速化を有効化")
    xp = cp
except ImportError:
    USE_GPU = False
    print("ℹ CuPyなし: CPUモードで実行")
    import numpy as np
    xp = np

# メインモジュールをインポート
from main import (
    State, HybridStrongestAI, random_action, 
    MY_PLAYER_NUM, SIMULATION_COUNT, ENABLE_ONLINE_LEARNING
)

def run_6000_game_test():
    """6000試合テストを実行"""
    game_count = 6000
    wins = [0, 0, 0]
    ai_pos = MY_PLAYER_NUM
    
    # AI初期化
    my_ai = HybridStrongestAI(my_player_num=ai_pos, simulation_count=SIMULATION_COUNT)
    
    print("=" * 70)
    print("7並べAI - 6000試合テスト")
    print("=" * 70)
    print(f"AIプレイヤー: P{ai_pos}")
    print(f"シミュレーション回数: {SIMULATION_COUNT}")
    print(f"オンライン学習: {'有効' if ENABLE_ONLINE_LEARNING else '無効'}")
    print(f"GPU: {'有効 (CuPy)' if USE_GPU else '無効 (NumPy)'}")
    print("=" * 70)
    print()
    
    start_time = time.time()
    last_milestone_time = start_time
    
    # 統計情報
    milestone_stats = []
    
    for i in range(game_count):
        # ゲーム準備
        my_ai.prepare_next_game()
        state = State()
        
        # ゲーム実行
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
        
        if winner == -1:
            survivors = [p for p in range(state.players_num) if p not in state.out_player]
            if len(survivors) == 1:
                winner = survivors[0]
        
        if winner != -1:
            wins[winner] += 1
        
        # 学習更新
        if my_ai._opponent_model:
            for p in range(state.players_num):
                if p != ai_pos:
                    my_ai._opponent_model.update_persistent_stats(p)
        
        won = (winner == ai_pos)
        my_ai.update_weights_after_game(won)
        
        # マイルストーン進捗表示（100ゲームごと）
        if (i + 1) % 100 == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            milestone_elapsed = current_time - last_milestone_time
            avg_time = elapsed / (i + 1)
            remaining_games = game_count - i - 1
            remaining_time = avg_time * remaining_games
            current_win_rate = wins[ai_pos] / (i + 1) * 100
            
            # マイルストーン統計
            milestone_stats.append({
                'games': i + 1,
                'win_rate': current_win_rate,
                'elapsed': elapsed,
                'milestone_time': milestone_elapsed
            })
            
            print(f"進捗: {i + 1:4d}/{game_count} | "
                  f"勝率: {current_win_rate:5.1f}% | "
                  f"速度: {100/milestone_elapsed:.1f}ゲーム/秒 | "
                  f"残り: {remaining_time/60:.0f}分")
            
            last_milestone_time = current_time
        
        # 重要マイルストーン（500, 1000, 2000, 4000ゲーム）
        if (i + 1) in [500, 1000, 2000, 4000]:
            print()
            print("-" * 70)
            print(f"マイルストーン: {i + 1}ゲーム達成")
            current_win_rate = wins[ai_pos] / (i + 1) * 100
            print(f"現在の勝率: {current_win_rate:.2f}%")
            
            if i + 1 == 500:
                if current_win_rate >= 60:
                    print("✓ 順調: 予定通り学習が進んでいます")
                else:
                    print("⚠ 注意: 学習がやや遅れています")
            elif i + 1 == 1000:
                if current_win_rate >= 70:
                    print("✓ 優秀: 期待以上のペースです")
                elif current_win_rate >= 60:
                    print("✓ 順調: 予定通りです")
                else:
                    print("⚠ 注意: さらなる学習が必要です")
            elif i + 1 == 2000:
                if current_win_rate >= 80:
                    print("✓ 優秀: 目標勝率に近づいています")
                elif current_win_rate >= 70:
                    print("✓ 順調: 学習が進んでいます")
                else:
                    print("⚠ 注意: 目標達成には改善が必要です")
            elif i + 1 == 4000:
                if current_win_rate >= 85:
                    print("🏆 優秀: 目標勝率を達成しています")
                elif current_win_rate >= 75:
                    print("✓ 良好: もう少しで目標達成です")
                else:
                    print("⚠ 注意: 最終調整が必要です")
            
            print("-" * 70)
            print()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 最終結果
    print()
    print("=" * 70)
    print("6000試合テスト完了")
    print("=" * 70)
    print()
    
    # 実行時間
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    print(f"総実行時間: {hours}時間{minutes}分{seconds}秒")
    print(f"平均時間: {duration/game_count:.3f}秒/ゲーム")
    print(f"処理速度: {game_count/duration:.2f}ゲーム/秒")
    print()
    
    # 勝率結果
    ai_wins = wins[ai_pos]
    ai_win_rate = ai_wins / game_count * 100
    print(f"🤖 AI最終勝率: {ai_wins}/{game_count} ({ai_win_rate:.2f}%)")
    print()
    
    # 各プレイヤーの成績
    print("各プレイヤーの成績:")
    for i, w in enumerate(wins):
        win_rate = w / game_count * 100
        label = "AI (学習型)" if i == ai_pos else f"Random AI {i}"
        bar_length = int(win_rate / 2)
        bar = "█" * bar_length
        print(f"  P{i} ({label:15s}): {w:4d}/{game_count} ({win_rate:5.2f}%) {bar}")
    
    total_wins = sum(wins)
    draws = game_count - total_wins
    if draws > 0:
        draw_rate = draws / game_count * 100
        print(f"  引き分け（全員バースト）: {draws}/{game_count} ({draw_rate:.2f}%)")
    
    print()
    
    # 評価
    print("=" * 70)
    print("評価:")
    print("=" * 70)
    baseline = 33.3  # 3人対戦のランダム期待値
    
    if ai_win_rate >= 90:
        print("🏆 驚異的！ 90%以上の勝率を達成しました！")
        grade = "S+"
    elif ai_win_rate >= 85:
        print("🏆 優秀！ 目標勝率85%以上を達成しました！")
        grade = "S"
    elif ai_win_rate >= 75:
        print("✓ 良好！ ベースラインを大きく上回っています")
        grade = "A"
    elif ai_win_rate >= 60:
        print("✓ 合格！ ベースラインを上回っています")
        grade = "B"
    elif ai_win_rate >= 45:
        print("△ 改善の余地あり: ベースラインをやや上回っています")
        grade = "C"
    else:
        print("⚠ 要改善: ベースラインに近い結果です")
        grade = "D"
    
    improvement = ai_win_rate - baseline
    print(f"ベースライン(33.3%)からの改善: +{improvement:.1f}ポイント")
    print(f"総合評価: {grade}")
    print("=" * 70)
    print()
    
    # 学習曲線の簡易表示
    if milestone_stats:
        print("学習曲線（100ゲームごと）:")
        print("-" * 70)
        for i in range(0, len(milestone_stats), 10):  # 1000ゲームごとに表示
            stat = milestone_stats[i]
            games = stat['games']
            wr = stat['win_rate']
            bar_length = int(wr / 2)
            bar = "█" * bar_length
            print(f"  {games:4d}ゲーム: {wr:5.1f}% {bar}")
        print("-" * 70)
        print()
    
    # 結果をファイルに保存
    try:
        with open('6000_game_test_result.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("7並べAI - 6000試合テスト結果\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"実行日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"総実行時間: {hours}時間{minutes}分{seconds}秒\n")
            f.write(f"AI最終勝率: {ai_win_rate:.2f}%\n")
            f.write(f"総合評価: {grade}\n\n")
            
            f.write("各プレイヤーの成績:\n")
            for i, w in enumerate(wins):
                win_rate = w / game_count * 100
                label = "AI (学習型)" if i == ai_pos else f"Random AI {i}"
                f.write(f"  P{i} ({label}): {w}/{game_count} ({win_rate:.2f}%)\n")
            
            f.write("\n学習統計:\n")
            if HybridStrongestAI._total_games > 0:
                f.write(f"  総ゲーム数: {HybridStrongestAI._total_games}\n")
                f.write(f"  総勝利数: {HybridStrongestAI._wins}\n")
                overall_wr = HybridStrongestAI._wins / HybridStrongestAI._total_games * 100
                f.write(f"  学習システム勝率: {overall_wr:.2f}%\n")
        
        print("✓ 結果を '6000_game_test_result.txt' に保存しました")
    except Exception as e:
        print(f"⚠ ファイル保存エラー: {e}")
    
    return ai_win_rate, milestone_stats

if __name__ == "__main__":
    print()
    print("7並べAI - 6000試合テスト")
    print("Google Colab対応版")
    print()
    print("このテストには2-3時間かかる場合があります。")
    print("GPU使用時は短縮される可能性があります。")
    print()
    
    # 確認
    try:
        response = input("テストを開始しますか？ (y/n): ")
        if response.lower() != 'y':
            print("テストをキャンセルしました。")
            sys.exit(0)
    except:
        # Colab環境などでinputが使えない場合は自動開始
        print("自動開始モード")
    
    print()
    
    # テスト実行
    try:
        final_win_rate, stats = run_6000_game_test()
        print()
        print(f"最終勝率: {final_win_rate:.2f}%")
        print()
        print("テスト完了！")
    except KeyboardInterrupt:
        print("\n\nテストが中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
