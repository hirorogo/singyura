# 参考用コード (Reference Code)

このディレクトリには、大会の基本フォーマットと参考実装が含まれています。

## ファイル構成

- `base_game_engine.py` - 大会で提供された基本的なゲームエンジン
- `random_ai.py` - ランダムAIの実装（ベンチマーク用）
- `README.md` - このファイル

## 説明

これらのファイルは、Singularityバトルクエスト大会で提供された基本フォーマットです。
`doc/misc/colab_notebook.md`に記載されている内容を元に抽出されています。

## 使い方

```python
from reference.base_game_engine import State, Card, Suit, Number
from reference.random_ai import random_action

# ゲームの初期化
state = State()

# ランダムAIでプレイ
while not state.is_done():
    action = random_action(state)
    state = state.next(action)
```

## 注意事項

- これらのコードは大会の基本フォーマットであり、そのまま提出しても勝率は低いです
- 実際の提出には`submission.py`を使用してください
- ベンチマークや開発の参考として使用してください
