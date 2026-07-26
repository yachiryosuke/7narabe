# player.py

class Player:
    """
    全エージェントの基底クラス
    """

    def __init__(self, name):

        # -----------------------
        # 基本情報
        # -----------------------
        self.name = name

        # -----------------------
        # 手札
        # -----------------------
        self.hand = []

        # -----------------------
        # パス回数
        # -----------------------
        self.pass_count = 0

        # -----------------------
        # 脱落フラグ
        # -----------------------
        self.eliminated = False

        # -----------------------
        # 順位
        # -----------------------
        self.rank = None

        # -----------------------
        # 学習用
        # （EvaluationAgentで使用）
        # -----------------------
        self.history = []

    # ==========================================================
    # ゲーム開始
    # ==========================================================

    def reset(self):

        self.hand.clear()

        self.pass_count = 0

        self.eliminated = False

        self.rank = None

        self.history.clear()

    # ==========================================================
    # 手札操作
    # ==========================================================

    def add_card(self, card):

        self.hand.append(card)

    def remove_card(self, card):

        self.hand.remove(card)

    def sort_hand(self):

        self.hand.sort(
            key=lambda x: (
                x[0],
                x[1]
            )
        )

    def clear_hand(self):

        self.hand.clear()

    def hand_size(self):

        return len(self.hand)

    # ==========================================================
    # パス
    # ==========================================================

    def pass_turn(self):

        self.pass_count += 1

    def reset_pass(self):

        self.pass_count = 0

    # ==========================================================
    # 学習履歴
    # ==========================================================

    def remember(self, state):

        """
        EvaluationAgent用

        行動履歴を保存
        """

        self.history.append(state)

    def clear_history(self):

        self.history.clear()

    # ==========================================================
    # エージェント共通
    # ==========================================================

    def choose_action(self, playable_cards, board):

        raise NotImplementedError

    # ==========================================================
    # デバッグ表示
    # ==========================================================

    def __str__(self):

        return (
            f"{self.name}"
            f" Hand:{len(self.hand)}"
            f" Pass:{self.pass_count}"
            f" Eliminated:{self.eliminated}"
        )