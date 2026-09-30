import pygame
import random
from .fruit import Fruit
from .sounds import SoundBank

# Game Engine

WHITE = (255, 255, 255)
BOMB_BLACK = (30, 30, 30)
RED = (230, 70, 70)
GREY = (170, 170, 190)
FRUIT_COLORS = [(220, 60, 60), (230, 140, 40), (230, 200, 40), (90, 180, 90)]

# name: (frames between spawns, bomb chance, launch speed scale)
DIFFICULTIES = {
    "Easy":   (70, 0.08, 0.95),
    "Medium": (55, 0.15, 1.00),
    "Hard":   (38, 0.25, 1.08),
}


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.sounds = SoundBank()

        self.quit_requested = False
        self.reset("Medium")

    # ---------- setup ----------
    def reset(self, difficulty):
        spawn_interval, bomb_chance, speed_scale = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.spawn_interval = spawn_interval
        self.bomb_chance = bomb_chance
        self.speed_scale = speed_scale

        self.fruits = []
        self.trail = []          # recent mouse positions, drawn as the "blade"
        self.last_pos = None     # previous mouse position for segment slicing
        self._moved_this_frame = False
        self._spawn_timer = 0

        self.lives = 3
        self.score = 0
        self.game_over = False
        self.game_over_reason = ""
        self.buttons = {}        # label -> Rect, filled in when drawing game over

    def spawn_fruit(self):
        x = random.randint(60, self.width - 60)
        vy = -random.uniform(13, 16) * self.speed_scale
        vx = random.uniform(-2, 2)
        gravity = 0.35
        kind = "bomb" if random.random() < self.bomb_chance else "fruit"

        fruit = Fruit(x, self.height + 30, vx, vy, gravity, kind=kind)
        fruit.color = BOMB_BLACK if kind == "bomb" else random.choice(FRUIT_COLORS)
        self.fruits.append(fruit)

    # ---------- input ----------
    def handle_event(self, event):
        if self.game_over:
            self._handle_game_over_event(event)
            return

        if event.type == pygame.MOUSEMOTION:
            self._handle_motion(event.pos)
        elif event.type == pygame.WINDOWLEAVE:
            # Don't draw a giant slice line when the mouse re-enters elsewhere
            self.last_pos = None

    def _handle_motion(self, pos):
        x, y = pos
        start = self.last_pos if self.last_pos is not None else pos
        for fruit in self.fruits:
            if not fruit.sliced and fruit.intersects_segment(start[0], start[1], x, y):
                self._slice(fruit)
                if self.game_over:
                    break

        self.last_pos = pos
        self._moved_this_frame = True
        self.trail.append(pos)
        if len(self.trail) > 15:
            self.trail.pop(0)

    def _handle_game_over_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.reset("Easy")
            elif event.key == pygame.K_2:
                self.reset("Medium")
            elif event.key == pygame.K_3:
                self.reset("Hard")
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.quit_requested = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if label == "Exit":
                        self.quit_requested = True
                    else:
                        self.reset(label)
                    break

    def _slice(self, fruit):
        fruit.sliced = True
        if fruit.kind == "bomb":
            self.sounds.bomb.play()
            self._end_game("You sliced a bomb!")
        else:
            self.sounds.slice.play()
            self.score += 1

    def _end_game(self, reason):
        if self.game_over:
            return
        self.game_over = True
        self.game_over_reason = reason
        self.sounds.game_over.play()

    def handle_input(self):
        # Reserved for continuously-held-key input; this game is
        # entirely mouse-driven, so there's nothing to poll here.
        pass

    # ---------- update ----------
    def update(self):
        # Let the blade trail fade out when the mouse stops moving
        if not self._moved_this_frame and self.trail:
            self.trail.pop(0)
        self._moved_this_frame = False

        if self.game_over:
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.spawn_fruit()

        still_alive = []
        for fruit in self.fruits:
            fruit.update()
            if fruit.sliced:
                continue
            if fruit.off_screen(self.height):
                if fruit.kind == "fruit":
                    self.lives -= 1
                continue
            still_alive.append(fruit)
        self.fruits = still_alive

        if self.lives <= 0:
            self.lives = 0
            self._end_game("You ran out of lives!")

    # ---------- drawing ----------
    def render(self, screen):
        for fruit in self.fruits:
            if fruit.sliced:
                continue
            color = getattr(fruit, "color", WHITE)
            pos = (int(fruit.x), int(fruit.y))
            pygame.draw.circle(screen, color, pos, fruit.radius)
            if fruit.kind == "bomb":
                pygame.draw.circle(screen, RED, pos, fruit.radius, 3)

        if len(self.trail) >= 2:
            pygame.draw.lines(screen, WHITE, False, self.trail, 3)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))
        diff_text = self.small_font.render(self.difficulty, True, GREY)
        screen.blit(diff_text, diff_text.get_rect(midtop=(self.width // 2, 14)))

        if self.game_over:
            self._render_game_over(screen)

    def _render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        cx = self.width // 2
        title = self.big_font.render("GAME OVER", True, RED)
        screen.blit(title, title.get_rect(center=(cx, 130)))

        reason = self.font.render(self.game_over_reason, True, WHITE)
        screen.blit(reason, reason.get_rect(center=(cx, 200)))

        score = self.font.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(score, score.get_rect(center=(cx, 245)))

        prompt = self.small_font.render("Play again - choose a difficulty:", True, GREY)
        screen.blit(prompt, prompt.get_rect(center=(cx, 300)))

        labels = ["Easy", "Medium", "Hard", "Exit"]
        keys = ["1", "2", "3", "Esc"]
        mouse = pygame.mouse.get_pos()
        self.buttons = {}
        for i, (label, key) in enumerate(zip(labels, keys)):
            rect = pygame.Rect(0, 0, 240, 44)
            rect.center = (cx, 350 + i * 56)
            hovered = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (70, 80, 120) if hovered else (45, 50, 80), rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
            text = self.small_font.render(f"[{key}]  {label}", True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))
            self.buttons[label] = rect
