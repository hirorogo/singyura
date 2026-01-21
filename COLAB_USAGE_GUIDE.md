# Google Colab 使用ガイド

## 概要

このドキュメントでは、Google Colabで7並べAIを実行する方法を説明します。

## ファイル構成

### 1. `colab_submission_learning_ai.ipynb`
- **用途**: Google Colab用の完全なノートブック
- **特徴**:
  - GPU対応（CuPyを自動検出）
  - 6000試合テスト機能内蔵
  - 学習統計の可視化
  - 提出用コードのテンプレート

### 2. `colab_6000_game_test.py`
- **用途**: 6000試合テストのスタンドアロンスクリプト
- **特徴**:
  - コマンドラインから実行可能
  - 進捗表示
  - 結果をファイルに保存

### 3. `src/main.py`
- **用途**: メインAI実装
- **特徴**:
  - オンライン学習機能
  - 相手プロファイリング
  - PIMC法による高精度な評価

## Google Colabでの使用方法

### 方法1: ノートブックを使用（推奨）

#### ステップ1: ファイルのアップロード
```python
# Colabで実行
from google.colab import files
import os

# ノートブックをアップロード
uploaded = files.upload()
```

#### ステップ2: セルを順番に実行
1. 環境セットアップセル（GPU検出）
2. パラメータ設定セル
3. ゲームエンジン定義セル
4. AI定義セル
5. 6000試合テストセル

#### ステップ3: 結果の確認
- 学習統計は10ゲームごとに表示されます
- 最終結果は表とグラフで表示されます

### 方法2: スクリプトを使用

#### ステップ1: リポジトリをクローン
```python
# Colabで実行
!git clone https://github.com/hirorogo/singyura.git
%cd singyura
```

#### ステップ2: 必要なパッケージをインストール
```python
!pip install numpy

# GPU使用の場合（オプション）
!pip install cupy-cuda11x  # CUDAバージョンに応じて調整
```

#### ステップ3: テストスクリプトを実行
```python
!python colab_6000_game_test.py
```

## GPU使用について

### GPU の有効化

Google Colabで GPU を使用するには:

1. メニューから「ランタイム」→「ランタイムのタイプを変更」
2. 「ハードウェアアクセラレータ」で「GPU」を選択
3. 「保存」をクリック

### GPU の確認

```python
# GPU が利用可能か確認
import torch
print("GPU available:", torch.cuda.is_available())

# または
!nvidia-smi
```

### CuPy のインストール（GPU使用時）

```python
# CUDA 11.x の場合
!pip install cupy-cuda11x

# CUDA 12.x の場合
!pip install cupy-cuda12x
```

**注意**: CuPyがない場合、自動的にCPUモード（NumPy）で動作します。

## 実行時間の目安

| モード | シミュレーション回数 | 予想時間 |
|--------|---------------------|----------|
| CPU (NumPy) | 700 | 3-4時間 |
| CPU (NumPy) | 500 | 2-3時間 |
| CPU (NumPy) | 200 | 1-2時間 |
| GPU (CuPy) | 700 | 1-2時間 |
| GPU (CuPy) | 500 | 45-90分 |
| GPU (CuPy) | 200 | 30-60分 |

**推奨設定（Colab）**:
- GPU使用時: `SIMULATION_COUNT = 500-700`
- CPU使用時: `SIMULATION_COUNT = 200-400`

## トラブルシューティング

### Q: セッションがタイムアウトする

**A**: Google Colabの無料版は90分でアイドルタイムアウトします。

対策:
1. GPU使用でテストを高速化
2. シミュレーション回数を減らす（500→200）
3. Google Colab Pro を使用（12時間のタイムアウト）

### Q: メモリ不足エラー

**A**: シミュレーション回数を減らしてください。

```python
SIMULATION_COUNT = 200  # 700から200に減らす
```

### Q: CuPyのインストールが失敗する

**A**: CUDAバージョンを確認してください。

```python
# CUDAバージョンを確認
!nvcc --version

# 適切なCuPyをインストール
# CUDA 11.x の場合
!pip install cupy-cuda11x

# CUDA 12.x の場合
!pip install cupy-cuda12x
```

### Q: 学習が進まない（勝率が上がらない）

**A**: 以下を確認:
1. `ENABLE_ONLINE_LEARNING = True` になっているか
2. 十分な試合数（100試合以上）をプレイしているか
3. `LEARNING_RATE` を 0.1 に増やしてみる

## 最適化のヒント

### 1. シミュレーション回数の調整

```python
# 高速テスト用（勝率: 70-80%）
SIMULATION_COUNT = 200

# バランス型（勝率: 75-85%）
SIMULATION_COUNT = 500

# 高精度型（勝率: 80-90%）
SIMULATION_COUNT = 700
```

### 2. 進捗表示の調整

```python
# benchmark.pyまたはテストスクリプト内
progress_interval = 50  # 50ゲームごとに表示（デフォルト: 100）
```

### 3. バッチ処理

大量のテストを行う場合:

```python
# 1000ゲーム × 6回 = 6000ゲーム
for batch in range(6):
    run_1000_game_test()
    save_checkpoint(f"checkpoint_{batch}.pkl")
```

## 提出用コードの準備

### ステップ1: ノートブックから完全なコードをコピー

`colab_submission_learning_ai.ipynb` の以下のセルをコピー:
1. パラメータ設定
2. 基本クラス定義（Suit, Number, Card, Hand, Deck, State）
3. CardTracker クラス
4. OpponentModel クラス
5. HybridStrongestAI クラス（完全版）
6. my_AI 関数

### ステップ2: 提出用ノートブックに貼り付け

大会提供のノートブックの `my_AI` セクションに貼り付けます。

### ステップ3: 設定の確認

```python
# 必須設定
ENABLE_ONLINE_LEARNING = True  # 学習を有効化
SIMULATION_COUNT = 700  # 精度と速度のバランス
MY_PLAYER_NUM = 0  # 大会側で指定される値に変更
```

### ステップ4: テスト実行

提出前に必ずテスト実行:

```python
# 短時間テスト（10ゲーム）
for i in range(10):
    state = State()
    # ゲームループ
```

## 結果の保存

### 自動保存

スクリプト実行後、以下のファイルが自動生成されます:

- `6000_game_test_result.txt`: テスト結果のサマリー

### 手動保存

```python
# Colabからダウンロード
from google.colab import files

files.download('6000_game_test_result.txt')
```

### Google Driveに保存

```python
# Google Driveをマウント
from google.colab import drive
drive.mount('/content/drive')

# 結果を保存
import shutil
shutil.copy('6000_game_test_result.txt', '/content/drive/MyDrive/')
```

## 期待される結果

### 学習曲線

```
0-500ゲーム:    40-60% 勝率（初期探索）
500-1000ゲーム: 50-70% 勝率（急速学習）
1000-2000ゲーム: 70-85% 勝率（収束）
2000-6000ゲーム: 80-95% 勝率（最適化）
```

### 最終勝率の目標

| 評価 | 勝率 |
|------|------|
| S+ | 90%以上 |
| S | 85-90% |
| A | 75-85% |
| B | 60-75% |
| C | 45-60% |

## 注意事項

### 1. 外部リクエスト禁止

このAIは完全にローカルで動作し、外部APIを使用していません。

✅ 使用可能:
- NumPy / CuPy
- 標準ライブラリ（random, copy, time等）
- ローカル計算

❌ 使用禁止:
- HTTP/HTTPSリクエスト
- 外部APIへのアクセス
- ネットワーク通信

### 2. セッション管理

Google Colabの無料版:
- アイドルタイムアウト: 90分
- 最大セッション時間: 12時間

長時間テストの場合:
- 定期的にセルを実行してアイドル状態を防ぐ
- Google Colab Pro の使用を検討

### 3. GPU使用時の注意

- CuPyのバージョンとCUDAのバージョンを合わせる
- GPUメモリ不足時はシミュレーション回数を減らす
- CPU/GPUで結果が微妙に異なる場合があります（浮動小数点の誤差）

## サポート

問題が発生した場合:

1. エラーメッセージを確認
2. GPU/CPUモードを切り替えて試す
3. シミュレーション回数を減らす
4. 最新版のコードを使用

---

**作成日**: 2026年1月21日  
**対応環境**: Google Colab（無料版/Pro）  
**推奨GPU**: Tesla T4, V100, P100以上
