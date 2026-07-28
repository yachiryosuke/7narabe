from agents import EvolutionAgent, ObstructAgent, RandomAgent, RuleAgent
from game import Game

TEST_GAMES = 5000

def main():
    evolution = EvolutionAgent(
        "Evolution", training=False, weights_path="evolution_weights.json"
    )
    players = [
        RandomAgent("Random"), RuleAgent("Rule"),
        ObstructAgent("Obstruct", show_evaluation=False), evolution,
    ]
    wins = {p.name: 0 for p in players}
    ranks = {p.name: 0 for p in players}
    for _ in range(TEST_GAMES):
        ranking = Game(players).play()
        wins[ranking[0]] += 1
        for rank, name in enumerate(ranking, 1):
            ranks[name] += rank
    for p in players:
        print(p.name, wins[p.name] / TEST_GAMES, ranks[p.name] / TEST_GAMES)

if __name__ == "__main__":
    main()
