# main.py

from game import Game

from agents import (
    RandomAgent,
    RuleAgent,
    ObstructAgent
)

# ============================================
# 実験設定
# ============================================

NUM_GAMES = 1000

RANK_POINTS = {
    1: 10,
    2: 5,
    3: 2,
    4: 0
}


# ============================================
# プレイヤー生成
# ============================================

def create_players():

    return [

        RandomAgent("Alice"),

        RandomAgent("Bob"),

        RuleAgent("Rachel"),

        ObstructAgent("Oscar")

    ]


# ============================================
# メイン
# ============================================

def main():

    # 集計用
    names = [
        "Alice",
        "Bob",
        "Rachel",
        "Oscar"
    ]

    win_count = {
        name: 0
        for name in names
    }

    rank_count = {

        name: {

            1: 0,
            2: 0,
            3: 0,
            4: 0

        }

        for name in names
    }

    point_sum = {

        name: 0

        for name in names
    }

    # ============================================

    for game_num in range(NUM_GAMES):

        players = create_players()

        game = Game(players)

        ranking = game.play()

        for rank, name in enumerate(ranking, start=1):

            rank_count[name][rank] += 1

            point_sum[name] += RANK_POINTS[rank]

        win_count[ranking[0]] += 1

        if (game_num + 1) % 100 == 0:

            print(f"{game_num+1} games completed.")

    # ============================================
    # 結果表示
    # ============================================

    print()

    print("=" * 50)
    print("Experiment Result")
    print("=" * 50)

    for name in names:

        print()

        print(name)

        print("-" * 30)

        print(
            f"Win Rate      : "
            f"{100*win_count[name]/NUM_GAMES:.2f}%"
        )

        average_rank = (

            rank_count[name][1]

            + rank_count[name][2] * 2

            + rank_count[name][3] * 3

            + rank_count[name][4] * 4

        ) / NUM_GAMES

        print(f"Average Rank  : {average_rank:.3f}")

        print(
            f"Average Point : "
            f"{point_sum[name]/NUM_GAMES:.3f}"
        )

        print()

        for rank in range(1, 5):

            print(

                f"{rank}位 : "

                f"{rank_count[name][rank]:5d} "

                f"({100*rank_count[name][rank]/NUM_GAMES:6.2f}%)"

            )


if __name__ == "__main__":

    main()