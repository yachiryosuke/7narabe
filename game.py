# game.py

import random
from board import Board


class Game:
    SUITS = ["S", "H", "D", "C"]
    RANKS = list(range(1, 14))

    def __init__(self, players, renderer=None):
        if len(players) != 4:
            raise ValueError("4人のエージェントを指定してください。")

        self.players = players
        self.board = Board()
        self.renderer = renderer
        self.current_player = 0
        self.finished_players = []
        self.eliminated_players = []
        self.ranking = []

    def play(self):
        self.initialize()
        self._render("初期配置")

        while not self.game_end():
            if self.renderer and not self.renderer.running:
                break

            player = self.players[self.current_player]
            playable = self.board.get_playable_cards(player.hand)
            action = player.choose_action(
                playable_cards=playable,
                board=self.board,
            )

            evaluation_text = ""
            if hasattr(player, "get_evaluation_text"):
                evaluation_text = player.get_evaluation_text()

            if action is None:
                self.pass_player(player)
                text = f"{player.name}: パス"
            else:
                if action not in playable:
                    raise ValueError(
                        f"{player.name}が不正な行動を返しました: {action}"
                    )
                self.play_card(player, action)
                text = f"{player.name}: {self.card_text(action)}"

            if evaluation_text:
                text += f" | {evaluation_text}"

            self._render(text)

            if self.renderer and not self.renderer.wait_for_turn():
                break

            self.next_player()

        if self.game_end():
            self.finish_game()

        return self.ranking

    def initialize(self):
        self.board.reset()
        self.finished_players.clear()
        self.eliminated_players.clear()
        self.ranking.clear()

        for player in self.players:
            player.reset()

        deck = self.create_deck()
        random.shuffle(deck)
        self.deal_cards(deck)
        self.place_initial_sevens()

    def create_deck(self):
        return [
            (suit, rank)
            for suit in self.SUITS
            for rank in self.RANKS
        ]

    def deal_cards(self, deck):
        for index, card in enumerate(deck):
            self.players[index % len(self.players)].add_card(card)

        for player in self.players:
            player.sort_hand()

    def place_initial_sevens(self):
        starter = None

        for index, player in enumerate(self.players):
            for card in list(player.hand):
                suit, rank = card
                if rank == 7:
                    self.board.place_initial_seven(suit)
                    player.remove_card(card)
                    if suit == "D":
                        starter = index

        if starter is None:
            raise RuntimeError("ダイヤの7が見つかりません。")

        self.current_player = starter

    def play_card(self, player, card):
        if card not in player.hand:
            raise ValueError(f"{player.name}は{card}を持っていません。")

        self.board.play(card)
        player.remove_card(card)

        # パス回数は1ゲーム中の累積制なのでリセットしない。
        if player.hand_size() == 0:
            player.eliminated = True
            self.finished_players.append(player.name)

    def pass_player(self, player):
        player.pass_turn()

        if player.pass_count >= 4:
            player.eliminated = True
            self.board.reveal_cards(player.hand)
            player.clear_hand()
            self.eliminated_players.append(player.name)

    def next_player(self):
        if self.game_end():
            return

        while True:
            self.current_player = (
                self.current_player + 1
            ) % len(self.players)

            if not self.players[self.current_player].eliminated:
                return

    def game_end(self):
        return sum(
            not player.eliminated
            for player in self.players
        ) <= 1

    def finish_game(self):
        for player in self.players:
            if not player.eliminated:
                player.eliminated = True
                self.finished_players.append(player.name)

        self.ranking = (
            self.finished_players
            + list(reversed(self.eliminated_players))
        )

        if len(self.ranking) != len(self.players):
            raise RuntimeError(f"順位決定に失敗しました: {self.ranking}")

    def card_text(self, card):
        suit, rank = card
        marks = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
        labels = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return f"{marks[suit]}{labels.get(rank, rank)}"

    def _render(self, action_text):
        if self.renderer is None:
            return
        self.renderer.set_last_action(action_text)
        self.renderer.draw(self)
