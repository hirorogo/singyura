---
marp: true
---

***

# XQ課題 - 7ならべAI作成

## 概要
これはは7ならべゲームのAIを作成する課題です。ランダムAIと対戦して勝率を評価します。

## 1. ランダム行動AI

```python
import random

def random_action(state):
    """ランダムに行動を選択するAI"""
    my_actions = state.my_actions()
    if my_actions != []:
        return my_actions[random.randint(0, len(my_actions)-1)]
    else:
        my_actions=[]
        return my_actions
```

## 2. 課題: my_AIの作成

**課題内容**: `return (出したいカード),(パスを行うか)` を行うAIを作成してください

```python
MY_PLAYER_NUM = 0

def my_AI(state):
    """自作AI - ここを実装する"""
    return random_action(state), 0
```

## 3. ランダムAIとの勝率チェック

```python
# パラメータ
EP_GAME_COUNT = 1000  # 1評価あたりのゲーム数

def player_point(ended_state):
    """勝者判定"""
    if ended_state.turn_player == MY_PLAYER_NUM:
        return 1
    return 0

def play(next_actions):
    """ゲームプレイ関数"""
    state = State()
    # ... (ゲームループ)
```

### ゲーム実行例

```python
# ランダムAIと対戦
state = State()
turn = 0

print("----------- ゲーム開始 -----------\nmy_AI :プレイヤー" + str(MY_PLAYER_NUM) + "番")

# ゲーム終了までのループ
while True:
    turn += 1
    num = state.turn_player
    
    # ゲーム終了時
    if state.is_done():
        print("------- ゲーム終了　ターン", turn, "-------")
        print("* 勝者 プレイヤー" + str(num) + "番")
        break
    else:
        print("------------ ターン", turn, "------------")
    
    pass_flag = 0
    
    # 行動の取得
    if num == MY_PLAYER_NUM:
        action, pass_flag = my_AI(state)
        print(termcolor.colored(state, 'red'))
    else:
        action = random_action(state)
        print(state)
    
    print("出したカード")
    if state.my_actions() == [] or pass_flag == 1:
        print("パス")
        if state.pass_count[num] >= 3:
            print("\n* プレイヤー" + str(num) + "番 バースト")
    else:
        print(action)
    
    # 次の状態の取得
    if pass_flag == 1:
        state = state.next(action, pass_flag)
    else:
        state = state.next(action)
```

## 4. 手札に関する関数

```python
# リストで手札を表示する
state.my_hands()

# リストで手札の数字を表示する
state.my_hands().check_number()

# リストで手札のマークを表示する
state.my_hands().check_suit()

# リストで自分が出せるカードを表示する
state.my_actions()

# リストで自分が出せるカードの数字を表示する
Hand(state.my_actions()).check_number()

# リストで自分が出せるカードの記号を表示する
Hand(state.my_actions()).check_suit()
```

## 5. 場の札に関する関数

```python
# 場のカードを表示する
state.field_cards

# 場で出せるカードをリストで取得する
state.legal_actions()

# 場で出せるカードの数字をリストで取得する
Hand(state.legal_actions()).check_number()

# 場で出せるカードの記号をリストで取得する
Hand(state.legal_actions()).check_suit()
```

## 6. Classの説明

このゲームではclassという概念が使われています。

### 例: personクラス

```python
class person:
    height = 0
    favcolor = "hoge"

# インスタンス作成
tanaka = person()
tanaka.height = 150
tanaka.favcolor = "blue"

print(tanaka.height)
print(tanaka.favcolor)
```

### メソッドを持つクラス

```python
class person:
    height = 0
    favcolor = "hoge"
    
    def explain(self):
        print("身長は" + str(self.height) + "、好きな色は" + self.favcolor)

okada = person()
okada.height = 160
okada.favcolor = "pink"
okada.explain()
```

### __init__メソッド

```python
class person:
    def __init__(self, height, favcolor):
        self.height = height
        self.favcolor = favcolor
    
    def explain(self):
        print("身長は" + str(self.height) + "、色は" + self.favcolor)

suzuki = person(170, "yellow")
suzuki.explain()
```

## AI作成のヒント

- `state.my_actions()` で出せるカードのリストを取得
- `state.my_hands()` で自分の手札を確認
- `state.field_cards` で場の状態を確認
- `pass_flag` を1にするとパス
- 戦略例:
  - 出せるカードの中から最適なものを選ぶ
  - 手札を早く減らせるカードを優先
  - 相手の出せるカードを減らす戦略

***

コーディング規約　このProjectは以下のコーディング規約に沿いコードを書いてください

PEP 8に沿いコードを書いてください
