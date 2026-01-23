import re
from collections import Counter
import matplotlib.pyplot as plt

# log.txtファイルを読み込む
with open('log.txt', 'r', encoding='utf-8') as file:
    log_text = file.read()

# 勝者の情報を正規表現で抽出
winners = re.findall(r"\* 勝者 プレイヤー(\d+)番", log_text)

# 勝利回数をカウント
count = Counter(winners)

# 結果を表示
print("=== 勝利回数集計 ===")
for player, wins in sorted(count.items()):
    print(f"プレイヤー{player}番: {wins}勝")

# 総ゲーム数も表示
total_games = len(winners)
print(f"\n総ゲーム数: {total_games}")

# 勝率も表示
print("\n=== 勝率 ===")
for player, wins in sorted(count.items()):
    win_rate = (wins / total_games) * 100 if total_games > 0 else 0
    print(f"プレイヤー{player}番: {win_rate:.1f}%")

# === 新機能: 勝率の推移分析（少ないデータ対応） ===
def analyze_win_rate_progression(winners, window_size=None):
    """
    勝率の推移を分析する（少ないゲーム数対応）
    window_size: 移動平均を計算するウィンドウサイズ（自動調整）
    """
    total_games = len(winners)
    
    # ゲーム数に応じて適切なウィンドウサイズを自動設定
    if window_size is None:
        if total_games >= 100:
            window_size = 50  # 100ゲーム以上なら50ゲーム移動平均
        elif total_games >= 50:
            window_size = 25  # 50ゲーム以上なら25ゲーム移動平均
        elif total_games >= 20:
            window_size = 10  # 20ゲーム以上なら10ゲーム移動平均
        else:
            window_size = max(5, total_games // 3)  # 最低5、または全体の1/3
    
    if len(winners) < window_size:
        print(f"\nデータが不足しています。最低{window_size}ゲーム必要です。")
        return
    
    # プレイヤーIDを取得
    unique_players = sorted(set(winners))
    
    # 各プレイヤーの推移データを格納
    progression_data = {player: [] for player in unique_players}
    game_numbers = []
    
    # 移動平均を計算
    for i in range(window_size, len(winners) + 1):
        window_games = winners[i-window_size:i]
        window_count = Counter(window_games)
        
        # 各プレイヤーの勝率を計算
        for player in unique_players:
            win_rate = (window_count.get(player, 0) / window_size) * 100
            progression_data[player].append(win_rate)
        
        game_numbers.append(i)
    
    # 結果を表示
    print(f"\n=== 勝率推移分析（移動平均: {window_size}ゲーム） ===")
    
    # 初期と後期の比較（データ数に応じて調整）
    if len(game_numbers) >= 2:
        early_rate_data = []
        late_rate_data = []
        
        # データ数に応じて比較区間を調整
        comparison_points = min(3, len(game_numbers))
        early_indices = list(range(comparison_points))
        late_indices = list(range(len(game_numbers) - comparison_points, len(game_numbers)))
        
        print("\n初期 vs 後期 勝率比較:")
        for player in unique_players:
            # 初期の平均
            early_rates = [progression_data[player][i] for i in early_indices if i < len(progression_data[player])]
            early_rate = sum(early_rates) / len(early_rates) if early_rates else 0
            
            # 後期の平均
            late_rates = [progression_data[player][i] for i in late_indices if i < len(progression_data[player])]
            late_rate = sum(late_rates) / len(late_rates) if late_rates else 0
            
            change = late_rate - early_rate
            trend = "上昇" if change > 1 else "下降" if change < -1 else "安定"
            print(f"プレイヤー{player}番: {early_rate:.1f}% → {late_rate:.1f}% ({change:+.1f}%) [{trend}]")
    
    # グラフ描画
    plt.figure(figsize=(12, 8))
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, player in enumerate(unique_players):
        plt.plot(game_numbers, progression_data[player], 
                label=f'プレイヤー{player}番', 
                color=colors[i % len(colors)],
                linewidth=2, marker='o', markersize=3)
    
    plt.xlabel(f'ゲーム数（{window_size}ゲーム移動平均）')
    plt.ylabel('勝率 (%)')
    plt.title(f'プレイヤー別勝率推移（移動平均: {window_size}ゲーム）')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max(60, max([max(data) for data in progression_data.values()]) + 5))
    
    # 33.3%ライン（3人対戦での期待勝率）を追加
    plt.axhline(y=33.3, color='gray', linestyle='--', alpha=0.7, label='期待勝率(33.3%)')
    
    plt.tight_layout()
    plt.savefig('win_rate_progression.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return progression_data, game_numbers

def analyze_flexible_performance(winners):
    """
    ゲーム数に応じて柔軟に期間分析
    """
    total = len(winners)
    
    if total >= 100:
        # 十分なデータがある場合は四半期分析
        quarter_size = total // 4
        periods = [
            ("第1四半期", winners[:quarter_size]),
            ("第2四半期", winners[quarter_size:quarter_size*2]),
            ("第3四半期", winners[quarter_size*2:quarter_size*3]),
            ("第4四半期", winners[quarter_size*3:])
        ]
        print(f"\n=== 四半期別分析（各{quarter_size}ゲーム前後） ===")
    elif total >= 40:
        # 中程度のデータなら三分割分析
        third_size = total // 3
        periods = [
            ("前期", winners[:third_size]),
            ("中期", winners[third_size:third_size*2]),
            ("後期", winners[third_size*2:])
        ]
        print(f"\n=== 三期分析（各{third_size}ゲーム前後） ===")
    elif total >= 20:
        # 少ないデータなら前後半分析
        half_size = total // 2
        periods = [
            ("前半", winners[:half_size]),
            ("後半", winners[half_size:])
        ]
        print(f"\n=== 前後半分析（前半{half_size}ゲーム、後半{total-half_size}ゲーム） ===")
    else:
        # 非常に少ないデータの場合
        print(f"\n=== 全期間分析（{total}ゲーム） ===")
        periods = [("全期間", winners)]
    
    for period_name, period_winners in periods:
        if not period_winners:
            continue
            
        period_count = Counter(period_winners)
        print(f"\n{period_name}:")
        for player in sorted(period_count.keys()):
            wins = period_count[player]
            rate = (wins / len(period_winners)) * 100
            print(f"  プレイヤー{player}番: {wins}勝 ({rate:.1f}%)")

def analyze_learning_trend(winners):
    """
    学習傾向の簡易分析（少ないデータ対応）
    """
    total = len(winners)
    if total < 10:
        print("\n学習傾向分析にはより多くのデータが必要です。")
        return
    
    print(f"\n=== 学習傾向分析 ===")
    
    # 初期・中期・後期に分割（最低3ゲームずつ）
    section_size = max(3, total // 3)
    
    early_games = winners[:section_size]
    late_games = winners[-section_size:]
    
    early_count = Counter(early_games)
    late_count = Counter(late_games)
    
    print(f"初期{section_size}ゲーム vs 後期{section_size}ゲーム:")
    
    unique_players = sorted(set(winners))
    for player in unique_players:
        early_rate = (early_count.get(player, 0) / len(early_games)) * 100
        late_rate = (late_count.get(player, 0) / len(late_games)) * 100
        change = late_rate - early_rate
        
        if abs(change) > 5:
            trend_strength = "強い"
        elif abs(change) > 2:
            trend_strength = "やや"
        else:
            trend_strength = ""
        
        if change > 2:
            trend = f"{trend_strength}上昇傾向"
        elif change < -2:
            trend = f"{trend_strength}下降傾向"
        else:
            trend = "安定"
        
        print(f"プレイヤー{player}番: {early_rate:.1f}% → {late_rate:.1f}% ({change:+.1f}%) [{trend}]")

# === メイン分析実行 ===
print(f"\n{'='*50}")
print(f"総ゲーム数: {total_games}ゲーム（分析実行）")
print(f"{'='*50}")

# データ量に応じた推移分析
if total_games >= 10:  # 10ゲーム以上あれば推移分析実行
    try:
        progression_data, game_numbers = analyze_win_rate_progression(winners)
    except Exception as e:
        print(f"推移分析でエラーが発生: {e}")
else:
    print("推移分析には最低10ゲームが必要です。")

# 期間別パフォーマンス分析
if total_games >= 6:  # 6ゲーム以上あれば期間分析実行
    analyze_flexible_performance(winners)

# 学習傾向分析
analyze_learning_trend(winners)

# 最終まとめ
print(f"\n=== 分析まとめ ===")
print(f"対象ゲーム数: {total_games}")
if total_games >= 50:
    print("✅ 十分なデータ量です。詳細な傾向分析が可能です。")
elif total_games >= 20:
    print("⚠️  中程度のデータ量です。傾向の判断には注意が必要です。")
elif total_games >= 10:
    print("⚠️  少ないデータ量です。大まかな傾向のみ参考程度に。")
else:
    print("❌ データが不足しています。より多くのゲームを実行してください。")

# 最も勝率の高いプレイヤーを表示
if count:
    best_player = max(count, key=count.get)
    best_rate = (count[best_player] / total_games) * 100
    print(f"最高勝率: プレイヤー{best_player}番 ({best_rate:.1f}%)")