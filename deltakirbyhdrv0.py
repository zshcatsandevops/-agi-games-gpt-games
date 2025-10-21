#!/usr/bin/env python3
# ============================================================
#  Kirby's Adventure Style Engine with HAL Lab Tweening (Stomp Physics)
# ============================================================

import pygame, numpy as np, math, random, sys, asyncio, platform, os
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception:
    pass

# ============================================================
# Display & Core Settings
# ============================================================
W, H = 800, 500
FPS = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Kirby's Adventure - HAL Lab Tweening + Physics")
clock = pygame.time.Clock()

# ============================================================
# Core Colors / Constants
# ============================================================
KIRBY_PINK = (255, 192, 203)
WADDLE_DEE_ORANGE = (255, 165, 0)
GRASS_GREEN = (34, 139, 34)
SKY_GRADIENT_TOP = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLOOR_Y = 400
LEVEL_LEN = 3600

# ============================================================
# Font
# ============================================================
font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 32)

# ============================================================
# Simplified Ability + Particle Definitions
# ============================================================
class Ability(Enum):
    NONE = 0

particles = []

def create_walk_dust(x, y):
    for _ in range(3):
        particles.append([x + random.randint(-10, 10), y, random.randint(-20, 20), random.randint(-30, -10), 0.4])

def create_explosion(x, y, color, count=10):
    for _ in range(count):
        particles.append([x + random.randint(-10, 10), y, random.randint(-100, 100), random.randint(-100, 0), 0.6])

def create_star_particles(x, y):
    for _ in range(6):
        particles.append([x + random.randint(-5, 5), y, random.randint(-80, 80), random.randint(-120, -20), 0.5])

# ============================================================
# Kirby Class (with Jump + Stomp)
# ============================================================
class Kirby:
    def __init__(self):
        self.x, self.y = 100, FLOOR_Y
        self.vx, self.vy = 0.0, 0.0
        self.r = 22
        self.on_ground = True
        self.ability = Ability.NONE
        self.hp = 6

    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r*2, self.r*2)

    def update(self, dt, keys):
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -200
        if keys[pygame.K_RIGHT]:
            self.vx = 200

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = -400
            self.on_ground = False

        self.vy += 1000 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= FLOOR_Y:
            self.y = FLOOR_Y
            self.vy = 0
            self.on_ground = True

    def draw(self, surf, camx):
        cx = int(self.x - camx)
        cy = int(self.y)
        pygame.draw.circle(surf, KIRBY_PINK, (cx, cy), self.r)

# ============================================================
# Simple Enemy Class (stompable)
# ============================================================
class WaddleDee:
    def __init__(self, x):
        self.x, self.y = float(x), FLOOR_Y
        self.speed = random.choice([-60, 60])
        self.dead = False
        self.ability = Ability.NONE

    def rect(self):
        return pygame.Rect(int(self.x - 15), int(self.y - 15), 30, 30)

    def update(self, dt):
        if not self.dead:
            self.x += self.speed * dt
            if self.x < 50 or self.x > LEVEL_LEN - 50:
                self.speed *= -1

    def draw(self, surf, camx):
        if not self.dead:
            sx = int(self.x - camx)
            pygame.draw.circle(surf, WADDLE_DEE_ORANGE, (sx, int(self.y - 10)), 15)

# ============================================================
# GameState
# ============================================================
class GameState:
    def __init__(self):
        self.player = Kirby()
        self.enemies = [WaddleDee(300), WaddleDee(600), WaddleDee(900)]
        self.camera_x = 0
        self.score = 0

game = GameState()

# ============================================================
# Main Loop with Stomp Physics
# ============================================================
async def main():
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        keys = pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        game.player.update(dt, keys)

        # Enemy update + Kirby stomp physics
        for enemy in game.enemies[:]:
            enemy.update(dt)
            if enemy.dead:
                continue

            if enemy.rect().colliderect(game.player.rect()):
                kirby_rect = game.player.rect()
                enemy_rect = enemy.rect()

                # Check stomp from above
                if game.player.vy > 150 and kirby_rect.bottom - enemy_rect.top < 20:
                    enemy.dead = True
                    game.score += 200
                    create_explosion(enemy.x, enemy.y, WADDLE_DEE_ORANGE, 8)

                    # Kirby bounce physics
                    game.player.vy = -250
                    game.player.on_ground = False
                    create_walk_dust(game.player.x, game.player.y + game.player.r)
                else:
                    # Kirby takes damage (simple knockback)
                    game.player.hp -= 1
                    game.player.vy = -300
                    game.player.vx = -200 if game.player.x < enemy.x else 200

        # Remove dead enemies
        game.enemies = [e for e in game.enemies if not e.dead]

        # Update particles
        for p in particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            p[3] += 200 * dt
            if p[4] <= 0:
                particles.remove(p)

        # Camera follow
        game.camera_x = max(0, min(LEVEL_LEN - W, game.player.x - W/2))

        # Draw
        screen.fill(SKY_GRADIENT_TOP)
        pygame.draw.rect(screen, GRASS_GREEN, (0, FLOOR_Y, W, H - FLOOR_Y))
        game.player.draw(screen, game.camera_x)
        for e in game.enemies:
            e.draw(screen, game.camera_x)
        for p in particles:
            pygame.draw.circle(screen, (255, 255, 0), (int(p[0] - game.camera_x), int(p[1])), 3)

        score_text = font.render(f"SCORE {game.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())
