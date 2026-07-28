from agents import EvolutionAgent, ObstructAgent, RandomAgent, RuleAgent
from game import Game

TRAIN_GAMES = 100000
SAVE_INTERVAL = 10000

def main():
    evolution = EvolutionAgent(
        "Evolution", training=True, weights_path="evolution_weights.json",
        temperature=1.2, min_temperature=0.15,
        temperature_decay=0.9997, seed=42,
    )
    players = [
        RandomAgent("Random"), RuleAgent("Rule"),
        ObstructAgent("Obstruct", show_evaluation=False), evolution,
    ]
    wins = {p.name: 0 for p in players}
    for game_number in range(1, TRAIN_GAMES + 1):
        ranking = Game(players).play()
        wins[ranking[0]] += 1
        if game_number % SAVE_INTERVAL == 0:
            evolution.save_weights()
            print(game_number, wins, "temperature=", round(evolution.temperature, 3))
    evolution.save_weights()

if __name__ == "__main__":
    main()
