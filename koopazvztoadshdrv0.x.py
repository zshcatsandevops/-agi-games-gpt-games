#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Koopas vs Toads — Basic Game Engine
# by Samsoft 1999-2025
import pygame
import time
import math
import random

pygame.init()

# ----------------------------------------------------------------
# GLOBAL CONFIG
# ----------------------------------------------------------------
W, H = 600, 400
WIN = pygame.display.set_mode((W, H))
pygame.display.set_caption("Koopas vs Toads — Basic Engine © Samsoft 1999-2025")
clock = pygame.time.Clock()

# Colors (Graphite Silver XP + PvZ greens)
SILVER = (170, 170, 170)
DARK = (60, 60, 60)
LIGHT = (220, 220, 220)
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
DARKGREEN = (0, 128, 0)

font = pygame.font.SysFont("segoeui", 24)
bigfont = pygame.font.SysFont("segoeui", 48, True)

# ----------------------------------------------------------------
# ENTITY CLASSES
# ----------------------------------------------------------------
class Sun:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.vel_y = 1

    def update(self):
        self.rect.y += self.vel_y

    def draw(self, surf):
        pygame.draw.circle(surf, YELLOW, self.rect.center, 10)

class Pea:
    def __init__(self, x, y, row):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.vel_x = 5
        self.row = row

    def update(self):
        self.rect.x += self.vel_x

    def draw(self, surf):
        pygame.draw.circle(surf, GREEN, self.rect.center, 5)

class Plant:
    def __init__(self, plant_type, row, col):
        self.type = plant_type
        self.row = row
        self.col = col
        tile_w, tile_h = 60, 80
        self.rect = pygame.Rect(col * tile_w, row * tile_h, tile_w, tile_h)
        self.health = 100 if plant_type == 'wallnut' else 50
        self.shoot_timer = 0
        self.produce_timer = 0

    def update(self, peas, suns):
        if self.type == 'peashooter':
            self.shoot_timer += 1
            if self.shoot_timer > 60:  # Shoot every second
                peas.append(Pea(self.rect.right, self.rect.centery, self.row))
                self.shoot_timer = 0
        elif self.type == 'sunflower':
            self.produce_timer += 1
            if self.produce_timer > 300:  # Produce every 5 seconds
                suns.append(Sun(self.rect.centerx, self.rect.bottom))
                self.produce_timer = 0

    def draw(self, surf):
        color = GREEN if self.type == 'peashooter' else YELLOW if self.type == 'sunflower' else BROWN
        pygame.draw.rect(surf, color, self.rect)

class Zombie:
    def __init__(self, row):
        tile_h = 80
        self.row = row
        self.rect = pygame.Rect(W, row * tile_h, 60, tile_h)
        self.health = 100
        self.speed = 1

    def update(self, plants):
        self.rect.x -= self.speed
        for plant in plants:
            if plant.row == self.row and plant.rect.colliderect(self.rect):
                plant.health -= 1
                if plant.health <= 0:
                    plants.remove(plant)
                break

    def draw(self, surf):
        pygame.draw.rect(surf, DARKGREEN, self.rect)

# ----------------------------------------------------------------
# UTILITIES
# ----------------------------------------------------------------
def gradient_bg(surf):
    for y in range(H):
        c = int(100 + 80 * (y / H))
        pygame.draw.line(surf, (c, c, c + 40), (0, y), (W, y))
    # bloom spot
    cx, cy = W - 80, 70
    for r in range(40, 120, 10):
        alpha = max(20, 160 - (r - 40) * 2)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 240, 180, alpha), (r, r), r)
        surf.blit(s, (cx - r, cy - r), special_flags=pygame.BLEND_PREMULTIPLIED)

def draw_button(txt, rect, hover=False):
    color = LIGHT if hover else SILVER
    pygame.draw.rect(WIN, color, rect, border_radius=10)
    pygame.draw.rect(WIN, DARK, rect, 2, border_radius=10)
    text = font.render(txt, True, BLACK)
    WIN.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                    rect.y + (rect.h - text.get_height()) // 2))

def fade_out():
    f = pygame.Surface((W, H))
    for a in range(0, 255, 8):
        gradient_bg(WIN)
        f.set_alpha(a)
        WIN.blit(f, (0, 0))
        pygame.display.flip()
        clock.tick(60)

# ----------------------------------------------------------------
# LOADING SCREEN
# ----------------------------------------------------------------
def loading_screen():
    start = time.time()
    progress = 0
    while progress < 1.0:
        gradient_bg(WIN)
        label = bigfont.render("Loading Koopas vs Toads...", True, BLACK)
        WIN.blit(label, (W // 2 - label.get_width() // 2, H // 2 - 60))
        # bar
        bar_w = 300
        bar_h = 20
        x = (W - bar_w) // 2
        y = H // 2
        pygame.draw.rect(WIN, DARK, (x, y, bar_w, bar_h), 2)
        fill = int(bar_w * progress)
        pygame.draw.rect(WIN, YELLOW, (x, y, fill, bar_h))
        pygame.display.flip()
        clock.tick(60)
        progress = min(1.0, (time.time() - start) / 2.0)
    fade_out()

# ----------------------------------------------------------------
# MENU LOOP
# ----------------------------------------------------------------
def main_menu():
    buttons = {
        "Play": pygame.Rect(W // 2 - 80, 180, 160, 45),
        "Options": pygame.Rect(W // 2 - 80, 240, 160, 45),
        "Quit": pygame.Rect(W // 2 - 80, 300, 160, 45)
    }
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for k, r in buttons.items():
                    if r.collidepoint(e.pos):
                        if k == "Play":
                            return "play"
                        elif k == "Quit":
                            return "quit"
        gradient_bg(WIN)
        title = bigfont.render("Koopas vs Toads © Samsoft 1999-2025", True, BLACK)
        WIN.blit(title, (W // 2 - title.get_width() // 2, 80))
        mpos = pygame.mouse.get_pos()
        for k, r in buttons.items():
            draw_button(k, r, r.collidepoint(mpos))
        pygame.display.flip()
        clock.tick(60)

# ----------------------------------------------------------------
# GAME STAGE
# ----------------------------------------------------------------
def play_stage():
    TILE_W, TILE_H = 60, 80
    GRID_ROWS, GRID_COLS = 5, 9
    grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    suns = []
    peas = []
    plants = []
    zombies = []
    sun_count = 50
    selected_plant = None
    available_plants = ['peashooter', 'sunflower', 'wallnut']
    costs = {'peashooter': 50, 'sunflower': 50, 'wallnut': 50}
    button_w, button_h = 60, 40
    plant_buttons = [pygame.Rect(50 + i * 70, H - 50, button_w, button_h) for i in range(len(available_plants))]
    spawn_timer = 0
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                # Select plant
                selected_index = -1
                for i, rect in enumerate(plant_buttons):
                    if rect.collidepoint(mx, my):
                        selected_index = i
                        break
                if selected_index != -1:
                    selected_plant = available_plants[selected_index]
                    continue
                # Plant on grid
                if selected_plant:
                    row = my // TILE_H
                    col = mx // TILE_W
                    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS and grid[row][col] is None and sun_count >= costs[selected_plant]:
                        plant = Plant(selected_plant, row, col)
                        plants.append(plant)
                        grid[row][col] = plant
                        sun_count -= costs[selected_plant]
                        selected_plant = None
                # Collect sun
                for sun in suns[:]:
                    if sun.rect.collidepoint(mx, my):
                        sun_count += 25
                        suns.remove(sun)
                        break
        # Spawn sun
        if random.random() < 0.005:
            x = random.randint(0, W - 20)
            suns.append(Sun(x, 0))
        # Spawn zombie
        spawn_timer += 1
        if spawn_timer > 180:
            row = random.randint(0, GRID_ROWS - 1)
            zombies.append(Zombie(row))
            spawn_timer = 0
        # Update suns
        for sun in suns[:]:
            sun.update()
            if sun.rect.bottom > H:
                suns.remove(sun)
        # Update peas
        for pea in peas[:]:
            pea.update()
            if pea.rect.left > W:
                peas.remove(pea)
            else:
                hit = False
                for zombie in zombies[:]:
                    if pea.row == zombie.row and pea.rect.colliderect(zombie.rect):
                        zombie.health -= 20
                        peas.remove(pea)
                        if zombie.health <= 0:
                            zombies.remove(zombie)
                        hit = True
                        break
                if hit:
                    continue
        # Update zombies
        for zombie in zombies[:]:
            zombie.update(plants)
            if zombie.rect.right < 0:
                running = False
        # Update plants
        for plant in plants[:]:
            plant.update(peas, suns)
        # Draw
        WIN.fill(GREEN)
        # Grid lines
        for r in range(GRID_ROWS + 1):
            pygame.draw.line(WIN, WHITE, (0, r * TILE_H), (W, r * TILE_H))
        for c in range(GRID_COLS + 1):
            pygame.draw.line(WIN, WHITE, (c * TILE_W, 0), (c * TILE_W, H - 50))
        for plant in plants:
            plant.draw(WIN)
        for zombie in zombies:
            zombie.draw(WIN)
        for pea in peas:
            pea.draw(WIN)
        for sun in suns:
            sun.draw(WIN)
        # Plant buttons
        for i, p in enumerate(available_plants):
            hover = selected_plant == p
            short_txt = p[:4].upper()
            draw_button(short_txt, plant_buttons[i], hover)
        # UI text
        sun_text = font.render(f"Sun: {sun_count}", True, BLACK)
        WIN.blit(sun_text, (10, H - 45))
        if selected_plant:
            sel_text = font.render(f"Selected: {selected_plant}", True, BLACK)
            WIN.blit(sel_text, (W // 2 - 60, H - 45))
        pygame.display.flip()
        clock.tick(60)
    fade_out()

# ----------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------
def run():
    loading_screen()
    while True:
        action = main_menu()
        if action == "quit":
            break
        elif action == "play":
            play_stage()
    pygame.quit()

if __name__ == "__main__":
    run()
