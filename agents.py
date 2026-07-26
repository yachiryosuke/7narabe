import random
from player import Player


# ==========================================================
# RandomAgent
# ==========================================================

class RandomAgent(Player):
    """
    合法手からランダムに1枚選択するエージェント
    """

    def __init__(self, name):
        super().__init__(name)

    def choose_action(self, playable_cards, board):

        if not playable_cards:
            return None

        return random.choice(playable_cards)


# ==========================================================
# RuleAgent
# ==========================================================

class RuleAgent(Player):
    """
    あらかじめ決められた優先順位でカードを選択するエージェント

    （簡易版）
    ・7から遠いカードほど優先
    ・同点ならランダム
    """

    def __init__(self, name):
        super().__init__(name)

    def choose_action(self, playable_cards, board):

        if not playable_cards:
            return None

        best_score = float("inf")
        best_cards = []

        for card in playable_cards:

            score = self.evaluate(card)

            if score < best_score:

                best_score = score
                best_cards = [card]

            elif score == best_score:

                best_cards.append(card)

        return random.choice(best_cards)

    ##################################################

    def evaluate(self, card):

        _, rank = card

        return self.rank_priority(rank)

    ##################################################

    def rank_priority(self, rank):
        """
        暫定版

        A,K
            ↓
        2,Q
            ↓
        3,J
            ↓
        4,10
            ↓
        5,9
            ↓
        6,8
        """

        priority = {
            1: 1,
            13: 1,

            2: 2,
            12: 2,

            3: 3,
            11: 3,

            4: 4,
            10: 4,

            5: 5,
            9: 5,

            6: 6,
            8: 6
        }

        return priority[rank]


# ==========================================================
# ObstructAgent
# ==========================================================

class ObstructAgent(Player):
    """
    事前に定めた13段階ルールを基礎にし、同じ優先度の合法手では
    相手へ開放する危険度が小さいカードを選ぶエージェント。

    優先順位（数値が小さいほど優先）
      1: A・K単品
      2: 階段
      3: 1間飛び
      4: パス（1～3回目）
      5: 2・Q単品
      6: 2間飛び
      7: 3・J単品
      8: 3間飛び
      9: 4・10単品
     10: 4間飛び
     11: 5・9単品
     12: 6・8単品
     13: 4回目のパス（合法手がなければ脱落）

    脱落者の公開札は合法手判定には使わないが、手札構造の評価では
    間を埋める札として扱う。例えば手札4・6、公開札5なら階段扱い。
    """

    PASS_PRIORITY = 4

    PRIORITY_LABELS = {
        1: "A・K単品",
        2: "階段",
        3: "1間飛び",
        4: "パス",
        5: "2・Q単品",
        6: "2間飛び",
        7: "3・J単品",
        8: "3間飛び",
        9: "4・10単品",
        10: "4間飛び",
        11: "5・9単品",
        12: "6・8単品",
        13: "4回目のパス",
    }

    SINGLE_PRIORITY = {
        1: 1, 13: 1,
        2: 5, 12: 5,
        3: 7, 11: 7,
        4: 9, 10: 9,
        5: 11, 9: 11,
        6: 12, 8: 12,
    }

    GAP_PRIORITY = {
        0: 2,   # 階段（間に不足札なし）
        1: 3,   # 1間飛び
        2: 6,   # 2間飛び
        3: 8,   # 3間飛び
        4: 10,  # 4間飛び
    }

    def __init__(self, name, show_evaluation=True):
        super().__init__(name)
        self.show_evaluation = show_evaluation
        self.last_evaluation = None

    def choose_action(self, playable_cards, board):
        self.last_evaluation = None

        if not playable_cards:
            if self.show_evaluation:
                print(f"[Obstruct評価] {self.name}: 合法手なし -> パス")
            return None

        scored_cards = []

        for card in playable_cards:
            rule_priority = self.rule_priority(card, board)
            unlock = board.evaluate_unlock(card, self.hand)
            pseudo_length = board.get_pseudo_stair_length(card, self.hand)

            scored_cards.append(
                (
                    rule_priority,             # まず13段階ルール
                    unlock["score"],           # 次に相手への危険度
                    unlock["chain_length"],    # 次に開放連鎖の短さ
                    -pseudo_length,             # 同点なら長い疑似階段
                    card[0],
                    card[1],
                    card,
                    pseudo_length,
                    unlock["opened_cards"],
                )
            )

        scored_cards.sort(key=lambda item: item[:6])
        (
            best_priority,
            unlock_score,
            chain_length,
            _,
            _,
            _,
            best_card,
            pseudo_length,
            opened_cards,
        ) = scored_cards[0]

        self.last_evaluation = {
            "action": "play",
            "card": best_card,
            "priority": best_priority,
            "priority_label": self.PRIORITY_LABELS[best_priority],
            "unlock_score": unlock_score,
            "chain_length": chain_length,
            "pseudo_length": pseudo_length,
            "opened_cards": opened_cards,
        }

        # 優先度1～3のカードはパスより先に出す。
        # 優先度5～12しかない場合は、1～3回目のパスを選ぶ。
        if self.pass_count < 3 and best_priority > self.PASS_PRIORITY:
            self.last_evaluation["action"] = "pass"
            if self.show_evaluation:
                print(
                    f"[Obstruct評価] {self.name}: パス | "
                    f"最良候補={self._card_text(best_card)} "
                    f"優先度={best_priority}({self.PRIORITY_LABELS[best_priority]}) "
                    f"妨害値={unlock_score} 連鎖={chain_length} "
                    f"疑似階段長={pseudo_length}"
                )
            return None

        if self.show_evaluation:
            print(
                f"[Obstruct評価] {self.name}: {self._card_text(best_card)}をプレイ | "
                f"優先度={best_priority}({self.PRIORITY_LABELS[best_priority]}) "
                f"妨害値={unlock_score} 連鎖={chain_length} "
                f"疑似階段長={pseudo_length}"
            )

        # 3回パス済みなら、合法手がある限り最良カードを必ず出す。
        return best_card

    def get_evaluation_text(self):
        """直前の判断をpygame表示などで使える文字列として返す。"""
        if not self.last_evaluation:
            return ""

        info = self.last_evaluation
        return (
            f"優先度{info['priority']}:{info['priority_label']} "
            f"妨害値={info['unlock_score']} "
            f"連鎖={info['chain_length']} "
            f"疑似階段={info['pseudo_length']}"
        )

    @staticmethod
    def _card_text(card):
        suit, rank = card
        marks = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
        labels = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return f"{marks[suit]}{labels.get(rank, rank)}"

    def rule_priority(self, card, board):
        """指定カードの13段階ルール上の優先順位を返す。"""
        suit, rank = card
        own_ranks = sorted(r for s, r in self.hand if s == suit)

        # 同スートの手札がこの1枚だけなら単品。
        if len(own_ranks) == 1:
            return self.SINGLE_PRIORITY[rank]

        missing_count = self._minimum_missing_between_own_cards(
            card=card,
            board=board,
        )

        # 4間飛びまでをルールに従って分類。
        if missing_count in self.GAP_PRIORITY:
            return self.GAP_PRIORITY[missing_count]

        # 5枚以上離れていて既定分類に入らない場合は、
        # そのカード自身の単品相当優先度をフォールバックにする。
        return self.SINGLE_PRIORITY[rank]

    def _minimum_missing_between_own_cards(self, card, board):
        """
        cardと同じ枝にある別の自分のカードまでの区間について、
        自分の手札または公開札で埋まっていないランク数の最小値を返す。

        例:
          手札4・6、公開5  -> 0（疑似階段）
          手札3・6、公開4 -> 1（5が不足するため1間飛び）
          手札3・6、公開4・5 -> 0（疑似階段）
        """
        suit, rank = card
        own_ranks = {r for s, r in self.hand if s == suit}
        revealed = board.revealed_cards[suit]

        branch = self._branch(rank)
        other_ranks = [
            other
            for other in own_ranks
            if other != rank and self._branch(other) == branch
        ]

        if not other_ranks:
            # 同スートにカードはあっても反対側の枝だけなら、
            # 現在の枝では単品として扱う。
            return None

        minimum = None

        for other in other_ranks:
            low, high = sorted((rank, other))
            intermediate = range(low + 1, high)
            missing = sum(
                value not in own_ranks and value not in revealed
                for value in intermediate
            )

            if minimum is None or missing < minimum:
                minimum = missing

        return minimum

    @staticmethod
    def _branch(rank):
        """A側を-1、K側を1として返す。7は手札に残らない。"""
        return -1 if rank < 7 else 1
