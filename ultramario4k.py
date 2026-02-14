import pygame
import sys
import random
import math

# -------------------------------------------------
# INITIALIZATION & CONSTANTS
# -------------------------------------------------
pygame.init()
pygame.display.set_caption("AC HOLDING'S SMB")

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 40

# Physics
GRAVITY = 0.5
FRICTION = 0.8
ACCEL = 0.5
MAX_SPEED = 7
JUMP_POWER = -14
BOUNCE_POWER = -8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (92, 148, 252)
UNDERGROUND_BG = (15, 15, 15)
CASTLE_BG = (10, 0, 0)
SKY_ALT_BG = (200, 220, 255)

GROUND_BROWN = (200, 76, 12)
BRICK_BROWN = (180, 90, 30)
UNDERGROUND_BRICK = (0, 100, 200)
CASTLE_BRICK = (120, 120, 120)
PIPE_GREEN = (0, 200, 0)
LAVA_RED = (200, 0, 0)
GOLD = (255, 215, 0)
BOWSER_GREEN = (50, 200, 50)
BOWSER_RED = (200, 50, 50)
MUSHROOM_COLOR = (255, 0, 0) 

# Fonts
try:
    font_lg = pygame.font.Font(None, 72)
    font_md = pygame.font.Font(None, 48)
    font_sm = pygame.font.Font(None, 24)
except:
    font_lg = pygame.font.SysFont('arial', 72)
    font_md = pygame.font.SysFont('arial', 48)
    font_sm = pygame.font.SysFont('arial', 24)

# -------------------------------------------------
# CAMERA
# -------------------------------------------------
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        
        # Limit scrolling to map bounds
        x = min(0, x)  # Left side
        x = max(-(self.width - SCREEN_WIDTH), x)  # Right side
        
        self.camera = pygame.Rect(x, 0, self.width, self.height)

# -------------------------------------------------
# ENTITIES
# -------------------------------------------------
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0
        self.color = color

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, (255, 0, 0)) # Mario Red
        self.on_ground = False
        self.facing_right = True
        self.dead = False
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.iframe_timer = 0
        self.invincible = False 

    def update(self, platforms, enemies, hazards, keys, goal_rect, current_theme):
        if self.dead:
            return
        
        if self.iframe_timer > 0:
            self.iframe_timer -= 1
        
        # --- Input ---
        if keys[pygame.K_LEFT]:
            self.vx -= ACCEL
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx += ACCEL
            self.facing_right = True
        else:
            self.vx *= FRICTION

        # Cap Speed
        if self.vx > MAX_SPEED: self.vx = MAX_SPEED
        if self.vx < -MAX_SPEED: self.vx = -MAX_SPEED
        if abs(self.vx) < 0.1: self.vx = 0

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = JUMP_POWER
            self.on_ground = False

        # Gravity
        self.vy += GRAVITY
        
        # --- X Movement & Collision ---
        self.rect.x += int(self.vx)
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for block in hits:
            if self.vx > 0:
                self.rect.right = block.rect.left
                self.vx = 0
            elif self.vx < 0:
                self.rect.left = block.rect.right
                self.vx = 0

        # --- Y Movement & Collision ---
        self.rect.y += int(self.vy)
        self.on_ground = False
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for block in hits:
            if self.vy > 0:
                self.rect.bottom = block.rect.top
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.rect.top = block.rect.bottom
                self.vy = 0
                if isinstance(block, Block) and block.type == "question":
                    block.hit()
                    self.score += 100
                    self.coins += 1

        # --- Hazards (Lava/Pits) ---
        for hazard in hazards:
            if self.rect.colliderect(hazard):
                self.die()
                break

        if self.rect.y > SCREEN_HEIGHT + 100:
            self.die()

        # --- Enemy Collision ---
        if self.iframe_timer == 0:
            e_hits = pygame.sprite.spritecollide(self, enemies, False)
            for e in e_hits:
                if self.vy > 0 and self.rect.bottom < e.rect.centery + 20:
                    e.die()
                    self.vy = BOUNCE_POWER
                    self.score += 200
                else:
                    self.die()
                    break

        # --- Bowser Fireball Collision ---
        for e in enemies:
            if isinstance(e, Bowser):
                for f in e.fireballs:
                    if self.rect.colliderect(f) and self.iframe_timer == 0:
                        self.die()
                        break

    def die(self):
        if self.iframe_timer > 0:
            return
        self.dead = True
        self.lives -= 1
        self.iframe_timer = 60

    def draw(self, screen, cam):
        rect = cam.apply(self)
        
        color = self.color
        if self.iframe_timer > 0 and (self.iframe_timer // 4) % 2 == 0:
            color = WHITE
            
        pygame.draw.rect(screen, color, rect)
        
        # Overalls
        overalls_color = (0, 0, 200)
        pygame.draw.rect(screen, overalls_color, (rect.x, rect.y + 20, 32, 12))
        
        # Eyes
        eye_x = rect.x + 20 if self.facing_right else rect.x + 4
        pygame.draw.rect(screen, BLACK, (eye_x, rect.y + 4, 4, 8))
        
        # Hat brim
        brim_x = rect.x + 16 if self.facing_right else rect.x - 4
        pygame.draw.rect(screen, (200, 0, 0), (brim_x, rect.y, 20, 4))

class Block(Entity):
    def __init__(self, x, y, w, h, color, btype="normal"):
        super().__init__(x, y, w, h, color)
        self.type = btype
        self.original_y = y
        self.bump_timer = 0
    
    def hit(self):
        if self.type == "question":
            self.type = "empty"
            self.color = (139, 69, 19) 
            self.bump_timer = 10
    
    def update(self):
        if self.bump_timer > 0:
            self.rect.y = self.original_y - 10
            self.bump_timer -= 1
        else:
            self.rect.y = self.original_y

class Enemy(Entity):
    def __init__(self, x, y, w, h, color, speed):
        super().__init__(x, y, w, h, color)
        self.vx = -speed
        self.alive = True
    
    def update(self, platforms):
        if not self.alive:
            return
        
        self.vy += GRAVITY
        self.rect.x += int(self.vx)
        
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for block in hits:
            if self.vx > 0:
                self.rect.right = block.rect.left
                self.vx *= -1
            elif self.vx < 0:
                self.rect.left = block.rect.right
                self.vx *= -1
        
        self.rect.y += int(self.vy)
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for block in hits:
            if self.vy > 0:
                self.rect.bottom = block.rect.top
                self.vy = 0

        if self.rect.y > SCREEN_HEIGHT + 200:
            self.kill()

    def die(self):
        self.alive = False
        self.kill()

class Goomba(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, (150, 75, 0), 2)

    def draw(self, screen, cam):
        r = cam.apply(self)
        pygame.draw.ellipse(screen, self.color, r)
        pygame.draw.circle(screen, WHITE, (r.x + 8, r.y + 10), 5)
        pygame.draw.circle(screen, WHITE, (r.x + 24, r.y + 10), 5)
        pygame.draw.circle(screen, BLACK, (r.x + 10, r.y + 10), 2)
        pygame.draw.circle(screen, BLACK, (r.x + 22, r.y + 10), 2)

class Bowser(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60, BOWSER_GREEN, 1)
        self.hp = 1
        self.timer = 0
        self.fireballs = []
        self.start_x = x
        self.jump_timer = 0
        self.alive = True

    def update(self, platforms):
        if not self.alive:
            return
        self.timer += 1
        self.jump_timer += 1
        
        if self.rect.x < self.start_x - 100:
            self.vx = 1
        if self.rect.x > self.start_x + 20:
            self.vx = -1
        
        if self.jump_timer > 120 and random.random() < 0.05:
            if self.vy == 0:
                self.vy = -12
                self.jump_timer = 0
        
        self.vy += GRAVITY
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for block in hits:
            if self.vy > 0:
                self.rect.bottom = block.rect.top
                self.vy = 0
        
        if self.timer % 150 == 0:
            self.fireballs.append(pygame.Rect(self.rect.x, self.rect.y + 20, 20, 10))
            
        for f in self.fireballs[:]:
            f.x -= 5
            if f.x < 0:
                self.fireballs.remove(f)

    def draw(self, screen, cam):
        r = cam.apply(self)
        pygame.draw.rect(screen, BOWSER_GREEN, r)
        pygame.draw.rect(screen, (50, 100, 50), (r.x + 40, r.y + 10, 20, 40))
        pygame.draw.rect(screen, BOWSER_RED, (r.x + 10, r.y - 10, 30, 10))
        pygame.draw.rect(screen, WHITE, (r.x + 5, r.y + 10, 10, 10))
        pygame.draw.rect(screen, BLACK, (r.x + 5, r.y + 10, 4, 4))
        
        for f in self.fireballs:
            fr = cam.apply_rect(f)
            pygame.draw.ellipse(screen, (255, 100, 0), fr)

# -------------------------------------------------
# LEVEL GENERATION
# -------------------------------------------------
def generate_level_data(abs_level_idx):
    """
    Returns (platforms, enemies, hazards, background_color, width, goal_rect, theme)
    abs_level_idx: 1 to 32
    """
    world = (abs_level_idx - 1) // 4 + 1
    stage = (abs_level_idx - 1) % 4 + 1
    
    # Theme Setup
    theme = "overworld"
    if stage == 2: theme = "underground"
    elif stage == 3: theme = "sky"
    elif stage == 4: theme = "castle"

    bg_color = SKY_BLUE
    ground_c = GROUND_BROWN
    brick_c = BRICK_BROWN
    
    if theme == "underground":
        bg_color = UNDERGROUND_BG
        ground_c = (0, 100, 0) 
        brick_c = UNDERGROUND_BRICK
    elif theme == "sky":
        bg_color = SKY_ALT_BG
        ground_c = WHITE
        brick_c = (200, 100, 100)
    elif theme == "castle":
        bg_color = CASTLE_BG
        ground_c = (80, 80, 80)
        brick_c = CASTLE_BRICK

    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    hazards = [] 
    
    ground_y = 13 # Row 13 from top (leaving 2 rows at bottom)
    
    # --- HELPER FUNCTIONS ---
    def add_block(tx, ty, btype="normal"):
        c = brick_c
        if btype == "question":
            c = GOLD
        elif btype == "solid":
            c = ground_c
        platforms.add(Block(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE, c, btype))

    def add_pipe(tx, height):
        # Pipe logic: Main body + rim
        for h in range(height):
            c = PIPE_GREEN
            platforms.add(Block(tx * TILE_SIZE, (ground_y - 1 - h) * TILE_SIZE, TILE_SIZE*2, TILE_SIZE, c, "pipe"))
        # Rim (top)
        platforms.add(Block((tx-0.2) * TILE_SIZE, (ground_y - height) * TILE_SIZE, TILE_SIZE*2.4, TILE_SIZE, (0, 230, 0), "pipe"))

    # --- GENERATION LOGIC ---
    
    # SPECIFIC LAYOUT FOR LEVEL 1-1 (abs_level_idx == 1)
    if abs_level_idx == 1:
        level_len = 220 # Approximate length of 1-1 in tiles
        
        # 1. Ground
        for x in range(level_len):
            # Main Ground
            add_block(x, ground_y, "solid")
            add_block(x, ground_y+1, "solid")
            
            # Gap 1
            if 69 <= x <= 70: 
                continue 
            # Gap 2
            if 86 <= x <= 88:
                continue
                
            add_block(x, ground_y, "solid")
            add_block(x, ground_y+1, "solid")

        # 2. Floating Blocks & Question Marks
        # Intro blocks
        add_block(16, ground_y - 4, "question")
        add_block(20, ground_y - 4, "normal")
        add_block(21, ground_y - 4, "question")
        add_block(22, ground_y - 4, "normal")
        add_block(23, ground_y - 4, "question")
        add_block(22, ground_y - 8, "question")
        
        # Post-gap blocks
        add_block(77, ground_y - 4, "question")
        
        # Stair blocks (Simplified representation)
        # Big Staircase near end
        for i in range(4):
            for j in range(i+1):
                add_block(134 + i, ground_y - 1 - j, "solid")
        # Descending side
        for i in range(4):
            for j in range(4 - i):
                add_block(138 + i, ground_y - 1 - j, "solid")

        # Final staircase to flag
        for i in range(8):
            for j in range(i+1):
                add_block(180 + i, ground_y - 1 - j, "solid")
                
        # 3. Pipes
        add_pipe(28, 2)
        add_pipe(38, 3)
        add_pipe(46, 4)
        add_pipe(57, 4) # Before first gap
        
        # 4. Enemies (Goombas)
        enemies.add(Goomba(22 * TILE_SIZE, (ground_y - 2) * TILE_SIZE))
        enemies.add(Goomba(100 * TILE_SIZE, (ground_y - 2) * TILE_SIZE))
        enemies.add(Goomba(110 * TILE_SIZE, (ground_y - 2) * TILE_SIZE))
        enemies.add(Goomba(120 * TILE_SIZE, (ground_y - 2) * TILE_SIZE))

        # 5. Goal
        flag_x = 198 * TILE_SIZE
        goal_rect = pygame.Rect(flag_x, (ground_y - 10) * TILE_SIZE, 10, 10 * TILE_SIZE)
        
        width = level_len * TILE_SIZE
        
        return platforms, enemies, hazards, bg_color, width, goal_rect, theme

    # PROCEDURAL GENERATION FOR OTHER LEVELS
    else:
        level_len = 150 + (world * 10) 
        if theme == "castle": level_len = 100 
        
        # Start Platform
        for x in range(0, 10):
            add_block(x, ground_y, "solid")
            add_block(x, ground_y+1, "solid")

        current_x = 10
        
        while current_x < level_len:
            segment_type = random.choice(["flat", "gap", "pipe", "stairs", "enemies"])
            if theme == "castle": 
                 segment_type = random.choice(["flat", "gap", "firebars", "bridge"])
                 if segment_type == "firebars": segment_type = "flat" 
                 if segment_type == "bridge": segment_type = "gap" 

            length = random.randint(3, 8)
            
            if segment_type == "gap":
                if theme == "castle":
                    hazards.append(pygame.Rect(current_x * TILE_SIZE, (ground_y + 1) * TILE_SIZE, length * TILE_SIZE, TILE_SIZE))
                    if length > 3:
                         add_block(current_x + length//2, ground_y - 3, "solid")
                pass

            elif segment_type == "pipe" and theme != "castle":
                for i in range(length):
                    add_block(current_x + i, ground_y, "solid")
                    add_block(current_x + i, ground_y+1, "solid")
                add_pipe(current_x + 1, random.randint(2, 4))
                
            elif segment_type == "stairs" and theme != "castle":
                 for i in range(length):
                     add_block(current_x + i, ground_y, "solid")
                     add_block(current_x + i, ground_y+1, "solid")
                     ht = min(i, length-1-i)
                     for h in range(ht):
                         add_block(current_x + i, ground_y - 1 - h, "solid")

            else: # Flat / Enemies
                for i in range(length):
                    add_block(current_x + i, ground_y, "solid")
                    add_block(current_x + i, ground_y+1, "solid")
                    
                    if theme in ["castle", "underground"]:
                        add_block(current_x + i, 0, "solid")
                        add_block(current_x + i, 1, "solid")
                        
                    if random.random() < 0.3:
                        h = random.randint(3, 5)
                        b = "question" if random.random() < 0.2 else "normal"
                        add_block(current_x + i, ground_y - h, b)
                        
                    if random.random() < 0.1 + (world * 0.02):
                        enemies.add(Goomba((current_x + i) * TILE_SIZE, (ground_y - 2) * TILE_SIZE))

            current_x += length

        # --- ENDING SEQUENCE ---
        for x in range(current_x, current_x + 5):
            add_block(x, ground_y, "solid")
            add_block(x, ground_y+1, "solid")
        current_x += 5

        goal_rect = None
        
        if theme == "castle":
            bridge_start = current_x
            bridge_len = 10
            hazards.append(pygame.Rect(bridge_start * TILE_SIZE, (ground_y+1)*TILE_SIZE, bridge_len*TILE_SIZE, TILE_SIZE))
            
            for i in range(bridge_len):
                add_block(bridge_start + i, ground_y, "solid")
            
            boss = Bowser((bridge_start + 6) * TILE_SIZE, (ground_y - 2) * TILE_SIZE)
            enemies.add(boss)
            
            axe_x = (bridge_start + bridge_len + 2) * TILE_SIZE
            goal_rect = pygame.Rect(axe_x, (ground_y - 2) * TILE_SIZE, 30, 30)
            
            for i in range(5):
                 add_block(bridge_start + bridge_len + i, ground_y, "solid")
                 add_block(bridge_start + bridge_len + i, ground_y+1, "solid")

            width = (bridge_start + bridge_len + 5) * TILE_SIZE
            
        else:
            # Flagpole
            for i in range(8):
                add_block(current_x + i, ground_y, "solid")
                for h in range(i):
                     add_block(current_x + i, ground_y - h, "solid")
            current_x += 8
            
            for i in range(5):
                 add_block(current_x + i, ground_y, "solid")
            
            flag_x = (current_x + 2) * TILE_SIZE
            goal_rect = pygame.Rect(flag_x, (ground_y - 9) * TILE_SIZE, 10, 9 * TILE_SIZE)
            
            width = (current_x + 5) * TILE_SIZE

    return platforms, enemies, hazards, bg_color, width, goal_rect, theme

# -------------------------------------------------
# GAME LOOPS & STATES
# -------------------------------------------------
def main():
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Game Variables
    level = 1
    player = Player(100, 100)
    
    # Level State
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    hazards = []
    bg_color = SKY_BLUE
    level_width = 0
    goal_rect = None
    current_theme = "overworld"
    
    # Camera
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    def load_level(lvl_idx):
        nonlocal platforms, enemies, hazards, bg_color, level_width, goal_rect, camera, current_theme
        platforms, enemies, hazards, bg_color, level_width, goal_rect, current_theme = generate_level_data(lvl_idx)
        camera = Camera(level_width, SCREEN_HEIGHT)
        player.rect.x = 100
        player.rect.y = 100
        player.vx = 0
        player.vy = 0
        player.dead = False
        player.iframe_timer = 0

    load_level(level)
    
    # Loop Logic
    running = True
    state = "MENU" 
    
    transition_timer = 0

    while running:
        # --- Events ---
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if state == "MENU":
                    if event.key == pygame.K_RETURN:
                        state = "PLAY"
                        level = 1
                        player.lives = 3
                        player.score = 0
                        player.coins = 0
                        load_level(level)
                elif state == "PLAY":
                    if event.key == pygame.K_r: 
                         load_level(level)

        # --- Update & Draw ---
        screen.fill(BLACK)
        
        if state == "MENU":
            screen.fill(SKY_BLUE)
            pygame.draw.rect(screen, GROUND_BROWN, (0, 500, 800, 100))
            
            title = font_lg.render("AC HOLDING'S SMB", True, (200, 0, 0))
            sub = font_md.render("Press ENTER to Start", True, WHITE)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
            screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 300))
            
            info = font_sm.render("Accurate 1-1 Layout | Arrows to Move, Space to Jump", True, WHITE)
            screen.blit(info, (SCREEN_WIDTH//2 - info.get_width()//2, 450))

        elif state == "PLAY":
            screen.fill(bg_color)
            
            player.update(platforms, enemies, hazards, keys, goal_rect, current_theme)
            enemies.update(platforms)
            camera.update(player)
            
            if goal_rect and player.rect.colliderect(goal_rect):
                if current_theme == "castle":
                    for e in enemies:
                        if isinstance(e, Bowser):
                            e.die() 
                    player.score += 5000
                else:
                    player.score += 1000 + (player.lives * 500)
                state = "TRANSITION"
                transition_timer = 120
                level += 1
                if level > 32:
                    level = 32 
            
            if player.dead:
                state = "TRANSITION"
                transition_timer = 120

            # Draw World
            for p in platforms:
                r = camera.apply(p)
                if r.right < 0 or r.left > SCREEN_WIDTH: continue
                pygame.draw.rect(screen, p.color, r)
                pygame.draw.rect(screen, (0,0,0), r, 1)
                if p.type == "question":
                     pygame.draw.rect(screen, (255,200,200), (r.x+5, r.y+5, 5, 5))

            for e in enemies:
                e.draw(screen, camera)

            for h in hazards:
                hr = camera.apply_rect(h)
                pygame.draw.rect(screen, LAVA_RED, hr)

            if goal_rect:
                gr = camera.apply_rect(goal_rect)
                if current_theme == "castle": 
                    pygame.draw.rect(screen, GOLD, gr)
                else: 
                    pygame.draw.rect(screen, (100, 100, 100), (gr.x + 4, gr.y, 2, gr.height)) 
                    pygame.draw.rect(screen, (0, 255, 0), (gr.x + 6, gr.y + 20, 30, 20)) 

            player.draw(screen, camera)
            
            # HUD
            w_num = (level - 1) // 4 + 1
            l_num = (level - 1) % 4 + 1
            hud_txt = f"WORLD {w_num}-{l_num}   LIVES x{player.lives}   COINS x{player.coins}   SCORE {player.score}"
            screen.blit(font_sm.render(hud_txt, True, WHITE), (20, 20))

        elif state == "TRANSITION":
            screen.fill(BLACK)
            
            if player.lives <= 0:
                txt = font_lg.render("GAME OVER", True, (200, 0, 0))
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 250))
            elif level > 32:
                txt = font_lg.render("YOU WIN!", True, GOLD)
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 250))
                sub = font_md.render("Princess Saved!", True, WHITE)
                screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 350))
            else:
                w_num = (level - 1) // 4 + 1
                l_num = (level - 1) % 4 + 1
                
                if player.dead:
                    status = f"x {player.lives}"
                    icon_color = (255, 0, 0)
                else:
                    status = "COURSE CLEAR!"
                    icon_color = GOLD
                
                txt = font_md.render(f"WORLD {w_num}-{l_num}", True, WHITE)
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 200))
                
                st_txt = font_md.render(status, True, WHITE)
                screen.blit(st_txt, (SCREEN_WIDTH//2 - st_txt.get_width()//2, 300))
                
                pygame.draw.rect(screen, icon_color, (SCREEN_WIDTH//2 - 20, 250, 40, 40))

            transition_timer -= 1
            if transition_timer <= 0:
                if player.lives <= 0:
                    state = "MENU"
                elif level > 32:
                    state = "MENU"
                else:
                    if player.dead:
                        player.dead = False 
                        load_level(level) 
                    else:
                        load_level(level) 
                    state = "PLAY"

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
