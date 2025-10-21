#!/usr/bin/env python3
# ============================================================
#  ULTRA! Kirby FX Adventure 0.x
#  Enhanced PC Port with Copy Abilities & FX
#  Features: 7 Copy Abilities, 6 Bosses, Particle System
# ============================================================

import pygame, numpy as np, math, random, sys, asyncio, platform
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
pygame.display.set_caption("ULTRA! Kirby FX Adventure 0.x")
clock = pygame.time.Clock()

# ============================================================
# Enhanced Color Palette
# ============================================================
KIRBY_PINK = (255, 170, 220)
KIRBY_FEET = (220, 0, 100)
SKY_GRADIENT_TOP = (135, 206, 250)
SKY_GRADIENT_BOTTOM = (255, 182, 193)
GRASS_GREEN = (50, 205, 50)
WADDLE_DEE_ORANGE = (255, 180, 100)
BOSS_HP_RED = (255, 50, 50)
BOSS_HP_YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
STAR_YELLOW = (255, 255, 100)
FIRE_ORANGE = (255, 100, 0)
FIRE_RED = (255, 50, 0)
ICE_BLUE = (100, 200, 255)
SPARK_YELLOW = (255, 255, 0)
STONE_GRAY = (128, 128, 128)
SWORD_SILVER = (192, 192, 192)
BEAM_PURPLE = (200, 100, 255)
TORNADO_GREEN = (100, 255, 100)

FLOOR_Y = 400
LEVEL_LEN = 3600

font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 32)
ultra_font = pygame.font.Font(None, 48)

# ============================================================
# Sound System
# ============================================================
def tone(freq, ms, vol=0.4):
    if not pygame.mixer.get_init():
        return None
    sample_rate = 44100
    n = int(sample_rate * ms / 1000)
    t = np.arange(n)
    buf = (np.sin(2 * math.pi * freq * t / sample_rate) * 32767 * vol).astype(np.int16)
    
    # Create stereo buffer
    stereo_buf = np.zeros((n, 2), dtype=np.int16)
    stereo_buf[:, 0] = buf
    stereo_buf[:, 1] = buf
    
    try:
        return pygame.mixer.Sound(buffer=stereo_buf)
    except:
        return pygame.mixer.Sound(buffer=stereo_buf.tobytes())

# Enhanced sound library
sounds = {
    "jump": tone(660, 120),
    "hit": tone(220, 150),
    "win": tone(1046.50, 200),
    "inhale": tone(440, 300, 0.3),
    "swallow": tone(880, 100),
    "fire": tone(200, 200, 0.5),
    "ice": tone(1200, 150, 0.3),
    "spark": tone(1500, 100, 0.4),
    "beam": tone(800, 250, 0.3),
    "sword": tone(400, 100, 0.5),
    "stone": tone(100, 200, 0.6),
    "tornado": tone(300, 400, 0.3),
    "boss_hurt": tone(150, 300, 0.5),
    "power_up": tone(1318.51, 150),  # E6 note
}

# ============================================================
# Copy Abilities System
# ============================================================
class Ability(Enum):
    NONE = 0
    FIRE = 1
    ICE = 2
    SPARK = 3
    STONE = 4
    SWORD = 5
    BEAM = 6
    TORNADO = 7

ABILITY_COLORS = {
    Ability.FIRE: FIRE_ORANGE,
    Ability.ICE: ICE_BLUE,
    Ability.SPARK: SPARK_YELLOW,
    Ability.STONE: STONE_GRAY,
    Ability.SWORD: SWORD_SILVER,
    Ability.BEAM: BEAM_PURPLE,
    Ability.TORNADO: TORNADO_GREEN,
}

# ============================================================
# Particle System
# ============================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, life=1.0, size=3, gravity=0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0
    
    def draw(self, surf, camx):
        alpha = self.life / self.max_life
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(surf, self.color, 
                             (int(self.x - camx), int(self.y)), size)

particles: List[Particle] = []

def create_explosion(x, y, color, count=20):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(50, 200)
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            color,
            life=random.uniform(0.3, 0.8),
            size=random.randint(2, 6),
            gravity=200
        ))

def create_star_particles(x, y):
    for _ in range(10):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100, 300)
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 100,
            STAR_YELLOW,
            life=0.5,
            size=4,
            gravity=400
        ))

# ============================================================
# Input System
# ============================================================
class Input:
    def __init__(self):
        self.prev = pygame.key.get_pressed()
        self.cur = self.prev
        self.binds = {
            "left": [pygame.K_a, pygame.K_LEFT],
            "right": [pygame.K_d, pygame.K_RIGHT],
            "jump": [pygame.K_SPACE, pygame.K_z, pygame.K_w, pygame.K_UP],
            "inhale": [pygame.K_x, pygame.K_c],
            "ability": [pygame.K_v, pygame.K_LSHIFT],
            "drop": [pygame.K_q],
            "pause": [pygame.K_p],
            "start": [pygame.K_RETURN],
        }
    
    def update(self):
        self.prev = self.cur
        self.cur = pygame.key.get_pressed()
    
    def down(self, action):
        return any(self.cur[k] for k in self.binds.get(action, []))
    
    def just_pressed(self, action):
        return any(self.cur[k] and not self.prev[k] 
                  for k in self.binds.get(action, []))

inputs = Input()

# ============================================================
# Projectile System
# ============================================================
class Projectile:
    def __init__(self, x, y, vx, vy, damage, ability, owner="player"):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.ability = ability
        self.owner = owner
        self.lifetime = 2.0
        self.dead = False
    
    def rect(self):
        return pygame.Rect(int(self.x - 10), int(self.y - 10), 20, 20)
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0 or self.y > FLOOR_Y + 50:
            self.dead = True
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        color = ABILITY_COLORS.get(self.ability, WHITE)
        pygame.draw.circle(surf, color, (sx, int(self.y)), 8)
        if self.ability == Ability.FIRE:
            pygame.draw.circle(surf, FIRE_RED, (sx, int(self.y)), 4)

projectiles: List[Projectile] = []

# ============================================================
# Enhanced Kirby with Copy Abilities
# ============================================================
class Kirby:
    def __init__(self):
        self.r = 22
        self.x, self.y = 100, FLOOR_Y
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = True
        self.facing_right = True
        
        # Movement
        self.max_speed = 200.0
        self.accel = 1400.0
        self.friction = 7.0
        self.gravity = 1500.0
        self.jump_vel = -480.0
        
        # Copy ability
        self.ability = Ability.NONE
        self.ability_cooldown = 0.0
        
        # Inhale system
        self.inhaling = False
        self.inhale_range = 120
        self.has_enemy = False
        self.stored_ability = Ability.NONE
        
        # Combat
        self.hp = 6
        self.max_hp = 6
        self.invuln_time = 0.0
        
        # Animation
        self.anim_time = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r), 
                          self.r * 2, self.r * 2)
    
    def update(self, dt):
        self.anim_time += dt
        self.ability_cooldown = max(0, self.ability_cooldown - dt)
        self.invuln_time = max(0, self.invuln_time - dt)
        
        # Movement
        move_dir = inputs.down("right") - inputs.down("left")
        if move_dir != 0:
            self.vx += move_dir * self.accel * dt
            self.facing_right = move_dir > 0
        else:
            self.vx *= max(0.0, 1.0 - self.friction * dt)
        
        self.vx = max(-self.max_speed, min(self.max_speed, self.vx))
        
        # Jumping
        if inputs.just_pressed("jump") and self.on_ground:
            self.vy = self.jump_vel
            self.on_ground = False
            if sounds["jump"]:
                sounds["jump"].play()
        
        # Gravity
        g = self.gravity
        if self.vy > 0:
            g *= 1.5  # Fall faster
        elif self.vy < 0 and not inputs.down("jump"):
            g *= 2.5  # Variable jump height
        self.vy += g * dt
        
        # Position update
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Ground collision
        if self.y >= FLOOR_Y:
            self.y = FLOOR_Y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
        
        # Level bounds
        self.x = max(25, min(LEVEL_LEN - 25, self.x))
        
        # Inhale system
        if inputs.down("inhale") and self.ability == Ability.NONE:
            self.inhaling = True
            if not self.has_enemy and sounds["inhale"] and random.random() < 0.1:
                sounds["inhale"].play()
        else:
            if self.inhaling and self.has_enemy:
                # Swallow enemy
                if sounds["swallow"]:
                    sounds["swallow"].play()
                self.ability = self.stored_ability
                self.has_enemy = False
                create_star_particles(self.x, self.y - 20)
            self.inhaling = False
        
        # Use ability
        if inputs.just_pressed("ability") and self.ability != Ability.NONE:
            if self.ability_cooldown <= 0:
                self.use_ability()
        
        # Drop ability
        if inputs.just_pressed("drop") and self.ability != Ability.NONE:
            create_star_particles(self.x, self.y - 20)
            self.ability = Ability.NONE
    
    def use_ability(self):
        self.ability_cooldown = 0.5
        
        if self.ability == Ability.FIRE:
            if sounds["fire"]:
                sounds["fire"].play()
            # Fire breath
            for i in range(3):
                offset = (i - 1) * 15
                projectiles.append(Projectile(
                    self.x + (40 if self.facing_right else -40),
                    self.y + offset,
                    (300 if self.facing_right else -300) + random.randint(-50, 50),
                    random.randint(-50, 50),
                    2, Ability.FIRE
                ))
            create_explosion(self.x + (30 if self.facing_right else -30), 
                           self.y, FIRE_ORANGE, 10)
        
        elif self.ability == Ability.ICE:
            if sounds["ice"]:
                sounds["ice"].play()
            # Ice breath
            projectiles.append(Projectile(
                self.x + (30 if self.facing_right else -30),
                self.y,
                250 if self.facing_right else -250,
                0,
                2, Ability.ICE
            ))
            for _ in range(5):
                particles.append(Particle(
                    self.x + (30 if self.facing_right else -30),
                    self.y + random.randint(-10, 10),
                    (100 if self.facing_right else -100) + random.randint(-30, 30),
                    random.randint(-30, 30),
                    ICE_BLUE, 0.5, 3
                ))
        
        elif self.ability == Ability.SPARK:
            if sounds["spark"]:
                sounds["spark"].play()
            # Electric field
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                projectiles.append(Projectile(
                    self.x + math.cos(rad) * 40,
                    self.y + math.sin(rad) * 40,
                    math.cos(rad) * 200,
                    math.sin(rad) * 200,
                    1, Ability.SPARK
                ))
            create_explosion(self.x, self.y, SPARK_YELLOW, 15)
        
        elif self.ability == Ability.STONE:
            if sounds["stone"]:
                sounds["stone"].play()
            # Stone drop (temporary invulnerability)
            self.invuln_time = 1.0
            self.vy = 500  # Slam down
            create_explosion(self.x, self.y, STONE_GRAY, 8)
        
        elif self.ability == Ability.SWORD:
            if sounds["sword"]:
                sounds["sword"].play()
            # Sword slash
            projectiles.append(Projectile(
                self.x + (40 if self.facing_right else -40),
                self.y,
                400 if self.facing_right else -400,
                -50,
                3, Ability.SWORD
            ))
        
        elif self.ability == Ability.BEAM:
            if sounds["beam"]:
                sounds["beam"].play()
            # Whip beam
            projectiles.append(Projectile(
                self.x + (30 if self.facing_right else -30),
                self.y,
                350 if self.facing_right else -350,
                0,
                2, Ability.BEAM
            ))
            for _ in range(3):
                particles.append(Particle(
                    self.x + (30 if self.facing_right else -30),
                    self.y,
                    (150 if self.facing_right else -150) + random.randint(-20, 20),
                    random.randint(-20, 20),
                    BEAM_PURPLE, 0.4, 4
                ))
        
        elif self.ability == Ability.TORNADO:
            if sounds["tornado"]:
                sounds["tornado"].play()
            # Tornado spin
            self.vx = 400 if self.facing_right else -400
            for i in range(8):
                angle = i * math.pi / 4
                particles.append(Particle(
                    self.x + math.cos(angle) * 30,
                    self.y + math.sin(angle) * 30,
                    math.cos(angle) * 100,
                    math.sin(angle) * 100,
                    TORNADO_GREEN, 0.6, 5
                ))
    
    def take_damage(self):
        if self.invuln_time <= 0:
            self.hp -= 1
            self.invuln_time = 1.5
            if sounds["hit"]:
                sounds["hit"].play()
            create_explosion(self.x, self.y, KIRBY_PINK, 10)
    
    def draw(self, surf, camx):
        cx = int(self.x - camx)
        cy = int(self.y)
        
        # Flashing when invulnerable
        if self.invuln_time > 0 and int(self.invuln_time * 10) % 2:
            return
        
        # Body color changes with ability
        body_color = KIRBY_PINK
        if self.ability != Ability.NONE:
            body_color = ABILITY_COLORS[self.ability]
        
        # Inflated when inhaling
        size = self.r + (5 if self.inhaling else 0)
        
        # Main body
        pygame.draw.circle(surf, body_color, (cx, cy), size)
        
        # Feet
        foot_y = cy + size - 5
        pygame.draw.ellipse(surf, KIRBY_FEET, 
                           (cx - 15, foot_y, 12, 8))
        pygame.draw.ellipse(surf, KIRBY_FEET, 
                           (cx + 3, foot_y, 12, 8))
        
        # Eyes
        eye_offset = 7 if not self.facing_right else 7
        pygame.draw.circle(surf, BLACK, 
                         (cx - eye_offset, cy - 2), 4)
        pygame.draw.circle(surf, BLACK, 
                         (cx + eye_offset, cy - 2), 4)
        pygame.draw.circle(surf, WHITE, 
                         (cx - eye_offset + 1, cy - 3), 2)
        pygame.draw.circle(surf, WHITE, 
                         (cx + eye_offset + 1, cy - 3), 2)
        
        # Mouth (inhaling)
        if self.inhaling:
            pygame.draw.circle(surf, BLACK, (cx, cy + 5), 6)
        
        # Ability hat/crown
        if self.ability == Ability.FIRE:
            # Fire crown
            for i in range(-1, 2):
                pygame.draw.polygon(surf, FIRE_ORANGE, [
                    (cx + i*8, cy - size),
                    (cx + i*8 - 3, cy - size - 10),
                    (cx + i*8 + 3, cy - size - 10)
                ])
        elif self.ability == Ability.ICE:
            # Ice crystal
            pygame.draw.polygon(surf, ICE_BLUE, [
                (cx, cy - size - 12),
                (cx - 6, cy - size - 6),
                (cx - 6, cy - size),
                (cx + 6, cy - size),
                (cx + 6, cy - size - 6)
            ])
        elif self.ability == Ability.SWORD:
            # Sword hat
            pygame.draw.polygon(surf, (0, 100, 0), [
                (cx - 10, cy - size),
                (cx + 10, cy - size),
                (cx, cy - size - 15)
            ])

# ============================================================
# Enemy Classes
# ============================================================
class Enemy:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.hp = 1
        self.dead = False
        self.ability = Ability.NONE
    
    def rect(self):
        return pygame.Rect(int(self.x - 15), int(self.y - 15), 30, 30)
    
    def take_damage(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.dead = True
            create_explosion(self.x, self.y, WHITE, 8)

class WaddleDee(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y)
        self.dir = random.choice([-1, 1])
        self.speed = 80
    
    def update(self, dt):
        if self.dead:
            return
        self.x += self.dir * self.speed * dt
        if self.x < 50 or self.x > LEVEL_LEN - 50:
            self.dir *= -1
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            pygame.draw.circle(surf, WADDLE_DEE_ORANGE, (sx, int(self.y)), 15)
            pygame.draw.circle(surf, BLACK, (sx - 5, int(self.y) - 3), 3)
            pygame.draw.circle(surf, BLACK, (sx + 5, int(self.y) - 3), 3)

class FireEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 20)
        self.ability = Ability.FIRE
        self.anim_time = random.random() * math.pi * 2
    
    def update(self, dt):
        if self.dead:
            return
        self.anim_time += dt * 3
        self.y = FLOOR_Y - 20 + math.sin(self.anim_time) * 10
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Flame body
            pygame.draw.circle(surf, FIRE_ORANGE, (sx, int(self.y)), 18)
            pygame.draw.circle(surf, FIRE_RED, (sx, int(self.y)), 10)
            # Flame particles
            if random.random() < 0.3:
                particles.append(Particle(
                    self.x + random.randint(-10, 10),
                    self.y - 10,
                    random.randint(-20, 20),
                    random.randint(-50, -20),
                    FIRE_ORANGE, 0.5, 4
                ))

class IceEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y)
        self.ability = Ability.ICE
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Ice cube body
            pygame.draw.rect(surf, ICE_BLUE, 
                           (sx - 15, int(self.y) - 15, 30, 30))
            pygame.draw.rect(surf, (200, 240, 255), 
                           (sx - 10, int(self.y) - 10, 20, 20))

class SparkEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 30)
        self.ability = Ability.SPARK
        self.orbit_angle = 0
    
    def update(self, dt):
        if self.dead:
            return
        self.orbit_angle += dt * 2
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Electric orb
            pygame.draw.circle(surf, SPARK_YELLOW, (sx, int(self.y)), 12)
            # Orbiting sparks
            for i in range(3):
                angle = self.orbit_angle + (i * math.pi * 2 / 3)
                spark_x = sx + math.cos(angle) * 20
                spark_y = int(self.y) + math.sin(angle) * 20
                pygame.draw.circle(surf, WHITE, (int(spark_x), int(spark_y)), 4)

class SwordKnight(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y)
        self.ability = Ability.SWORD
        self.hp = 2
        self.dir = 1
    
    def update(self, dt):
        if self.dead:
            return
        self.x += self.dir * 60 * dt
        if self.x < 100 or self.x > LEVEL_LEN - 100:
            self.dir *= -1
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Knight body
            pygame.draw.rect(surf, SWORD_SILVER, 
                           (sx - 12, int(self.y) - 25, 24, 25))
            # Helmet
            pygame.draw.rect(surf, (100, 100, 100), 
                           (sx - 15, int(self.y) - 30, 30, 12))
            # Sword
            pygame.draw.rect(surf, WHITE, 
                           (sx + (15 if self.dir > 0 else -20), 
                            int(self.y) - 20, 5, 20))

# ============================================================
# Boss Classes
# ============================================================
class Boss:
    def __init__(self, x, y, hp):
        self.x, self.y = float(x), float(y)
        self.hp, self.max_hp = hp, hp
        self.last_hit = 1.0
        self.attack_timer = 0.0
        self.state = "idle"
    
    def take_damage(self, damage=1):
        if self.last_hit > 0.5:
            self.hp -= damage
            self.last_hit = 0.0
            if sounds["boss_hurt"]:
                sounds["boss_hurt"].play()
            create_explosion(self.x, self.y - 50, WHITE, 15)

class WhispyWoods(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y, 15)
        self.apple_timer = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 60), int(self.y - 180), 120, 180)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.apple_timer += dt
        
        # Drop apples
        if self.apple_timer > 2.0:
            self.apple_timer = 0.0
            # Create falling apple projectile
            apple_x = self.x + random.randint(-100, 100)
            projectiles.append(Projectile(
                apple_x, self.y - 200,
                0, 150,
                1, Ability.NONE, "boss"
            ))
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -150 <= sx <= W + 150:
            # Flash white when hit
            trunk_color = (139, 69, 19) if self.last_hit > 0.2 else WHITE
            leaves_color = (34, 139, 34) if self.last_hit > 0.2 else WHITE
            
            # Trunk
            pygame.draw.rect(surf, trunk_color, 
                           (sx - 40, int(self.y) - 150, 80, 150))
            # Leaves
            pygame.draw.circle(surf, leaves_color, 
                          (sx, int(self.y) - 140), 70)
            # Eyes
            pygame.draw.circle(surf, BLACK, (sx - 20, int(self.y) - 140), 8)
            pygame.draw.circle(surf, BLACK, (sx + 20, int(self.y) - 140), 8)
            # Angry eyebrows
            pygame.draw.line(surf, BLACK, 
                           (sx - 30, int(self.y) - 150), 
                           (sx - 10, int(self.y) - 145), 3)
            pygame.draw.line(surf, BLACK, 
                           (sx + 30, int(self.y) - 150), 
                           (sx + 10, int(self.y) - 145), 3)

class KingDedede(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y, 25)
        self.vy = 0.0
        self.hammer_angle = 0
    
    def rect(self):
        return pygame.Rect(int(self.x - 50), int(self.y - 80), 100, 80)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.hammer_angle += dt * 2
        
        if self.state == "idle":
            if self.attack_timer > 2.5:
                self.state = "jumping"
                self.attack_timer = 0.0
                self.vy = -550
        
        elif self.state == "jumping":
            self.vy += 1600 * dt
            self.y += self.vy * dt
            
            # Move toward player
            if player.x > self.x:
                self.x += 250 * dt
            else:
                self.x -= 250 * dt
            
            if self.y >= FLOOR_Y:
                self.y = FLOOR_Y
                self.state = "slam"
                # Create shockwave
                for i in range(-3, 4):
                    projectiles.append(Projectile(
                        self.x + i * 30,
                        FLOOR_Y,
                        i * 100,
                        -200,
                        1, Ability.STONE, "boss"
                    ))
                create_explosion(self.x, FLOOR_Y, STONE_GRAY, 20)
        
        elif self.state == "slam":
            if self.attack_timer > 1.0:
                self.state = "idle"
                self.attack_timer = 0.0
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -150 <= sx <= W + 150:
            body_color = (0, 0, 200) if self.last_hit > 0.2 else WHITE
            
            # Body
            pygame.draw.circle(surf, body_color, 
                             (sx, int(self.y) - 40), 50)
            # Crown
            pygame.draw.polygon(surf, (255, 215, 0), [
                (sx - 30, int(self.y) - 80),
                (sx - 20, int(self.y) - 100),
                (sx - 10, int(self.y) - 85),
                (sx, int(self.y) - 95),
                (sx + 10, int(self.y) - 85),
                (sx + 20, int(self.y) - 100),
                (sx + 30, int(self.y) - 80)
            ])
            # Hammer
            hammer_x = sx + math.cos(self.hammer_angle) * 60
            hammer_y = int(self.y) - 40 + math.sin(self.hammer_angle) * 30
            pygame.draw.rect(surf, (139, 69, 19), 
                           (int(hammer_x) - 5, int(hammer_y) - 30, 10, 40))
            pygame.draw.rect(surf, SWORD_SILVER, 
                           (int(hammer_x) - 20, int(hammer_y) - 35, 40, 15))

class MetaKnight(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 30, 20)
        self.teleport_timer = 0.0
        self.sword_attacks = []
    
    def rect(self):
        return pygame.Rect(int(self.x - 25), int(self.y - 35), 50, 70)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.teleport_timer += dt
        
        # Teleport
        if self.teleport_timer > 3.0:
            self.teleport_timer = 0.0
            old_x = self.x
            self.x = player.x + random.choice([-150, 150])
            self.x = max(100, min(LEVEL_LEN - 100, self.x))
            create_explosion(old_x, self.y, BEAM_PURPLE, 15)
            create_explosion(self.x, self.y, BEAM_PURPLE, 15)
        
        # Sword wave attack
        if self.attack_timer > 1.5:
            self.attack_timer = 0.0
            for i in range(3):
                angle = math.radians(i * 30 - 30)
                projectiles.append(Projectile(
                    self.x,
                    self.y,
                    math.cos(angle) * 300 * (1 if player.x > self.x else -1),
                    math.sin(angle) * 150,
                    2, Ability.SWORD, "boss"
                ))
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -100 <= sx <= W + 100:
            # Cape
            cape_color = (75, 0, 130) if self.last_hit > 0.2 else WHITE
            pygame.draw.polygon(surf, cape_color, [
                (sx - 25, int(self.y) + 30),
                (sx + 25, int(self.y) + 30),
                (sx + 20, int(self.y) - 20),
                (sx - 20, int(self.y) - 20)
            ])
            # Body
            pygame.draw.circle(surf, (0, 0, 100), (sx, int(self.y)), 20)
            # Mask
            pygame.draw.ellipse(surf, SWORD_SILVER, 
                              (sx - 15, int(self.y) - 15, 30, 25))
            # Eyes
            pygame.draw.circle(surf, (255, 255, 0), 
                             (sx - 7, int(self.y) - 5), 4)
            pygame.draw.circle(surf, (255, 255, 0), 
                             (sx + 7, int(self.y) - 5), 4)
            # Sword
            pygame.draw.line(surf, WHITE, 
                           (sx + 25, int(self.y) - 10),
                           (sx + 45, int(self.y) - 30), 3)

class NightmareWizard(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 100, 30)
        self.float_time = 0.0
        self.orb_angle = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 40), int(self.y - 40), 80, 80)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.float_time += dt
        self.orb_angle += dt * 2
        
        # Float motion
        self.y = FLOOR_Y - 100 + math.sin(self.float_time) * 30
        
        # Dark orb attack
        if self.attack_timer > 2.0:
            self.attack_timer = 0.0
            for i in range(6):
                angle = i * math.pi / 3
                projectiles.append(Projectile(
                    self.x + math.cos(angle) * 50,
                    self.y + math.sin(angle) * 50,
                    math.cos(angle) * 200,
                    math.sin(angle) * 200,
                    2, Ability.BEAM, "boss"
                ))
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -100 <= sx <= W + 100:
            # Dark aura
            for i in range(3):
                alpha = (3 - i) / 3
                size = 50 + i * 15
                color = (100 - i*30, 0, 100 - i*30)
                pygame.draw.circle(surf, color, (sx, int(self.y)), size, 2)
            
            # Body
            body_color = (50, 0, 100) if self.last_hit > 0.2 else WHITE
            pygame.draw.circle(surf, body_color, (sx, int(self.y)), 35)
            
            # Eyes
            pygame.draw.polygon(surf, (255, 0, 0), [
                (sx - 15, int(self.y) - 10),
                (sx - 8, int(self.y) - 5),
                (sx - 15, int(self.y))
            ])
            pygame.draw.polygon(surf, (255, 0, 0), [
                (sx + 15, int(self.y) - 10),
                (sx + 8, int(self.y) - 5),
                (sx + 15, int(self.y))
            ])

class Marx(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 80, 35)
        self.wings_angle = 0
        self.teleport_cooldown = 0
        self.attack_pattern = 0
    
    def rect(self):
        return pygame.Rect(int(self.x - 35), int(self.y - 35), 70, 70)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.wings_angle += dt * 3
        self.teleport_cooldown = max(0, self.teleport_cooldown - dt)
        
        # Float and move
        self.y = FLOOR_Y - 80 + math.sin(self.wings_angle) * 20
        
        # Teleport occasionally
        if self.teleport_cooldown <= 0 and random.random() < 0.01:
            self.teleport_cooldown = 3.0
            create_explosion(self.x, self.y, BEAM_PURPLE, 20)
            self.x = random.randint(200, LEVEL_LEN - 200)
            create_explosion(self.x, self.y, BEAM_PURPLE, 20)
        
        # Varied attack patterns
        if self.attack_timer > 1.5:
            self.attack_timer = 0.0
            self.attack_pattern = (self.attack_pattern + 1) % 3
            
            if self.attack_pattern == 0:
                # Spread shot
                for angle in range(-60, 61, 30):
                    rad = math.radians(angle)
                    projectiles.append(Projectile(
                        self.x,
                        self.y,
                        math.sin(rad) * 250,
                        math.cos(rad) * 250 + 100,
                        2, Ability.BEAM, "boss"
                    ))
            elif self.attack_pattern == 1:
                # Laser beams
                for i in range(4):
                    projectiles.append(Projectile(
                        self.x + (i - 1.5) * 40,
                        self.y,
                        0,
                        400,
                        3, Ability.SPARK, "boss"
                    ))
            else:
                # Bouncing balls
                for i in range(2):
                    projectiles.append(Projectile(
                        self.x,
                        self.y,
                        random.choice([-200, 200]),
                        -300,
                        2, Ability.FIRE, "boss"
                    ))
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -100 <= sx <= W + 100:
            # Wings
            wing_offset = abs(math.sin(self.wings_angle)) * 30
            wing_color = (200, 0, 200) if self.last_hit > 0.2 else WHITE
            
            # Left wing
            pygame.draw.polygon(surf, wing_color, [
                (sx - 25, int(self.y)),
                (sx - 60 - wing_offset, int(self.y) - 20),
                (sx - 55 - wing_offset, int(self.y) + 20)
            ])
            # Right wing  
            pygame.draw.polygon(surf, wing_color, [
                (sx + 25, int(self.y)),
                (sx + 60 + wing_offset, int(self.y) - 20),
                (sx + 55 + wing_offset, int(self.y) + 20)
            ])
            
            # Body
            body_color = (150, 0, 150) if self.last_hit > 0.2 else WHITE
            pygame.draw.circle(surf, body_color, (sx, int(self.y)), 30)
            
            # Hat
            pygame.draw.polygon(surf, (255, 0, 255), [
                (sx - 20, int(self.y) - 25),
                (sx + 20, int(self.y) - 25),
                (sx, int(self.y) - 45)
            ])
            
            # Face
            pygame.draw.circle(surf, BLACK, (sx - 10, int(self.y) - 5), 5)
            pygame.draw.circle(surf, BLACK, (sx + 10, int(self.y) - 5), 5)
            pygame.draw.arc(surf, BLACK, 
                           (sx - 15, int(self.y), 30, 20), 0, math.pi, 2)

class ZeroTwo(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 120, 50)
        self.eye_angle = 0
        self.blood_timer = 0
        self.phase = 1
    
    def rect(self):
        return pygame.Rect(int(self.x - 60), int(self.y - 60), 120, 120)
    
    def update(self, dt, player):
        self.last_hit += dt
        self.attack_timer += dt
        self.blood_timer += dt
        self.eye_angle += dt
        
        # Phase change
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            create_explosion(self.x, self.y, (255, 0, 0), 30)
        
        # Floating movement
        self.y = FLOOR_Y - 120 + math.sin(self.eye_angle * 0.5) * 40
        self.x += math.sin(self.eye_angle * 0.3) * 100 * dt
        self.x = max(150, min(LEVEL_LEN - 150, self.x))
        
        # Blood tears (phase 2)
        if self.phase == 2 and self.blood_timer > 0.5:
            self.blood_timer = 0
            projectiles.append(Projectile(
                self.x + random.randint(-20, 20),
                self.y + 30,
                random.randint(-50, 50),
                200,
                3, Ability.NONE, "boss"
            ))
        
        # Crystal shards attack
        if self.attack_timer > 2.5:
            self.attack_timer = 0
            if self.phase == 1:
                # Normal pattern
                for i in range(8):
                    angle = i * math.pi / 4 + self.eye_angle
                    projectiles.append(Projectile(
                        self.x + math.cos(angle) * 60,
                        self.y + math.sin(angle) * 60,
                        math.cos(angle) * 250,
                        math.sin(angle) * 250,
                        2, Ability.ICE, "boss"
                    ))
            else:
                # Chaotic pattern
                for i in range(12):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(150, 350)
                    projectiles.append(Projectile(
                        self.x,
                        self.y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        3, Ability.BEAM, "boss"
                    ))
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -150 <= sx <= W + 150:
            # Wings (phase 2)
            if self.phase == 2:
                wing_color = (100, 0, 0)
                # Left wing
                pygame.draw.polygon(surf, wing_color, [
                    (sx - 40, int(self.y)),
                    (sx - 100, int(self.y) - 40),
                    (sx - 90, int(self.y) + 40)
                ])
                # Right wing
                pygame.draw.polygon(surf, wing_color, [
                    (sx + 40, int(self.y)),
                    (sx + 100, int(self.y) - 40),
                    (sx + 90, int(self.y) + 40)
                ])
            
            # Main eye body
            body_color = WHITE if self.last_hit > 0.2 else (255, 100, 100)
            pygame.draw.circle(surf, body_color, (sx, int(self.y)), 55)
            
            # Iris
            iris_color = (0, 200, 0) if self.phase == 1 else (200, 0, 0)
            pygame.draw.circle(surf, iris_color, (sx, int(self.y)), 35)
            
            # Pupil
            pupil_x = sx + math.cos(self.eye_angle) * 10
            pupil_y = int(self.y) + math.sin(self.eye_angle) * 10
            pygame.draw.circle(surf, BLACK, (int(pupil_x), int(pupil_y)), 15)
            
            # Blood tears (phase 2)
            if self.phase == 2:
                pygame.draw.line(surf, (150, 0, 0), 
                               (sx - 20, int(self.y) + 30),
                               (sx - 25, int(self.y) + 60), 3)
                pygame.draw.line(surf, (150, 0, 0), 
                               (sx + 20, int(self.y) + 30),
                               (sx + 25, int(self.y) + 60), 3)
            
            # Halo (phase 1) or thorns (phase 2)
            if self.phase == 1:
                pygame.draw.circle(surf, (255, 255, 100), 
                                 (sx, int(self.y) - 70), 30, 3)
            else:
                for i in range(6):
                    angle = i * math.pi / 3
                    thorn_x = sx + math.cos(angle) * 70
                    thorn_y = int(self.y) + math.sin(angle) * 70
                    pygame.draw.line(surf, (100, 0, 0),
                                   (sx, int(self.y)),
                                   (int(thorn_x), int(thorn_y)), 3)

# ============================================================
# Level System
# ============================================================
LEVEL_DATA = {
    1: {
        "name": "Green Greens",
        "enemies": [
            (WaddleDee, [300, 500, 700, 900]),
            (FireEnemy, [400, 800]),
        ],
        "boss": WhispyWoods,
        "bg_color": SKY_GRADIENT_TOP
    },
    2: {
        "name": "Castle Dedede",
        "enemies": [
            (WaddleDee, [350, 550, 750]),
            (SwordKnight, [450, 850]),
            (IceEnemy, [600]),
        ],
        "boss": KingDedede,
        "bg_color": (100, 100, 150)
    },
    3: {
        "name": "Orange Ocean",
        "enemies": [
            (FireEnemy, [400, 700, 1000]),
            (SparkEnemy, [500, 900]),
            (WaddleDee, [600, 800]),
        ],
        "boss": MetaKnight,
        "bg_color": (255, 150, 100)
    },
    4: {
        "name": "Nightmare Land",
        "enemies": [
            (SparkEnemy, [400, 600, 800]),
            (IceEnemy, [500, 700, 900]),
            (SwordKnight, [550, 750]),
        ],
        "boss": NightmareWizard,
        "bg_color": (50, 0, 100)
    },
    5: {
        "name": "Milky Way Wishes",
        "enemies": [
            (FireEnemy, [400, 600]),
            (SparkEnemy, [500, 700]),
            (IceEnemy, [450, 650]),
            (SwordKnight, [550, 750]),
        ],
        "boss": Marx,
        "bg_color": (20, 0, 50)
    },
    6: {
        "name": "Dark Star",
        "enemies": [
            (SparkEnemy, [400, 600, 800, 1000]),
            (FireEnemy, [500, 700, 900]),
            (IceEnemy, [450, 650, 850]),
            (SwordKnight, [550, 750, 950]),
        ],
        "boss": ZeroTwo,
        "bg_color": (0, 0, 0)
    }
}

# ============================================================
# Game State
# ============================================================
class GameState:
    def __init__(self):
        self.state = "title"  # title, playing, paused, victory, game_over
        self.level = 1
        self.score = 0
        self.lives = 3
        self.player = None
        self.enemies = []
        self.boss = None
        self.camera_x = 0
        self.transition_timer = 0
    
    def setup_level(self, level_num):
        self.level = level_num
        self.player = Kirby()
        self.enemies = []
        
        level_info = LEVEL_DATA.get(level_num, LEVEL_DATA[1])
        
        # Spawn enemies
        for enemy_class, positions in level_info["enemies"]:
            for pos in positions:
                self.enemies.append(enemy_class(pos))
        
        # Spawn boss
        boss_class = level_info["boss"]
        self.boss = boss_class(LEVEL_LEN - 300)
        
        self.camera_x = 0
        
        # Clear projectiles and particles for new level
        global projectiles, particles
        projectiles = []
        particles = []

game = GameState()

# ============================================================
# Drawing Functions
# ============================================================
def draw_gradient_bg(surf, color1, color2):
    for y in range(H):
        ratio = y / H
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (W, y))

def draw_kirby_face(surf, x, y, size=15):
    """Draw a small Kirby face for the lives display"""
    # Face
    pygame.draw.circle(surf, KIRBY_PINK, (x, y), size)
    
    # Eyes
    pygame.draw.circle(surf, BLACK, (x - 5, y - 2), 3)
    pygame.draw.circle(surf, BLACK, (x + 5, y - 2), 3)
    pygame.draw.circle(surf, WHITE, (x - 4, y - 3), 1)
    pygame.draw.circle(surf, WHITE, (x + 6, y - 3), 1)
    
    # Mouth
    pygame.draw.arc(surf, BLACK, (x - 5, y - 2, 10, 8), 0, math.pi, 2)

def draw_star(surf, x, y, size=10, color=STAR_YELLOW):
    """Draw a star for the star counter"""
    points = []
    for i in range(10):
        angle = math.pi * i / 5
        if i % 2 == 0:
            r = size
        else:
            r = size * 0.5
        px = x + r * math.cos(angle - math.pi / 2)
        py = y + r * math.sin(angle - math.pi / 2)
        points.append((px, py))
    pygame.draw.polygon(surf, color, points)

def draw_hud(surf):
    # Draw HUD background panel
    hud_bg = pygame.Surface((W, 60))
    hud_bg.set_alpha(200)
    hud_bg.fill((0, 0, 50))
    surf.blit(hud_bg, (0, 0))
    
    # Draw border
    pygame.draw.rect(surf, WHITE, (0, 0, W, 60), 2)
    
    # Score
    score_text = font.render(f"SCORE {game.score:06d}", True, WHITE)
    surf.blit(score_text, (10, 10))
    
    # Lives as Kirby faces
    lives_text = font.render("LIVES", True, WHITE)
    surf.blit(lives_text, (10, 35))
    for i in range(game.lives):
        draw_kirby_face(surf, 70 + i * 35, 43, 12)
    
    # Star counter
    stars_text = font.render("STARS", True, WHITE)
    surf.blit(stars_text, (200, 10))
    draw_star(surf, 250, 18, 8)
    stars_count_text = font.render(f"X {game.score // 100}", True, WHITE)
    surf.blit(stars_count_text, (265, 10))
    
    # HP bar (only show if not at max HP)
    if game.player.hp < game.player.max_hp:
        hp_text = font.render("HP", True, WHITE)
        surf.blit(hp_text, (200, 35))
        hp_width = 80
        hp_height = 10
        hp_x = 230
        hp_y = 37
        pygame.draw.rect(surf, BLACK, (hp_x - 1, hp_y - 1, hp_width + 2, hp_height + 2))
        pygame.draw.rect(surf, (100, 0, 0), (hp_x, hp_y, hp_width, hp_height))
        hp_fill = int((game.player.hp / game.player.max_hp) * hp_width)
        pygame.draw.rect(surf, KIRBY_PINK, (hp_x, hp_y, hp_fill, hp_height))
    
    # Ability icon with background
    if game.player.ability != Ability.NONE:
        ability_name = game.player.ability.name
        ability_color = ABILITY_COLORS[game.player.ability]
        
        # Draw ability icon background
        pygame.draw.rect(surf, BLACK, (350, 10, 100, 40))
        pygame.draw.rect(surf, ability_color, (350, 10, 100, 40), 2)
        
        # Draw ability icon
        if game.player.ability == Ability.FIRE:
            # Fire icon
            pygame.draw.polygon(surf, FIRE_ORANGE, [
                (400, 20),
                (390, 35),
                (410, 35)
            ])
        elif game.player.ability == Ability.ICE:
            # Ice icon
            pygame.draw.polygon(surf, ICE_BLUE, [
                (400, 15),
                (395, 25),
                (395, 35),
                (405, 35),
                (405, 25)
            ])
        elif game.player.ability == Ability.SPARK:
            # Spark icon
            pygame.draw.circle(surf, SPARK_YELLOW, (400, 30), 8)
            for i in range(4):
                angle = i * math.pi / 2
                pygame.draw.line(surf, WHITE, 
                               (400, 30),
                               (400 + math.cos(angle) * 12, 30 + math.sin(angle) * 12), 2)
        elif game.player.ability == Ability.STONE:
            # Stone icon
            pygame.draw.rect(surf, STONE_GRAY, (395, 20, 10, 20))
        elif game.player.ability == Ability.SWORD:
            # Sword icon
            pygame.draw.rect(surf, SWORD_SILVER, (398, 15, 4, 25))
            pygame.draw.rect(surf, (100, 100, 100), (395, 10, 10, 8))
        elif game.player.ability == Ability.BEAM:
            # Beam icon
            for i in range(3):
                pygame.draw.circle(surf, BEAM_PURPLE, (390 + i*5, 30 - i*3), 3)
        elif game.player.ability == Ability.TORNADO:
            # Tornado icon
            for i in range(3):
                pygame.draw.arc(surf, TORNADO_GREEN, 
                              (390 + i*3, 20 + i*3, 20 - i*3, 20 - i*3), 
                              0, math.pi, 2)
        
        # Ability name
        ability_text = font.render(ability_name, True, WHITE)
        surf.blit(ability_text, (360, 35))
    
    # Boss HP
    if game.boss and game.boss.hp > 0:
        boss_hp_width = 300
        boss_hp_x = W - boss_hp_width - 10
        boss_hp_y = 20
        
        # Boss name
        boss_name = game.boss.__class__.__name__
        name_text = font.render(boss_name, True, WHITE)
        surf.blit(name_text, (boss_hp_x, boss_hp_y - 15))
        
        # HP bar background
        pygame.draw.rect(surf, BLACK, 
                        (boss_hp_x - 2, boss_hp_y - 2, 
                         boss_hp_width + 4, 14))
        pygame.draw.rect(surf, (50, 0, 0), 
                        (boss_hp_x, boss_hp_y, boss_hp_width, 10))
        
        # HP fill
        hp_fill = int((game.boss.hp / game.boss.max_hp) * boss_hp_width)
        hp_color = BOSS_HP_YELLOW if game.boss.hp > game.boss.max_hp // 2 else BOSS_HP_RED
        pygame.draw.rect(surf, hp_color, 
                        (boss_hp_x, boss_hp_y, hp_fill, 10))
        
        # HP text
        hp_text = font.render(f"{game.boss.hp}/{game.boss.max_hp}", True, WHITE)
        surf.blit(hp_text, (boss_hp_x + boss_hp_width // 2 - 20, boss_hp_y - 2))

# ============================================================
# Main Game Loop
# ============================================================
async def main():
    global particles, projectiles
    
    running = True
    dt = 0
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == "playing":
                        game.state = "paused"
                    elif game.state == "paused":
                        game.state = "playing"
        
        inputs.update()
        
        # Title screen
        if game.state == "title":
            draw_gradient_bg(screen, (50, 0, 100), (255, 100, 150))
            
            # Title
            title_text = ultra_font.render("ULTRA! Kirby FX", True, KIRBY_PINK)
            title_rect = title_text.get_rect(center=(W//2, H//2 - 100))
            screen.blit(title_text, title_rect)
            
            subtitle = big_font.render("Adventure 0.x", True, WHITE)
            subtitle_rect = subtitle.get_rect(center=(W//2, H//2 - 50))
            screen.blit(subtitle, subtitle_rect)
            
            # Instructions
            instructions = [
                "Arrow Keys/WASD - Move",
                "Space/Z - Jump",
                "X/C - Inhale",
                "V/Shift - Use Ability",
                "Q - Drop Ability",
                "",
                "Press ENTER to Start!"
            ]
            
            y_offset = H//2 + 20
            for line in instructions:
                text = font.render(line, True, WHITE)
                text_rect = text.get_rect(center=(W//2, y_offset))
                screen.blit(text, text_rect)
                y_offset += 25
            
            # Floating Kirby animation
            kirby_y = H//2 + math.sin(pygame.time.get_ticks() * 0.002) * 20
            pygame.draw.circle(screen, KIRBY_PINK, (100, int(kirby_y)), 30)
            pygame.draw.circle(screen, KIRBY_PINK, (W - 100, int(kirby_y)), 30)
            
            if inputs.just_pressed("start"):
                game.setup_level(1)
                game.state = "playing"
                if sounds["power_up"]:
                    sounds["power_up"].play()
        
        # Main gameplay
        elif game.state == "playing":
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap dt to prevent physics issues
            
            # Update player
            game.player.update(dt)
            
            # Update camera
            target_cam_x = game.player.x - W // 2
            game.camera_x += (target_cam_x - game.camera_x) * 0.1
            game.camera_x = max(0, min(LEVEL_LEN - W, game.camera_x))
            
            # Update enemies
            for enemy in game.enemies[:]:
                if not enemy.dead:
                    enemy.update(dt)
                    
                    # Check collision with player
                    if enemy.rect().colliderect(game.player.rect()):
                        if game.player.inhaling and game.player.ability == Ability.NONE:
                            # Inhale enemy
                            distance = math.hypot(enemy.x - game.player.x, 
                                                enemy.y - game.player.y)
                            if distance < game.player.inhale_range:
                                # Pull enemy toward Kirby
                                pull_speed = 300 * dt
                                dx = game.player.x - enemy.x
                                dy = game.player.y - enemy.y
                                length = math.sqrt(dx*dx + dy*dy)
                                if length > 0:
                                    enemy.x += (dx / length) * pull_speed
                                    enemy.y += (dy / length) * pull_speed
                                
                                # Swallow if close enough
                                if distance < 30:
                                    enemy.dead = True
                                    game.player.has_enemy = True
                                    game.player.stored_ability = enemy.ability
                                    game.score += 100
                                    create_star_particles(enemy.x, enemy.y)
                        else:
                            # Take damage
                            game.player.take_damage()
            
            # Update boss
            if game.boss and game.boss.hp > 0:
                game.boss.update(dt, game.player)
                
                # Check collision with boss
                if game.boss.rect().colliderect(game.player.rect()):
                    if game.player.invuln_time <= 0:
                        game.player.take_damage()
                        game.boss.take_damage(1)
                        game.score += 500
                
                # Boss defeated
                if game.boss.hp <= 0:
                    game.score += 5000
                    create_explosion(game.boss.x, game.boss.y - 50, WHITE, 50)
                    if sounds["win"]:
                        sounds["win"].play()
                    
                    # Next level or victory
                    if game.level >= len(LEVEL_DATA):
                        game.state = "victory"
                    else:
                        game.level += 1
                        game.setup_level(game.level)
            
            # Update projectiles
            for proj in projectiles[:]:
                proj.update(dt)
                if proj.dead:
                    projectiles.remove(proj)
                    continue
                
                # Player projectiles hit enemies
                if proj.owner == "player":
                    for enemy in game.enemies:
                        if not enemy.dead and enemy.rect().colliderect(proj.rect()):
                            enemy.take_damage(proj.damage)
                            if enemy.dead:
                                game.score += 200
                            proj.dead = True
                            create_explosion(proj.x, proj.y, 
                                          ABILITY_COLORS.get(proj.ability, WHITE), 8)
                            break
                    
                    # Hit boss
                    if game.boss and game.boss.hp > 0:
                        if game.boss.rect().colliderect(proj.rect()):
                            game.boss.take_damage(proj.damage)
                            game.score += 100
                            proj.dead = True
                            create_explosion(proj.x, proj.y, 
                                          ABILITY_COLORS.get(proj.ability, WHITE), 12)
                
                # Enemy projectiles hit player
                elif proj.owner == "boss":
                    if game.player.rect().colliderect(proj.rect()):
                        game.player.take_damage()
                        proj.dead = True
                        create_explosion(proj.x, proj.y, WHITE, 8)
            
            # Update particles
            for particle in particles[:]:
                if not particle.update(dt):
                    particles.remove(particle)
            
            # Check game over
            if game.player.hp <= 0:
                game.lives -= 1
                if game.lives <= 0:
                    game.state = "game_over"
                else:
                    # Respawn
                    game.setup_level(game.level)
            
            # Draw everything
            level_info = LEVEL_DATA.get(game.level, LEVEL_DATA[1])
            draw_gradient_bg(screen, level_info["bg_color"], GRASS_GREEN)
            
            # Ground
            pygame.draw.rect(screen, GRASS_GREEN, 
                           (0, FLOOR_Y, W, H - FLOOR_Y))
            
            # Decorative clouds
            for i in range(3):
                cloud_x = (i * 300 - game.camera_x * 0.3) % (W + 200) - 100
                cloud_y = 50 + i * 40
                pygame.draw.ellipse(screen, WHITE, 
                                  (int(cloud_x), cloud_y, 80, 40))
                pygame.draw.ellipse(screen, WHITE, 
                                  (int(cloud_x) + 30, cloud_y - 10, 60, 35))
            
            # Draw entities
            game.player.draw(screen, game.camera_x)
            
            for enemy in game.enemies:
                enemy.draw(screen, game.camera_x)
            
            if game.boss:
                game.boss.draw(screen, game.camera_x)
            
            for proj in projectiles:
                proj.draw(screen, game.camera_x)
            
            for particle in particles:
                particle.draw(screen, game.camera_x)
            
            # Draw HUD
            draw_hud(screen)
            
            # Level name
            level_name = level_info["name"]
            level_text = big_font.render(level_name, True, WHITE)
            level_rect = level_text.get_rect(center=(W//2, 80))
            screen.blit(level_text, level_rect)
            
            # Pause
            if inputs.just_pressed("pause"):
                game.state = "paused"
        
        # Paused
        elif game.state == "paused":
            # Darken screen
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            pause_text = ultra_font.render("PAUSED", True, WHITE)
            pause_rect = pause_text.get_rect(center=(W//2, H//2))
            screen.blit(pause_text, pause_rect)
            
            hint_text = font.render("Press ESC to Resume", True, WHITE)
            hint_rect = hint_text.get_rect(center=(W//2, H//2 + 50))
            screen.blit(hint_text, hint_rect)
        
        # Victory screen
        elif game.state == "victory":
            draw_gradient_bg(screen, (255, 215, 0), (255, 100, 200))
            
            victory_text = ultra_font.render("VICTORY!", True, WHITE)
            victory_rect = victory_text.get_rect(center=(W//2, H//2 - 100))
            screen.blit(victory_text, victory_rect)
            
            score_text = big_font.render(f"Final Score: {game.score:08d}", True, WHITE)
            score_rect = score_text.get_rect(center=(W//2, H//2))
            screen.blit(score_text, score_rect)
            
            congrats = font.render("You saved Dream Land from darkness!", True, WHITE)
            congrats_rect = congrats.get_rect(center=(W//2, H//2 + 50))
            screen.blit(congrats, congrats_rect)
            
            restart_text = font.render("Press ENTER to Play Again", True, WHITE)
            restart_rect = restart_text.get_rect(center=(W//2, H//2 + 100))
            screen.blit(restart_text, restart_rect)
            
            # Victory particles
            if random.random() < 0.3:
                create_star_particles(random.randint(50, W - 50), 
                                    random.randint(50, H - 50))
            
            for particle in particles:
                particle.update(0.016)
                particle.draw(screen, 0)
            
            if inputs.just_pressed("start"):
                game.score = 0
                game.lives = 3
                game.state = "title"
        
        # Game over
        elif game.state == "game_over":
            draw_gradient_bg(screen, (100, 0, 0), BLACK)
            
            game_over_text = ultra_font.render("GAME OVER", True, WHITE)
            game_over_rect = game_over_text.get_rect(center=(W//2, H//2 - 50))
            screen.blit(game_over_text, game_over_rect)
            
            score_text = big_font.render(f"Score: {game.score:08d}", True, WHITE)
            score_rect = score_text.get_rect(center=(W//2, H//2 + 20))
            screen.blit(score_text, score_rect)
            
            continue_text = font.render("Press ENTER to Try Again", True, WHITE)
            continue_rect = continue_text.get_rect(center=(W//2, H//2 + 70))
            screen.blit(continue_text, continue_rect)
            
            if inputs.just_pressed("start"):
                game.score = 0
                game.lives = 3
                game.state = "title"
        
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
