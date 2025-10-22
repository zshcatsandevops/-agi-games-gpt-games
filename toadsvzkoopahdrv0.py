import platform
import pygame
import random
import math
import time
from pygame.locals import (
    QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONDOWN, USEREVENT
)

# -------------------------
# Init & global config
# -------------------------
pygame.init()
pygame.display.set_caption("Toads vs Koopas — Tower Defense (60 FPS Fixed)")

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (135, 206, 235)
LAWN_GREEN = (34, 139, 34)
SUN_YELLOW = (255, 215, 0)
GREEN = (0, 200, 0)
BLUE = (50, 120, 255)
BROWN = (139, 69, 19)
RED = (200, 0, 0)
GRAY = (120, 120, 120)
GRAY_DARK = (80, 80, 80)
ORANGE = (255, 140, 0)
PURPLE = (160, 32, 240)

# Grid (5x9 like PvZ)
ROWS, COLS = 5, 9
TILE_SIZE = 80
LAWN_LEFT, LAWN_TOP = 100, 100
LAWN_WIDTH, LAWN_HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE

# Fonts
font = pygame.font.SysFont(None, 22)
bigfont = pygame.font.SysFont(None, 36)
titlefont = pygame.font.SysFont(None, 48)

# Resources
sun_count = 50

# Event timers
SPAWN_SUN_SKY = USEREVENT + 1

# Game state
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"
state = STATE_PLAY

# Grid occupancy (None or Plant instance)
grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

# Sprite groups
all_sprites = pygame.sprite.Group()
plant_sprites = pygame.sprite.Group()
enemy_sprites = pygame.sprite.Group()
projectile_sprites = pygame.sprite.Group()
sun_sprites = pygame.sprite.Group()
mower_sprites = pygame.sprite.Group()
explosion_sprites = pygame.sprite.Group()

# 60 FPS fixed logic timestep (NES-style)
LOGIC_FPS = 60
LOGIC_DT = 1.0 / LOGIC_FPS

# -------------------------
# Helpers
# -------------------------
def cell_from_pos(pos):
    x, y = pos
    if not (LAWN_LEFT <= x < LAWN_LEFT + LAWN_WIDTH and LAWN_TOP <= y < LAWN_TOP + LAWN_HEIGHT):
        return None
    col = (x - LAWN_LEFT) // TILE_SIZE
    row = (y - LAWN_TOP) // TILE_SIZE
    return int(row), int(col)

def topleft_from_cell(row, col, inner_pad=5):
    return (LAWN_LEFT + col * TILE_SIZE + inner_pad,
            LAWN_TOP + row * TILE_SIZE + inner_pad)

def rect_for_cell(row, col, pad=5):
    x, y = topleft_from_cell(row, col, pad)
    size = TILE_SIZE - 2*pad
    return pygame.Rect(x, y, size, size)

def draw_grid(surface):
    pygame.draw.rect(surface, LAWN_GREEN, (LAWN_LEFT, LAWN_TOP, LAWN_WIDTH, LAWN_HEIGHT))
    for r in range(ROWS + 1):
        pygame.draw.line(surface, (0, 100, 0), (LAWN_LEFT, LAWN_TOP + r*TILE_SIZE),
                         (LAWN_LEFT + LAWN_WIDTH, LAWN_TOP + r*TILE_SIZE), 2)
    for c in range(COLS + 1):
        pygame.draw.line(surface, (0, 100, 0), (LAWN_LEFT + c*TILE_SIZE, LAWN_TOP),
                         (LAWN_LEFT + c*TILE_SIZE, LAWN_TOP + LAWN_HEIGHT), 2)

# -------------------------
# Tutorial
# -------------------------
class Tutorial:
    def __init__(self):
        self.steps = [
            "Welcome! Click falling suns to collect them.",
            "Click a Toad packet, then click a lawn tile to plant.",
            "Green Toad shoots. Yellow Toad makes suns. Blue Toad slows.",
            "Brick Toad is a wall. Bomb Toad is a one-shot AoE. Spore Mine arms then pops.",
            "Koopas come in waves—don't let them pass the left! Shell-mowers save a lane once.",
            "Use the shovel to dig plants. Good luck!"
        ]
        self.idx = 0
        self.active = True

    def advance(self):
        self.idx += 1
        if self.idx >= len(self.steps):
            self.active = False

    def draw(self, surf):
        if not self.active:
            return
        prof_rect = pygame.Rect(20, 20, 50, 50)
        pygame.draw.rect(surf, BROWN, prof_rect)
        pygame.draw.circle(surf, (255, 200, 150), (prof_rect.x + 25, prof_rect.y + 20), 10)
        pygame.draw.circle(surf, BLACK, (prof_rect.x + 20, prof_rect.y + 18), 2)
        pygame.draw.circle(surf, BLACK, (prof_rect.x + 30, prof_rect.y + 18), 2)
        txt = font.render(self.steps[self.idx], True, BLACK)
        bubble_width = min(820, txt.get_width() + 20)
        bubble = pygame.Surface((bubble_width, 50), pygame.SRCALPHA)
        bubble.fill((255, 255, 255, 220))
        bubble_rect = bubble.get_rect(topleft=(80, 20))
        surf.blit(bubble, bubble_rect)
        surf.blit(txt, (bubble_rect.x + 10, bubble_rect.y + 13))
        if self.idx < len(self.steps) - 1:
            hint = font.render("Click to continue", True, BLACK)
            surf.blit(hint, (bubble_rect.x + 10, bubble_rect.y + 30))

tutorial = Tutorial()

# -------------------------
# Suns
# -------------------------
class Sun(pygame.sprite.Sprite):
    def __init__(self, x, y, falling=True):
        super().__init__()
        self.surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, SUN_YELLOW, (20, 20), 15)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = 20 + 15 * math.cos(rad)
            y1 = 20 + 15 * math.sin(rad)
            x2 = 20 + 20 * math.cos(rad)
            y2 = 20 + 20 * math.sin(rad)
            pygame.draw.line(self.surf, SUN_YELLOW, (x1, y1), (x2, y2), 3)
        self.rect = self.surf.get_rect(center=(x, y))
        self.falling = falling
        self.speed = random.randint(40, 70)
        self.target_y = random.randint(LAWN_TOP + 10, LAWN_TOP + LAWN_HEIGHT - 10)
        self.lifetime = 10.0
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        if self.age > self.lifetime:
            self.kill()
            return
        if self.falling:
            self.rect.y += int(self.speed * dt)
            if self.rect.y >= self.target_y:
                self.falling = False

# -------------------------
# Projectiles
# -------------------------
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, row, damage=1, speed=300, slow_factor=0.0, slow_duration=0.0, color=GREEN):
        super().__init__()
        self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, color, (8, 8), 8)
        if color == BLUE:
            pygame.draw.circle(self.surf, (200, 200, 255), (8, 8), 5)
        self.rect = self.surf.get_rect(center=(x, y))
        self.row = row
        self.damage = damage
        self.speed = speed
        self.slow_factor = slow_factor
        self.slow_duration = slow_duration

    def update(self, dt):
        self.rect.x += int(self.speed * dt)
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

# -------------------------
# Enemies (Koopas)
# -------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, row, hp, speed, dps, color=ORANGE, armor_hp=0):
        super().__init__()
        self.surf = pygame.Surface((46, 56), pygame.SRCALPHA)
        self._base_color = color
        self.armor_hp = armor_hp
        self.draw_enemy(color)
        cx = SCREEN_WIDTH + random.randint(40, 160)
        cy = LAWN_TOP + row*TILE_SIZE + TILE_SIZE//2
        self.rect = self.surf.get_rect(center=(cx, cy))
        self.row = row
        self.base_speed = speed
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.max_armor_hp = float(armor_hp)
        self.dps = dps
        self.attacking = False
        self.target_plant = None
        self.slow_timer = 0.0
        self.slow_factor = 0.0
        self.attack_animation_timer = 0.0

    def draw_enemy(self, color):
        self.surf.fill((0,0,0,0))
        pygame.draw.ellipse(self.surf, color, (5, 10, 36, 40))
        pygame.draw.circle(self.surf, color, (23, 15), 12)
        pygame.draw.circle(self.surf, WHITE, (18, 12), 4)
        pygame.draw.circle(self.surf, WHITE, (28, 12), 4)
        pygame.draw.circle(self.surf, BLACK, (18, 12), 2)
        pygame.draw.circle(self.surf, BLACK, (28, 12), 2)
        pygame.draw.ellipse(self.surf, color, (10, 45, 10, 8))
        pygame.draw.ellipse(self.surf, color, (26, 45, 10, 8))
        if self.armor_hp > 0:
            pygame.draw.ellipse(self.surf, GRAY_DARK, (8, 15, 30, 25))
            pygame.draw.ellipse(self.surf, GRAY, (10, 17, 26, 21))
            for i in range(3):
                pygame.draw.line(self.surf, GRAY_DARK, (12, 20 + i*6), (34, 20 + i*6), 1)

    def take_damage(self, dmg):
        if self.armor_hp > 0:
            absorbed = min(self.armor_hp, dmg)
            self.armor_hp -= absorbed
            dmg -= absorbed
            self.draw_enemy(self._base_color)
        if dmg > 0:
            self.hp -= dmg
        if self.hp <= 0:
            self.kill()

    def apply_slow(self, factor, duration):
        self.slow_factor = max(self.slow_factor, factor)
        self.slow_timer = max(self.slow_timer, duration)

    def _front_cell(self):
        front_x = self.rect.left
        col = (front_x - LAWN_LEFT) // TILE_SIZE
        return int(self.row), int(col)

    def update(self, dt):
        # Slow logic
        if self.slow_timer > 0:
            self.slow_timer -= dt
            cur_speed = self.base_speed * (1.0 - self.slow_factor)
        else:
            cur_speed = self.base_speed
            self.slow_factor = 0.0

        if self.attack_animation_timer > 0:
            self.attack_animation_timer -= dt

        self.attacking = False
        self.target_plant = None
        r, c = self._front_cell()
        if 0 <= r < ROWS and 0 <= c < COLS:
            p = grid[r][c]
            if p and self.rect.colliderect(p.rect):
                self.attacking = True
                self.target_plant = p
                if self.attack_animation_timer <= 0:
                    self.attack_animation_timer = 0.3

        if self.attacking and self.target_plant:
            self.target_plant.take_damage(self.dps * dt)
            if self.target_plant.dead:
                self.attacking = False
        else:
            self.rect.x -= int(cur_speed * dt)

class Koopa(Enemy):
    def __init__(self, row):
        super().__init__(row=row, hp=10, speed=45, dps=10, color=ORANGE)

class FastKoopa(Enemy):
    def __init__(self, row):
        super().__init__(row=row, hp=7, speed=75, dps=10, color=RED)

class HeavyKoopa(Enemy):
    def __init__(self, row):
        super().__init__(row=row, hp=20, speed=30, dps=12, color=PURPLE)

class ShellKoopa(Enemy):
    def __init__(self, row):
        super().__init__(row=row, hp=12, speed=40, dps=10, color=GRAY_DARK, armor_hp=10)

# -------------------------
# Plants (Toads)
# -------------------------
class Plant(pygame.sprite.Sprite):
    HP = 10
    COST = 50
    COOLDOWN = 5000
    NAME = "Plant"
    COLOR = GREEN
    def __init__(self, row, col):
        super().__init__()
        self.row, self.col = row, col
        self.rect = rect_for_cell(row, col, pad=6)
        self.surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.animation_timer = 0.0
        self.draw_plant()
        self.hp = float(self.HP)
        self.max_hp = float(self.HP)
        self.dead = False

    def draw_plant(self):
        pygame.draw.ellipse(self.surf, self.COLOR, (10, 10, self.rect.width-20, self.rect.height-20))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0 and not self.dead:
            self.dead = True
            if grid[self.row][self.col] is self:
                grid[self.row][self.col] = None
            self.kill()

    def update(self, dt):
        self.animation_timer += dt

class GreenToad(Plant):
    NAME = "Green Toad"
    COLOR = GREEN
    HP = 10
    COST = 100
    COOLDOWN = 4500
    FIRE_RATE = 1.2
    BULLET_DMG = 1
    BULLET_SPEED = 300

    def __init__(self, row, col):
        super().__init__(row, col)
        self.shoot_timer = 0.0

    def draw_plant(self):
        pygame.draw.ellipse(self.surf, GREEN, (10, 15, self.rect.width-20, self.rect.height-25))
        pygame.draw.circle(self.surf, GREEN, (self.rect.width//2, 15), 12)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 - 5, 12), 4)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 + 5, 12), 4)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 5, 12), 2)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 5, 12), 2)
        pygame.draw.arc(self.surf, BLACK, (self.rect.width//2 - 5, 15, 10, 5), 0, math.pi, 1)

    def update(self, dt):
        super().update(dt)
        self.shoot_timer += dt
        lane_has_enemy = any(e.row == self.row and e.rect.left > self.rect.right - 4
                             for e in enemy_sprites)
        if lane_has_enemy and self.shoot_timer >= 1.0 / self.FIRE_RATE:
            p = Projectile(self.rect.right - 5, self.rect.centery, self.row,
                           damage=self.BULLET_DMG, speed=self.BULLET_SPEED, color=GREEN)
            projectile_sprites.add(p); all_sprites.add(p)
            self.shoot_timer = 0.0

class BlueToad(Plant):
    NAME = "Blue Toad"
    COLOR = BLUE
    HP = 10
    COST = 175
    COOLDOWN = 6000
    FIRE_RATE = 0.9
    BULLET_DMG = 1
    BULLET_SPEED = 300
    SLOW_FACTOR = 0.45
    SLOW_DURATION = 3.0

    def __init__(self, row, col):
        super().__init__(row, col)
        self.shoot_timer = 0.0

    def draw_plant(self):
        pygame.draw.ellipse(self.surf, BLUE, (10, 15, self.rect.width-20, self.rect.height-25))
        pygame.draw.circle(self.surf, BLUE, (self.rect.width//2, 15), 12)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 - 5, 12), 4)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 + 5, 12), 4)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 5, 12), 2)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 5, 12), 2)
        pygame.draw.polygon(self.surf, (200, 200, 255), 
                           [(self.rect.width//2 - 8, 5), 
                            (self.rect.width//2 + 8, 5), 
                            (self.rect.width//2, 15)])
        pygame.draw.arc(self.surf, BLACK, (self.rect.width//2 - 5, 15, 10, 5), 0, math.pi, 1)

    def update(self, dt):
        super().update(dt)
        self.shoot_timer += dt
        lane_has_enemy = any(e.row == self.row and e.rect.left > self.rect.right - 4
                             for e in enemy_sprites)
        if lane_has_enemy and self.shoot_timer >= 1.0 / self.FIRE_RATE:
            p = Projectile(self.rect.right - 5, self.rect.centery, self.row,
                           damage=self.BULLET_DMG, speed=self.BULLET_SPEED,
                           slow_factor=self.SLOW_FACTOR, slow_duration=self.SLOW_DURATION,
                           color=BLUE)
            projectile_sprites.add(p); all_sprites.add(p)
            self.shoot_timer = 0.0

class YellowToad(Plant):
    NAME = "Yellow Toad"
    COLOR = SUN_YELLOW
    HP = 7
    COST = 50
    COOLDOWN = 5000
    SUN_RATE = (6.5, 8.5)

    def __init__(self, row, col):
        super().__init__(row, col)
        self.timer = random.uniform(*self.SUN_RATE)

    def draw_plant(self):
        pygame.draw.ellipse(self.surf, SUN_YELLOW, (10, 15, self.rect.width-20, self.rect.height-25))
        pygame.draw.circle(self.surf, SUN_YELLOW, (self.rect.width//2, 15), 12)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 - 5, 12), 4)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 + 5, 12), 4)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 5, 12), 2)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 5, 12), 2)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = self.rect.width//2 + 12 * math.cos(rad)
            y1 = 15 + 12 * math.sin(rad)
            x2 = self.rect.width//2 + 18 * math.cos(rad)
            y2 = 15 + 18 * math.sin(rad)
            pygame.draw.line(self.surf, SUN_YELLOW, (x1, y1), (x2, y2), 2)
        pygame.draw.arc(self.surf, BLACK, (self.rect.width//2 - 5, 15, 10, 5), 0, math.pi, 1)

    def update(self, dt):
        super().update(dt)
        self.timer -= dt
        if self.timer <= 0:
            x = self.rect.centerx + random.randint(-10, 10)
            y = self.rect.top - 6
            s = Sun(x, y, falling=True)
            sun_sprites.add(s); all_sprites.add(s)
            self.timer = random.uniform(*self.SUN_RATE)

class BrickToad(Plant):
    NAME = "Brick Toad"
    COLOR = (110, 70, 40)
    HP = 60
    COST = 50
    COOLDOWN = 8000

    def draw_plant(self):
        brick_color = (110, 70, 40)
        for row in range(0, self.rect.height, 10):
            for col in range(0, self.rect.width, 20):
                offset = 10 if (row // 10) % 2 else 0
                pygame.draw.rect(self.surf, brick_color, 
                                (col + offset, row, 20, 10))
                pygame.draw.rect(self.surf, (90, 50, 20), 
                                (col + offset, row, 20, 10), 1)
        pygame.draw.circle(self.surf, (200, 150, 100), (self.rect.width//2, 15), 10)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 - 4, 13), 3)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 + 4, 13), 3)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 4, 13), 1)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 4, 13), 1)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, radius=100, lifetime=0.2):
        super().__init__()
        self.surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (255, 80, 0, 110), (radius, radius), radius)
        self.rect = self.surf.get_rect(center=center)
        self.age = 0.0
        self.lifetime = lifetime
    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()

class BombToad(Plant):
    NAME = "Bomb Toad"
    COLOR = RED
    HP = 5
    COST = 150
    COOLDOWN = 12000
    FUSE = 1.0
    RADIUS = 100
    DAMAGE = 999

    def __init__(self, row, col):
        super().__init__(row, col)
        self.fuse = self.FUSE

    def draw_plant(self):
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2, self.rect.height//2), 20)
        pygame.draw.circle(self.surf, RED, (self.rect.width//2, self.rect.height//2), 18)
        fuse_end_x = self.rect.width//2 + 15 * math.cos(self.animation_timer * 2)
        fuse_end_y = self.rect.height//2 - 15 * math.sin(self.animation_timer * 2)
        pygame.draw.line(self.surf, BLACK, 
                        (self.rect.width//2, self.rect.height//2 - 18), 
                        (fuse_end_x, fuse_end_y), 2)
        pygame.draw.circle(self.surf, SUN_YELLOW, (int(fuse_end_x), int(fuse_end_y)), 3)
        pygame.draw.circle(self.surf, (200, 100, 100), (self.rect.width//2, self.rect.height//2), 12)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 - 5, self.rect.height//2 - 3), 3)
        pygame.draw.circle(self.surf, WHITE, (self.rect.width//2 + 5, self.rect.height//2 - 3), 3)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 5, self.rect.height//2 - 3), 1)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 5, self.rect.height//2 - 3), 1)

    def update(self, dt):
        super().update(dt)
        self.fuse -= dt
        if self.fuse <= 0:
            center = self.rect.center
            boom = Explosion(center, radius=self.RADIUS, lifetime=0.22)
            explosion_sprites.add(boom); all_sprites.add(boom)
            for e in list(enemy_sprites):
                if (e.rect.centerx - center[0])**2 + (e.rect.centery - center[1])**2 <= self.RADIUS**2:
                    e.take_damage(self.DAMAGE)
            if grid[self.row][self.col] is self:
                grid[self.row][self.col] = None
            self.kill()

class SporeMine(Plant):
    NAME = "Spore Mine"
    COLOR = (170, 0, 170)
    HP = 5
    COST = 25
    COOLDOWN = 9000
    ARM_TIME = 8.0
    DAMAGE = 999
    RADIUS = 70
    armed = False

    def __init__(self, row, col):
        super().__init__(row, col)
        self.arm_timer = self.ARM_TIME
        self.armed = False

    def draw_plant(self):
        color = (200, 0, 200) if self.armed else (170, 0, 170)
        self.surf.fill((0,0,0,0))
        pygame.draw.circle(self.surf, color, (self.rect.width//2, self.rect.height//2), 20)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = self.rect.width//2 + 15 * math.cos(rad)
            y1 = self.rect.height//2 + 15 * math.sin(rad)
            x2 = self.rect.width//2 + 20 * math.cos(rad)
            y2 = self.rect.height//2 + 20 * math.sin(rad)
            pygame.draw.line(self.surf, BLACK, (x1, y1), (x2, y2), 2)
        face_color = (220, 100, 220) if self.armed else (190, 70, 190)
        pygame.draw.circle(self.surf, face_color, (self.rect.width//2, self.rect.height//2), 12)
        eye_color = RED if self.armed else WHITE
        pygame.draw.circle(self.surf, eye_color, (self.rect.width//2 - 5, self.rect.height//2 - 3), 3)
        pygame.draw.circle(self.surf, eye_color, (self.rect.width//2 + 5, self.rect.height//2 - 3), 3)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 - 5, self.rect.height//2 - 3), 1)
        pygame.draw.circle(self.surf, BLACK, (self.rect.width//2 + 5, self.rect.height//2 - 3), 1)
        if self.armed:
            pygame.draw.arc(self.surf, BLACK, (self.rect.width//2 - 5, self.rect.height//2, 10, 5), math.pi, 0, 1)
        else:
            pygame.draw.arc(self.surf, BLACK, (self.rect.width//2 - 5, self.rect.height//2 - 3, 10, 5), 0, math.pi, 1)

    def update(self, dt):
        super().update(dt)
        if not self.armed:
            self.arm_timer -= dt
            if self.arm_timer <= 0:
                self.armed = True
                self.draw_plant()
        else:
            for e in list(enemy_sprites):
                if e.row == self.row and self.rect.colliderect(e.rect):
                    center = self.rect.center
                    for target in list(enemy_sprites):
                        if (target.rect.centerx - center[0])**2 + (target.rect.centery - center[1])**2 <= self.RADIUS**2:
                            target.take_damage(self.DAMAGE)
                    if grid[self.row][self.col] is self:
                        grid[self.row][self.col] = None
                    self.kill()
                    break

PLANT_TYPES = [
    YellowToad,
    GreenToad,
    BlueToad,
    BrickToad,
    BombToad,
    SporeMine
]

# -------------------------
# Seed packets & shovel
# -------------------------
class SeedCard:
    def __init__(self, plant_cls, idx):
        self.cls = plant_cls
        self.idx = idx
        self.rect = pygame.Rect(100 + idx * 90, 20, 80, 60)
        self.last_planted_ms = -plant_cls.COOLDOWN
        # Cache icon once (no per-frame plant construction)
        self.icon = self._render_icon()

    def _render_icon(self):
        icon_surf = pygame.Surface((self.rect.width-10, self.rect.height-20), pygame.SRCALPHA)
        # Quick, lightweight icon: instantiate once, draw into icon surface
        temp_plant = self.cls(0, 0)
        temp_plant.rect = pygame.Rect(0, 0, icon_surf.get_width(), icon_surf.get_height())
        temp_plant.surf = icon_surf
        temp_plant.draw_plant()
        return icon_surf

    def ready(self):
        now = pygame.time.get_ticks()
        return (now - self.last_planted_ms) >= self.cls.COOLDOWN

    def draw(self, surf, can_afford, selected):
        color = self.cls.COLOR
        card = pygame.Surface((self.rect.width, self.rect.height))
        card.fill(color)
        surf.blit(card, self.rect.topleft)

        # Plant name + cost
        name = font.render(self.cls.NAME, True, BLACK)
        cost = font.render(f"{self.cls.COST}", True, BLACK)
        surf.blit(name, (self.rect.x + 4, self.rect.y + 2))
        surf.blit(self.icon, (self.rect.x + 5, self.rect.y + 20))
        surf.blit(cost, (self.rect.x + 4, self.rect.y + self.rect.height - 18))

        # Cooldown veil
        if not self.ready():
            veil = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 120))
            surf.blit(veil, self.rect.topleft)
            now = pygame.time.get_ticks()
            cooldown_remaining = max(0, self.cls.COOLDOWN - (now - self.last_planted_ms))
            cooldown_pct = cooldown_remaining / self.cls.COOLDOWN
            pygame.draw.rect(surf, BLACK, self.rect, 2)
            pygame.draw.rect(surf, BLACK, 
                            (self.rect.x, self.rect.y + self.rect.height - 5, 
                             int(self.rect.width * (1 - cooldown_pct)), 5))

        # Affordability veil
        if not can_afford:
            veil = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            veil.fill((255, 255, 255, 110))
            surf.blit(veil, self.rect.topleft)

        pygame.draw.rect(surf, BLACK, self.rect, 3 if selected else 1)

seed_cards = [SeedCard(cls, i) for i, cls in enumerate(PLANT_TYPES)]

# Shovel
shovel_rect = pygame.Rect(100 + len(seed_cards) * 90 + 20, 20, 80, 60)
selected_card = None
shovel_selected = False

# -------------------------
# Lawn mowers (shells)
# -------------------------
class LawnShell(pygame.sprite.Sprite):
    def __init__(self, row):
        super().__init__()
        self.row = row
        self.surf = pygame.Surface((60, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(self.surf, GRAY, (5, 5, 50, 30))
        pygame.draw.ellipse(self.surf, GRAY_DARK, (10, 10, 40, 20))
        pygame.draw.circle(self.surf, BLACK, (15, 35), 5)
        pygame.draw.circle(self.surf, BLACK, (45, 35), 5)
        y = LAWN_TOP + row*TILE_SIZE + TILE_SIZE//2
        self.rect = self.surf.get_rect(center=(LAWN_LEFT - 40, y))
        self.active = False
        self.speed = 420

    def trigger(self):
        self.active = True

    def update(self, dt):
        if self.active:
            self.rect.x += int(self.speed * dt)
            for e in list(enemy_sprites):
                if e.row == self.row and self.rect.colliderect(e.rect):
                    e.kill()
            if self.rect.left > LAWN_LEFT + LAWN_WIDTH + 40:
                self.kill()

mowers_by_row = [LawnShell(r) for r in range(ROWS)]
for m in mowers_by_row:
    mower_sprites.add(m); all_sprites.add(m)

# -------------------------
# Level / Waves
# -------------------------
class LevelManager:
    def __init__(self):
        self.time = 0.0
        self.duration = 120.0
        self.final_wave_spawned = False
        self.spawn_timer = 2.0
        self.difficulty = 0.0
        self.finished_spawning = False
        self.wave_number = 1
        self.enemies_in_wave = 0
        self.max_enemies_per_wave = 10

    def update(self, dt):
        self.time += dt
        self.difficulty = min(1.0, self.time / self.duration)
        
        if not self.final_wave_spawned:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.enemies_in_wave < self.max_enemies_per_wave:
                self.spawn_enemy()
                self.enemies_in_wave += 1
                self.spawn_timer = max(0.8, 2.0 - 1.2 * self.difficulty)
            
            if self.enemies_in_wave >= self.max_enemies_per_wave and len(enemy_sprites) == 0:
                self.wave_number += 1
                self.max_enemies_per_wave = min(30, 10 + self.wave_number * 5)
                self.enemies_in_wave = 0
                self.spawn_timer = 5.0
                
        if self.time >= self.duration and not self.final_wave_spawned:
            self.final_wave()
        if self.final_wave_spawned and len(enemy_sprites) == 0:
            self.finished_spawning = True

    def spawn_enemy(self):
        row = random.randint(0, ROWS-1)
        roll = random.random()
        if roll < 0.55 - 0.35*self.difficulty:
            enemy = Koopa(row)
        elif roll < 0.75:
            enemy = FastKoopa(row)
        elif roll < 0.92:
            enemy = HeavyKoopa(row)
        else:
            enemy = ShellKoopa(row)
        enemy_sprites.add(enemy); all_sprites.add(enemy)

    def final_wave(self):
        self.final_wave_spawned = True
        for _ in range(14):
            row = random.randint(0, ROWS-1)
            enemy_cls = random.choice([Koopa, FastKoopa, HeavyKoopa, ShellKoopa])
            e = enemy_cls(row)
            e.rect.x = SCREEN_WIDTH + random.randint(0, 60)
            enemy_sprites.add(e); all_sprites.add(e)

    def draw_progress(self, surf):
        bar_w, bar_h = 240, 16
        x, y = SCREEN_WIDTH - bar_w - 40, 28
        pygame.draw.rect(surf, BLACK, (x-2, y-2, bar_w+4, bar_h+4), 2)
        pct = min(1.0, self.time / self.duration)
        fill_w = int(bar_w * pct)
        pygame.draw.rect(surf, ORANGE, (x, y, fill_w, bar_h))
        label = font.render(f"Wave {self.wave_number}", True, BLACK)
        bubble = pygame.Surface((label.get_width() + 20, label.get_height() + 8), pygame.SRCALPHA)
        bubble.fill((255, 255, 255, 220))
        bubble.blit(label, (10, 4))
        surf.blit(bubble, (x, y + bar_h + 4))
        if self.final_wave_spawned:
            fw = bigfont.render("FINAL WAVE!", True, RED)
            bubble = pygame.Surface((fw.get_width() + 20, fw.get_height() + 8), pygame.SRCALPHA)
            bubble.fill((255, 255, 255, 220))
            bubble.blit(fw, (10, 4))
            surf.blit(bubble, (x - 10, y - 28))

level = LevelManager()

# -------------------------
# Collision helpers
# -------------------------
def handle_projectile_hits():
    for proj in list(projectile_sprites):
        for e in enemy_sprites:
            if e.row == proj.row and proj.rect.colliderect(e.rect):
                e.take_damage(proj.damage)
                if proj.slow_factor > 0:
                    e.apply_slow(proj.slow_factor, proj.slow_duration)
                proj.kill()
                break

# -------------------------
# UI drawing
# -------------------------
def draw_topbar():
    global selected_card, shovel_selected
    pygame.draw.rect(screen, (100, 100, 100), (0, 0, SCREEN_WIDTH, 90))
    
    for card in seed_cards:
        can_afford = sun_count >= card.cls.COST
        is_sel = (selected_card is card and not shovel_selected)
        card.draw(screen, can_afford, is_sel)
    
    shovel_surf = pygame.Surface(shovel_rect.size)
    shovel_surf.fill(GRAY)
    pygame.draw.rect(shovel_surf, BROWN, (30, 10, 20, 30))
    pygame.draw.polygon(shovel_surf, GRAY, [(30, 10), (50, 10), (40, 25)])
    screen.blit(shovel_surf, shovel_rect.topleft)
    s_txt = font.render("Shovel", True, BLACK)
    screen.blit(s_txt, (shovel_rect.x + 10, shovel_rect.y + 20))
    pygame.draw.rect(screen, BLACK, shovel_rect, 3 if shovel_selected else 1)

    counter = bigfont.render(f"Suns: {sun_count}", True, BLACK)
    screen.blit(counter, (shovel_rect.right + 20, 30))

def draw_health_bars():
    # Plants
    for p in plant_sprites:
        if p.hp < p.max_hp and p.max_hp > 0:
            bar_width = p.rect.width - 10
            bar_height = 4
            bar_x = p.rect.x + 5
            bar_y = p.rect.y - 8
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * (p.hp / p.max_hp)), bar_height))
    # Enemies
    for e in enemy_sprites:
        if e.hp < e.max_hp and e.max_hp > 0:
            bar_width = 40
            bar_height = 4
            bar_x = e.rect.x + 3
            bar_y = e.rect.y - 8
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * (e.hp / e.max_hp)), bar_height))

# -------------------------
# Placement / removal
# -------------------------
def try_place(row, col, plant_cls, card):
    global sun_count
    if grid[row][col] is not None:
        return False
    if sun_count < plant_cls.COST:
        return False
    p = plant_cls(row, col)
    grid[row][col] = p
    plant_sprites.add(p); all_sprites.add(p)
    sun_count -= plant_cls.COST
    if card:
        card.last_planted_ms = pygame.time.get_ticks()
    return True

def dig_up(row, col):
    p = grid[row][col]
    if p:
        p.kill()
        grid[row][col] = None

# -------------------------
# Click handling
# -------------------------
def handle_click(pos):
    global sun_count, selected_card, shovel_selected
    for s in list(sun_sprites):
        if s.rect.collidepoint(pos):
            sun_count += 25
            s.kill()
            return
    for card in seed_cards:
        if card.rect.collidepoint(pos):
            if card.ready():
                selected_card = card
                shovel_selected = False
            return
    if shovel_rect.collidepoint(pos):
        shovel_selected = True
        selected_card = None
        return
    cell = cell_from_pos(pos)
    if not cell:
        if tutorial.active:
            tutorial.advance()
        return
    row, col = cell
    if shovel_selected:
        dig_up(row, col)
        return
    if selected_card and selected_card.ready():
        try_place(row, col, selected_card.cls, selected_card)
        return

# -------------------------
# Sky sun spawner
# -------------------------
def spawn_sky_sun():
    x = random.randint(LAWN_LEFT + 20, LAWN_LEFT + LAWN_WIDTH - 20)
    s = Sun(x, LAWN_TOP - 20, falling=True)
    sun_sprites.add(s); all_sprites.add(s)

# -------------------------
# Lose / mower logic
# -------------------------
def check_left_edge_and_mowers():
    # If an enemy reaches the lawn edge, trigger lane mower once, else lose if it exits screen
    for e in list(enemy_sprites):
        row = e.row
        mower = mowers_by_row[row] if row < len(mowers_by_row) else None
        if e.rect.left <= LAWN_LEFT - 8:
            if mower and mower.alive() and not mower.active:
                mower.trigger()
            elif e.rect.right <= 0:
                return True
    return False

# -------------------------
# Menu / end screens
# -------------------------
def draw_center_message(title, subtitle=None, prompt=None):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    box_width, box_height = 600, 300
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, BLACK, (box_x, box_y, box_width, box_height), 3)
    
    title_surf = titlefont.render(title, True, BLACK)
    screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH//2, box_y + 80)))
    if subtitle:
        sub_surf = bigfont.render(subtitle, True, BLACK)
        screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH//2, box_y + 140)))
    if prompt:
        p_surf = font.render(prompt, True, BLACK)
        screen.blit(p_surf, p_surf.get_rect(center=(SCREEN_WIDTH//2, box_y + 200)))

def reset_game():
    global sun_count, grid, selected_card, shovel_selected, level, mowers_by_row, state
    sun_count = 50
    selected_card = None
    shovel_selected = False
    for g in [all_sprites, plant_sprites, enemy_sprites, projectile_sprites,
              sun_sprites, mower_sprites, explosion_sprites]:
        for s in list(g):
            s.kill()
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    mowers_by_row = [LawnShell(r) for r in range(ROWS)]
    for m in mowers_by_row:
        mower_sprites.add(m); all_sprites.add(m)
    for c in seed_cards:
        c.last_planted_ms = -c.cls.COOLDOWN
    level = LevelManager()
    state = STATE_PLAY

# -------------------------
# Main loop (fixed 60Hz logic)
# -------------------------
def run():
    global state
    pygame.time.set_timer(SPAWN_SUN_SKY, 8000)
    clock = pygame.time.Clock()

    accumulator = 0.0
    prev = time.perf_counter()

    running = True
    while running:
        # ---- Time management (fixed step) ----
        now = time.perf_counter()
        frame_time = now - prev
        prev = now
        # Clamp to avoid spiral of death after pauses
        accumulator += min(frame_time, 0.25)

        # ---- Input / events ----
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and state in (STATE_WIN, STATE_LOSE):
                    reset_game()
            elif event.type == MOUSEBUTTONDOWN:
                if state == STATE_PLAY:
                    handle_click(pygame.mouse.get_pos())
                else:
                    reset_game()
            elif event.type == SPAWN_SUN_SKY and state == STATE_PLAY:
                spawn_sky_sun()

        # ---- Update (fixed 60 Hz) ----
        while accumulator >= LOGIC_DT:
            if state == STATE_PLAY:
                level.update(LOGIC_DT)
                for p in list(plant_sprites): p.update(LOGIC_DT)
                for s in list(sun_sprites): s.update(LOGIC_DT)
                for pr in list(projectile_sprites): pr.update(LOGIC_DT)
                for e in list(enemy_sprites): e.update(LOGIC_DT)
                for m in list(mower_sprites): m.update(LOGIC_DT)
                for ex in list(explosion_sprites): ex.update(LOGIC_DT)
                handle_projectile_hits()

                if check_left_edge_and_mowers():
                    state = STATE_LOSE
                if level.final_wave_spawned and len(enemy_sprites) == 0:
                    state = STATE_WIN
            accumulator -= LOGIC_DT

        # ---- Render ----
        screen.fill(SKY_BLUE)
        # Sky sun
        pygame.draw.circle(screen, SUN_YELLOW, (SCREEN_WIDTH - 100, 100), 40)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = SCREEN_WIDTH - 100 + 40 * math.cos(rad)
            y1 = 100 + 40 * math.sin(rad)
            x2 = SCREEN_WIDTH - 100 + 50 * math.cos(rad)
            y2 = 100 + 50 * math.sin(rad)
            pygame.draw.line(screen, SUN_YELLOW, (x1, y1), (x2, y2), 3)

        draw_grid(screen)
        draw_topbar()

        for grp in (sun_sprites, plant_sprites, enemy_sprites, projectile_sprites, mower_sprites, explosion_sprites):
            for s in grp:
                screen.blit(s.surf, s.rect)

        draw_health_bars()
        level.draw_progress(screen)

        if tutorial.active and state == STATE_PLAY:
            tutorial.draw(screen)
        if state == STATE_WIN:
            draw_center_message("You Win!", "All Koopas cleared.", "Press R to play again or click to continue.")
        elif state == STATE_LOSE:
            draw_center_message("Game Over", "Koopas invaded your lawn!", "Press R to retry or click to continue.")

        pygame.display.flip()
        # Visual cap to ~60 FPS
        clock.tick(60)

    pygame.quit()

# Web builds may need a different approach, but desktop runs with run()
if __name__ == "__main__":
    run()
