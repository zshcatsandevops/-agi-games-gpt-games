#!/usr/bin/env python3
# ============================================================
#  Dream Puff Engine 1.0  [C] Samsoft 2025
#  Kirby-style platformer clone — self-contained Pygame build
#  No external assets: all art & sound generated on the fly
# ============================================================

import pygame, numpy as np, math, random, sys
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ------------------------------------------------------------
# Window setup
# ------------------------------------------------------------
W, H = 600, 400
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Dream Puff Engine 1.0 [C] Samsoft 2025")
clock = pygame.time.Clock()

# ------------------------------------------------------------
# Utility: make sine wave tones
# ------------------------------------------------------------
def tone(freq, ms, vol=0.4):
    sample_rate = 44100
    n = int(sample_rate * ms / 1000)
    t = np.arange(n)
    buf = (np.sin(2 * math.pi * freq * t / sample_rate) * 32767 * vol).astype(np.int16)
    return pygame.mixer.Sound(buffer=buf)

jump_snd = tone(880, 150)
pop_snd  = tone(440, 120)
music_snd = tone(220, 1000, 0.1)

# ------------------------------------------------------------
# Game constants
# ------------------------------------------------------------
GROUND_Y = 330
GRAVITY  = 0.6
JUMP_PWR = -10
MOVE_SPD = 4
SKY = (140, 200, 255)
GRASS = (80, 200, 80)
PINK = (255, 120, 200)
TREEGREEN = (40, 180, 60)
BROWN = (100, 70, 30)

# ------------------------------------------------------------
# Player
# ------------------------------------------------------------
class Puff:
    def __init__(self):
        self.x, self.y = 100, GROUND_Y
        self.vx, self.vy = 0, 0
        self.on_ground = True
        self.r = 18
    def rect(self): return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)
    def update(self, keys):
        self.vx = (-MOVE_SPD if keys[pygame.K_a] else MOVE_SPD if keys[pygame.K_d] else 0)
        if keys[pygame.K_w]: self.vy -= 0.2
        if not self.on_ground: self.vy += GRAVITY
        if self.y >= GROUND_Y: 
            self.y, self.vy, self.on_ground = GROUND_Y, 0, True
        self.x += self.vx
        self.y += self.vy
        self.x = max(20, min(W-20, self.x))
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_PWR
            self.on_ground = False
            jump_snd.play()
    def draw(self, surf):
        # body
        pygame.draw.circle(surf, PINK, (int(self.x), int(self.y)), self.r)
        # face
        pygame.draw.circle(surf, (255,255,255), (int(self.x-5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x-5), int(self.y-4)), 2)
        pygame.draw.circle(surf, (255,255,255), (int(self.x+5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x+5), int(self.y-4)), 2)

# ------------------------------------------------------------
# Enemies
# ------------------------------------------------------------
class Waddle:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.dir = random.choice([-1,1])
        self.dead = False
    def rect(self): return pygame.Rect(self.x-10, self.y-10, 20, 20)
    def update(self):
        self.x += self.dir * 2
        if self.x < 50 or self.x > W-50: self.dir *= -1
    def draw(self, surf):
        if not self.dead:
            pygame.draw.rect(surf, (255,150,50), self.rect())

# ------------------------------------------------------------
# Whispy-like Tree boss
# ------------------------------------------------------------
class TreeBoss:
    def __init__(self, x):
        self.x, self.y = x, GROUND_Y-60
        self.hp = 5
        self.timer = 0
    def rect(self): return pygame.Rect(self.x-40, self.y-80, 80, 140)
    def update(self):
        self.timer += 1
    def draw(self, surf):
        pygame.draw.rect(surf, BROWN, (self.x-15, self.y, 30, 80))
        pygame.draw.circle(surf, TREEGREEN, (self.x, self.y-40), 50)
        # eyes
        pygame.draw.circle(surf, (0,0,0), (self.x-15, self.y-40), 6)
        pygame.draw.circle(surf, (0,0,0), (self.x+15, self.y-40), 6)
        # mouth
        pygame.draw.rect(surf, (0,0,0), (self.x-10, self.y-15, 20, 10))

# ------------------------------------------------------------
# Game setup
# ------------------------------------------------------------
player = Puff()
enemies = [Waddle(300), Waddle(500)]
boss = TreeBoss(900)
scroll_x = 0
score = 0
state = "menu"

font = pygame.font.SysFont("consolas", 18)
music_snd.play(-1)

# ------------------------------------------------------------
# Draw background
# ------------------------------------------------------------
def draw_background(surf, scroll):
    surf.fill(SKY)
    for i in range(0, 1200, 120):
        x = i - scroll
        pygame.draw.circle(surf, (255,255,255), (x%1200, 60), 20)
    pygame.draw.rect(surf, GRASS, (0,GROUND_Y,W,H-GROUND_Y))

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if state == "menu" and e.key == pygame.K_RETURN:
                state = "play"; score = 0; scroll_x = 0
            if state == "play" and e.key in (pygame.K_z, pygame.K_SPACE):
                player.jump()

    keys = pygame.key.get_pressed()
    if state == "menu":
        screen.fill((40,20,80))
        title = font.render("DREAM PUFF ENGINE", True, (255,180,220))
        hint  = font.render("Press ENTER to start  (WASD + Z to play)", True, (255,255,255))
        screen.blit(title, (W/2 - title.get_width()/2, 150))
        screen.blit(hint,  (W/2 - hint.get_width()/2, 200))
    elif state == "play":
        # scrolling background
        scroll_x = (scroll_x + player.vx) % 1200
        draw_background(screen, scroll_x)

        player.update(keys)
        player.draw(screen)

        for w in enemies:
            if not w.dead:
                w.update()
                if w.rect().colliderect(player.rect()):
                    pop_snd.play()
                    w.dead = True
                    score += 1
            w.draw(screen)

        if boss.x - scroll_x < W:
            boss.update()
            boss.draw(screen)
            if boss.rect().colliderect(player.rect()) and boss.hp > 0:
                boss.hp -= 1
                pop_snd.play()
                if boss.hp <= 0:
                    state = "win"

        screen.blit(font.render(f"Score: {score}", True, (0,0,0)), (10,10))
    elif state == "win":
        screen.fill((255,230,250))
        txt = font.render("You befriended the Great Tree!", True, (0,0,0))
        screen.blit(txt, (W/2 - txt.get_width()/2, H/2))
        if keys[pygame.K_RETURN]: state = "menu"

    pygame.display.flip()
    clock.tick(60)
#!/usr/bin/env python3
# ============================================================
#  Dream Puff Engine 1.0  [C] Samsoft 2025
#  Kirby-style platformer clone — self-contained Pygame build
#  No external assets: all art & sound generated on the fly
# ============================================================

import pygame, numpy as np, math, random, sys
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ------------------------------------------------------------
# Window setup
# ------------------------------------------------------------
W, H = 600, 400
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Dream Puff Engine 1.0 [C] Samsoft 2025")
clock = pygame.time.Clock()

# ------------------------------------------------------------
# Utility: make sine wave tones
# ------------------------------------------------------------
def tone(freq, ms, vol=0.4):
    sample_rate = 44100
    n = int(sample_rate * ms / 1000)
    t = np.arange(n)
    buf = (np.sin(2 * math.pi * freq * t / sample_rate) * 32767 * vol).astype(np.int16)
    return pygame.mixer.Sound(buffer=buf)

jump_snd = tone(880, 150)
pop_snd  = tone(440, 120)
music_snd = tone(220, 1000, 0.1)

# ------------------------------------------------------------
# Game constants
# ------------------------------------------------------------
GROUND_Y = 330
GRAVITY  = 0.6
JUMP_PWR = -10
MOVE_SPD = 4
SKY = (140, 200, 255)
GRASS = (80, 200, 80)
PINK = (255, 120, 200)
TREEGREEN = (40, 180, 60)
BROWN = (100, 70, 30)

# ------------------------------------------------------------
# Player
# ------------------------------------------------------------
class Puff:
    def __init__(self):
        self.x, self.y = 100, GROUND_Y
        self.vx, self.vy = 0, 0
        self.on_ground = True
        self.r = 18
    def rect(self): return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)
    def update(self, keys):
        self.vx = (-MOVE_SPD if keys[pygame.K_a] else MOVE_SPD if keys[pygame.K_d] else 0)
        if keys[pygame.K_w]: self.vy -= 0.2
        if not self.on_ground: self.vy += GRAVITY
        if self.y >= GROUND_Y: 
            self.y, self.vy, self.on_ground = GROUND_Y, 0, True
        self.x += self.vx
        self.y += self.vy
        self.x = max(20, min(W-20, self.x))
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_PWR
            self.on_ground = False
            jump_snd.play()
    def draw(self, surf):
        # body
        pygame.draw.circle(surf, PINK, (int(self.x), int(self.y)), self.r)
        # face
        pygame.draw.circle(surf, (255,255,255), (int(self.x-5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x-5), int(self.y-4)), 2)
        pygame.draw.circle(surf, (255,255,255), (int(self.x+5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x+5), int(self.y-4)), 2)

# ------------------------------------------------------------
# Enemies
# ------------------------------------------------------------
class Waddle:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.dir = random.choice([-1,1])
        self.dead = False
    def rect(self): return pygame.Rect(self.x-10, self.y-10, 20, 20)
    def update(self):
        self.x += self.dir * 2
        if self.x < 50 or self.x > W-50: self.dir *= -1
    def draw(self, surf):
        if not self.dead:
            pygame.draw.rect(surf, (255,150,50), self.rect())

# ------------------------------------------------------------
# Whispy-like Tree boss
# ------------------------------------------------------------
class TreeBoss:
    def __init__(self, x):
        self.x, self.y = x, GROUND_Y-60
        self.hp = 5
        self.timer = 0
    def rect(self): return pygame.Rect(self.x-40, self.y-80, 80, 140)
    def update(self):
        self.timer += 1
    def draw(self, surf):
        pygame.draw.rect(surf, BROWN, (self.x-15, self.y, 30, 80))
        pygame.draw.circle(surf, TREEGREEN, (self.x, self.y-40), 50)
        # eyes
        pygame.draw.circle(surf, (0,0,0), (self.x-15, self.y-40), 6)
        pygame.draw.circle(surf, (0,0,0), (self.x+15, self.y-40), 6)
        # mouth
        pygame.draw.rect(surf, (0,0,0), (self.x-10, self.y-15, 20, 10))

# ------------------------------------------------------------
# Game setup
# ------------------------------------------------------------
player = Puff()
enemies = [Waddle(300), Waddle(500)]
boss = TreeBoss(900)
scroll_x = 0
score = 0
state = "menu"

font = pygame.font.SysFont("consolas", 18)
music_snd.play(-1)

# ------------------------------------------------------------
# Draw background
# ------------------------------------------------------------
def draw_background(surf, scroll):
    surf.fill(SKY)
    for i in range(0, 1200, 120):
        x = i - scroll
        pygame.draw.circle(surf, (255,255,255), (x%1200, 60), 20)
    pygame.draw.rect(surf, GRASS, (0,GROUND_Y,W,H-GROUND_Y))

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if state == "menu" and e.key == pygame.K_RETURN:
                state = "play"; score = 0; scroll_x = 0
            if state == "play" and e.key in (pygame.K_z, pygame.K_SPACE):
                player.jump()

    keys = pygame.key.get_pressed()
    if state == "menu":
        screen.fill((40,20,80))
        title = font.render("DREAM PUFF ENGINE", True, (255,180,220))
        hint  = font.render("Press ENTER to start  (WASD + Z to play)", True, (255,255,255))
        screen.blit(title, (W/2 - title.get_width()/2, 150))
        screen.blit(hint,  (W/2 - hint.get_width()/2, 200))
    elif state == "play":
        # scrolling background
        scroll_x = (scroll_x + player.vx) % 1200
        draw_background(screen, scroll_x)

        player.update(keys)
        player.draw(screen)

        for w in enemies:
            if not w.dead:
                w.update()
                if w.rect().colliderect(player.rect()):
                    pop_snd.play()
                    w.dead = True
                    score += 1
            w.draw(screen)

        if boss.x - scroll_x < W:
            boss.update()
            boss.draw(screen)
            if boss.rect().colliderect(player.rect()) and boss.hp > 0:
                boss.hp -= 1
                pop_snd.play()
                if boss.hp <= 0:
                    state = "win"

        screen.blit(font.render(f"Score: {score}", True, (0,0,0)), (10,10))
    elif state == "win":
        screen.fill((255,230,250))
        txt = font.render("You befriended the Great Tree!", True, (0,0,0))
        screen.blit(txt, (W/2 - txt.get_width()/2, H/2))
        if keys[pygame.K_RETURN]: state = "menu"

    pygame.display.flip()
    clock.tick(60)
#!/usr/bin/env python3
# ============================================================
#  Dream Puff Engine 1.0  [C] Samsoft 2025
#  Kirby-style platformer clone — self-contained Pygame build
#  No external assets: all art & sound generated on the fly
# ============================================================

import pygame, numpy as np, math, random, sys
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# ------------------------------------------------------------
# Window setup
# ------------------------------------------------------------
W, H = 600, 400
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Dream Puff Engine 1.0 [C] Samsoft 2025")
clock = pygame.time.Clock()

# ------------------------------------------------------------
# Utility: make sine wave tones
# ------------------------------------------------------------
def tone(freq, ms, vol=0.4):
    sample_rate = 44100
    n = int(sample_rate * ms / 1000)
    t = np.arange(n)
    buf = (np.sin(2 * math.pi * freq * t / sample_rate) * 32767 * vol).astype(np.int16)
    return pygame.mixer.Sound(buffer=buf)

jump_snd = tone(880, 150)
pop_snd  = tone(440, 120)
music_snd = tone(220, 1000, 0.1)

# ------------------------------------------------------------
# Game constants
# ------------------------------------------------------------
GROUND_Y = 330
GRAVITY  = 0.6
JUMP_PWR = -10
MOVE_SPD = 4
SKY = (140, 200, 255)
GRASS = (80, 200, 80)
PINK = (255, 120, 200)
TREEGREEN = (40, 180, 60)
BROWN = (100, 70, 30)

# ------------------------------------------------------------
# Player
# ------------------------------------------------------------
class Puff:
    def __init__(self):
        self.x, self.y = 100, GROUND_Y
        self.vx, self.vy = 0, 0
        self.on_ground = True
        self.r = 18
    def rect(self): return pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)
    def update(self, keys):
        self.vx = (-MOVE_SPD if keys[pygame.K_a] else MOVE_SPD if keys[pygame.K_d] else 0)
        if keys[pygame.K_w]: self.vy -= 0.2
        if not self.on_ground: self.vy += GRAVITY
        if self.y >= GROUND_Y: 
            self.y, self.vy, self.on_ground = GROUND_Y, 0, True
        self.x += self.vx
        self.y += self.vy
        self.x = max(20, min(W-20, self.x))
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_PWR
            self.on_ground = False
            jump_snd.play()
    def draw(self, surf):
        # body
        pygame.draw.circle(surf, PINK, (int(self.x), int(self.y)), self.r)
        # face
        pygame.draw.circle(surf, (255,255,255), (int(self.x-5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x-5), int(self.y-4)), 2)
        pygame.draw.circle(surf, (255,255,255), (int(self.x+5), int(self.y-4)), 3)
        pygame.draw.circle(surf, (0,0,0), (int(self.x+5), int(self.y-4)), 2)

# ------------------------------------------------------------
# Enemies
# ------------------------------------------------------------
class Waddle:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.dir = random.choice([-1,1])
        self.dead = False
    def rect(self): return pygame.Rect(self.x-10, self.y-10, 20, 20)
    def update(self):
        self.x += self.dir * 2
        if self.x < 50 or self.x > W-50: self.dir *= -1
    def draw(self, surf):
        if not self.dead:
            pygame.draw.rect(surf, (255,150,50), self.rect())

# ------------------------------------------------------------
# Whispy-like Tree boss
# ------------------------------------------------------------
class TreeBoss:
    def __init__(self, x):
        self.x, self.y = x, GROUND_Y-60
        self.hp = 5
        self.timer = 0
    def rect(self): return pygame.Rect(self.x-40, self.y-80, 80, 140)
    def update(self):
        self.timer += 1
    def draw(self, surf):
        pygame.draw.rect(surf, BROWN, (self.x-15, self.y, 30, 80))
        pygame.draw.circle(surf, TREEGREEN, (self.x, self.y-40), 50)
        # eyes
        pygame.draw.circle(surf, (0,0,0), (self.x-15, self.y-40), 6)
        pygame.draw.circle(surf, (0,0,0), (self.x+15, self.y-40), 6)
        # mouth
        pygame.draw.rect(surf, (0,0,0), (self.x-10, self.y-15, 20, 10))

# ------------------------------------------------------------
# Game setup
# ------------------------------------------------------------
player = Puff()
enemies = [Waddle(300), Waddle(500)]
boss = TreeBoss(900)
scroll_x = 0
score = 0
state = "menu"

font = pygame.font.SysFont("consolas", 18)
music_snd.play(-1)

# ------------------------------------------------------------
# Draw background
# ------------------------------------------------------------
def draw_background(surf, scroll):
    surf.fill(SKY)
    for i in range(0, 1200, 120):
        x = i - scroll
        pygame.draw.circle(surf, (255,255,255), (x%1200, 60), 20)
    pygame.draw.rect(surf, GRASS, (0,GROUND_Y,W,H-GROUND_Y))

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if state == "menu" and e.key == pygame.K_RETURN:
                state = "play"; score = 0; scroll_x = 0
            if state == "play" and e.key in (pygame.K_z, pygame.K_SPACE):
                player.jump()

    keys = pygame.key.get_pressed()
    if state == "menu":
        screen.fill((40,20,80))
        title = font.render("DREAM PUFF ENGINE", True, (255,180,220))
        hint  = font.render("Press ENTER to start  (WASD + Z to play)", True, (255,255,255))
        screen.blit(title, (W/2 - title.get_width()/2, 150))
        screen.blit(hint,  (W/2 - hint.get_width()/2, 200))
    elif state == "play":
        # scrolling background
        scroll_x = (scroll_x + player.vx) % 1200
        draw_background(screen, scroll_x)

        player.update(keys)
        player.draw(screen)

        for w in enemies:
            if not w.dead:
                w.update()
                if w.rect().colliderect(player.rect()):
                    pop_snd.play()
                    w.dead = True
                    score += 1
            w.draw(screen)

        if boss.x - scroll_x < W:
            boss.update()
            boss.draw(screen)
            if boss.rect().colliderect(player.rect()) and boss.hp > 0:
                boss.hp -= 1
                pop_snd.play()
                if boss.hp <= 0:
                    state = "win"

        screen.blit(font.render(f"Score: {score}", True, (0,0,0)), (10,10))
    elif state == "win":
        screen.fill((255,230,250))
        txt = font.render("You befriended the Great Tree!", True, (0,0,0))
        screen.blit(txt, (W/2 - txt.get_width()/2, H/2))
        if keys[pygame.K_RETURN]: state = "menu"

    pygame.display.flip()
    clock.tick(60)
