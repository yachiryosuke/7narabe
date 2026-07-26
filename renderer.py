import pygame


class GameRenderer:
    WIDTH = 1200
    HEIGHT = 760
    FPS = 60

    BG = (28, 110, 72)
    PANEL = (245, 245, 235)
    TEXT = (25, 25, 25)
    RED = (185, 35, 45)
    BLACK = (20, 20, 20)
    ACCENT = (255, 220, 90)

    SUIT_MARKS = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
    RANK_LABELS = {1: "A", 11: "J", 12: "Q", 13: "K"}

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("七並べ - Agent Battle")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("meiryo", 24)
        self.small_font = pygame.font.SysFont("meiryo", 18)
        self.large_font = pygame.font.SysFont("meiryo", 34, bold=True)
        self.running = True
        self.paused = False
        self.step_requested = False
        self.last_action = "ゲーム開始"
        self.speed_ms = 500

    def process_events(self):
        self.step_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_RIGHT:
                    self.step_requested = True
                elif event.key == pygame.K_UP:
                    self.speed_ms = max(50, self.speed_ms - 100)
                elif event.key == pygame.K_DOWN:
                    self.speed_ms = min(2000, self.speed_ms + 100)
        return self.running

    def wait_for_turn(self):
        elapsed = 0
        while self.running:
            self.process_events()
            if self.step_requested:
                return True
            if not self.paused:
                elapsed += self.clock.tick(self.FPS)
                if elapsed >= self.speed_ms:
                    return True
            else:
                self.clock.tick(self.FPS)
        return False

    def rank_text(self, rank):
        return self.RANK_LABELS.get(rank, str(rank))

    def suit_color(self, suit):
        return self.RED if suit in ("H", "D") else self.BLACK

    def draw_card(self, x, y, suit, rank, played=True):
        rect = pygame.Rect(x, y, 72, 92)
        if played:
            pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=7)
            pygame.draw.rect(self.screen, (35, 35, 35), rect, 2, border_radius=7)
            color = self.suit_color(suit)
            self.screen.blit(
                self.small_font.render(self.rank_text(rank), True, color),
                (x + 7, y + 5),
            )
            self.screen.blit(
                self.font.render(self.SUIT_MARKS[suit], True, color),
                (x + 24, y + 35),
            )
        else:
            pygame.draw.rect(self.screen, (65, 120, 175), rect, border_radius=7)
            pygame.draw.rect(self.screen, (225, 225, 225), rect, 2, border_radius=7)

    def draw_board(self, board):
        self.screen.blit(
            self.large_font.render("盤面", True, (255, 255, 255)),
            (35, 20),
        )
        start_x, start_y = 110, 75
        for row, suit in enumerate(board.SUITS):
            y = start_y + row * 105
            self.screen.blit(
                self.large_font.render(
                    self.SUIT_MARKS[suit], True, self.suit_color(suit)
                ),
                (35, y + 24),
            )
            for rank in range(1, 14):
                played = rank in board.cards[suit]
                self.draw_card(
                    start_x + (rank - 1) * 78,
                    y,
                    suit,
                    rank,
                    played,
                )

                # 脱落者の公開札は黄色い枠で区別する。
                if played and hasattr(board, "revealed_cards"):
                    if rank in board.revealed_cards[suit]:
                        pygame.draw.rect(
                            self.screen,
                            self.ACCENT,
                            pygame.Rect(
                                start_x + (rank - 1) * 78,
                                y,
                                72,
                                92,
                            ),
                            4,
                            border_radius=7,
                        )

    def draw_players(self, players, current_index):
        panel_y = 520
        pygame.draw.rect(
            self.screen,
            self.PANEL,
            pygame.Rect(20, panel_y, self.WIDTH - 40, 180),
            border_radius=12,
        )
        width = (self.WIDTH - 70) // len(players)
        for i, player in enumerate(players):
            x = 35 + i * width
            if i == current_index and not player.eliminated:
                pygame.draw.rect(
                    self.screen,
                    self.ACCENT,
                    pygame.Rect(x - 8, panel_y + 10, width - 12, 155),
                    border_radius=10,
                )
            self.screen.blit(
                self.font.render(player.name, True, self.TEXT),
                (x, panel_y + 20),
            )
            status = "脱落" if player.eliminated else "参加中"
            lines = [
                f"手札: {player.hand_size()} 枚",
                f"パス: {player.pass_count} / 4",
                f"状態: {status}",
            ]
            for n, line in enumerate(lines):
                self.screen.blit(
                    self.small_font.render(line, True, self.TEXT),
                    (x, panel_y + 60 + n * 27),
                )

    def draw(self, game):
        self.screen.fill(self.BG)
        name = game.players[game.current_player].name
        self.screen.blit(
            self.font.render(
                f"手番: {name}    直前: {self.last_action}",
                True,
                (255, 255, 255),
            ),
            (420, 25),
        )
        self.screen.blit(
            self.small_font.render(
                f"SPACE: 一時停止  →: 1手  ↑↓: 速度 ({self.speed_ms}ms)  ESC: 終了",
                True,
                (235, 235, 235),
            ),
            (430, 55),
        )
        self.draw_board(game.board)
        self.draw_players(game.players, game.current_player)
        pygame.display.flip()
        self.clock.tick(self.FPS)

    def set_last_action(self, text):
        self.last_action = text

    def show_result(self, ranking):
        self.screen.fill(self.BG)
        self.screen.blit(
            self.large_font.render("ゲーム終了", True, (255, 255, 255)),
            (490, 90),
        )
        for index, name in enumerate(ranking, start=1):
            self.screen.blit(
                self.large_font.render(
                    f"{index}位  {name}", True, (255, 255, 255)
                ),
                (470, 160 + index * 75),
            )
        pygame.display.flip()
        while self.running:
            self.process_events()
            self.clock.tick(self.FPS)

    def close(self):
        pygame.quit()
