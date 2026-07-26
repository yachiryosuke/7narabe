# board.py


class Board:
    """七並べの盤面、公開札、合法手判定を管理するクラス。"""

    SUITS = ["S", "H", "D", "C"]
    MIN_RANK = 1
    MAX_RANK = 13
    CENTER_RANK = 7

    def __init__(self):
        self.reset()

    def reset(self):
        """
        盤面を初期化する。

        cards:
            画面上に存在する全カード。通常プレイ札と脱落者の公開札を含む。
        connected_cards:
            初期の7、または合法手として通常プレイされたカードだけを保持する。
            合法手判定はこの集合だけを基準にする。
        revealed_cards:
            脱落時に公開されたカード。表示はするが、連続列を伸ばさない。
        """
        self.cards = {suit: set() for suit in self.SUITS}
        self.connected_cards = {suit: set() for suit in self.SUITS}
        self.revealed_cards = {suit: set() for suit in self.SUITS}

    def copy(self):
        """盤面を複製して返す。"""
        new_board = Board()
        new_board.cards = {
            suit: self.cards[suit].copy()
            for suit in self.SUITS
        }
        new_board.connected_cards = {
            suit: self.connected_cards[suit].copy()
            for suit in self.SUITS
        }
        new_board.revealed_cards = {
            suit: self.revealed_cards[suit].copy()
            for suit in self.SUITS
        }
        return new_board

    def place_initial_seven(self, suit):
        """ゲーム開始時に指定スートの7を配置する。"""
        self._validate_suit(suit)
        self.cards[suit].add(self.CENTER_RANK)
        self.connected_cards[suit].add(self.CENTER_RANK)

    def get_contiguous_range(self, suit):
        """
        通常プレイされたカードだけを対象に、7から連続する範囲を返す。

        脱落者の公開札は画面上で隣接していても、この範囲には含めない。
        """
        self._validate_suit(suit)
        connected = self.connected_cards[suit]

        if self.CENTER_RANK not in connected:
            return None

        lower = self.CENTER_RANK
        upper = self.CENTER_RANK

        while lower > self.MIN_RANK and lower - 1 in connected:
            lower -= 1

        while upper < self.MAX_RANK and upper + 1 in connected:
            upper += 1

        return lower, upper

    def can_play(self, card):
        """
        指定カードが合法手か判定する。

        条件:
        1. 手札のカードがまだ盤面に存在しない。
        2. 初期7または通常プレイ札でできた連続列の端である。
        3. 脱落者が公開したカードは、連続列の基準には使用しない。
        """
        suit, rank = self._validate_card(card)

        # 公開札を含め、すでに盤面にあるカードは出せない。
        if rank in self.cards[suit]:
            return False

        if rank == self.CENTER_RANK:
            return False

        contiguous = self.get_contiguous_range(suit)
        if contiguous is None:
            return False

        lower, upper = contiguous
        return rank == lower - 1 or rank == upper + 1

    def play(self, card):
        """合法なカードを通常プレイ札として場へ出す。"""
        if not self.can_play(card):
            raise ValueError(f"Illegal move: {card}")

        suit, rank = card
        self.cards[suit].add(rank)
        self.connected_cards[suit].add(rank)

    def get_playable_cards(self, hand):
        """手札のうち、現在合法なカードだけを返す。"""
        return [card for card in hand if self.can_play(card)]

    def get_open_range(self, suit):
        """通常プレイによる7からの連続列の次候補を返す。"""
        contiguous = self.get_contiguous_range(suit)
        if contiguous is None:
            return None

        lower, upper = contiguous
        lower_candidate = lower - 1 if lower > self.MIN_RANK else None
        upper_candidate = upper + 1 if upper < self.MAX_RANK else None
        return lower_candidate, upper_candidate

    def next_rank(self, rank):
        """7から外側へ進む方向の次ランクを返す。"""
        self._validate_rank(rank)

        if rank < self.CENTER_RANK:
            return rank - 1 if rank > self.MIN_RANK else None
        if rank > self.CENTER_RANK:
            return rank + 1 if rank < self.MAX_RANK else None
        return None

    def rank_weight(self, rank):
        """7に近いカードほど高い危険度を返す。"""
        self._validate_rank(rank)
        if rank == self.CENTER_RANK:
            return 0
        return rank if rank < self.CENTER_RANK else 14 - rank

    def evaluate_unlock(self, card, hand):
        """
        cardを通常プレイした後、相手へ開放し得るカード列を評価する。

        公開札に到達した時点で探索を停止する。公開札は合法手として
        プレイできず、通常プレイの連続列も伸ばさないためである。
        """
        if not self.can_play(card):
            return {
                "score": float("inf"),
                "opened_cards": [],
                "chain_length": 0,
            }

        suit, rank = card
        virtual = self.copy()
        virtual.play(card)
        hand_set = set(hand)
        hand_set.discard(card)

        opened_cards = []
        score = 0
        current = virtual.next_rank(rank)

        while current is not None:
            candidate = (suit, current)

            # 公開札または既存の盤面札に到達したら、その先は評価しない。
            if current in virtual.cards[suit]:
                break

            # 自分が持っているなら、相手への開放はここで止まる。
            if candidate in hand_set:
                break

            # 現在の仮想盤面で本当に合法なカードだけを評価する。
            if not virtual.can_play(candidate):
                break

            opened_cards.append(candidate)
            score += virtual.rank_weight(current)
            virtual.play(candidate)
            current = virtual.next_rank(current)

        return {
            "score": score,
            "opened_cards": opened_cards,
            "chain_length": len(opened_cards),
        }


    def get_pseudo_stair_length(self, card, hand):
        """
        自分の手札と脱落者の公開札を合わせ、cardを含む疑似階段の長さを返す。

        公開札は合法手判定には使用しない。ここではObstructAgentの
        手札評価にだけ使う。例えば手札が4・6で公開札が5なら、
        4-(5)-6を長さ3の疑似階段として扱う。
        """
        suit, rank = self._validate_card(card)
        hand_ranks = {r for s, r in hand if s == suit}
        available = hand_ranks | self.revealed_cards[suit]

        if rank not in hand_ranks:
            return 0

        lower = rank
        upper = rank

        # 7をまたいで反対側へつなげない。
        branch_min = self.MIN_RANK if rank < self.CENTER_RANK else self.CENTER_RANK + 1
        branch_max = self.CENTER_RANK - 1 if rank < self.CENTER_RANK else self.MAX_RANK

        while lower > branch_min and lower - 1 in available:
            lower -= 1
        while upper < branch_max and upper + 1 in available:
            upper += 1

        return upper - lower + 1

    def reveal_cards(self, cards):
        """
        脱落者の残り札を公開する。

        公開札は画面には表示するが connected_cards には追加しないため、
        合法手の連続列を伸ばさない。
        """
        for card in cards:
            suit, rank = self._validate_card(card)

            # 通常プレイ済みの札を公開札へ重複登録しない。
            if rank in self.connected_cards[suit]:
                continue

            self.cards[suit].add(rank)
            self.revealed_cards[suit].add(rank)

    def is_played(self, card):
        """指定カードが通常札または公開札として盤面にあるか返す。"""
        suit, rank = self._validate_card(card)
        return rank in self.cards[suit]

    def is_connected(self, card):
        """指定カードが通常プレイされた連続列の札か返す。"""
        suit, rank = self._validate_card(card)
        return rank in self.connected_cards[suit]

    def is_revealed(self, card):
        """指定カードが脱落者による公開札か返す。"""
        suit, rank = self._validate_card(card)
        return rank in self.revealed_cards[suit]

    def is_complete(self, suit):
        """指定スート13枚がすべて盤面上にあるか返す。"""
        self._validate_suit(suit)
        return len(self.cards[suit]) == self.MAX_RANK

    def get_board(self):
        """AIや表示用にソート済み盤面を返す。"""
        return {
            suit: sorted(self.cards[suit])
            for suit in self.SUITS
        }

    def display(self):
        """通常プレイ札と公開札を区別してコンソール表示する。"""
        marks = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
        labels = {1: "A", 11: "J", 12: "Q", 13: "K"}

        print()
        for suit in self.SUITS:
            cells = []
            for rank in range(self.MIN_RANK, self.MAX_RANK + 1):
                label = labels.get(rank, str(rank))
                if rank in self.connected_cards[suit]:
                    cells.append(label)
                elif rank in self.revealed_cards[suit]:
                    cells.append(f"({label})")
                else:
                    cells.append("-")
            print(f"{marks[suit]} : {' '.join(cells)}")
        print("※ 括弧付きは脱落者の公開札（合法手の連続列には使用しない）")
        print()

    def _validate_suit(self, suit):
        if suit not in self.SUITS:
            raise ValueError(f"Unknown suit: {suit}")

    def _validate_rank(self, rank):
        if not isinstance(rank, int) or not self.MIN_RANK <= rank <= self.MAX_RANK:
            raise ValueError(f"Invalid rank: {rank}")

    def _validate_card(self, card):
        if not isinstance(card, tuple) or len(card) != 2:
            raise ValueError(f"Invalid card: {card}")
        suit, rank = card
        self._validate_suit(suit)
        self._validate_rank(rank)
        return suit, rank
