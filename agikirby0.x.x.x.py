#!/usr/bin/env python3
# ============================================================
#  Kirby's Adventure Style Engine with HAL Lab Tweening
#  Enhanced with Copy Abilities & FX
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
pygame.display.set_caption("Kirby's Adventure Style Engine - HAL Lab Tweening")
clock = pygame.time.Clock()

# ============================================================
# Enhanced Color Palette (Kirby's Adventure Style)
# ============================================================
KIRBY_PINK = (255, 192, 203)
KIRBY_FEET = (255, 105, 180)
SKY_GRADIENT_TOP = (135, 206, 235)
SKY_GRADIENT_BOTTOM = (255, 255, 224)
GRASS_GREEN = (34, 139, 34)
WADDLE_DEE_ORANGE = (255, 165, 0)
BOSS_HP_RED = (220, 20, 60)
BOSS_HP_YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
STAR_YELLOW = (255, 255, 0)
FIRE_ORANGE = (255, 69, 0)
FIRE_RED = (178, 34, 34)
ICE_BLUE = (173, 216, 230)
SPARK_YELLOW = (255, 255, 0)
STONE_GRAY = (105, 105, 105)
SWORD_SILVER = (192, 192, 192)
BEAM_PURPLE = (138, 43, 226)
TORNADO_GREEN = (0, 255, 127)

FLOOR_Y = 400
LEVEL_LEN = 3600

font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 32)
ultra_font = pygame.font.Font(None, 48)

# ============================================================
# HAL Lab Tweening System
# ============================================================
class Tween:
    """HAL Lab style easing functions for smooth animations"""
    
    @staticmethod
    def ease_out_quad(t):
        """Quadratic easing out - decelerating to zero velocity"""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_quad(t):
        """Quadratic easing in - accelerating from zero velocity"""
        return t * t
    
    @staticmethod
    def ease_out_elastic(t):
        """Elastic easing out - HAL's signature bounce effect"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        
        p = 0.3
        return math.pow(2, -10 * t) * math.sin((t - p / 4) * (2 * math.pi) / p) + 1
    
    @staticmethod
    def ease_out_bounce(t):
        """Bounce easing out - HAL's characteristic bounce"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    @staticmethod
    def smooth_step(t):
        """Smooth step function for gentle transitions"""
        return t * t * (3 - 2 * t)
    
    @staticmethod
    def bouncy_step(t):
        """HAL's signature bouncy step function"""
        return 0.5 - 0.5 * math.cos(t * math.pi * 2 + math.sin(t * math.pi * 8) * 0.2)

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
    "jump": tone(523.25, 100),  # C5 note
    "hit": tone(196, 150),
    "win": tone(880, 200),
    "inhale": tone(330, 300, 0.3),
    "swallow": tone(659.25, 100),  # E5 note
    "fire": tone(220, 200, 0.5),
    "ice": tone(880, 150, 0.3),
    "spark": tone(1760, 100, 0.4),
    "beam": tone(440, 250, 0.3),
    "sword": tone(330, 100, 0.5),
    "stone": tone(110, 200, 0.6),
    "tornado": tone(220, 400, 0.3),
    "boss_hurt": tone(110, 300, 0.5),
    "power_up": tone(1046.50, 150),  # C6 note
    "bump": tone(146.83, 50),  # D3 note
    "walk": tone(100, 30, 0.1),
}

# ============================================================
# Copy Abilities System (Kirby's Adventure Style)
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
# Particle System with HAL Lab Tweening
# ============================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, life=1.0, size=3, gravity=0, tween_type="smooth"):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.tween_type = tween_type
        self.start_size = size
        self.rotation = random.uniform(0, math.pi * 2)
        self.rotation_speed = random.uniform(-5, 5)
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        self.rotation += self.rotation_speed * dt
        
        # Apply tweening to size
        t = 1 - (self.life / self.max_life)
        if self.tween_type == "bouncy":
            self.size = self.start_size * (1 - Tween.ease_out_bounce(t) * 0.8)
        elif self.tween_type == "elastic":
            self.size = self.start_size * (1 - Tween.ease_out_elastic(t) * 0.5)
        else:
            self.size = self.start_size * (1 - t * 0.8)
        
        return self.life > 0
    
    def draw(self, surf, camx):
        if self.size > 0:
            # Apply rotation to create spinning effect
            sx = int(self.x - camx)
            sy = int(self.y)
            
            # Draw with rotation for star particles
            if self.color == STAR_YELLOW:
                points = []
                for i in range(10):
                    angle = math.pi * i / 5 + self.rotation
                    if i % 2 == 0:
                        r = self.size
                    else:
                        r = self.size * 0.5
                    px = sx + r * math.cos(angle)
                    py = sy + r * math.sin(angle)
                    points.append((px, py))
                pygame.draw.polygon(surf, self.color, points)
            else:
                pygame.draw.circle(surf, self.color, (sx, sy), int(self.size))

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
            gravity=200,
            tween_type="bouncy"
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
            gravity=400,
            tween_type="elastic"
        ))

def create_walk_dust(x, y):
    for _ in range(3):
        particles.append(Particle(
            x + random.randint(-10, 10),
            y,
            random.randint(-20, 20),
            random.randint(-30, -10),
            (205, 133, 63),  # Brown color
            life=0.3,
            size=random.randint(2, 4),
            gravity=100,
            tween_type="smooth"
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
# Projectile System with HAL Lab Tweening
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
        self.size = 8
        self.pulse = 0.0
        self.trail = []  # Store previous positions for trail effect
    
    def rect(self):
        return pygame.Rect(int(self.x - 10), int(self.y - 10), 20, 20)
    
    def update(self, dt):
        # Store current position for trail
        self.trail.append((self.x, self.y, self.size))
        if len(self.trail) > 5:
            self.trail.pop(0)
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.pulse += dt * 5
        
        # Apply HAL's bouncy pulse effect
        self.size = 8 + math.sin(self.pulse) * 2
        
        if self.lifetime <= 0 or self.y > FLOOR_Y + 50:
            self.dead = True
    
    def draw(self, surf, camx):
        if self.dead:
            return
            
        # Draw trail with fading effect
        for i, (tx, ty, tsize) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            trail_size = int(tsize * alpha * 0.7)
            sx = int(tx - camx)
            color = ABILITY_COLORS.get(self.ability, WHITE)
            # Fade trail color
            trail_color = tuple(int(c * alpha) for c in color)
            pygame.draw.circle(surf, trail_color, (sx, int(ty)), trail_size)
        
        # Draw main projectile
        sx = int(self.x - camx)
        color = ABILITY_COLORS.get(self.ability, WHITE)
        pygame.draw.circle(surf, color, (sx, int(self.y)), int(self.size))
        
        # Draw inner details
        if self.ability == Ability.FIRE:
            pygame.draw.circle(surf, FIRE_RED, (sx, int(self.y)), int(self.size * 0.6))
        elif self.ability == Ability.ICE:
            # Draw ice crystal shape
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                px = sx + math.cos(angle) * self.size * 0.7
                py = int(self.y) + math.sin(angle) * self.size * 0.7
                points.append((px, py))
            pygame.draw.polygon(surf, WHITE, points)

projectiles: List[Projectile] = []

# ============================================================
# Enhanced Kirby with HAL Lab Tweening
# ============================================================
class Kirby:
    def __init__(self):
        self.r = 22
        self.x, self.y = 100, FLOOR_Y
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = True
        self.facing_right = True
        
        # Movement (Kirby's Adventure style physics)
        self.max_speed = 180.0
        self.accel = 1200.0
        self.friction = 8.0
        self.gravity = 1200.0
        self.jump_vel = -420.0
        self.float_timer = 0.0
        self.max_float_time = 1.5
        
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
        
        # Animation with HAL Lab tweening
        self.anim_time = 0.0
        self.walk_cycle = 0.0
        self.prev_x = self.x
        self.prev_y = self.y
        
        # HAL Lab style squash and stretch
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.target_squash_x = 1.0
        self.target_squash_y = 1.0
        self.squash_speed = 15.0
        
        # Eye animation
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
        
        # Mouth animation
        self.mouth_openness = 0.0
        self.target_mouth_openness = 0.0
        
        # Ability hat animation
        self.hat_bounce = 0.0
        self.hat_rotation = 0.0
    
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
            
            # Create walk dust particles
            if self.on_ground and abs(self.vx) > 50 and random.random() < 0.3:
                create_walk_dust(self.x, self.y + self.r)
                
            # Add squash and stretch when accelerating
            if abs(self.vx) > 100:
                self.target_squash_x = 0.9
                self.target_squash_y = 1.1
        else:
            self.vx *= max(0.0, 1.0 - self.friction * dt)
            self.target_squash_x = 1.0
            self.target_squash_y = 1.0
        
        self.vx = max(-self.max_speed, min(self.max_speed, self.vx))
        
        # Jumping and floating
        if inputs.just_pressed("jump") and self.on_ground:
            self.vy = self.jump_vel
            self.on_ground = False
            self.float_timer = 0.0
            if sounds["jump"]:
                sounds["jump"].play()
            
            # Squash and stretch for jump
            self.target_squash_x = 1.2
            self.target_squash_y = 0.8
        elif inputs.down("jump") and not self.on_ground and self.vy > 0 and self.float_timer < self.max_float_time:
            # Float ability
            self.vy = min(self.vy, 100)  # Slow fall
            self.float_timer += dt
            
            # Create float particles
            if random.random() < 0.2:
                particles.append(Particle(
                    self.x + random.randint(-15, 15),
                    self.y + self.r,
                    random.randint(-30, 30),
                    random.randint(-10, 10),
                    (255, 255, 255, 128),  # Semi-transparent white
                    life=0.4,
                    size=3,
                    tween_type="elastic"
                ))
        elif self.on_ground:
            self.float_timer = 0.0
        
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
            
            # Create landing particles
            if abs(self.prev_y - self.y) > 50:
                for _ in range(5):
                    particles.append(Particle(
                        self.x + random.randint(-15, 15),
                        self.y,
                        random.randint(-50, 50),
                        random.randint(-30, -10),
                        (205, 133, 63),  # Brown color
                        life=0.3,
                        size=random.randint(2, 4),
                        gravity=100,
                        tween_type="bouncy"
                    ))
                
                # Squash and stretch for landing
                self.target_squash_x = 1.3
                self.target_squash_y = 0.7
        else:
            self.on_ground = False
        
        # Update walk cycle with HAL's bouncy step
        if self.on_ground and abs(self.vx) > 10:
            self.walk_cycle += abs(self.vx) * dt * 0.01
            # Add bounce to walk cycle
            bounce = math.sin(self.walk_cycle * 2) * 0.1
            self.target_squash_y += bounce
        else:
            self.walk_cycle = 0.0
        
        # Update squash and stretch with tweening
        squash_speed = self.squash_speed * dt
        self.squash_x += (self.target_squash_x - self.squash_x) * squash_speed
        self.squash_y += (self.target_squash_y - self.squash_y) * squash_speed
        
        # Reset target squash after applying bounce
        if self.on_ground and abs(self.vx) > 10:
            self.target_squash_x = 1.0
            self.target_squash_y = 1.0
        
        self.prev_y = self.y
        self.prev_x = self.x
        
        # Level bounds
        self.x = max(25, min(LEVEL_LEN - 25, self.x))
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
        
        # Inhale system
        if inputs.down("inhale") and self.ability == Ability.NONE:
            self.inhaling = True
            self.target_mouth_openness = 1.0
            
            if not self.has_enemy and sounds["inhale"] and random.random() < 0.1:
                sounds["inhale"].play()
                
            # Create inhale particles
            if random.random() < 0.3:
                particles.append(Particle(
                    self.x + (20 if self.facing_right else -20),
                    self.y,
                    (50 if self.facing_right else -50) + random.randint(-20, 20),
                    random.randint(-20, 20),
                    (200, 200, 255),  # Light blue
                    life=0.3,
                    size=4,
                    tween_type="elastic"
                ))
        else:
            self.target_mouth_openness = 0.0
            if self.inhaling and self.has_enemy:
                # Swallow enemy
                if sounds["swallow"]:
                    sounds["swallow"].play()
                self.ability = self.stored_ability
                self.has_enemy = False
                create_star_particles(self.x, self.y - 20)
                
                # Squash and stretch for swallowing
                self.target_squash_x = 1.2
                self.target_squash_y = 0.8
            self.inhaling = False
        
        # Update mouth openness with tweening
        self.mouth_openness += (self.target_mouth_openness - self.mouth_openness) * 10 * dt
        
        # Use ability
        if inputs.just_pressed("ability") and self.ability != Ability.NONE:
            if self.ability_cooldown <= 0:
                self.use_ability()
        
        # Drop ability
        if inputs.just_pressed("drop") and self.ability != Ability.NONE:
            create_star_particles(self.x, self.y - 20)
            self.ability = Ability.NONE
        
        # Update ability hat animation
        self.hat_bounce += dt * 3
        self.hat_rotation += dt * 2
    
    def use_ability(self):
        self.ability_cooldown = 0.5
        
        # Squash and stretch for ability use
        self.target_squash_x = 0.8
        self.target_squash_y = 1.2
        
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
                    ICE_BLUE, 0.5, 3,
                    tween_type="elastic"
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
                    BEAM_PURPLE, 0.4, 4,
                    tween_type="elastic"
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
                    TORNADO_GREEN, 0.6, 5,
                    tween_type="bouncy"
                ))
    
    def take_damage(self):
        if self.invuln_time <= 0:
            self.hp -= 1
            self.invuln_time = 1.5
            if sounds["hit"]:
                sounds["hit"].play()
            create_explosion(self.x, self.y, KIRBY_PINK, 10)
            
            # Knockback with squash and stretch
            self.vx = -200 if self.facing_right else 200
            self.vy = -300
            self.target_squash_x = 0.7
            self.target_squash_y = 1.3
    
    def draw(self, surf, camx):
        cx = int(self.x - camx)
        cy = int(self.y)
        
        # Flashing when invulnerable
        if self.invuln_time > 0 and int(self.invuln_time * 10) % 2:
            return
        
        # Apply squash and stretch
        width = int(self.r * 2 * self.squash_x)
        height = int(self.r * 2 * self.squash_y)
        
        # Body color changes with ability
        body_color = KIRBY_PINK
        if self.ability != Ability.NONE:
            body_color = ABILITY_COLORS[self.ability]
        
        # Inflated when inhaling
        inhale_scale = 1.0 + (0.2 * self.mouth_openness)
        width = int(width * inhale_scale)
        height = int(height * inhale_scale)
        
        # Main body with squash and stretch
        pygame.draw.ellipse(surf, body_color, 
                           (cx - width//2, cy - height//2, width, height))
        
        # Feet with animation and squash and stretch
        foot_offset = 0
        if self.on_ground and abs(self.vx) > 10:
            foot_offset = int(Tween.bouncy_step(self.walk_cycle) * 5)
        
        foot_y = cy + height//2 - 5
        foot_width = int(12 * self.squash_x)
        foot_height = int(8 * self.squash_y)
        
        pygame.draw.ellipse(surf, KIRBY_FEET, 
                           (cx - 15, foot_y + foot_offset, foot_width, foot_height))
        pygame.draw.ellipse(surf, KIRBY_FEET, 
                           (cx + 3, foot_y - foot_offset, foot_width, foot_height))
        
        # Eyes with blink animation
        eye_height = int(8 * self.eye_openness)
        if eye_height > 0:
            eye_offset = 7 if not self.facing_right else 7
            pygame.draw.ellipse(surf, BLACK, 
                               (cx - eye_offset - 4, cy - 2 - eye_height//2, 8, eye_height))
            pygame.draw.ellipse(surf, BLACK, 
                               (cx + eye_offset - 4, cy - 2 - eye_height//2, 8, eye_height))
            
            # Eye highlights
            if self.eye_openness > 0.5:
                pygame.draw.circle(surf, WHITE, 
                                 (cx - eye_offset + 1, cy - 3), 2)
                pygame.draw.circle(surf, WHITE, 
                                 (cx + eye_offset + 1, cy - 3), 2)
        
        # Mouth with animation
        if self.mouth_openness > 0:
            mouth_width = int(12 * self.mouth_openness)
            mouth_height = int(6 * self.mouth_openness)
            pygame.draw.ellipse(surf, BLACK, 
                               (cx - mouth_width//2, cy + 5 - mouth_height//2, 
                                mouth_width, mouth_height))
        
        # Ability hat/crown with HAL Lab tweening
        if self.ability == Ability.FIRE:
            # Fire crown with bounce
            bounce = math.sin(self.hat_bounce) * 3
            for i in range(-1, 2):
                flame_height = 10 + bounce
                pygame.draw.polygon(surf, FIRE_ORANGE, [
                    (cx + i*8, cy - height//2),
                    (cx + i*8 - 3, cy - height//2 - flame_height),
                    (cx + i*8 + 3, cy - height//2 - flame_height)
                ])
            # Fire on top with rotation
            fire_x = cx + math.cos(self.hat_rotation) * 5
            fire_y = cy - height//2 - 15 - bounce
            pygame.draw.circle(surf, FIRE_RED, (int(fire_x), int(fire_y)), 5)
            
        elif self.ability == Ability.ICE:
            # Ice crystal hat with bounce
            bounce = math.sin(self.hat_bounce) * 2
            pygame.draw.polygon(surf, ICE_BLUE, [
                (cx, cy - height//2 - 12 - bounce),
                (cx - 6, cy - height//2 - 6 - bounce),
                (cx - 6, cy - height//2 - bounce),
                (cx + 6, cy - height//2 - bounce),
                (cx + 6, cy - height//2 - 6 - bounce)
            ])
            # Ice sparkles with rotation
            for i in range(3):
                angle = self.hat_rotation + i * math.pi * 2 / 3
                sparkle_x = cx + math.cos(angle) * 10
                sparkle_y = cy - height//2 - 10 - bounce + math.sin(angle) * 5
                pygame.draw.circle(surf, WHITE, (int(sparkle_x), int(sparkle_y)), 2)
                
        elif self.ability == Ability.SPARK:
            # Spark hat with electricity and bounce
            bounce = math.sin(self.hat_bounce) * 3
            pygame.draw.circle(surf, SPARK_YELLOW, 
                             (cx, cy - height//2 - 8 - bounce), 10)
            for i in range(4):
                angle = i * math.pi / 2 + self.hat_rotation
                end_x = cx + math.cos(angle) * 15
                end_y = cy - height//2 - 8 - bounce + math.sin(angle) * 15
                pygame.draw.line(surf, WHITE, 
                               (cx, cy - height//2 - 8 - bounce), 
                               (end_x, end_y), 2)
                
        elif self.ability == Ability.STONE:
            # Stone hat with bounce
            bounce = math.sin(self.hat_bounce) * 1
            pygame.draw.rect(surf, STONE_GRAY, 
                           (cx - 10, cy - height//2 - 15 - bounce, 20, 15))
            # Stone texture
            for i in range(3):
                for j in range(2):
                    pygame.draw.circle(surf, (80, 80, 80), 
                                     (cx - 7 + i*7, cy - height//2 - 12 + j*7 - bounce), 2)
                                     
        elif self.ability == Ability.SWORD:
            # Sword hat with bounce
            bounce = math.sin(self.hat_bounce) * 2
            pygame.draw.polygon(surf, (0, 100, 0), [
                (cx - 10, cy - height//2 - bounce),
                (cx + 10, cy - height//2 - bounce),
                (cx, cy - height//2 - 15 - bounce)
            ])
            # Sword blade with rotation
            sword_x = cx + math.sin(self.hat_rotation) * 2
            pygame.draw.rect(surf, SWORD_SILVER, 
                           (int(sword_x) - 2, cy - height//2 - 25 - bounce, 4, 15))
                           
        elif self.ability == Ability.BEAM:
            # Beam hat with antenna and bounce
            bounce = math.sin(self.hat_bounce) * 2
            pygame.draw.circle(surf, BEAM_PURPLE, 
                             (cx, cy - height//2 - 8 - bounce), 10)
            pygame.draw.line(surf, BEAM_PURPLE, 
                           (cx, cy - height//2 - 8 - bounce), 
                           (cx, cy - height//2 - 20 - bounce), 3)
            # Antenna tip with rotation
            tip_x = cx + math.cos(self.hat_rotation) * 3
            tip_y = cy - height//2 - 22 - bounce + math.sin(self.hat_rotation) * 2
            pygame.draw.circle(surf, WHITE, (int(tip_x), int(tip_y)), 4)
            
        elif self.ability == Ability.TORNADO:
            # Tornado hat with bounce
            bounce = math.sin(self.hat_bounce) * 3
            for i in range(3):
                radius = 12 - i * 3
                offset = math.sin(self.hat_rotation + i) * 2
                pygame.draw.arc(surf, TORNADO_GREEN, 
                              (cx - radius + offset, cy - height//2 - 15 - i*5 - bounce, 
                               radius*2, radius*2), 
                              0, math.pi, 2)

# ============================================================
# Enemy Classes with HAL Lab Tweening
# ============================================================
class Enemy:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.hp = 1
        self.dead = False
        self.ability = Ability.NONE
        self.anim_time = 0.0
        
        # HAL Lab style squash and stretch
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.target_squash_x = 1.0
        self.target_squash_y = 1.0
        self.squash_speed = 10.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 15), int(self.y - 15), 30, 30)
    
    def take_damage(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.dead = True
            create_explosion(self.x, self.y, WHITE, 8)
            if sounds["bump"]:
                sounds["bump"].play()
        else:
            # Squash and stretch when hit
            self.target_squash_x = 0.8
            self.target_squash_y = 1.2
    
    def update_squash_stretch(self, dt):
        # Update squash and stretch with tweening
        squash_speed = self.squash_speed * dt
        self.squash_x += (self.target_squash_x - self.squash_x) * squash_speed
        self.squash_y += (self.target_squash_y - self.squash_y) * squash_speed
        
        # Reset target squash
        self.target_squash_x = 1.0
        self.target_squash_y = 1.0

class WaddleDee(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y)
        self.dir = random.choice([-1, 1])
        self.speed = 80
        self.walk_cycle = 0.0
        
        # Eye blink animation
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
    
    def update(self, dt):
        if self.dead:
            return
        self.anim_time += dt
        self.x += self.dir * self.speed * dt
        self.walk_cycle += abs(self.speed) * dt * 0.05
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Add bounce to walk
        if abs(self.speed) > 0:
            bounce = math.sin(self.walk_cycle * 2) * 0.1
            self.target_squash_y = 1.0 + bounce
        
        if self.x < 50 or self.x > LEVEL_LEN - 50:
            self.dir *= -1
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Apply squash and stretch
            width = int(30 * self.squash_x)
            height = int(30 * self.squash_y)
            
            # Body
            pygame.draw.ellipse(surf, WADDLE_DEE_ORANGE, 
                              (sx - width//2, int(self.y) - height//2, width, height))
            
            # Eyes with blink animation
            eye_height = int(6 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx - 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx + 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            
            # Feet with animation
            foot_offset = int(Tween.bouncy_step(self.walk_cycle) * 3)
            foot_width = int(8 * self.squash_x)
            foot_height = int(6 * self.squash_y)
            
            pygame.draw.ellipse(surf, (255, 140, 0), 
                               (sx - 10, int(self.y) + 10 + foot_offset, foot_width, foot_height))
            pygame.draw.ellipse(surf, (255, 140, 0), 
                               (sx + 2, int(self.y) + 10 - foot_offset, foot_width, foot_height))
            
            # Face
            pygame.draw.arc(surf, BLACK, 
                           (sx - 5, int(self.y) + 2, 10, 8), 0, math.pi, 2)

class FireEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 20)
        self.ability = Ability.FIRE
        self.anim_time = random.random() * math.pi * 2
        self.flame_flicker = 0.0
    
    def update(self, dt):
        if self.dead:
            return
        self.anim_time += dt * 3
        self.y = FLOOR_Y - 20 + math.sin(self.anim_time) * 10
        self.flame_flicker += dt * 10
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Add flicker effect
        flicker = math.sin(self.flame_flicker) * 0.1
        self.target_squash_x = 1.0 + flicker
        self.target_squash_y = 1.0 - flicker
        
        # Create flame particles
        if random.random() < 0.3:
            particles.append(Particle(
                self.x + random.randint(-10, 10),
                self.y - 10,
                random.randint(-20, 20),
                random.randint(-50, -20),
                FIRE_ORANGE, 0.5, 4,
                tween_type="bouncy"
            ))
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Apply squash and stretch
            width = int(36 * self.squash_x)
            height = int(36 * self.squash_y)
            
            # Flame body
            pygame.draw.ellipse(surf, FIRE_ORANGE, 
                              (sx - width//2, int(self.y) - height//2, width, height))
            
            # Inner flame
            inner_width = int(20 * self.squash_x)
            inner_height = int(20 * self.squash_y)
            pygame.draw.ellipse(surf, FIRE_RED, 
                              (sx - inner_width//2, int(self.y) - inner_height//2, 
                               inner_width, inner_height))
            
            # Eyes
            eye_height = int(6 * self.squash_y)
            pygame.draw.ellipse(surf, BLACK, 
                               (sx - 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            pygame.draw.ellipse(surf, BLACK, 
                               (sx + 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            
            # Angry mouth
            mouth_width = int(10 * self.squash_x)
            pygame.draw.arc(surf, BLACK, 
                           (sx - mouth_width//2, int(self.y) + 2, mouth_width, 8), 
                           0, math.pi, 2)

class IceEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y)
        self.ability = Ability.ICE
        self.anim_time = 0.0
        self.shimmer = 0.0
    
    def update(self, dt):
        if self.dead:
            return
        self.anim_time += dt
        self.shimmer += dt * 5
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Add shimmer effect
        shimmer = math.sin(self.shimmer) * 0.05
        self.target_squash_x = 1.0 + shimmer
        self.target_squash_y = 1.0 - shimmer
        
        # Create ice particles
        if random.random() < 0.2:
            particles.append(Particle(
                self.x + random.randint(-15, 15),
                self.y - 15,
                random.randint(-10, 10),
                random.randint(-10, 0),
                ICE_BLUE, 0.4, 3,
                tween_type="elastic"
            ))
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Apply squash and stretch
            width = int(30 * self.squash_x)
            height = int(30 * self.squash_y)
            
            # Ice cube body
            pygame.draw.rect(surf, ICE_BLUE, 
                           (sx - width//2, int(self.y) - height//2, width, height))
            
            # Inner ice
            inner_width = int(20 * self.squash_x)
            inner_height = int(20 * self.squash_y)
            pygame.draw.rect(surf, (200, 240, 255), 
                           (sx - inner_width//2, int(self.y) - inner_height//2, 
                            inner_width, inner_height))
            
            # Eyes
            eye_height = int(6 * self.squash_y)
            pygame.draw.ellipse(surf, BLACK, 
                               (sx - 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            pygame.draw.ellipse(surf, BLACK, 
                               (sx + 5 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            
            # Mouth
            mouth_width = int(10 * self.squash_x)
            pygame.draw.arc(surf, BLACK, 
                           (sx - mouth_width//2, int(self.y) + 2, mouth_width, 8), 
                           0, math.pi, 2)

class SparkEnemy(Enemy):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 30)
        self.ability = Ability.SPARK
        self.orbit_angle = 0
        self.anim_time = 0.0
        self.electric_pulse = 0.0
    
    def update(self, dt):
        if self.dead:
            return
        self.anim_time += dt
        self.orbit_angle += dt * 2
        self.electric_pulse += dt * 15
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Add electric pulse effect
        pulse = math.sin(self.electric_pulse) * 0.2
        self.target_squash_x = 1.0 + pulse
        self.target_squash_y = 1.0 - pulse
        
        # Create spark particles
        if random.random() < 0.4:
            particles.append(Particle(
                self.x + random.randint(-15, 15),
                self.y + random.randint(-15, 15),
                random.randint(-30, 30),
                random.randint(-30, 30),
                SPARK_YELLOW, 0.3, 2,
                tween_type="elastic"
            ))
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Apply squash and stretch
            width = int(24 * self.squash_x)
            height = int(24 * self.squash_y)
            
            # Electric orb
            pygame.draw.ellipse(surf, SPARK_YELLOW, 
                              (sx - width//2, int(self.y) - height//2, width, height))
            
            # Inner core
            core_width = int(12 * self.squash_x)
            core_height = int(12 * self.squash_y)
            pygame.draw.ellipse(surf, WHITE, 
                              (sx - core_width//2, int(self.y) - core_height//2, 
                               core_width, core_height))
            
            # Eyes
            eye_height = int(6 * self.squash_y)
            pygame.draw.ellipse(surf, BLACK, 
                               (sx - 4 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            pygame.draw.ellipse(surf, BLACK, 
                               (sx + 4 - 3, int(self.y) - 3 - eye_height//2, 6, eye_height))
            
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
        self.walk_cycle = 0.0
        
        # Eye blink animation
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
    
    def update(self, dt):
        if self.dead:
            return
        self.x += self.dir * 60 * dt
        self.walk_cycle += abs(self.dir * 60) * dt * 0.05
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Add bounce to walk
        if abs(self.dir * 60) > 0:
            bounce = math.sin(self.walk_cycle * 2) * 0.1
            self.target_squash_y = 1.0 + bounce
        
        if self.x < 100 or self.x > LEVEL_LEN - 100:
            self.dir *= -1
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
    
    def draw(self, surf, camx):
        if self.dead:
            return
        sx = int(self.x - camx)
        if -50 <= sx <= W + 50:
            # Apply squash and stretch
            width = int(24 * self.squash_x)
            height = int(25 * self.squash_y)
            
            # Knight body
            pygame.draw.rect(surf, SWORD_SILVER, 
                           (sx - width//2, int(self.y) - height, width, height))
            
            # Helmet
            helmet_width = int(30 * self.squash_x)
            pygame.draw.rect(surf, (100, 100, 100), 
                           (sx - helmet_width//2, int(self.y) - height - 12, helmet_width, 12))
            
            # Eyes with blink animation
            eye_height = int(6 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx - 5 - 3, int(self.y) - height - 8 - eye_height//2, 6, eye_height))
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx + 5 - 3, int(self.y) - height - 8 - eye_height//2, 6, eye_height))
            
            # Feet with animation
            foot_offset = int(Tween.bouncy_step(self.walk_cycle) * 3)
            foot_width = int(8 * self.squash_x)
            foot_height = int(5 * self.squash_y)
            
            pygame.draw.rect(surf, (80, 80, 80), 
                           (sx - 10, int(self.y) + foot_offset, foot_width, foot_height))
            pygame.draw.rect(surf, (80, 80, 80), 
                           (sx + 2, int(self.y) - foot_offset, foot_width, foot_height))
            
            # Sword
            sword_width = int(5 * self.squash_x)
            sword_height = int(20 * self.squash_y)
            pygame.draw.rect(surf, WHITE, 
                           (sx + (15 if self.dir > 0 else -20), 
                            int(self.y) - 20, sword_width, sword_height))

# ============================================================
# Boss Classes with HAL Lab Tweening
# ============================================================
class Boss:
    def __init__(self, x, y, hp):
        self.x, self.y = float(x), float(y)
        self.hp, self.max_hp = hp, hp
        self.last_hit = 1.0
        self.attack_timer = 0.0
        self.state = "idle"
        self.anim_time = 0.0
        
        # HAL Lab style squash and stretch
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.target_squash_x = 1.0
        self.target_squash_y = 1.0
        self.squash_speed = 8.0
    
    def take_damage(self, damage=1):
        if self.last_hit > 0.5:
            self.hp -= damage
            self.last_hit = 0.0
            if sounds["boss_hurt"]:
                sounds["boss_hurt"].play()
            create_explosion(self.x, self.y - 50, WHITE, 15)
            
            # Squash and stretch when hit
            self.target_squash_x = 0.8
            self.target_squash_y = 1.2
    
    def update_squash_stretch(self, dt):
        # Update squash and stretch with tweening
        squash_speed = self.squash_speed * dt
        self.squash_x += (self.target_squash_x - self.squash_x) * squash_speed
        self.squash_y += (self.target_squash_y - self.squash_y) * squash_speed
        
        # Reset target squash
        self.target_squash_x = 1.0
        self.target_squash_y = 1.0

class WhispyWoods(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y, 15)
        self.apple_timer = 0.0
        self.shake_amount = 0.0
        self.sway_angle = 0.0
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 60), int(self.y - 180), 120, 180)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.apple_timer += dt
        self.sway_angle += dt * 0.5
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Shake when hit
        if self.last_hit < 0.5:
            self.shake_amount = 5.0
        else:
            self.shake_amount *= 0.9
        
        # Add sway effect
        sway = math.sin(self.sway_angle) * 0.05
        self.target_squash_x = 1.0 + sway
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
        
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
            
            # Create apple particles
            for _ in range(5):
                particles.append(Particle(
                    apple_x + random.randint(-10, 10),
                    self.y - 200,
                    random.randint(-20, 20),
                    random.randint(-20, 0),
                    (255, 0, 0), 0.5, 4,
                    tween_type="bouncy"
                ))
            
            # Squash and stretch when dropping apples
            self.target_squash_x = 1.1
            self.target_squash_y = 0.9
    
    def draw(self, surf, camx):
        sx = int(self.x - camx + random.uniform(-self.shake_amount, self.shake_amount))
        if -150 <= sx <= W + 150:
            # Apply squash and stretch
            trunk_width = int(80 * self.squash_x)
            trunk_height = int(150 * self.squash_y)
            
            # Flash white when hit
            trunk_color = (139, 69, 19) if self.last_hit > 0.2 else WHITE
            leaves_color = (34, 139, 34) if self.last_hit > 0.2 else WHITE
            
            # Trunk
            pygame.draw.rect(surf, trunk_color, 
                           (sx - trunk_width//2, int(self.y) - trunk_height, 
                            trunk_width, trunk_height))
            
            # Leaves with animation
            leaves_offset = math.sin(self.anim_time) * 5
            leaves_width = int(140 * self.squash_x)
            leaves_height = int(140 * self.squash_y)
            pygame.draw.ellipse(surf, leaves_color, 
                              (sx - leaves_width//2, int(self.y) - 140 + leaves_offset - leaves_height//2, 
                               leaves_width, leaves_height))
            
            # Eyes with blink animation
            eye_height = int(16 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx - 20 - 8, int(self.y) - 140 + leaves_offset - eye_height//2, 16, eye_height))
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx + 20 - 8, int(self.y) - 140 + leaves_offset - eye_height//2, 16, eye_height))
            
            # Angry eyebrows
            brow_width = int(20 * self.squash_x)
            pygame.draw.line(surf, BLACK, 
                           (sx - 30, int(self.y) - 150 + leaves_offset), 
                           (sx - 10, int(self.y) - 145 + leaves_offset), 3)
            pygame.draw.line(surf, BLACK, 
                           (sx + 30, int(self.y) - 150 + leaves_offset), 
                           (sx + 10, int(self.y) - 145 + leaves_offset), 3)
            
            # Mouth
            mouth_width = int(30 * self.squash_x)
            pygame.draw.arc(surf, BLACK, 
                           (sx - mouth_width//2, int(self.y) - 130 + leaves_offset, mouth_width, 20), 
                           0, math.pi, 2)

class KingDedede(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y, 25)
        self.vy = 0.0
        self.hammer_angle = 0
        self.walk_cycle = 0.0
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
        self.mouth_openness = 0.0
        self.target_mouth_openness = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 50), int(self.y - 80), 100, 80)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.hammer_angle += dt * 2
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
        
        # Update mouth openness with tweening
        self.mouth_openness += (self.target_mouth_openness - self.mouth_openness) * 10 * dt
        
        if self.state == "idle":
            self.walk_cycle += 50 * dt * 0.05
            
            # Add bounce to walk
            bounce = math.sin(self.walk_cycle * 2) * 0.05
            self.target_squash_y = 1.0 + bounce
            
            if self.attack_timer > 2.5:
                self.state = "jumping"
                self.attack_timer = 0.0
                self.vy = -550
                
                # Squash and stretch for jump
                self.target_squash_x = 1.2
                self.target_squash_y = 0.8
                
                # Open mouth when jumping
                self.target_mouth_openness = 1.0
        
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
                
                # Squash and stretch for landing
                self.target_squash_x = 1.3
                self.target_squash_y = 0.7
                
                # Close mouth after landing
                self.target_mouth_openness = 0.0
                
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
            # Apply squash and stretch
            body_width = int(100 * self.squash_x)
            body_height = int(80 * self.squash_y)
            
            body_color = (0, 0, 200) if self.last_hit > 0.2 else WHITE
            
            # Body
            pygame.draw.ellipse(surf, body_color, 
                              (sx - body_width//2, int(self.y) - 40 - body_height//2, 
                               body_width, body_height))
            
            # Crown
            crown_width = int(60 * self.squash_x)
            crown_points = [
                (sx - 30, int(self.y) - 80),
                (sx - 20, int(self.y) - 100),
                (sx - 10, int(self.y) - 85),
                (sx, int(self.y) - 95),
                (sx + 10, int(self.y) - 85),
                (sx + 20, int(self.y) - 100),
                (sx + 30, int(self.y) - 80)
            ]
            pygame.draw.polygon(surf, (255, 215, 0), crown_points)
            
            # Eyes with blink animation
            eye_height = int(10 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx - 15 - 5, int(self.y) - 45 - eye_height//2, 10, eye_height))
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx + 15 - 5, int(self.y) - 45 - eye_height//2, 10, eye_height))
                
                # Eye highlights
                if self.eye_openness > 0.5:
                    pygame.draw.circle(surf, WHITE, 
                                     (sx - 13, int(self.y) - 47), 2)
                    pygame.draw.circle(surf, WHITE, 
                                     (sx + 17, int(self.y) - 47), 2)
            
            # Mouth with animation
            if self.mouth_openness > 0:
                mouth_width = int(20 * self.mouth_openness * self.squash_x)
                mouth_height = int(10 * self.mouth_openness * self.squash_y)
                
                if self.state == "slam":
                    pygame.draw.arc(surf, BLACK, 
                                   (sx - mouth_width//2, int(self.y) - 30, mouth_width, mouth_height), 
                                   0, math.pi, 3)
                else:
                    pygame.draw.ellipse(surf, BLACK, 
                                       (sx - mouth_width//2, int(self.y) - 25 - mouth_height//2, 
                                        mouth_width, mouth_height))
            else:
                pygame.draw.line(surf, BLACK, 
                               (sx - 10, int(self.y) - 25), 
                               (sx + 10, int(self.y) - 25), 2)
            
            # Feet with animation
            foot_width = int(15 * self.squash_x)
            foot_height = int(10 * self.squash_y)
            
            if self.state == "idle":
                foot_offset = int(Tween.bouncy_step(self.walk_cycle) * 5)
                pygame.draw.ellipse(surf, (0, 0, 150), 
                                   (sx - 20, int(self.y) + 5 + foot_offset, foot_width, foot_height))
                pygame.draw.ellipse(surf, (0, 0, 150), 
                                   (sx + 5, int(self.y) + 5 - foot_offset, foot_width, foot_height))
            else:
                pygame.draw.ellipse(surf, (0, 0, 150), 
                                   (sx - 20, int(self.y) + 5, foot_width, foot_height))
                pygame.draw.ellipse(surf, (0, 0, 150), 
                                   (sx + 5, int(self.y) + 5, foot_width, foot_height))
            
            # Hammer
            hammer_x = sx + math.cos(self.hammer_angle) * 60
            hammer_y = int(self.y) - 40 + math.sin(self.hammer_angle) * 30
            hammer_width = int(10 * self.squash_x)
            hammer_height = int(40 * self.squash_y)
            
            pygame.draw.rect(surf, (139, 69, 19), 
                           (int(hammer_x) - hammer_width//2, int(hammer_y) - hammer_height//2, 
                            hammer_width, hammer_height))
            
            hammer_head_width = int(40 * self.squash_x)
            hammer_head_height = int(15 * self.squash_y)
            pygame.draw.rect(surf, SWORD_SILVER, 
                           (int(hammer_x) - hammer_head_width//2, 
                            int(hammer_y) - hammer_height//2 - hammer_head_height//2, 
                            hammer_head_width, hammer_head_height))

class MetaKnight(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 30, 20)
        self.teleport_timer = 0.0
        self.sword_attacks = []
        self.mask_angle = 0.0
        self.cape_flap = 0.0
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 25), int(self.y - 35), 50, 70)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.teleport_timer += dt
        self.mask_angle += dt * 0.5
        self.cape_flap += dt * 5
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
        
        # Teleport
        if self.teleport_timer > 3.0:
            self.teleport_timer = 0.0
            old_x = self.x
            self.x = player.x + random.choice([-150, 150])
            self.x = max(100, min(LEVEL_LEN - 100, self.x))
            create_explosion(old_x, self.y, BEAM_PURPLE, 15)
            create_explosion(self.x, self.y, BEAM_PURPLE, 15)
            
            # Squash and stretch for teleport
            self.target_squash_x = 0.5
            self.target_squash_y = 1.5
        
        # Sword wave attack
        if self.attack_timer > 1.5:
            self.attack_timer = 0.0
            
            # Squash and stretch for attack
            self.target_squash_x = 1.2
            self.target_squash_y = 0.8
            
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
            # Apply squash and stretch
            body_width = int(40 * self.squash_x)
            body_height = int(40 * self.squash_y)
            
            # Cape with animation
            cape_color = (75, 0, 130) if self.last_hit > 0.2 else WHITE
            cape_offset = math.sin(self.cape_flap) * 5
            cape_width = int(50 * self.squash_x)
            cape_height = int(50 * self.squash_y)
            
            pygame.draw.polygon(surf, cape_color, [
                (sx - 25, int(self.y) + 30),
                (sx + 25, int(self.y) + 30),
                (sx + 20 + cape_offset, int(self.y) - 20),
                (sx - 20 + cape_offset, int(self.y) - 20)
            ])
            
            # Body
            pygame.draw.ellipse(surf, (0, 0, 100), 
                              (sx - body_width//2, int(self.y) - body_height//2, 
                               body_width, body_height))
            
            # Mask with animation
            mask_offset = math.sin(self.mask_angle) * 2
            mask_width = int(30 * self.squash_x)
            mask_height = int(25 * self.squash_y)
            
            pygame.draw.ellipse(surf, SWORD_SILVER, 
                              (sx - mask_width//2, int(self.y) - 15 + mask_offset - mask_height//2, 
                               mask_width, mask_height))
            
            # Eyes with blink animation
            eye_height = int(8 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, (255, 255, 0), 
                                   (sx - 7 - 4, int(self.y) - 5 + mask_offset - eye_height//2, 8, eye_height))
                pygame.draw.ellipse(surf, (255, 255, 0), 
                                   (sx + 7 - 4, int(self.y) - 5 + mask_offset - eye_height//2, 8, eye_height))
            
            # Sword
            sword_width = int(3 * self.squash_x)
            sword_height = int(30 * self.squash_y)
            
            pygame.draw.rect(surf, WHITE, 
                           (sx + 25, int(self.y) - 10 - sword_height//2, sword_width, sword_height))

class NightmareWizard(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 100, 30)
        self.float_time = 0.0
        self.orb_angle = 0.0
        self.hand_angle = 0.0
        self.eye_glow = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 40), int(self.y - 40), 80, 80)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.float_time += dt
        self.orb_angle += dt * 2
        self.hand_angle += dt
        self.eye_glow += dt * 3
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Float motion with bounce
        self.y = FLOOR_Y - 100 + math.sin(self.float_time) * 30
        bounce = math.sin(self.float_time * 2) * 0.1
        self.target_squash_y = 1.0 + bounce
        
        # Dark orb attack
        if self.attack_timer > 2.0:
            self.attack_timer = 0.0
            
            # Squash and stretch for attack
            self.target_squash_x = 1.2
            self.target_squash_y = 0.8
            
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
            # Apply squash and stretch
            body_width = int(80 * self.squash_x)
            body_height = int(80 * self.squash_y)
            
            # Dark aura with animation
            for i in range(3):
                alpha = (3 - i) / 3
                size = 50 + i * 15 + math.sin(self.anim_time * 2 + i) * 5
                color = (100 - i*30, 0, 100 - i*30)
                pygame.draw.circle(surf, color, (sx, int(self.y)), int(size), 2)
            
            # Body
            body_color = (50, 0, 100) if self.last_hit > 0.2 else WHITE
            pygame.draw.ellipse(surf, body_color, 
                              (sx - body_width//2, int(self.y) - body_height//2, 
                               body_width, body_height))
            
            # Hands with animation
            hand_offset = math.sin(self.hand_angle) * 10
            hand_width = int(30 * self.squash_x)
            hand_height = int(30 * self.squash_y)
            
            pygame.draw.ellipse(surf, body_color, 
                              (sx - 40 - hand_width//2, int(self.y) + hand_offset - hand_height//2, 
                               hand_width, hand_height))
            pygame.draw.ellipse(surf, body_color, 
                              (sx + 40 - hand_width//2, int(self.y) - hand_offset - hand_height//2, 
                               hand_width, hand_height))
            
            # Eyes with glow animation
            eye_offset = math.sin(self.anim_time * 3) * 2
            glow = math.sin(self.eye_glow) * 0.3 + 0.7
            
            eye_width = int(15 * self.squash_x * glow)
            eye_height = int(15 * self.squash_y * glow)
            
            pygame.draw.polygon(surf, (255, 0, 0), [
                (sx - 15, int(self.y) - 10 + eye_offset),
                (sx - 8, int(self.y) - 5 + eye_offset),
                (sx - 15, int(self.y) + eye_offset)
            ])
            pygame.draw.polygon(surf, (255, 0, 0), [
                (sx + 15, int(self.y) - 10 + eye_offset),
                (sx + 8, int(self.y) - 5 + eye_offset),
                (sx + 15, int(self.y) + eye_offset)
            ])
            
            # Mouth
            mouth_width = int(20 * self.squash_x)
            pygame.draw.arc(surf, BLACK, 
                           (sx - mouth_width//2, int(self.y) + 5, mouth_width, 15), 
                           0, math.pi, 2)

class Marx(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 80, 35)
        self.wings_angle = 0
        self.teleport_cooldown = 0
        self.attack_pattern = 0
        self.eye_offset = 0.0
        self.wing_flap = 0.0
        self.eye_blink_timer = random.uniform(3, 8)
        self.eye_blinking = False
        self.eye_openness = 1.0
        self.mouth_openness = 0.0
        self.target_mouth_openness = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 35), int(self.y - 35), 70, 70)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.wings_angle += dt * 3
        self.teleport_cooldown = max(0, self.teleport_cooldown - dt)
        self.eye_offset = math.sin(self.anim_time * 2) * 3
        self.wing_flap += dt * 10
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Eye blink animation
        self.eye_blink_timer -= dt
        if self.eye_blink_timer <= 0:
            self.eye_blinking = True
            self.eye_blink_timer = random.uniform(3, 8)
        
        if self.eye_blinking:
            self.eye_openness -= dt * 10
            if self.eye_openness <= 0:
                self.eye_openness = 0
                self.eye_blinking = False
        else:
            self.eye_openness += dt * 8
            if self.eye_openness >= 1:
                self.eye_openness = 1
        
        # Update mouth openness with tweening
        self.mouth_openness += (self.target_mouth_openness - self.mouth_openness) * 10 * dt
        
        # Float and move
        self.y = FLOOR_Y - 80 + math.sin(self.wings_angle) * 20
        bounce = math.sin(self.wings_angle * 2) * 0.1
        self.target_squash_y = 1.0 + bounce
        
        # Teleport occasionally
        if self.teleport_cooldown <= 0 and random.random() < 0.01:
            self.teleport_cooldown = 3.0
            create_explosion(self.x, self.y, BEAM_PURPLE, 20)
            self.x = random.randint(200, LEVEL_LEN - 200)
            create_explosion(self.x, self.y, BEAM_PURPLE, 20)
            
            # Squash and stretch for teleport
            self.target_squash_x = 0.5
            self.target_squash_y = 1.5
        
        # Varied attack patterns
        if self.attack_timer > 1.5:
            self.attack_timer = 0.0
            self.attack_pattern = (self.attack_pattern + 1) % 3
            
            # Squash and stretch for attack
            self.target_squash_x = 1.2
            self.target_squash_y = 0.8
            
            # Open mouth when attacking
            self.target_mouth_openness = 1.0
            
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
        else:
            # Close mouth after attack
            self.target_mouth_openness = 0.0
    
    def draw(self, surf, camx):
        sx = int(self.x - camx)
        if -100 <= sx <= W + 100:
            # Apply squash and stretch
            body_width = int(70 * self.squash_x)
            body_height = int(70 * self.squash_y)
            
            # Wings with animation
            wing_offset = abs(math.sin(self.wing_flap)) * 30
            wing_color = (200, 0, 200) if self.last_hit > 0.2 else WHITE
            
            # Left wing
            left_wing_points = [
                (sx - 25, int(self.y)),
                (sx - 60 - wing_offset, int(self.y) - 20),
                (sx - 55 - wing_offset, int(self.y) + 20)
            ]
            pygame.draw.polygon(surf, wing_color, left_wing_points)
            
            # Right wing  
            right_wing_points = [
                (sx + 25, int(self.y)),
                (sx + 60 + wing_offset, int(self.y) - 20),
                (sx + 55 + wing_offset, int(self.y) + 20)
            ]
            pygame.draw.polygon(surf, wing_color, right_wing_points)
            
            # Body
            body_color = (150, 0, 150) if self.last_hit > 0.2 else WHITE
            pygame.draw.ellipse(surf, body_color, 
                              (sx - body_width//2, int(self.y) - body_height//2, 
                               body_width, body_height))
            
            # Hat
            hat_width = int(40 * self.squash_x)
            hat_height = int(20 * self.squash_y)
            pygame.draw.polygon(surf, (255, 0, 255), [
                (sx - 20, int(self.y) - 25),
                (sx + 20, int(self.y) - 25),
                (sx, int(self.y) - 45)
            ])
            
            # Eyes with blink animation
            eye_height = int(10 * self.eye_openness)
            if eye_height > 0:
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx - 10 - 5, int(self.y) - 5 + self.eye_offset - eye_height//2, 10, eye_height))
                pygame.draw.ellipse(surf, BLACK, 
                                   (sx + 10 - 5, int(self.y) - 5 - self.eye_offset - eye_height//2, 10, eye_height))
                
                # Eye highlights
                if self.eye_openness > 0.5:
                    pygame.draw.circle(surf, WHITE, 
                                     (sx - 8, int(self.y) - 7 + self.eye_offset), 2)
                    pygame.draw.circle(surf, WHITE, 
                                     (sx + 12, int(self.y) - 7 - self.eye_offset), 2)
            
            # Mouth with animation
            if self.mouth_openness > 0:
                mouth_width = int(20 * self.mouth_openness * self.squash_x)
                mouth_height = int(10 * self.mouth_openness * self.squash_y)
                
                if self.attack_pattern == 2:
                    pygame.draw.arc(surf, BLACK, 
                                   (sx - mouth_width//2, int(self.y), mouth_width, mouth_height), 
                                   0, math.pi, 3)
                else:
                    pygame.draw.ellipse(surf, BLACK, 
                                       (sx - mouth_width//2, int(self.y) + 5 - mouth_height//2, 
                                        mouth_width, mouth_height))
            else:
                pygame.draw.line(surf, BLACK, 
                               (sx - 10, int(self.y) + 5), 
                               (sx + 10, int(self.y) + 5), 2)

class ZeroTwo(Boss):
    def __init__(self, x):
        super().__init__(x, FLOOR_Y - 120, 50)
        self.eye_angle = 0
        self.blood_timer = 0
        self.phase = 1
        self.iris_pulse = 0.0
        self.wing_flap = 0.0
        self.halo_rotation = 0.0
        self.thorn_pulse = 0.0
    
    def rect(self):
        return pygame.Rect(int(self.x - 60), int(self.y - 60), 120, 120)
    
    def update(self, dt, player):
        self.anim_time += dt
        self.last_hit += dt
        self.attack_timer += dt
        self.blood_timer += dt
        self.eye_angle += dt
        self.iris_pulse += dt * 2
        self.wing_flap += dt * 3
        self.halo_rotation += dt
        self.thorn_pulse += dt * 4
        
        # Update squash and stretch
        self.update_squash_stretch(dt)
        
        # Phase change
        if self.hp < self.max_hp // 2 and self.phase == 1:
            self.phase = 2
            create_explosion(self.x, self.y, (255, 0, 0), 30)
            
            # Squash and stretch for phase change
            self.target_squash_x = 1.5
            self.target_squash_y = 0.5
        
        # Floating movement with bounce
        self.y = FLOOR_Y - 120 + math.sin(self.eye_angle * 0.5) * 40
        self.x += math.sin(self.eye_angle * 0.3) * 100 * dt
        self.x = max(150, min(LEVEL_LEN - 150, self.x))
        
        bounce = math.sin(self.eye_angle) * 0.1
        self.target_squash_x = 1.0 + bounce
        self.target_squash_y = 1.0 - bounce
        
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
            
            # Blood particles
            for _ in range(3):
                particles.append(Particle(
                    self.x + random.randint(-20, 20),
                    self.y + 30,
                    random.randint(-20, 20),
                    random.randint(50, 100),
                    (150, 0, 0), 0.5, 4,
                    tween_type="bouncy"
                ))
        
        # Crystal shards attack
        if self.attack_timer > 2.5:
            self.attack_timer = 0
            
            # Squash and stretch for attack
            self.target_squash_x = 1.2
            self.target_squash_y = 0.8
            
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
            # Apply squash and stretch
            body_width = int(120 * self.squash_x)
            body_height = int(120 * self.squash_y)
            
            # Wings (phase 2) with animation
            if self.phase == 2:
                wing_color = (100, 0, 0)
                wing_flap = math.sin(self.wing_flap) * 10
                
                # Left wing
                left_wing_points = [
                    (sx - 40, int(self.y)),
                    (sx - 100, int(self.y) - 40 + wing_flap),
                    (sx - 90, int(self.y) + 40 - wing_flap)
                ]
                pygame.draw.polygon(surf, wing_color, left_wing_points)
                
                # Right wing
                right_wing_points = [
                    (sx + 40, int(self.y)),
                    (sx + 100, int(self.y) - 40 + wing_flap),
                    (sx + 90, int(self.y) + 40 - wing_flap)
                ]
                pygame.draw.polygon(surf, wing_color, right_wing_points)
            
            # Main eye body
            body_color = WHITE if self.last_hit > 0.2 else (255, 100, 100)
            pygame.draw.ellipse(surf, body_color, 
                              (sx - body_width//2, int(self.y) - body_height//2, 
                               body_width, body_height))
            
            # Iris with pulse animation
            iris_size = 35 + math.sin(self.iris_pulse) * 3
            iris_color = (0, 200, 0) if self.phase == 1 else (200, 0, 0)
            pygame.draw.circle(surf, iris_color, (sx, int(self.y)), int(iris_size))
            
            # Pupil with animation
            pupil_x = sx + math.cos(self.eye_angle) * 10
            pupil_y = int(self.y) + math.sin(self.eye_angle) * 10
            pygame.draw.circle(surf, BLACK, (int(pupil_x), int(pupil_y)), 15)
            
            # Blood tears (phase 2) with animation
            if self.phase == 2:
                tear_length = 30 + math.sin(self.anim_time * 5) * 5
                pygame.draw.line(surf, (150, 0, 0), 
                               (sx - 20, int(self.y) + 30),
                               (sx - 25, int(self.y) + 30 + tear_length), 3)
                pygame.draw.line(surf, (150, 0, 0), 
                               (sx + 20, int(self.y) + 30),
                               (sx + 25, int(self.y) + 30 + tear_length), 3)
                
                # Blood drops
                if int(self.anim_time * 10) % 2 == 0:
                    pygame.draw.circle(surf, (150, 0, 0), 
                                     (sx - 25, int(self.y) + 30 + tear_length + 5), 3)
                    pygame.draw.circle(surf, (150, 0, 0), 
                                     (sx + 25, int(self.y) + 30 + tear_length + 5), 3)
            
            # Halo (phase 1) or thorns (phase 2) with animation
            if self.phase == 1:
                for i in range(6):
                    angle = i * math.pi / 3 + self.halo_rotation
                    halo_x = sx + math.cos(angle) * 30
                    halo_y = int(self.y) - 70 + math.sin(angle) * 30
                    pygame.draw.circle(surf, (255, 255, 100), 
                                     (int(halo_x), int(halo_y)), 5)
            else:
                thorn_pulse = math.sin(self.thorn_pulse) * 5
                for i in range(6):
                    angle = i * math.pi / 3
                    thorn_x = sx + math.cos(angle) * (70 + thorn_pulse)
                    thorn_y = int(self.y) + math.sin(angle) * (70 + thorn_pulse)
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
        self.camera_shake = 0.0
    
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
            
            # Title with bounce animation
            title_bounce = math.sin(pygame.time.get_ticks() * 0.003) * 5
            title_text = ultra_font.render("Kirby's Adventure", True, KIRBY_PINK)
            title_rect = title_text.get_rect(center=(W//2, H//2 - 100 + title_bounce))
            screen.blit(title_text, title_rect)
            
            subtitle = big_font.render("HAL Lab Tweening Style", True, WHITE)
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
            
            # Floating Kirby animation with HAL Lab tweening
            kirby_y = H//2 + math.sin(pygame.time.get_ticks() * 0.002) * 20
            kirby_squash = 1.0 + math.sin(pygame.time.get_ticks() * 0.004) * 0.1
            
            # Left Kirby
            kirby_width = int(30 * kirby_squash)
            kirby_height = int(30 / kirby_squash)
            pygame.draw.ellipse(screen, KIRBY_PINK, 
                              (100 - kirby_width//2, int(kirby_y) - kirby_height//2, 
                               kirby_width, kirby_height))
            
            # Right Kirby
            pygame.draw.ellipse(screen, KIRBY_PINK, 
                              (W - 100 - kirby_width//2, int(kirby_y) - kirby_height//2, 
                               kirby_width, kirby_height))
            
            if inputs.just_pressed("start"):
                game.setup_level(1)
                game.state = "playing"
                if sounds["power_up"]:
                    sounds["power_up"].play()
        
        # Main gameplay
        elif game.state == "playing":
            dt = clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap dt to prevent physics issues
            
            # Update camera shake
            if game.camera_shake > 0:
                game.camera_shake -= dt * 5
            
            # Update player
            game.player.update(dt)
            
            # Update camera with smooth following
            target_cam_x = game.player.x - W // 2
            cam_speed = 0.1
            game.camera_x += (target_cam_x - game.camera_x) * cam_speed
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
                            # Add camera shake when hit
                            game.camera_shake = 5.0
            
            # Update boss
            if game.boss and game.boss.hp > 0:
                game.boss.update(dt, game.player)
                
                # Check collision with boss
                if game.boss.rect().colliderect(game.player.rect()):
                    if game.player.invuln_time <= 0:
                        game.player.take_damage()
                        game.boss.take_damage(1)
                        game.score += 500
                        # Add camera shake when hit
                        game.camera_shake = 5.0
                
                # Boss defeated
                if game.boss.hp <= 0:
                    game.score += 5000
                    create_explosion(game.boss.x, game.boss.y - 50, WHITE, 50)
                    if sounds["win"]:
                        sounds["win"].play()
                    
                    # Add camera shake for boss defeat
                    game.camera_shake = 10.0
                    
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
                        # Add camera shake when hit
                        game.camera_shake = 3.0
            
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
            
            # Apply camera shake
            shake_x = 0
            shake_y = 0
            if game.camera_shake > 0:
                shake_x = random.uniform(-game.camera_shake, game.camera_shake)
                shake_y = random.uniform(-game.camera_shake, game.camera_shake)
            
            # Create a temporary surface for the game world
            game_surface = pygame.Surface((W, H))
            game_surface.set_colorkey((0, 0, 0))
            
            # Ground
            pygame.draw.rect(game_surface, GRASS_GREEN, 
                           (0, FLOOR_Y, W, H - FLOOR_Y))
            
            # Decorative clouds with HAL Lab tweening
            for i in range(3):
                cloud_x = (i * 300 - game.camera_x * 0.3) % (W + 200) - 100
                cloud_y = 50 + i * 40
                cloud_bounce = math.sin(pygame.time.get_ticks() * 0.001 + i) * 5
                cloud_width = int(80 * (1.0 + math.sin(pygame.time.get_ticks() * 0.002 + i) * 0.1))
                cloud_height = int(40 * (1.0 - math.sin(pygame.time.get_ticks() * 0.002 + i) * 0.1))
                
                pygame.draw.ellipse(game_surface, WHITE, 
                                  (int(cloud_x), cloud_y + cloud_bounce, cloud_width, cloud_height))
                pygame.draw.ellipse(game_surface, WHITE, 
                                  (int(cloud_x) + 30, cloud_y - 10 + cloud_bounce, 
                                   int(cloud_width * 0.75), int(cloud_height * 0.875)))
            
            # Draw entities
            game.player.draw(game_surface, game.camera_x)
            
            for enemy in game.enemies:
                enemy.draw(game_surface, game.camera_x)
            
            if game.boss:
                game.boss.draw(game_surface, game.camera_x)
            
            for proj in projectiles:
                proj.draw(game_surface, game.camera_x)
            
            for particle in particles:
                particle.draw(game_surface, game.camera_x)
            
            # Blit game surface with shake
            screen.blit(game_surface, (shake_x, shake_y))
            
            # Draw HUD
            draw_hud(screen)
            
            # Level name with bounce animation
            level_name = level_info["name"]
            level_bounce = math.sin(pygame.time.get_ticks() * 0.003) * 3
            level_text = big_font.render(level_name, True, WHITE)
            level_rect = level_text.get_rect(center=(W//2, 80 + level_bounce))
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
            
            # Paused text with bounce animation
            pause_bounce = math.sin(pygame.time.get_ticks() * 0.003) * 5
            pause_text = ultra_font.render("PAUSED", True, WHITE)
            pause_rect = pause_text.get_rect(center=(W//2, H//2 + pause_bounce))
            screen.blit(pause_text, pause_rect)
            
            hint_text = font.render("Press ESC to Resume", True, WHITE)
            hint_rect = hint_text.get_rect(center=(W//2, H//2 + 50))
            screen.blit(hint_text, hint_rect)
        
        # Victory screen
        elif game.state == "victory":
            draw_gradient_bg(screen, (255, 215, 0), (255, 100, 200))
            
            # Victory text with bounce animation
            victory_bounce = math.sin(pygame.time.get_ticks() * 0.003) * 10
            victory_text = ultra_font.render("VICTORY!", True, WHITE)
            victory_rect = victory_text.get_rect(center=(W//2, H//2 - 100 + victory_bounce))
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
            
            # Game over text with bounce animation
            game_over_bounce = math.sin(pygame.time.get_ticks() * 0.003) * 5
            game_over_text = ultra_font.render("GAME OVER", True, WHITE)
            game_over_rect = game_over_text.get_rect(center=(W//2, H//2 - 50 + game_over_bounce))
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
