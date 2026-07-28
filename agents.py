import json
import math
import random
from pathlib import Path

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
            """
            if self.show_evaluation:
                print(
                    f"[Obstruct評価] {self.name}: パス | "
                    f"最良候補={self._card_text(best_card)} "
                    f"優先度={best_priority}({self.PRIORITY_LABELS[best_priority]}) "
                    f"妨害値={unlock_score} 連鎖={chain_length} "
                    f"疑似階段長={pseudo_length}"
                )
            """
            return None
        """
        if self.show_evaluation:
            print(
                f"[Obstruct評価] {self.name}: {self._card_text(best_card)}をプレイ | "
                f"優先度={best_priority}({self.PRIORITY_LABELS[best_priority]}) "
                f"妨害値={unlock_score} 連鎖={chain_length} "
                f"疑似階段長={pseudo_length}"
            )
        """

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


# ==========================================================
# EvolutionAgent
# ==========================================================

class EvolutionAgent(ObstructAgent):
    """
    REINFORCEでカード選択ルールの重みを学習するエージェント。

    他プレイヤーについて利用するのは公開情報のみ:
      ・残り手札枚数
      ・累積パス回数 / 安全に残っているパス回数

    注意:
    相手情報は候補カード間で同じため、単独の特徴量にするとsoftmax内で
    相殺される。そこでカード固有の特徴（妨害度など）との積を用いる。
    """

    FEATURE_NAMES = (
        "bias",
        "rule_quality",
        "obstruction_quality",
        "short_chain",
        "pseudo_stair",
        "far_from_seven",
        "same_suit_support",
        "finish_bonus",
        "pass_action",
        "own_pass_pressure",
        # 他エージェントの残り手札枚数を考慮
        "obstruction_x_lowest_hand_threat",
        "rule_x_lowest_hand_threat",
        "obstruction_x_mean_hand_threat",
        "obstruction_x_next_hand_threat",
        # 他エージェントの残りパス回数を考慮
        "obstruction_x_highest_pass_pressure",
        "obstruction_x_mean_pass_pressure",
        "obstruction_x_next_pass_pressure",
        # パス行動と相手状況の相互作用
        "pass_x_lowest_hand_threat",
        "pass_x_highest_pass_pressure",
    )

    DEFAULT_WEIGHTS = {
        "bias": 0.0,
        "rule_quality": 1.2,
        "obstruction_quality": 0.8,
        "short_chain": 0.4,
        "pseudo_stair": 0.6,
        "far_from_seven": 0.2,
        "same_suit_support": 0.2,
        "finish_bonus": 1.0,
        "pass_action": -0.2,
        "own_pass_pressure": -0.3,
        "obstruction_x_lowest_hand_threat": 0.8,
        "rule_x_lowest_hand_threat": 0.3,
        "obstruction_x_mean_hand_threat": 0.3,
        "obstruction_x_next_hand_threat": 0.5,
        "obstruction_x_highest_pass_pressure": 0.4,
        "obstruction_x_mean_pass_pressure": 0.2,
        "obstruction_x_next_pass_pressure": 0.3,
        "pass_x_lowest_hand_threat": -0.2,
        "pass_x_highest_pass_pressure": 0.2,
    }

    def __init__(
        self,
        name,
        learning_rate=0.02,
        gamma=0.98,
        temperature=1.0,
        min_temperature=0.15,
        temperature_decay=0.9995,
        training=True,
        weights_path="evolution_weights.json",
        show_evaluation=False,
        seed=None,
    ):
        super().__init__(name, show_evaluation=show_evaluation)
        self.learning_rate = float(learning_rate)
        self.gamma = float(gamma)
        self.temperature = float(temperature)
        self.min_temperature = float(min_temperature)
        self.temperature_decay = float(temperature_decay)
        self.training = bool(training)
        self.weights_path = Path(weights_path)
        self.rng = random.Random(seed)
        self.weights = dict(self.DEFAULT_WEIGHTS)
        self.episode_steps = []
        self.reward_baseline = 0.0
        self.games_learned = 0
        self.load_weights(silent=True)

    def reset(self):
        super().reset()
        self.episode_steps = []

    def choose_action(self, playable_cards, board):
        actions = list(playable_cards)
        if self.pass_count < 3:
            actions.append(None)
        if not actions:
            return None

        candidates = []
        for action in actions:
            features = self.extract_features(action, board)
            candidates.append({
                "action": action,
                "features": features,
                "value": self._dot(features),
            })

        probabilities = self._softmax([c["value"] for c in candidates])
        if self.training:
            selected_index = self._sample_index(probabilities)
        else:
            selected_index = max(
                range(len(candidates)),
                key=lambda i: candidates[i]["value"],
            )
        selected = candidates[selected_index]

        if self.training:
            expected = {
                name: sum(
                    probability * candidate["features"][name]
                    for probability, candidate in zip(probabilities, candidates)
                )
                for name in self.FEATURE_NAMES
            }
            gradient = {
                name: selected["features"][name] - expected[name]
                for name in self.FEATURE_NAMES
            }
            self.episode_steps.append({"gradient": gradient})

        self.last_evaluation = {
            "action": selected["action"],
            "policy_value": selected["value"],
            "probability": probabilities[selected_index],
            "features": selected["features"],
        }

        if self.show_evaluation:
            self._print_evolution_evaluation(
                candidates, probabilities, selected_index, board
            )

        return selected["action"]

    def extract_features(self, action, board):
        opponent = self._opponent_state_features(board)
        pass_action = 1.0 if action is None else 0.0

        if action is None:
            rule_quality = 0.0
            obstruction_quality = 0.0
            short_chain = 0.0
            pseudo_stair = 0.0
            far_from_seven = 0.0
            same_suit_support = 0.0
            finish_bonus = 0.0
        else:
            base = self._evolution_card_evaluation(action, board)
            suit, rank = action
            same_suit_count = sum(1 for s, _ in self.hand if s == suit)
            rule_quality = (13.0 - base["priority"]) / 12.0
            obstruction_quality = 1.0 / (1.0 + base["unlock_score"])
            short_chain = 1.0 / (1.0 + base["chain_length"])
            pseudo_stair = min(base["pseudo_length"], 6) / 6.0
            far_from_seven = abs(rank - 7) / 6.0
            same_suit_support = min(same_suit_count, 6) / 6.0
            finish_bonus = 1.0 if len(self.hand) == 1 else 0.0

        return {
            "bias": 1.0,
            "rule_quality": rule_quality,
            "obstruction_quality": obstruction_quality,
            "short_chain": short_chain,
            "pseudo_stair": pseudo_stair,
            "far_from_seven": far_from_seven,
            "same_suit_support": same_suit_support,
            "finish_bonus": finish_bonus,
            "pass_action": pass_action,
            "own_pass_pressure": self.pass_count / 3.0,
            "obstruction_x_lowest_hand_threat": (
                obstruction_quality * opponent["lowest_hand_threat"]
            ),
            "rule_x_lowest_hand_threat": (
                rule_quality * opponent["lowest_hand_threat"]
            ),
            "obstruction_x_mean_hand_threat": (
                obstruction_quality * opponent["mean_hand_threat"]
            ),
            "obstruction_x_next_hand_threat": (
                obstruction_quality * opponent["next_hand_threat"]
            ),
            "obstruction_x_highest_pass_pressure": (
                obstruction_quality * opponent["highest_pass_pressure"]
            ),
            "obstruction_x_mean_pass_pressure": (
                obstruction_quality * opponent["mean_pass_pressure"]
            ),
            "obstruction_x_next_pass_pressure": (
                obstruction_quality * opponent["next_pass_pressure"]
            ),
            "pass_x_lowest_hand_threat": (
                pass_action * opponent["lowest_hand_threat"]
            ),
            "pass_x_highest_pass_pressure": (
                pass_action * opponent["highest_pass_pressure"]
            ),
        }

    def _evolution_card_evaluation(self, card, board):
        priority = self.rule_priority(card, board)
        unlock = board.evaluate_unlock(card, self.hand)
        pseudo_length = board.get_pseudo_stair_length(card, self.hand)
        return {
            "priority": priority,
            "unlock_score": float(unlock["score"]),
            "chain_length": int(unlock["chain_length"]),
            "pseudo_length": int(pseudo_length),
        }

    def _opponent_state_features(self, board):
        state = getattr(board, "public_state", None) or {}
        opponents = state.get("opponents", [])

        if not opponents:
            return {
                "lowest_hand_threat": 0.0,
                "mean_hand_threat": 0.0,
                "next_hand_threat": 0.0,
                "highest_pass_pressure": 0.0,
                "mean_pass_pressure": 0.0,
                "next_pass_pressure": 0.0,
            }

        hand_threats = [
            1.0 - min(max(float(p["hand_size"]), 0.0), 13.0) / 13.0
            for p in opponents
        ]
        # pass_count=3なら安全パス残り0で最大圧力1.0
        pass_pressures = [
            min(max(float(p["pass_count"]), 0.0), 3.0) / 3.0
            for p in opponents
        ]

        next_opponent = next(
            (p for p in opponents if p.get("is_next")),
            opponents[0],
        )
        next_hand_threat = (
            1.0
            - min(max(float(next_opponent["hand_size"]), 0.0), 13.0) / 13.0
        )
        next_pass_pressure = (
            min(max(float(next_opponent["pass_count"]), 0.0), 3.0) / 3.0
        )

        return {
            "lowest_hand_threat": max(hand_threats),
            "mean_hand_threat": sum(hand_threats) / len(hand_threats),
            "next_hand_threat": next_hand_threat,
            "highest_pass_pressure": max(pass_pressures),
            "mean_pass_pressure": sum(pass_pressures) / len(pass_pressures),
            "next_pass_pressure": next_pass_pressure,
        }

    def on_game_end(self, rank, reward=None):
        if reward is None:
            reward = {1: 1.0, 2: 0.3, 3: -0.3, 4: -1.0}[int(rank)]
        if self.training and self.episode_steps:
            self._reinforce_update(float(reward))
        self.games_learned += 1
        self.reward_baseline = (
            0.99 * self.reward_baseline + 0.01 * float(reward)
        )
        self.temperature = max(
            self.min_temperature,
            self.temperature * self.temperature_decay,
        )
        self.episode_steps = []

    def _reinforce_update(self, reward):
        advantage = reward - self.reward_baseline
        total = len(self.episode_steps)
        for index, step in enumerate(self.episode_steps):
            discount = self.gamma ** (total - index - 1)
            scale = self.learning_rate * advantage * discount
            for name in self.FEATURE_NAMES:
                self.weights[name] += scale * step["gradient"][name]
        for name in self.FEATURE_NAMES:
            self.weights[name] = max(-10.0, min(10.0, self.weights[name]))

    def _dot(self, features):
        return sum(
            self.weights[name] * features[name]
            for name in self.FEATURE_NAMES
        )

    def _softmax(self, values):
        temperature = max(self.temperature, 1e-6)
        scaled = [value / temperature for value in values]
        maximum = max(scaled)
        exps = [math.exp(value - maximum) for value in scaled]
        total = sum(exps)
        return [value / total for value in exps]

    def _sample_index(self, probabilities):
        value = self.rng.random()
        cumulative = 0.0
        for index, probability in enumerate(probabilities):
            cumulative += probability
            if value <= cumulative:
                return index
        return len(probabilities) - 1

    def save_weights(self, path=None):
        target = Path(path) if path else self.weights_path
        target.write_text(
            json.dumps({
                "weights": self.weights,
                "reward_baseline": self.reward_baseline,
                "temperature": self.temperature,
                "games_learned": self.games_learned,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_weights(self, path=None, silent=False):
        target = Path(path) if path else self.weights_path
        if not target.exists():
            return False
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            loaded = data.get("weights", {})
            # 旧ファイルに新特徴がなくても初期値を維持する。
            for name in self.FEATURE_NAMES:
                if name in loaded:
                    self.weights[name] = float(loaded[name])
            self.reward_baseline = float(
                data.get("reward_baseline", self.reward_baseline)
            )
            self.temperature = float(
                data.get("temperature", self.temperature)
            )
            self.games_learned = int(
                data.get("games_learned", self.games_learned)
            )
            return True
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            if not silent:
                raise
            return False

    def get_evaluation_text(self):
        info = self.last_evaluation
        if not info:
            return ""
        action = info.get("action")
        action_text = "パス" if action is None else self._card_text(action)
        return (
            f"Evolution {action_text} "
            f"方策値={info.get('policy_value', 0.0):.3f} "
            f"確率={info.get('probability', 0.0):.3f}"
        )

    def _print_evolution_evaluation(
        self, candidates, probabilities, selected_index, board
    ):
        ranked = sorted(
            zip(candidates, probabilities),
            key=lambda pair: pair[0]["value"],
            reverse=True,
        )
        print(f"\n[Evolution評価] {self.name}")
        for rank, (candidate, probability) in enumerate(ranked[:3], 1):
            selected = candidate is candidates[selected_index]
            marker = "*" if selected else " "
            print(
                f"{marker}{rank}. action={candidate['action']} "
                f"value={candidate['value']:.4f} prob={probability:.3f}"
            )
        print("opponents:", getattr(board, "public_state", {}).get("opponents", []))
