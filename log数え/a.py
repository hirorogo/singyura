import re
from collections import Counter

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