#!/usr/bin/env python3
"""3层隔板射击游戏 | 2玩家 | 6级武器 | Pygame"""
import pygame, sys, random, math
pygame.init()
W, H = 900, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("隔板射击战")
clock = pygame.time.Clock()
FPS = 60
# 颜色
BLACK=(0,0,0); WHITE=(255,255,255); RED=(220,50,50); BLUE=(50,100,220)
GREEN=(50,200,50); YELLOW=(255,220,50); GRAY=(100,100,100); DGRAY=(60,60,60)
ORANGE=(240,160,40); CYAN=(50,200,220); LGRAY=(160,160,160); PURPLE=(180,60,220)
BG_COLOR=(20,20,35)
# 中文字体
def get_font(size, bold=False):
    for name in ["stheitimedium","hiraginosansgb","songti","arialunicode","applegothic"]:
        try: return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.SysFont("arial", size, bold=bold)

def draw_gradient_text(surf, text, font, pos, colors):
    """绘制水平渐变文字，colors 为从左到右的颜色列表"""
    rendered = font.render(text, True, WHITE)
    w, h = rendered.get_size()
    gradient_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        t = x / max(w - 1, 1)
        if len(colors) == 2:
            c0, c1 = colors
            r = int(c0[0] + (c1[0] - c0[0]) * t)
            g = int(c0[1] + (c1[1] - c0[1]) * t)
            b = int(c0[2] + (c1[2] - c0[2]) * t)
        else:
            seg = t * (len(colors) - 1)
            idx = min(int(seg), len(colors) - 2)
            local_t = seg - idx
            c0, c1 = colors[idx], colors[idx + 1]
            r = int(c0[0] + (c1[0] - c0[0]) * local_t)
            g = int(c0[1] + (c1[1] - c0[1]) * local_t)
            b = int(c0[2] + (c1[2] - c0[2]) * local_t)
        pygame.draw.line(gradient_surf, (r, g, b, 255), (x, 0), (x, h))
    gradient_surf.blit(rendered, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(gradient_surf, pos)

# 武器数据: (名称, 伤害, 射速ms, 子弹速度, 自动, 后座力, 爆炸, 颜色)
WEAPONS = [
    ("手枪",   1, 400, 12, False, 0,  False, YELLOW),
    ("步枪",   1, 250, 18, False, 0,  False, GREEN),
    ("冲锋枪", 1, 90,  14, True,  0,  False, CYAN),
    ("机枪",   1, 50,  13, True,  0,  False, ORANGE),
    ("加特林", 1, 28,  13, True,  4,  False, PURPLE),
    ("火箭弹", 5, 800, 7,  False, 0,  True,  RED),
]
WEAPON_NAMES = ["手枪","步枪","冲锋枪","机枪","加特林","火箭弹"]
# 僵尸颜色
ZOMBIE_GREEN=(80,160,60); ZOMBIE_DARK=(50,100,40); ZOMBIE_RED=(180,40,40)
# AI颜色
AI_PURPLE=(180,60,220); AI_ORANGE=(240,160,40)
# 闯关模式颜色
STAGE_CYAN=(50,200,220)

def generate_stage_platforms(level):
    """根据关卡数随机生成平台"""
    platforms = [
        # 地面
        (0, 575, 900, 25),
        # 天花板
        (0, 0, 900, 12),
        # 左右墙壁
        (0, 0, 12, 600),
        (888, 0, 12, 600),
    ]
    # 每层的高度
    layer_ys = [480, 390, 300, 210, 120]
    # 关卡越高，平台数量越多
    num_platforms_per_layer = min(4, 2 + level // 3)
    for y in layer_ys:
        # 在该层随机生成平台
        used_ranges = []
        for _ in range(num_platforms_per_layer):
            pw = random.randint(80, 180)
            px = random.randint(30, W - pw - 30)
            # 检查是否重叠
            overlap = False
            for (sx, ex) in used_ranges:
                if not (px + pw + 20 < sx or px - 20 > ex):
                    overlap = True
                    break
            if not overlap:
                platforms.append((px, y, pw, 14))
                used_ranges.append((px, px + pw))
    return platforms

# ─── 地图设计: 6层矮层板，无纵向隔板 ────────────────────
# 平台格式: (x, y, w, h)
PLATFORMS = [
    # === 第1层(地面) ===
    (0, 575, 900, 25),
    # === 第2层 ===
    (0, 480, 200, 14),
    (260, 480, 180, 14),
    (500, 480, 200, 14),
    (760, 480, 140, 14),
    # === 第3层 ===
    (50, 390, 180, 14),
    (300, 390, 160, 14),
    (520, 390, 200, 14),
    (780, 390, 120, 14),
    # === 第4层 ===
    (0, 300, 150, 14),
    (210, 300, 180, 14),
    (450, 300, 160, 14),
    (670, 300, 230, 14),
    # === 第5层 ===
    (80, 210, 170, 14),
    (310, 210, 140, 14),
    (510, 210, 180, 14),
    (750, 210, 150, 14),
    # === 第6层 ===
    (0, 120, 130, 14),
    (190, 120, 160, 14),
    (410, 120, 150, 14),
    (620, 120, 180, 14),
    (860, 120, 40, 14),
    # 天花板
    (0, 0, 900, 12),
    # 左侧墙壁
    (0, 0, 12, 600),
    # 右侧墙壁
    (888, 0, 12, 600),
]

class Player:
    def __init__(self, x, y, color, name, controls):
        self.spawn_x = x; self.spawn_y = y
        self.x = float(x); self.y = float(y)
        self.w = 24; self.h = 36
        self.vx = 0.0; self.vy = 0.0
        self.color = color; self.name = name
        self.controls = controls  # dict: left,right,up,shoot
        self.hp = 5; self.max_hp = 5
        self.weapon = 0
        self.facing = 1  # 1右 -1左
        self.on_ground = False
        self.alive = True
        self.respawn_cd = 0
        self.last_shot = 0
        self.kills = 0
        self.shoot_pressed = False  # 用于半自动检测
        self.permanently_dead = False
        self.lives = 4  # 复活次数
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def update(self, keys, platforms, now):
        if not self.alive:
            if self.permanently_dead: return
            self.respawn_cd -= 1
            if self.respawn_cd <= 0: self.respawn()
            return
        # 移动
        spd = 5.0
        self.vx = 0
        if keys[self.controls["left"]]:  self.vx = -spd; self.facing = -1
        if keys[self.controls["right"]]: self.vx = spd;  self.facing = 1
        # 跳跃
        if keys[self.controls["up"]] and self.on_ground:
            self.vy = -11.5; self.on_ground = False
        # 重力
        self.vy += 0.55
        if self.vy > 12: self.vy = 12
        # 加特林后座力
        wp = WEAPONS[self.weapon]
        if self.weapon == 4 and keys[self.controls["shoot"]]:
            self.vx -= self.facing * wp[5]
        # 碰撞 - 水平
        self.x += self.vx
        r = self.rect()
        for p in platforms:
            pr = self.get_collision_rect(p)
            if pr and r.colliderect(pr):
                if self.vx > 0: self.x = pr.left - self.w
                elif self.vx < 0: self.x = pr.right
                self.vx = 0; r = self.rect()
        # 碰撞 - 垂直
        self.y += self.vy
        r = self.rect(); self.on_ground = False
        for p in platforms:
            pr = self.get_collision_rect(p)
            if pr and r.colliderect(pr):
                if self.vy > 0:
                    self.y = pr.top - self.h; self.vy = 0; self.on_ground = True
                elif self.vy < 0:
                    self.y = pr.bottom; self.vy = 0
                r = self.rect()
    def get_collision_rect(self, p):
        """返回平台碰撞矩形"""
        x, y, w, h = p
        # 地面和天花板 - 实心
        if h >= 20 and w > 200:
            return pygame.Rect(x, y, w, h)
        # 所有层板 - 实心(可从下方跳上)
        return pygame.Rect(x, y, w, h)
    def take_damage(self, dmg):
        if not self.alive: return False
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0; self.die(); return True
        return False
    def die(self):
        self.alive = False; self.respawn_cd = 90  # 1.5秒
    def respawn(self):
        self.x = float(self.spawn_x); self.y = float(self.spawn_y)
        self.hp = self.max_hp; self.alive = True
        self.vx = 0; self.vy = 0
    def upgrade_weapon(self):
        if self.weapon < 5: self.weapon += 1
    def draw(self, surf):
        if not self.alive:
            # 死亡标记
            mx = int(self.x + self.w//2); my = int(self.y + self.h//2)
            pygame.draw.line(surf, self.color, (mx-8,my-8),(mx+8,my+8), 2)
            pygame.draw.line(surf, self.color, (mx+8,my-8),(mx-8,my+8), 2)
            return
        r = self.rect()
        # 身体
        pygame.draw.rect(surf, self.color, r, border_radius=4)
        # 头
        hx = int(self.x + self.w//2)
        hy = int(self.y - 2)
        pygame.draw.circle(surf, self.color, (hx, hy), 10)
        pygame.draw.circle(surf, WHITE, (hx, hy), 10, 1)
        # 眼睛
        ex = hx + self.facing * 4
        pygame.draw.circle(surf, WHITE, (ex, hy-1), 3)
        pygame.draw.circle(surf, BLACK, (ex + self.facing, hy-1), 1)
        # 枪
        gx = int(self.x + (self.w if self.facing==1 else -16))
        gy = int(self.y + 14)
        wp = WEAPONS[self.weapon]
        gun_c = wp[7]
        pygame.draw.rect(surf, gun_c, (gx, gy, 16, 5), border_radius=2)
        pygame.draw.rect(surf, WHITE, (gx, gy, 16, 5), 1, border_radius=2)
        # HP条
        bw = 30; bx = int(self.x - 3); by = int(self.y - 18)
        pygame.draw.rect(surf, RED, (bx, by, bw, 5))
        hp_w = int(bw * self.hp / self.max_hp)
        pygame.draw.rect(surf, GREEN, (bx, by, hp_w, 5))
        pygame.draw.rect(surf, WHITE, (bx, by, bw, 5), 1)
        # 武器名
        wn = WEAPON_NAMES[self.weapon]
        ts = get_font(10).render(wn, True, gun_c)
        surf.blit(ts, (bx - 2, by - 12))

class Bullet:
    def __init__(self, x, y, dx, dy, dmg, color, explosion, owner):
        self.x = float(x); self.y = float(y)
        self.dx = dx; self.dy = dy
        self.dmg = dmg; self.color = color
        self.explosion = explosion; self.owner = owner
        self.alive = True; self.age = 0
        self.trail = []
    def update(self, platforms):
        self.age += 1
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6: self.trail.pop(0)
        self.x += self.dx; self.y += self.dy
        # 重力(火箭弹)
        if self.explosion: self.dy += 0.08
        # 碰撞
        r = pygame.Rect(int(self.x)-3, int(self.y)-3, 6, 6)
        for p in platforms:
            pr = self.get_collision_rect(p)
            if pr and r.colliderect(pr):
                self.alive = False; return
        if self.x < -20 or self.x > W+20 or self.y < -20 or self.y > H+20:
            self.alive = False
        if self.age > 300: self.alive = False
    def get_collision_rect(self, p):
        """子弹碰撞检测"""
        x, y, w, h = p
        return pygame.Rect(x, y, w, h)
    def draw(self, surf):
        if not self.alive: return
        ix, iy = int(self.x), int(self.y)
        # 尾焰
        for i, (tx, ty) in enumerate(self.trail):
            a = int(80 * (i / len(self.trail)))
            c = tuple(min(255, ch + a) for ch in self.color)
            pygame.draw.circle(surf, c, (int(tx), int(ty)), 2)
        if self.explosion:
            pygame.draw.circle(surf, self.color, (ix, iy), 6)
            pygame.draw.circle(surf, YELLOW, (ix, iy), 3)
        else:
            pygame.draw.circle(surf, self.color, (ix, iy), 3)
            pygame.draw.circle(surf, WHITE, (ix, iy), 1)

class Explosion:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.radius = 0; self.max_r = 70
        self.alive = True; self.age = 0
    def update(self):
        self.age += 1; self.radius += 5
        if self.radius >= self.max_r: self.alive = False
    def draw(self, surf):
        if not self.alive: return
        r = self.radius
        alpha = max(0, 255 - self.age * 15)
        c = (255, min(255, 100 + self.age*10), 0)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), r, 3)
        pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), r//2, 2)

class Zombie:
    def __init__(self, x, y, speed=1.5, hp=2):
        self.x = float(x); self.y = float(y)
        self.w = 20; self.h = 32
        self.vx = 0.0; self.vy = 0.0
        self.speed = speed; self.hp = hp; self.max_hp = hp
        self.alive = True; self.on_ground = False
        self.atk_cd = 0  # 攻击冷却
        self.facing = 1
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def update(self, targets, platforms):
        # 寻找最近目标
        nearest = None; min_d = 9999
        for t in targets:
            if not t.alive: continue
            d = math.hypot(self.x - t.x, self.y - t.y)
            if d < min_d: min_d = d; nearest = t
        if nearest:
            dx = nearest.x - self.x; dy = nearest.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.vx = (dx / dist) * self.speed
                self.facing = 1 if dx > 0 else -1
            # 跳跃(如果目标在上方且自己在地面)
            if dy < -30 and self.on_ground and abs(dx) < 100:
                self.vy = -9
        else:
            self.vx = 0
        # 重力
        self.vy += 0.5
        if self.vy > 10: self.vy = 10
        # 水平碰撞
        self.x += self.vx
        r = self.rect()
        for p in platforms:
            pr = pygame.Rect(p[0], p[1], p[2], p[3])
            if r.colliderect(pr):
                if self.vx > 0: self.x = pr.left - self.w
                elif self.vx < 0: self.x = pr.right
                self.vx = 0; r = self.rect()
        # 垂直碰撞
        self.y += self.vy
        r = self.rect(); self.on_ground = False
        for p in platforms:
            pr = pygame.Rect(p[0], p[1], p[2], p[3])
            if r.colliderect(pr):
                if self.vy > 0:
                    self.y = pr.top - self.h; self.vy = 0; self.on_ground = True
                elif self.vy < 0:
                    self.y = pr.bottom; self.vy = 0
                r = self.rect()
        # 边界
        self.x = max(0, min(self.x, W - self.w))
        if self.y > H: self.alive = False
        if self.atk_cd > 0: self.atk_cd -= 1
    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0: self.alive = False; return True
        return False
    def draw(self, surf):
        if not self.alive: return
        ix, iy = int(self.x), int(self.y)
        # 身体
        pygame.draw.rect(surf, ZOMBIE_GREEN, (ix, iy+8, self.w, self.h-8), border_radius=3)
        # 头
        pygame.draw.circle(surf, ZOMBIE_GREEN, (ix+self.w//2, iy+6), 8)
        pygame.draw.circle(surf, ZOMBIE_DARK, (ix+self.w//2, iy+6), 8, 1)
        # 眼睛(红色)
        ex = ix + self.w//2 + self.facing * 3
        pygame.draw.circle(surf, ZOMBIE_RED, (ex, iy+4), 2)
        pygame.draw.circle(surf, WHITE, (ex, iy+4), 1)
        # 手臂
        arm_y = iy + 14
        pygame.draw.rect(surf, ZOMBIE_DARK, (ix-3, arm_y, 5, 10))
        pygame.draw.rect(surf, ZOMBIE_DARK, (ix+self.w-2, arm_y, 5, 10))
        # HP条
        if self.hp < self.max_hp:
            bw = 20; bx = ix; by = iy - 8
            pygame.draw.rect(surf, RED, (bx, by, bw, 3))
            pygame.draw.rect(surf, GREEN, (bx, by, int(bw * self.hp / self.max_hp), 3))

class AIPlayer(Player):
    """AI电脑对手"""
    def __init__(self, x, y, color, name, difficulty=1.0):
        super().__init__(x, y, color, name, {})
        self.difficulty = difficulty  # 0.5~1.5
        self.think_timer = 0
        self.target = None
        self.shoot_cd = 0
        self.weapon = 0
        self.permanently_dead = False
    def update_ai(self, enemies, platforms, frame):
        """AI逻辑"""
        if not self.alive:
            if self.permanently_dead: return
            self.respawn_cd -= 1
            if self.respawn_cd <= 0: self.respawn()
            return
        # 寻找最近敌人
        nearest = None; min_d = 9999
        for e in enemies:
            if not e.alive: continue
            d = math.hypot(self.x - e.x, self.y - e.y)
            if d < min_d: min_d = d; nearest = e
        self.target = nearest
        if not nearest: return
        # 移动逻辑
        dx = nearest.x - self.x
        dy = nearest.y - self.y
        dist = math.hypot(dx, dy)
        # 保持距离(根据武器)
        wp = WEAPONS[self.weapon]
        ideal_dist = 150 if wp[4] else 100  # 自动武器保持远一点
        self.vx = 0
        if dist > ideal_dist + 30:
            self.vx = 3 * (1 if dx > 0 else -1)
            self.facing = 1 if dx > 0 else -1
        elif dist < ideal_dist - 30:
            self.vx = -3 * (1 if dx > 0 else -1)
            self.facing = 1 if dx > 0 else -1
        else:
            # 左右移动闪避
            if frame % 80 < 30:
                self.vx = 2 * (1 if dy > 0 else -1)
            self.facing = 1 if dx > 0 else -1
        # 跳跃
        if dy < -50 and self.on_ground and abs(dx) < 200:
            self.vy = -11
        # 随机跳跃闪避
        if frame % 180 < 5 and self.on_ground:
            self.vy = -9
        # 重力
        self.vy += 0.55
        if self.vy > 12: self.vy = 12
        # 加特林后座力
        if self.weapon == 4:
            self.vx -= self.facing * wp[5]
        # 水平碰撞
        self.x += self.vx
        r = self.rect()
        for p in platforms:
            pr = pygame.Rect(p[0], p[1], p[2], p[3])
            if r.colliderect(pr):
                if self.vx > 0: self.x = pr.left - self.w
                elif self.vx < 0: self.x = pr.right
                self.vx = 0; r = self.rect()
        # 垂直碰撞
        self.y += self.vy
        r = self.rect(); self.on_ground = False
        for p in platforms:
            pr = pygame.Rect(p[0], p[1], p[2], p[3])
            if r.colliderect(pr):
                if self.vy > 0:
                    self.y = pr.top - self.h; self.vy = 0; self.on_ground = True
                elif self.vy < 0:
                    self.y = pr.bottom; self.vy = 0
                r = self.rect()
        self.x = max(12, min(self.x, W - self.w - 12))
        # 射击逻辑
        self.shoot_cd -= 1
        if self.shoot_cd <= 0 and nearest:
            # 命中率根据难度和距离
            hit_chance = 0.2 * self.difficulty
            if dist > 300: hit_chance *= 0.5
            if random.random() < hit_chance:
                return self.try_shoot_ai(enemies, frame)
        return None
    def try_shoot_ai(self, enemies, frame):
        """AI射击 - 支持所有武器特性"""
        wp = WEAPONS[self.weapon]
        now = pygame.time.get_ticks()
        if now - self.last_shot < wp[2]: return None
        self.last_shot = now
        # 发射点
        gx = self.x + (self.w if self.facing==1 else -2)
        gy = self.y + 16
        spd = wp[3]
        dx = self.facing * spd
        dy = random.uniform(-0.8, 0.8) if wp[4] else 0
        # 加特林后座力
        if self.weapon == 4:
            self.vx -= self.facing * wp[5]
        return (gx, gy, dx, dy, wp[1], wp[7], wp[6], self)
    def upgrade_weapon(self):
        if self.weapon < 5: self.weapon += 1

class Game:
    def __init__(self):
        self.state = "mode_select"  # mode_select, menu, playing, ...
        self.mode = "pvp"  # pvp, zombie, coop, stage
        self.menu_sel = 0
        self.mode_select_sel = 0  # 0=单人, 1=双人
        self.player_count = 2  # 1或2
        self.winner = None
        self.bullets = []
        self.explosions = []
        self.zombies = []
        self.ai_players = []  # AI对手
        self.notifications = []  # 升级提示 [(text, color, timer)]
        self.zombie_spawn_timer = 0
        self.zombie_spawn_rate = 120
        self.game_timer = 0
        self.game_time_limit = 60 * 120
        self.platforms = list(PLATFORMS)
        # 闯关模式变量
        self.stage_level = 1
        self.stage_zombies_total = 0
        self.stage_zombies_spawned = 0
        self.stage_zombies_killed = 0
        self.stage_spawn_timer = 0
        self.stage_spawn_rate = 90
        self.stage_clear = False  # 通关标志
        self.stage_clear_timer = 0
        self.p1 = Player(80, 70, BLUE, "玩家1",
            {"left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w, "shoot": pygame.K_f})
        self.p2 = Player(800, 530, RED, "玩家2",
            {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "shoot": pygame.K_l})
        self.font = get_font(28, bold=True)
        self.sfont = get_font(18)
        self.tfont = get_font(52, bold=True)
        self.frame = 0
    def reset(self):
        self.p1 = Player(80, 70, BLUE, "玩家1",
            {"left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w, "shoot": pygame.K_f})
        self.p2 = Player(800, 530, RED, "玩家2",
            {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "shoot": pygame.K_l})
        self.bullets = []; self.explosions = []; self.winner = None
        self.zombies = []; self.ai_players = []; self.notifications = []
        self.zombie_spawn_timer = 0; self.game_timer = 0
        self.zombie_spawn_rate = 120
        if self.player_count == 1:
            # 单人模式
            self.p1.controls = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "shoot": pygame.K_PERIOD}
            self.p2.alive = False; self.p2.permanently_dead = True
            self.p1.weapon = 0
            if self.mode == "stage":
                self.p1.kills = 0
                self.start_stage()
            else:
                self.mode = "coop"
                self.ai_players = [AIPlayer(800, 300, AI_PURPLE, "AI", 0.5)]
        elif self.mode == "zombie":
            self.p1.weapon = 0; self.p2.weapon = 0
        elif self.mode == "coop":
            self.p1.weapon = 0; self.p2.weapon = 0
            self.ai_players = [
                AIPlayer(800, 70, AI_PURPLE, "AI-1", 0.4),
                AIPlayer(80, 530, AI_ORANGE, "AI-2", 0.5),
            ]
        elif self.mode == "stage":
            self.p1.weapon = 0; self.p2.weapon = 0
            self.stage_level = 1
            self.start_stage()
    def start_stage(self):
        """开始新关卡"""
        # 生成随机平台
        self.platforms = generate_stage_platforms(self.stage_level)
        # 重置玩家位置和武器
        self.p1.x = float(self.p1.spawn_x); self.p1.y = float(self.p1.spawn_y)
        self.p1.hp = self.p1.max_hp; self.p1.alive = True; self.p1.vx = 0; self.p1.vy = 0
        self.p1.weapon = 0; self.p1.kills = 0; self.p1.lives = 4; self.p1.permanently_dead = False
        # 单人模式不需要p2
        if self.player_count == 2:
            self.p2.x = float(self.p2.spawn_x); self.p2.y = float(self.p2.spawn_y)
            self.p2.hp = self.p2.max_hp; self.p2.alive = True; self.p2.vx = 0; self.p2.vy = 0
            self.p2.weapon = 0; self.p2.kills = 0; self.p2.lives = 4; self.p2.permanently_dead = False
        # 关卡僵尸数量: 单人模式减半
        if self.player_count == 1:
            self.stage_zombies_total = 3 + (self.stage_level - 1) * 2
            self.stage_spawn_rate = max(40, 110 - self.stage_level * 5)
        else:
            self.stage_zombies_total = 5 + (self.stage_level - 1) * 3
            self.stage_spawn_rate = max(30, 90 - self.stage_level * 5)
        self.stage_zombies_spawned = 0
        self.stage_zombies_killed = 0
        self.stage_spawn_timer = 0
        self.zombies = []
        self.bullets = []
        self.explosions = []
        self.stage_clear = False
        self.stage_clear_timer = 0
        # 通知
        self.notifications.append(
            [f"第 {self.stage_level} 关 | 僵尸: {self.stage_zombies_total}", STAGE_CYAN, 180])
    def next_stage(self):
        """进入下一关"""
        self.stage_level += 1
        self.start_stage()
    def try_shoot(self, player, keys):
        if not player.alive: return
        now = pygame.time.get_ticks()
        wp = WEAPONS[player.weapon]
        rate = wp[2]; auto = wp[4]
        pressed = keys[player.controls["shoot"]]
        if auto:
            if not pressed: return
            if now - player.last_shot < rate: return
        else:
            if pressed and not player.shoot_pressed:
                pass  # 首次按下
            else:
                player.shoot_pressed = pressed; return
            if now - player.last_shot < rate: return
        player.shoot_pressed = pressed; player.last_shot = now
        # 发射
        gx = player.x + (player.w if player.facing==1 else -2)
        gy = player.y + 16
        spd = wp[3]
        dx = player.facing * spd
        dy = random.uniform(-0.8, 0.8) if wp[4] else 0
        self.bullets.append(Bullet(gx, gy, dx, dy, wp[1], wp[7], wp[6], player))
    def check_hits(self):
        for b in self.bullets:
            if not b.alive: continue
            br = pygame.Rect(int(b.x)-4, int(b.y)-4, 8, 8)
            # PvP模式
            if self.mode == "pvp":
                targets = [self.p1, self.p2] if b.owner == self.p2 else [self.p2, self.p1]
                for t in targets:
                    if not t.alive: continue
                    if br.colliderect(t.rect()):
                        b.alive = False
                        if b.explosion:
                            self.explosions.append(Explosion(b.x, b.y))
                            for t2 in [self.p1, self.p2]:
                                dist = math.hypot(b.x-(t2.x+t2.w//2), b.y-(t2.y+t2.h//2))
                                if dist < 80:
                                    if t2.take_damage(b.dmg): self.on_kill(t2)
                        else:
                            if t.take_damage(b.dmg): self.on_kill(t)
                        break
            # 僵尸模式
            elif self.mode == "zombie":
                for z in self.zombies:
                    if not z.alive: continue
                    if br.colliderect(z.rect()):
                        b.alive = False
                        if b.explosion:
                            self.explosions.append(Explosion(b.x, b.y))
                            for z2 in self.zombies:
                                if not z2.alive: continue
                                dist = math.hypot(b.x-(z2.x+z2.w//2), b.y-(z2.y+z2.h//2))
                                if dist < 80:
                                    if z2.take_damage(b.dmg):
                                        b.owner.kills += 1
                                        if b.owner.kills % 4 == 0 and b.owner.weapon < 5:
                                            b.owner.weapon += 1
                                            self.notifications.append(
                                                [f"{b.owner.name} 武器升级: {WEAPON_NAMES[b.owner.weapon]}", b.owner.color, 120])
                        else:
                            if z.take_damage(b.dmg):
                                b.owner.kills += 1
                                if b.owner.kills % 4 == 0 and b.owner.weapon < 5:
                                    b.owner.weapon += 1
                                    self.notifications.append(
                                        [f"{b.owner.name} 武器升级: {WEAPON_NAMES[b.owner.weapon]}", b.owner.color, 120])
                        break
            # 合作模式
            elif self.mode == "coop":
                is_player_bullet = b.owner in [self.p1, self.p2]
                if is_player_bullet:
                    # 玩家子弹打AI
                    for ai in self.ai_players:
                        if not ai.alive: continue
                        if br.colliderect(ai.rect()):
                            b.alive = False
                            killed = False
                            if b.explosion:
                                self.explosions.append(Explosion(b.x, b.y))
                                for ai2 in self.ai_players:
                                    if not ai2.alive: continue
                                    dist = math.hypot(b.x-(ai2.x+ai2.w//2), b.y-(ai2.y+ai2.h//2))
                                    if dist < 80:
                                        if ai2.take_damage(b.dmg):
                                            b.owner.kills += 1
                                            b.owner.upgrade_weapon()
                                            if not ai2.alive: killed = True
                            else:
                                if ai.take_damage(b.dmg):
                                    b.owner.kills += 1
                                    b.owner.upgrade_weapon()
                                    if not ai.alive: killed = True
                            # 非火箭弹击杀 → AI复活
                            if killed and not b.explosion:
                                ai.hp = ai.max_hp
                                ai.x = float(ai.spawn_x); ai.y = float(ai.spawn_y)
                                ai.alive = True; ai.vx = 0; ai.vy = 0
                            # 火箭弹击杀 → 永久死亡 + 检查AI是否全灭
                            if killed and b.explosion:
                                for a in self.ai_players:
                                    if not a.alive: a.permanently_dead = True
                                if all(not a.alive for a in self.ai_players):
                                    self.winner = "玩家队"; self.state = "coop_result"
                            break
                else:
                    # AI子弹打玩家
                    for p in [self.p1, self.p2]:
                        if not p.alive: continue
                        if br.colliderect(p.rect()):
                            b.alive = False
                            killed = False
                            if b.explosion:
                                self.explosions.append(Explosion(b.x, b.y))
                                for p2 in [self.p1, self.p2]:
                                    if not p2.alive: continue
                                    dist = math.hypot(b.x-(p2.x+p2.w//2), b.y-(p2.y+p2.h//2))
                                    if dist < 80:
                                        if p2.take_damage(b.dmg):
                                            b.owner.kills += 1
                                            b.owner.upgrade_weapon()
                                            if not p2.alive: killed = True
                            else:
                                if p.take_damage(b.dmg):
                                    b.owner.kills += 1
                                    b.owner.upgrade_weapon()
                                    if not p.alive: killed = True
                            # 非火箭弹击杀 → 玩家复活
                            if killed and not b.explosion:
                                p.hp = p.max_hp
                                p.x = float(p.spawn_x); p.y = float(p.spawn_y)
                                p.alive = True; p.vx = 0; p.vy = 0
                            # 火箭弹击杀 → 永久死亡 + 检查玩家是否全灭
                            if killed and b.explosion:
                                for pp in [self.p1, self.p2]:
                                    if not pp.alive: pp.permanently_dead = True
                                if all(not p2.alive for p2 in [self.p1, self.p2]):
                                    self.winner = "AI队"; self.state = "coop_result"
                            break
            # 闯关模式 - 玩家打僵尸
            elif self.mode == "stage":
                if b.owner in [self.p1, self.p2]:
                    for z in self.zombies:
                        if not z.alive: continue
                        if br.colliderect(z.rect()):
                            b.alive = False
                            if b.explosion:
                                self.explosions.append(Explosion(b.x, b.y))
                                for z2 in self.zombies:
                                    if not z2.alive: continue
                                    dist = math.hypot(b.x-(z2.x+z2.w//2), b.y-(z2.y+z2.h//2))
                                    if dist < 80:
                                        if z2.take_damage(b.dmg):
                                            b.owner.kills += 1
                                            self.stage_zombies_killed += 1
                                            if b.owner.kills % 4 == 0 and b.owner.weapon < 5:
                                                b.owner.weapon += 1
                                                self.notifications.append(
                                                    [f"{b.owner.name} 武器升级: {WEAPON_NAMES[b.owner.weapon]}", b.owner.color, 120])
                            else:
                                if z.take_damage(b.dmg):
                                    b.owner.kills += 1
                                    self.stage_zombies_killed += 1
                                    if b.owner.kills % 4 == 0 and b.owner.weapon < 5:
                                        b.owner.weapon += 1
                                        self.notifications.append(
                                            [f"{b.owner.name} 武器升级: {WEAPON_NAMES[b.owner.weapon]}", b.owner.color, 120])
                            break
    def on_kill(self, victim):
        killer = self.p2 if victim == self.p1 else self.p1
        killer.kills += 1
        killer.upgrade_weapon()
        # 火箭弹击杀 = 胜利
        if killer.weapon == 5 and victim.hp <= 0:
            self.winner = killer.name
            self.state = "gameover"
    def update(self):
        self.frame += 1
        if self.state != "playing": return
        keys = pygame.key.get_pressed()
        self.p1.update(keys, self.platforms, self.frame)
        self.p2.update(keys, self.platforms, self.frame)
        self.try_shoot(self.p1, keys)
        self.try_shoot(self.p2, keys)
        # 僵尸模式逻辑
        if self.mode == "zombie":
            self.game_timer += 1
            # 时间到
            if self.game_timer >= self.game_time_limit:
                self.state = "zombie_result"
                return
            # 生成僵尸
            self.zombie_spawn_timer += 1
            # 随时间加快生成速度
            rate = max(30, self.zombie_spawn_rate - self.game_timer // 300)
            if self.zombie_spawn_timer >= rate:
                self.zombie_spawn_timer = 0
                self.spawn_zombie()
            # 更新僵尸
            targets = [self.p1, self.p2]
            for z in self.zombies:
                z.update(targets, self.platforms)
            # 僵尸攻击玩家
            for z in self.zombies:
                if not z.alive or z.atk_cd > 0: continue
                for p in targets:
                    if not p.alive: continue
                    if z.rect().colliderect(p.rect()):
                        p.take_damage(1)
                        z.atk_cd = 30  # 0.5秒冷却
                        if p.hp <= 0:
                            p.hp = p.max_hp  # 僵尸模式快速复活
                            p.x = float(p.spawn_x); p.y = float(p.spawn_y)
                            p.alive = True; p.vx = 0; p.vy = 0
            self.zombies = [z for z in self.zombies if z.alive]
        # 合作模式 - AI逻辑
        elif self.mode == "coop":
            enemies = [self.p1, self.p2]
            for ai in self.ai_players:
                shot = ai.update_ai(enemies, self.platforms, self.frame)
                if shot:
                    self.bullets.append(Bullet(shot[0], shot[1], shot[2], shot[3], shot[4], shot[5], shot[6], shot[7]))
        # 闯关模式逻辑
        elif self.mode == "stage":
            if not self.stage_clear:
                # 生成僵尸
                if self.stage_zombies_spawned < self.stage_zombies_total:
                    self.stage_spawn_timer += 1
                    if self.stage_spawn_timer >= self.stage_spawn_rate:
                        self.stage_spawn_timer = 0
                        self.spawn_stage_zombie()
                # 更新僵尸
                targets = [self.p1, self.p2]
                for z in self.zombies:
                    z.update(targets, self.platforms)
                # 僵尸攻击玩家
                for z in self.zombies:
                    if not z.alive or z.atk_cd > 0: continue
                    for p in targets:
                        if not p.alive: continue
                        if z.rect().colliderect(p.rect()):
                            p.take_damage(1)
                            z.atk_cd = 30
                            if p.hp <= 0:
                                p.lives -= 1
                                if p.lives > 0:
                                    p.hp = p.max_hp
                                    p.x = float(p.spawn_x); p.y = float(p.spawn_y)
                                    p.alive = True; p.vx = 0; p.vy = 0
                                    self.notifications.append(
                                        [f"{p.name} 剩余 {p.lives} 次复活", p.color, 90])
                                else:
                                    p.alive = False; p.permanently_dead = True
                                    self.notifications.append(
                                        [f"{p.name} 已阵亡!", RED, 150])
                self.zombies = [z for z in self.zombies if z.alive]
                # 检查玩家是否全灭
                if self.p1.permanently_dead and self.p2.permanently_dead:
                    self.winner = "僵尸队"
                    self.state = "stage_gameover"
                    return
                # 检查是否通关
                if (self.stage_zombies_spawned >= self.stage_zombies_total and 
                    len(self.zombies) == 0):
                    self.stage_clear = True
                    self.stage_clear_timer = 120
                    self.notifications.append(
                        [f"第 {self.stage_level} 关 通关!", GREEN, 150])
            else:
                # 通关等待
                self.stage_clear_timer -= 1
                if self.stage_clear_timer <= 0:
                    self.next_stage()
        for b in self.bullets: b.update(self.platforms)
        self.bullets = [b for b in self.bullets if b.alive]
        self.check_hits()
        self.bullets = [b for b in self.bullets if b.alive]
        for e in self.explosions: e.update()
        self.explosions = [e for e in self.explosions if e.alive]
        # 更新通知
        for n in self.notifications:
            n[2] -= 1
        self.notifications = [n for n in self.notifications if n[2] > 0]
    def spawn_zombie(self):
        """生成僵尸"""
        # 随机选择楼层
        spawn_points = [
            (random.randint(50, W-50), 540),  # 底层
            (random.randint(50, W-50), 448),  # 第2层
            (random.randint(50, W-50), 358),  # 第3层
            (random.randint(50, W-50), 268),  # 第4层
            (random.randint(50, W-50), 178),  # 第5层
            (random.randint(50, W-50), 88),   # 第6层
        ]
        x, y = random.choice(spawn_points)
        # 随时间增加僵尸属性
        minute = self.game_timer / 3600  # 分钟数
        speed = 1.5 + minute * 0.3
        hp = 2 + int(minute * 0.5)
        self.zombies.append(Zombie(x, y, speed, hp))
    def spawn_stage_zombie(self):
        """闯关模式生成僵尸"""
        spawn_points = [
            (random.randint(50, W-50), 540),
            (random.randint(50, W-50), 448),
            (random.randint(50, W-50), 358),
            (random.randint(50, W-50), 268),
            (random.randint(50, W-50), 178),
            (random.randint(50, W-50), 88),
        ]
        x, y = random.choice(spawn_points)
        # 根据关卡增加难度，单人模式降低
        if self.player_count == 1:
            speed = 1.2 + self.stage_level * 0.1
            hp = 1 + self.stage_level // 3
        else:
            speed = 1.5 + self.stage_level * 0.15
            hp = 2 + self.stage_level // 2
        self.zombies.append(Zombie(x, y, speed, hp))
        self.stage_zombies_spawned += 1
    def draw_platforms(self):
        for i, p in enumerate(self.platforms):
            x, y, w, h = p
            # 侧墙(垂直)
            if (x == 0 or x == 888) and h > 100:
                pygame.draw.rect(screen, (90,70,60), (x,y,w,h))
                pygame.draw.rect(screen, (120,100,80), (x,y,3,h) if x==0 else (x+w-3,y,3,h))
                pygame.draw.rect(screen, (70,50,40), (x,y+h-2,w,2))
            # 地面和天花板
            elif h >= 20 and w > 200:
                pygame.draw.rect(screen, (70,70,90), (x,y,w,h))
                pygame.draw.rect(screen, (100,100,130), (x,y,w,3))
                pygame.draw.rect(screen, (50,50,65), (x,y+h-2,w,2))
            # 层板
            else:
                pygame.draw.rect(screen, (70,70,90), (x,y,w,h))
                pygame.draw.rect(screen, (100,100,130), (x,y,w,3))
                pygame.draw.rect(screen, (140,140,160), (x,y,4,h))
                pygame.draw.rect(screen, (140,140,160), (x+w-4,y,4,h))
    def draw_hud(self):
        # 玩家1信息
        p = self.p1
        pygame.draw.rect(screen, (20,20,40), (5, 5, 200, 70), border_radius=5)
        pygame.draw.rect(screen, BLUE, (5, 5, 200, 70), 2, border_radius=5)
        t1 = self.sfont.render(f"玩家1 | {WEAPON_NAMES[p.weapon]}", True, BLUE)
        screen.blit(t1, (12, 10))
        # HP条
        pygame.draw.rect(screen, DGRAY, (12, 32, 120, 12))
        hw = int(120 * p.hp / p.max_hp)
        hc = GREEN if p.hp > 3 else YELLOW if p.hp > 1 else RED
        pygame.draw.rect(screen, hc, (12, 32, hw, 12))
        pygame.draw.rect(screen, WHITE, (12, 32, 120, 12), 1)
        ht = self.sfont.render(f"HP {p.hp}/{p.max_hp}", True, WHITE)
        screen.blit(ht, (135, 30))
        # 击杀数
        kt = self.sfont.render(f"击杀: {p.kills}", True, LGRAY)
        screen.blit(kt, (12, 50))
        # 武器进度
        prog = " ".join([WEAPON_NAMES[i] if i <= p.weapon else "?" for i in range(6)])
        pt = get_font(10).render(prog, True, LGRAY)
        screen.blit(pt, (12, 65))
        # 玩家2信息 (双人模式才显示)
        if self.player_count == 2:
            p = self.p2
            pygame.draw.rect(screen, (20,20,40), (W-205, 5, 200, 70), border_radius=5)
            pygame.draw.rect(screen, RED, (W-205, 5, 200, 70), 2, border_radius=5)
            t1 = self.sfont.render(f"玩家2 | {WEAPON_NAMES[p.weapon]}", True, RED)
            screen.blit(t1, (W-198, 10))
            pygame.draw.rect(screen, DGRAY, (W-198, 32, 120, 12))
            hw = int(120 * p.hp / p.max_hp)
            hc = GREEN if p.hp > 3 else YELLOW if p.hp > 1 else RED
            pygame.draw.rect(screen, hc, (W-198, 32, hw, 12))
            pygame.draw.rect(screen, WHITE, (W-198, 32, 120, 12), 1)
            ht = self.sfont.render(f"HP {p.hp}/{p.max_hp}", True, WHITE)
            screen.blit(ht, (W-60, 30))
            kt = self.sfont.render(f"击杀: {p.kills}", True, LGRAY)
            screen.blit(kt, (W-198, 50))
            prog = " ".join([WEAPON_NAMES[i] if i <= p.weapon else "?" for i in range(6)])
            pt = get_font(10).render(prog, True, LGRAY)
            screen.blit(pt, (W-198, 65))
        # 僵尸模式 - 显示计时器
        if self.mode == "zombie":
            remaining = max(0, self.game_time_limit - self.game_timer)
            secs = remaining // 60
            mins = secs // 60; secs = secs % 60
            timer_text = self.font.render(f"{mins:02d}:{secs:02d}", True, YELLOW)
            screen.blit(timer_text, (W//2 - timer_text.get_width()//2, 5))
            zt = self.sfont.render(f"僵尸: {len(self.zombies)}", True, ZOMBIE_GREEN)
            screen.blit(zt, (W//2 - zt.get_width()//2, 38))
        # 合作模式 - 显示AI信息
        elif self.mode == "coop":
            for i, ai in enumerate(self.ai_players):
                bx = W//2 - 90 + i * 120
                pygame.draw.rect(screen, (30,20,40), (bx, 5, 110, 30), border_radius=4)
                pygame.draw.rect(screen, ai.color, (bx, 5, 110, 30), 1, border_radius=4)
                status = f"{'存活' if ai.alive else '阵亡'} | {WEAPON_NAMES[ai.weapon]}"
                at = self.sfont.render(status, True, ai.color)
                screen.blit(at, (bx + 5, 10))
        # 闯关模式 - 显示关卡信息
        elif self.mode == "stage":
            # 关卡标题
            stage_text = self.font.render(f"第 {self.stage_level} 关", True, STAGE_CYAN)
            screen.blit(stage_text, (W//2 - stage_text.get_width()//2, 5))
            # 僵尸进度
            remaining = self.stage_zombies_total - self.stage_zombies_killed
            zt = self.sfont.render(f"剩余僵尸: {remaining}", True, ZOMBIE_GREEN)
            screen.blit(zt, (W//2 - zt.get_width()//2, 38))
            # 进度条
            bar_w = 200; bar_h = 8; bar_x = W//2 - bar_w//2; bar_y = 60
            pygame.draw.rect(screen, DGRAY, (bar_x, bar_y, bar_w, bar_h))
            if self.stage_zombies_total > 0:
                prog_w = int(bar_w * self.stage_zombies_killed / self.stage_zombies_total)
            else:
                prog_w = 0
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, prog_w, bar_h))
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
            # 显示复活次数
            p1_lives = f"P1: {'♥' * self.p1.lives}{'♡' * (4 - self.p1.lives)}" if not self.p1.permanently_dead else "P1: 阵亡"
            p2_lives = f"P2: {'♥' * self.p2.lives}{'♡' * (4 - self.p2.lives)}" if not self.p2.permanently_dead else "P2: 阵亡"
            lt1 = self.sfont.render(p1_lives, True, BLUE)
            lt2 = self.sfont.render(p2_lives, True, RED)
            screen.blit(lt1, (10, H - 45))
            screen.blit(lt2, (W - lt2.get_width() - 10, H - 45))
        # 中央提示
        if self.player_count == 1:
            mid = self.sfont.render("← → 移动 | ↑ 跳 | . 射击", True, (150,150,150))
        else:
            mid = self.sfont.render("← → 移动 | ↑ 跳 | F/L 射击", True, (150,150,150))
        screen.blit(mid, (W//2 - mid.get_width()//2, H - 18))
    def draw_mode_select(self):
        screen.fill(BG_COLOR)
        t = self.tfont.render("隔 板 射 击 战", True, WHITE)
        draw_gradient_text(screen, "隔 板 射 击 战", self.tfont, (W//2 - t.get_width()//2, 50),
            [(255,80,80), (255,200,50), (80,255,180), (80,200,255), (200,100,255)])
        sub = self.sfont.render("选择游戏模式", True, LGRAY)
        screen.blit(sub, (W//2 - sub.get_width()//2, 120))
        options = [("单人模式 (vs AI)", AI_PURPLE), ("双人模式 (P1+P2)", BLUE)]
        for i, (name, col) in enumerate(options):
            sel = (i == self.mode_select_sel)
            c = YELLOW if sel else col
            txt = self.font.render(f"{'▶ ' if sel else '  '}{name}", True, c)
            screen.blit(txt, (W//2 - txt.get_width()//2, 180 + i * 55))
        if self.mode_select_sel == 0:
            lines = [
                ("玩家 (蓝): ←→移动, ↑跳跃, .射击", BLUE),
                ("击败1个AI对手, 用火箭弹击杀获胜!", WHITE),
            ]
        else:
            lines = [
                ("玩家1 (蓝): WASD移动, F射击", BLUE),
                ("玩家2 (红): 方向键移动, L射击", RED),
                ("支持对战/僵尸/2v2合作/闯关模式", WHITE),
            ]
        for i, (txt, col) in enumerate(lines):
            s = self.sfont.render(txt, True, col)
            screen.blit(s, (W//2 - s.get_width()//2, 310 + i * 28))
        hint = self.sfont.render("↑↓选择 | ENTER确认", True, (150,150,150))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 30))
    def draw_menu(self):
        screen.fill(BG_COLOR)
        t = self.tfont.render("隔 板 射 击 战", True, WHITE)
        draw_gradient_text(screen, "隔 板 射 击 战", self.tfont, (W//2 - t.get_width()//2, 30),
            [(255,80,80), (255,200,50), (80,255,180), (80,200,255), (200,100,255)])
        if self.player_count == 1:
            # 单人模式 - 2种模式
            modes = [("对战模式 (vs AI)", AI_PURPLE), ("闯关模式", STAGE_CYAN)]
            for i, (name, col) in enumerate(modes):
                sel = (i == self.menu_sel)
                c = YELLOW if sel else col
                txt = self.font.render(f"{'▶ ' if sel else '  '}{name}", True, c)
                screen.blit(txt, (W//2 - txt.get_width()//2, 130 + i * 45))
            if self.menu_sel == 0:
                lines = [
                    ("玩家 (蓝): ←→移动, ↑跳跃, .射击", BLUE),
                    ("击败1个AI对手, 用火箭弹击杀获胜!", WHITE),
                    ("每次击杀升级武器, 6种武器!", YELLOW),
                ]
            else:
                lines = [
                    ("单人闯关!", STAGE_CYAN),
                    ("消灭所有僵尸通关, 难度较低", WHITE),
                    ("4次复活, 每关重置!", YELLOW),
                ]
            for i, (tx, col) in enumerate(lines):
                s = self.sfont.render(tx, True, col)
                screen.blit(s, (W//2 - s.get_width()//2, 230 + i * 28))
            # 预览
            if self.menu_sel == 0:
                x = W//2 - 40; y = H - 90
                ai = AIPlayer(x, y, AI_PURPLE, "AI", 0.5)
                ai.draw(screen)
                nt = get_font(11).render("AI对手 难度:0.5", True, AI_PURPLE)
                screen.blit(nt, (x - 30, y + 40))
            else:
                for i in range(3):
                    x = 200 + i * 180; y = H - 70
                    pygame.draw.rect(screen, STAGE_CYAN, (x, y, 100, 10), border_radius=3)
                    nt = get_font(11).render(f"第{i+1}关", True, STAGE_CYAN)
                    screen.blit(nt, (x + 50 - nt.get_width()//2, y + 15))
                    zt = get_font(10).render(f"{3+i*2}只僵尸", True, ZOMBIE_GREEN)
                    screen.blit(zt, (x + 50 - zt.get_width()//2, y + 30))
        else:
            # 双人模式 - 4种模式
            modes = [("对战模式 (PvP)", BLUE), ("僵尸模式 (合作)", ZOMBIE_GREEN), ("2v2模式 (vs AI)", AI_PURPLE), ("闯关模式 (合作)", STAGE_CYAN)]
            for i, (name, col) in enumerate(modes):
                sel = (i == self.menu_sel)
                c = YELLOW if sel else col
                txt = self.font.render(f"{'▶ ' if sel else '  '}{name}", True, c)
                screen.blit(txt, (W//2 - txt.get_width()//2, 110 + i * 45))
            if self.menu_sel == 0:
                lines = [
                    ("玩家1 (蓝): WASD移动, F射击", BLUE),
                    ("玩家2 (红): 方向键移动, L射击", RED),
                    ("每次击杀升级武器, 用火箭弹击杀获胜!", WHITE),
                ]
            elif self.menu_sel == 1:
                lines = [
                    ("合作抵抗僵尸潮!", ZOMBIE_GREEN),
                    ("2分钟内消灭尽可能多的僵尸", WHITE),
                    ("死亡后快速复活, 击杀数多者获胜!", YELLOW),
                ]
            elif self.menu_sel == 2:
                lines = [
                    ("P1+P2 合作 vs 2个AI对手", AI_PURPLE),
                    ("每人5血, 用火箭弹击杀AI获胜!", WHITE),
                    ("AI会用火箭弹反击, 小心!", RED),
                ]
            else:
                lines = [
                    ("P1+P2 合作闯关!", STAGE_CYAN),
                    ("每关消灭所有僵尸即可通关", WHITE),
                    ("每人4次复活, 每关重置!", YELLOW),
                ]
            for i, (tx, col) in enumerate(lines):
                s = self.sfont.render(tx, True, col)
                screen.blit(s, (W//2 - s.get_width()//2, 250 + i * 28))
            if self.menu_sel == 0:
                for i in range(6):
                    x = 120 + i * 110; y = H - 80
                    wp = WEAPONS[i]
                    pygame.draw.rect(screen, wp[7], (x, y, 80, 50), border_radius=5)
                    pygame.draw.rect(screen, WHITE, (x, y, 80, 50), 1, border_radius=5)
                    nt = get_font(12).render(wp[0], True, WHITE)
                    screen.blit(nt, (x + 40 - nt.get_width()//2, y + 5))
                    dt = get_font(10).render(f"伤害:{wp[1]}", True, WHITE)
                    screen.blit(dt, (x + 40 - dt.get_width()//2, y + 25))
            elif self.menu_sel == 1:
                for i in range(3):
                    x = 250 + i * 120; y = H - 80
                    z = Zombie(x, y, 1.5+i*0.3, 2+i)
                    z.draw(screen)
                    nt = get_font(11).render(f"速度:{1.5+i*0.3:.1f} HP:{2+i}", True, ZOMBIE_GREEN)
                    screen.blit(nt, (x - 10, y + 35))
            elif self.menu_sel == 2:
                for i, (c, n) in enumerate([(AI_PURPLE,"AI-1"),(AI_ORANGE,"AI-2")]):
                    x = 300 + i * 150; y = H - 80
                    ai = AIPlayer(x, y, c, n, 0.8+i*0.2)
                    ai.draw(screen)
                    nt = get_font(11).render(f"{n} 难度:{0.8+i*0.2:.1f}", True, c)
                    screen.blit(nt, (x - 20, y + 35))
            else:
                # 闯关模式预览 - 显示关卡平台示意
                for i in range(3):
                    x = 200 + i * 180; y = H - 70
                    pygame.draw.rect(screen, STAGE_CYAN, (x, y, 100, 10), border_radius=3)
                    nt = get_font(11).render(f"第{i+1}关", True, STAGE_CYAN)
                    screen.blit(nt, (x + 50 - nt.get_width()//2, y + 15))
                    zt = get_font(10).render(f"{5+i*3}只僵尸", True, ZOMBIE_GREEN)
                    screen.blit(zt, (x + 50 - zt.get_width()//2, y + 30))
        hint = self.sfont.render("↑↓选择 | ENTER确认 | ESC返回", True, (150,150,150))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 25))
    def draw_game(self):
        screen.fill(BG_COLOR)
        self.draw_platforms()
        for z in self.zombies: z.draw(screen)
        for ai in self.ai_players: ai.draw(screen)
        for b in self.bullets: b.draw(screen)
        for e in self.explosions: e.draw(screen)
        self.p1.draw(screen)
        if self.player_count == 2: self.p2.draw(screen)
        self.draw_hud()
        # 绘制通知
        for i, (text, color, timer) in enumerate(self.notifications):
            alpha = min(255, timer * 4)
            ts = self.font.render(text, True, color)
            ty = 100 + i * 35
            # 背景
            bg = pygame.Surface((ts.get_width() + 20, ts.get_height() + 10), pygame.SRCALPHA)
            bg.fill((20, 20, 40, min(180, alpha)))
            screen.blit(bg, (W//2 - ts.get_width()//2 - 10, ty - 5))
            screen.blit(ts, (W//2 - ts.get_width()//2, ty))
    def draw_gameover(self):
        self.draw_game()
        ov = pygame.Surface((W, H)); ov.fill(BLACK); ov.set_alpha(140)
        screen.blit(ov, (0,0))
        wt = self.tfont.render(f"{self.winner} 获胜!", True, YELLOW)
        screen.blit(wt, (W//2 - wt.get_width()//2, H//2 - 40))
        ht = self.sfont.render("使用火箭弹击杀对手! 按 ENTER 返回菜单", True, WHITE)
        screen.blit(ht, (W//2 - ht.get_width()//2, H//2 + 20))
    def draw_zombie_result(self):
        screen.fill(BG_COLOR)
        t = self.tfont.render("僵尸模式 结束!", True, ZOMBIE_GREEN)
        screen.blit(t, (W//2 - t.get_width()//2, 60))
        p1k = self.p1.kills; p2k = self.p2.kills
        if p1k > p2k:
            winner = "玩家1 (蓝色)"; wc = BLUE
        elif p2k > p1k:
            winner = "玩家2 (红色)"; wc = RED
        else:
            winner = "平手!"; wc = YELLOW
        pygame.draw.rect(screen, (20,20,40), (W//2-200, 140, 400, 60), border_radius=8)
        pygame.draw.rect(screen, BLUE, (W//2-200, 140, 400, 60), 2, border_radius=8)
        t1 = self.font.render(f"玩家1 击杀: {p1k}", True, BLUE)
        screen.blit(t1, (W//2 - t1.get_width()//2, 155))
        pygame.draw.rect(screen, (20,20,40), (W//2-200, 220, 400, 60), border_radius=8)
        pygame.draw.rect(screen, RED, (W//2-200, 220, 400, 60), 2, border_radius=8)
        t2 = self.font.render(f"玩家2 击杀: {p2k}", True, RED)
        screen.blit(t2, (W//2 - t2.get_width()//2, 235))
        wt = self.tfont.render(f"{winner} 获胜!", True, wc)
        screen.blit(wt, (W//2 - wt.get_width()//2, 320))
        ht = self.sfont.render("按 ENTER 返回菜单", True, WHITE)
        screen.blit(ht, (W//2 - ht.get_width()//2, H - 40))
    def draw_coop_result(self):
        screen.fill(BG_COLOR)
        is_win = (self.winner == "玩家队")
        t = self.tfont.render("2v2 合作模式 结束!", True, AI_PURPLE)
        screen.blit(t, (W//2 - t.get_width()//2, 60))
        # 结果
        if is_win:
            rt = self.tfont.render("玩家队 获胜!", True, GREEN)
        else:
            rt = self.tfont.render("AI队 获胜!", True, RED)
        screen.blit(rt, (W//2 - rt.get_width()//2, 140))
        # 统计
        pygame.draw.rect(screen, (20,20,40), (W//2-200, 220, 400, 160), border_radius=8)
        pygame.draw.rect(screen, BLUE, (W//2-200, 220, 400, 160), 2, border_radius=8)
        t1 = self.font.render(f"玩家1 击杀: {self.p1.kills} | {WEAPON_NAMES[self.p1.weapon]}", True, BLUE)
        screen.blit(t1, (W//2 - t1.get_width()//2, 235))
        t2 = self.font.render(f"玩家2 击杀: {self.p2.kills} | {WEAPON_NAMES[self.p2.weapon]}", True, RED)
        screen.blit(t2, (W//2 - t2.get_width()//2, 270))
        for i, ai in enumerate(self.ai_players):
            at = self.font.render(f"{ai.name} 击杀: {ai.kills} | {WEAPON_NAMES[ai.weapon]}", True, ai.color)
            screen.blit(at, (W//2 - at.get_width()//2, 305 + i * 35))
        ht = self.sfont.render("按 ENTER 返回菜单", True, WHITE)
        screen.blit(ht, (W//2 - ht.get_width()//2, H - 40))
    def draw_stage_gameover(self):
        screen.fill(BG_COLOR)
        t = self.tfont.render("闯关模式 结束!", True, RED)
        screen.blit(t, (W//2 - t.get_width()//2, 60))
        # 结果
        rt = self.tfont.render("全军覆没!", True, RED)
        screen.blit(rt, (W//2 - rt.get_width()//2, 140))
        # 统计
        pygame.draw.rect(screen, (20,20,40), (W//2-200, 220, 400, 120), border_radius=8)
        pygame.draw.rect(screen, BLUE, (W//2-200, 220, 400, 120), 2, border_radius=8)
        t1 = self.font.render(f"玩家1 击杀: {self.p1.kills}", True, BLUE)
        screen.blit(t1, (W//2 - t1.get_width()//2, 235))
        t2 = self.font.render(f"玩家2 击杀: {self.p2.kills}", True, RED)
        screen.blit(t2, (W//2 - t2.get_width()//2, 270))
        lt = self.sfont.render(f"到达: 第 {self.stage_level} 关", True, STAGE_CYAN)
        screen.blit(lt, (W//2 - lt.get_width()//2, 310))
        ht = self.sfont.render("按 ENTER 返回菜单", True, WHITE)
        screen.blit(ht, (W//2 - ht.get_width()//2, H - 40))

def main():
    game = Game()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if game.state == "playing": game.state = "menu"
                    elif game.state == "menu": game.state = "mode_select"
                    elif game.state == "mode_select": pygame.quit(); sys.exit()
                    else: game.state = "menu"
                if ev.key == pygame.K_RETURN:
                    if game.state == "mode_select":
                        game.player_count = 1 if game.mode_select_sel == 0 else 2
                        game.menu_sel = 0
                        game.state = "menu"
                    elif game.state == "menu":
                        if game.player_count == 1:
                            game.mode = ["coop", "stage"][game.menu_sel]
                        else:
                            game.mode = ["pvp","zombie","coop","stage"][game.menu_sel]
                        game.state = "playing"; game.reset()
                    elif game.state in ["gameover","zombie_result","coop_result","stage_gameover"]:
                        game.state = "menu"
                if game.state == "mode_select":
                    if ev.key == pygame.K_UP: game.mode_select_sel = (game.mode_select_sel - 1) % 2
                    if ev.key == pygame.K_DOWN: game.mode_select_sel = (game.mode_select_sel + 1) % 2
                if game.state == "menu":
                    max_sel = 2 if game.player_count == 1 else 4
                    if ev.key == pygame.K_UP: game.menu_sel = (game.menu_sel - 1) % max_sel
                    if ev.key == pygame.K_DOWN: game.menu_sel = (game.menu_sel + 1) % max_sel
        game.update()
        if game.state == "mode_select": game.draw_mode_select()
        elif game.state == "menu": game.draw_menu()
        elif game.state == "playing": game.draw_game()
        elif game.state == "gameover": game.draw_gameover()
        elif game.state == "zombie_result": game.draw_zombie_result()
        elif game.state == "coop_result": game.draw_coop_result()
        elif game.state == "stage_gameover": game.draw_stage_gameover()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
