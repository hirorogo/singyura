"""
設定ファイル - AI動作のカスタマイズ

このファイルで各種パラメータを調整できます。
"""

# === GPU設定 ===
# GPU使用を強制的に無効化する場合はTrueに設定
FORCE_CPU = False

# === シミュレーション設定 ===
# 自動設定（GPU/CPU）を上書きする場合は数値を設定
# None の場合は自動設定が使用されます
CUSTOM_SIMULATION_COUNT = None  # 例: 500
CUSTOM_SIMULATION_DEPTH = None  # 例: 250

# === AI戦略設定 ===
# PASS戦略
# True: 合法手がある場合はPASSを含めない（推奨）
# False: PASSを候補に含める（探索分散するが柔軟）
DISABLE_PASS_WITH_LEGAL_ACTIONS = True

# バッチサイズ（GPU使用時の並列度）
GPU_BATCH_SIZE = 10
CPU_BATCH_SIZE = 1

# === ロールアウトポリシー設定 ===
# True: 端（A/K）を優先
# False: ランダム選択
PRIORITIZE_ENDS_IN_ROLLOUT = True

# True: Safe move（次のカードを持つ）を優先
# False: 優先しない
PRIORITIZE_SAFE_IN_ROLLOUT = True

# === デバッグ設定 ===
# 詳細なログを出力
VERBOSE_LOGGING = False

# シミュレーション進捗を表示
SHOW_SIMULATION_PROGRESS = False

# === パフォーマンス設定 ===
# 推論エンジンの制約付き確定化リトライ回数
DETERMINIZATION_RETRY_COUNT = 30

# プレイアウトの最大深度（無限ループ防止）
MAX_PLAYOUT_DEPTH = 300

# === ベンチマーク設定 ===
# デフォルトのベンチマークゲーム数
DEFAULT_BENCHMARK_GAMES = 100

# === 推奨設定プリセット ===
def apply_preset(preset_name):
    """
    プリセットを適用
    
    プリセット:
    - 'fastest': 最速（精度低）
    - 'balanced': バランス型（推奨）
    - 'strongest': 最強（遅い）
    - 'gpu_optimal': GPU最適化
    """
    global CUSTOM_SIMULATION_COUNT, CUSTOM_SIMULATION_DEPTH
    global GPU_BATCH_SIZE, DETERMINIZATION_RETRY_COUNT
    
    if preset_name == 'fastest':
        CUSTOM_SIMULATION_COUNT = 20
        CUSTOM_SIMULATION_DEPTH = 100
        DETERMINIZATION_RETRY_COUNT = 10
        
    elif preset_name == 'balanced':
        CUSTOM_SIMULATION_COUNT = 200
        CUSTOM_SIMULATION_DEPTH = 200
        DETERMINIZATION_RETRY_COUNT = 30
        
    elif preset_name == 'strongest':
        CUSTOM_SIMULATION_COUNT = 500
        CUSTOM_SIMULATION_DEPTH = 300
        DETERMINIZATION_RETRY_COUNT = 50
        
    elif preset_name == 'gpu_optimal':
        CUSTOM_SIMULATION_COUNT = 2000
        CUSTOM_SIMULATION_DEPTH = 300
        GPU_BATCH_SIZE = 20
        DETERMINIZATION_RETRY_COUNT = 30
    
    else:
        raise ValueError(f"Unknown preset: {preset_name}")

# プリセットの適用例（コメントアウトを外して使用）
# apply_preset('balanced')
