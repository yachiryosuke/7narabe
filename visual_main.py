# visual_main.py

from agents import RandomAgent, RuleAgent, ObstructAgent
from game import Game
from renderer import GameRenderer


def main():
    players = [
        RandomAgent("Random A"),
        RandomAgent("Random B"),
        RuleAgent("Rule"),
        ObstructAgent("Obstruct"),
    ]

    renderer = GameRenderer()

    try:
        game = Game(players, renderer=renderer)
        ranking = game.play()

        if ranking and renderer.running:
            renderer.show_result(ranking)
    finally:
        renderer.close()


if __name__ == "__main__":
    main()
