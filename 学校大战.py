#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学校大战 School Battle - Python (Pygame) 版
根据 "学校大战.sb3" Scratch 游戏还原

玩法：
  - 方向键 / WASD ：移动
  - 空格 ：射击（消耗子弹）
  - Q ：发动技能
  - 回车 ：进入战斗 / 继续
  - P ：暂停
  - Esc ：退出

目标：在废弃教室中打败怪物，提升楼层，存活！
"""

import pygame
import sys
import math
import random
import os

# ========== 基础配置 ==========
WIDTH, HEIGHT = 480, 360
FPS = 60
TITLE = "学校大战 School Battle"

pygame.init()
screen = pygame.display.set_mode((WIDTH * 2, HEIGHT * 2))  # 2x 放大更清晰
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()


def _load_cn_font(size, bold=False):
    """显式加载 macOS 中文字体，避免 SysFont 乱码"""
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Songti.ttc",
        "/System/Library/Fonts/CJKSymbolsFallback.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    # 终极 fallback
    return pygame.font.SysFont(None, size, bold=bold)


font_sm = pygame.font.SysFont("menlo,arial", 14)
font_md = pygame.font.SysFont("menlo,arial", 18, bold=True)
font_lg = pygame.font.SysFont("menlo,arial", 28, bold=True)
font_cn = _load_cn_font(16)
font_cn_lg = _load_cn_font(24)

# 小画布 (480x360)，然后放大到屏幕
canvas = pygame.Surface((WIDTH, HEIGHT))

# ========== 颜色 ==========
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (15, 76, 129)
GREEN = (76, 175, 80)
DARK_GREEN = (34, 139, 66)
RED = (231, 76, 60)
DARK_RED = (192, 57, 43)
BLUE = (52, 152, 219)
SKIN = (245, 201, 160)
BROWN = (91, 55, 30)
PURPLE = (155, 89, 182)
YELLOW = (241, 196, 15)
ORANGE = (230, 126, 34)
SILVER = (189, 195, 199)
DIRTY = (130, 110, 80)

# ========== 游戏状态 ==========
STATE_INTRO = 0      # 开始界面（普通教室）
STATE_BATTLE = 1     # 战斗中（废弃教室）
STATE_DEAD = 2       # 死亡
STATE_WIN_FLOOR = 3  # 通过当前楼层
STATE_PAUSE = 4


class Game:
    def __init__(self):
        self.state = STATE_INTRO
        self.floor = 1
        self.score = 0
        self.bullets_total = 100
        self.fire_rate = 0.3        # 子弹间隔秒数
        self.fire_cd = 0
        self.player_hp = 100
        self.player_hp_max = 100
        self.skill_level = 1
        self.skill_cd = 0
        self.shield_timer = 0.0
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.bullets = []
        self.enemies = []
        self.skill_blasts = []
        self.heal_items = []
        self.shield_items = []
        self.particles = []
        self.enemy_spawn_timer = 0
        self.heal_spawn_timer = 6.0
        self.shield_spawn_timer = 9.0
        self.enemies_required = 8
        self.enemies_killed = 0
        self.floor_cleared_shown = 0
        self.kill_target = 8
        self.time = 0
        self.player_name = "ruirui"

    # ========== 背景绘制 ==========
    def draw_classroom_bg(self):
        """普通教室 - 开始界面"""
        # 天花板
        canvas.fill((245, 240, 230))
        pygame.draw.rect(canvas, (255, 248, 231), (0, 50, WIDTH, 200))
        # 地板
        pygame.draw.rect(canvas, (196, 145, 59), (0, 250, WIDTH, 110))
        pygame.draw.rect(canvas, (212, 162, 76), (0, 250, WIDTH, 10))
        for y in range(270, 360, 20):
            pygame.draw.line(canvas, (176, 126, 42), (0, y), (WIDTH, y), 1)
        # 黑板
        pygame.draw.rect(canvas, (139, 115, 85), (115, 55, 250, 130), 6)
        pygame.draw.rect(canvas, (45, 90, 61), (120, 65, 240, 120))
        # 粉笔槽
        pygame.draw.rect(canvas, (139, 115, 85), (130, 185, 220, 8))
        # 文字
        t1 = font_cn_lg.render("学校大战", True, WHITE)
        canvas.blit(t1, t1.get_rect(center=(240, 100)))
        t2 = font_cn.render("按 回车 进入战斗", True, (255, 235, 59))
        canvas.blit(t2, t2.get_rect(center=(240, 140)))
        t3 = font_cn.render("WASD/方向键移动  空格射击  Q技能", True, WHITE)
        canvas.blit(t3, t3.get_rect(center=(240, 170)))
        # 窗
        pygame.draw.rect(canvas, (135, 206, 235), (20, 70, 80, 100))
        pygame.draw.rect(canvas, WHITE, (20, 70, 80, 100), 3)
        pygame.draw.line(canvas, WHITE, (60, 70), (60, 170), 2)
        pygame.draw.line(canvas, WHITE, (20, 120), (100, 120), 2)
        pygame.draw.rect(canvas, (135, 206, 235), (380, 70, 80, 100))
        pygame.draw.rect(canvas, WHITE, (380, 70, 80, 100), 3)
        pygame.draw.line(canvas, WHITE, (420, 70), (420, 170), 2)
        pygame.draw.line(canvas, WHITE, (380, 120), (460, 120), 2)
        # 桌椅
        for x in (40, 140, 270, 370):
            pygame.draw.rect(canvas, (212, 162, 76), (x, 220, 70, 35))
            pygame.draw.rect(canvas, (139, 115, 85), (x + 5, 255, 4, 15))
            pygame.draw.rect(canvas, (139, 115, 85), (x + 61, 255, 4, 15))
            pygame.draw.rect(canvas, (196, 145, 59), (x + 10, 275, 50, 8))
            pygame.draw.rect(canvas, (139, 115, 85), (x + 10, 283, 4, 20))
            pygame.draw.rect(canvas, (139, 115, 85), (x + 56, 283, 4, 20))
        # 讲台
        pygame.draw.rect(canvas, (139, 115, 85), (170, 195, 140, 50))
        # 时钟
        pygame.draw.circle(canvas, WHITE, (240, 55), 16)
        pygame.draw.circle(canvas, BLACK, (240, 55), 16, 2)
        pygame.draw.line(canvas, BLACK, (240, 55), (240, 45), 2)
        pygame.draw.line(canvas, BLACK, (240, 55), (248, 58), 1)

    def draw_abandoned_bg(self):
        """废弃教室 - 战斗场景"""
        # 天花板 + 水渍
        canvas.fill((139, 128, 112))
        pygame.draw.ellipse(canvas, (90, 74, 53), (90, 30, 60, 16))
        pygame.draw.ellipse(canvas, (90, 74, 53), (310, 20, 80, 20))
        # 墙壁 发黄 + 发霉
        pygame.draw.rect(canvas, (194, 178, 128), (0, 50, WIDTH, 200))
        pygame.draw.ellipse(canvas, (107, 142, 35), (45, 155, 70, 50))
        pygame.draw.ellipse(canvas, (85, 107, 47), (390, 125, 60, 70))
        pygame.draw.ellipse(canvas, (74, 107, 61), (275, 200, 50, 40))
        # 墙皮剥落
        pygame.draw.polygon(canvas, (138, 122, 90),
                            [(180, 80), (190, 95), (215, 85), (235, 105), (210, 115), (185, 105)])
        pygame.draw.polygon(canvas, (138, 122, 90),
                            [(360, 100), (375, 120), (400, 110), (405, 130), (380, 135)])
        # 地板 破损
        pygame.draw.rect(canvas, (122, 92, 48), (0, 250, WIDTH, 110))
        pygame.draw.rect(canvas, (138, 106, 58), (0, 250, WIDTH, 10))
        for y in range(275, 360, 25):
            pygame.draw.line(canvas, (74, 53, 32), (0, y), (WIDTH, y), 2)
        pygame.draw.ellipse(canvas, (42, 26, 8), (125, 295, 50, 20))
        pygame.draw.ellipse(canvas, (42, 26, 8), (355, 260, 40, 12))
        pygame.draw.ellipse(canvas, (58, 42, 21), (55, 275, 50, 10))
        pygame.draw.ellipse(canvas, (58, 42, 21), (320, 330, 60, 12))

        # 蜘蛛网
        def web(cx, cy, r, alpha=90):
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            col = (255, 255, 255, alpha)
            for ang in (0, 45, 90, 135, 180, 225, 270, 315):
                rad = math.radians(ang)
                pygame.draw.line(surf, col, (r, r),
                                 (r + math.cos(rad) * r, r + math.sin(rad) * r), 1)
            for rr in (r // 3, r * 2 // 3, r):
                pygame.draw.circle(surf, col, (r, r), rr, 1)
            canvas.blit(surf, (cx - r, cy - r))

        web(35, 70, 38)
        web(450, 70, 40, 70)
        web(40, 220, 28, 60)

        # 黑板 破旧
        pygame.draw.rect(canvas, (90, 69, 48), (115, 55, 250, 130), 6)
        pygame.draw.rect(canvas, (42, 46, 32), (120, 65, 240, 120))
        pygame.draw.line(canvas, (26, 26, 16), (150, 70), (180, 175), 1)
        pygame.draw.line(canvas, (26, 26, 16), (280, 80), (310, 170), 1)
        pygame.draw.rect(canvas, (90, 69, 48), (130, 185, 220, 8))
        # 粉笔灰
        pygame.draw.ellipse(canvas, (220, 200, 160), (290, 188, 36, 6))

        # 窗户（破裂）
        pygame.draw.rect(canvas, (58, 72, 86), (20, 70, 80, 100))
        pygame.draw.rect(canvas, (74, 48, 32), (20, 70, 80, 100), 4)
        pygame.draw.line(canvas, (74, 48, 32), (60, 70), (60, 170), 3)
        pygame.draw.line(canvas, (74, 48, 32), (20, 120), (100, 120), 3)
        # 破洞
        pygame.draw.polygon(canvas, (26, 26, 26),
                            [(75, 130), (90, 135), (82, 150), (95, 155), (78, 160), (70, 148)])
        pygame.draw.polygon(canvas, (26, 26, 26),
                            [(25, 125), (38, 130), (32, 145), (40, 148), (22, 155), (20, 140)])
        # 右窗更大破洞
        pygame.draw.rect(canvas, (58, 72, 86), (380, 70, 80, 100))
        pygame.draw.rect(canvas, (74, 48, 32), (380, 70, 80, 100), 4)
        pygame.draw.line(canvas, (74, 48, 32), (420, 70), (420, 170), 3)
        pygame.draw.line(canvas, (74, 48, 32), (380, 120), (460, 120), 3)
        pygame.draw.polygon(canvas, (26, 26, 26),
                            [(390, 75), (440, 80), (450, 105), (430, 115), (385, 100)])
        pygame.draw.polygon(canvas, (26, 26, 26),
                            [(385, 130), (455, 125), (450, 160), (395, 165)])

        # 门（歪掉）
        door_surf = pygame.Surface((60, 65), pygame.SRCALPHA)
        pygame.draw.rect(door_surf, (74, 58, 32), (2, 2, 48, 55), border_radius=2)
        pygame.draw.line(door_surf, (42, 26, 8), (8, 10), (20, 45), 1)
        pygame.draw.circle(door_surf, (107, 90, 64), (40, 35), 3)
        r = pygame.transform.rotate(door_surf, -3)
        canvas.blit(r, r.get_rect(center=(245, 228)))

        # 破损讲台
        pygame.draw.rect(canvas, (90, 74, 48), (170, 195, 140, 50))
        pygame.draw.ellipse(canvas, (26, 16, 0), (222, 193, 36, 8))
        # 破角落
        pygame.draw.polygon(canvas, (26, 16, 0),
                            [(170, 195), (180, 200), (175, 210), (170, 208)])
        pygame.draw.polygon(canvas, (26, 16, 0),
                            [(310, 245), (295, 250), (298, 240)])

        # 课桌椅 杂乱
        def desk(x, y, rot=0, broken=False):
            s = pygame.Surface((80, 90), pygame.SRCALPHA)
            pygame.draw.rect(s, (106, 85, 58), (0, 0, 70, 35), border_radius=2)
            pygame.draw.rect(s, (90, 74, 48), (5, 35, 4, 20))
            pygame.draw.rect(s, (90, 74, 48), (61, 35, 4, 20 if not broken else 10))
            pygame.draw.rect(s, (106, 85, 58), (10, 55, 50, 8), border_radius=2)
            pygame.draw.rect(s, (90, 74, 48), (10, 63, 4, 25))
            pygame.draw.rect(s, (90, 74, 48), (56, 63, 4, 25))
            if rot:
                s = pygame.transform.rotate(s, rot)
            canvas.blit(s, (x, y))

        desk(40, 210, 15, True)
        desk(140, 220, -5)
        desk(270, 215, -8)
        desk(370, 210, 10, True)

    # ========== HUD ==========
    def draw_hud(self):
        # 绿色框架（Scratch 原 flower_frame 风格）
        fx, fy, fw, fh = 10, 320, 460, 36
        pygame.draw.rect(canvas, DARK_GREEN, (fx, fy, fw, fh), border_radius=4)
        pygame.draw.rect(canvas, (34, 168, 66), (fx + 2, fy + 2, fw - 4, fh - 4), 2, border_radius=3)
        # 小花点缀
        def flower(px, py):
            for ang in (0, 72, 144, 216, 288):
                rad = math.radians(ang)
                ex = px + math.cos(rad) * 5
                ey = py + math.sin(rad) * 5
                pygame.draw.ellipse(canvas, RED, (ex - 3, ey - 4, 6, 8))
            pygame.draw.circle(canvas, YELLOW, (px, py), 3)

        flower(fx + 10, fy + 18)
        flower(fx + fw - 10, fy + 18)

        # HP 条
        pygame.draw.rect(canvas, (60, 20, 20), (fx + 24, fy + 6, 100, 10))
        hp_ratio = max(0, self.player_hp / self.player_hp_max)
        pygame.draw.rect(canvas, RED, (fx + 24, fy + 6, int(100 * hp_ratio), 10))
        pygame.draw.rect(canvas, WHITE, (fx + 24, fy + 6, 100, 10), 1)
        hp_txt = font_cn.render(f"HP {int(self.player_hp)}/{self.player_hp_max}", True, WHITE)
        canvas.blit(hp_txt, (fx + 25, fy + 18))

        # 子弹
        bl_txt = font_cn.render(f"子弹: {self.bullets_total}", True, WHITE)
        canvas.blit(bl_txt, (fx + 140, fy + 6))
        # 分数
        sc_txt = font_cn.render(f"分数: {self.score}", True, WHITE)
        canvas.blit(sc_txt, (fx + 140, fy + 18))
        # 楼层
        fl_txt = font_cn.render(f"第 {self.floor} 层  ({self.enemies_killed}/{self.kill_target})", True, WHITE)
        canvas.blit(fl_txt, (fx + 230, fy + 6))
        # 技能
        sk_txt = font_cn.render(f"技能Lv{self.skill_level} [Q]", True,
                                 (0, 220, 255) if self.skill_cd <= 0 else (120, 120, 120))
        canvas.blit(sk_txt, (fx + 230, fy + 18))
        # 玩家名
        nm = font_cn.render(self.player_name, True, (255, 235, 59))
        canvas.blit(nm, (fx + fw - 60, fy + 12))

    # ========== 敌人/子弹生成 ==========
    def spawn_enemy(self):
        # 随机从屏幕边缘生成
        side = random.randint(0, 3)
        margin = 30
        if side == 0:
            x, y = random.randint(30, WIDTH - 30), -margin
        elif side == 1:
            x, y = WIDTH + margin, random.randint(30, HEIGHT - 120)
        elif side == 2:
            x, y = random.randint(30, WIDTH - 30), -margin
        else:
            x, y = -margin, random.randint(30, HEIGHT - 120)
        # 不同楼层 怪物血量不同
        hp = 20 + int(self.floor * 6)
        spd = 0.6 + self.floor * 0.08
        variant = random.choice([1, 2, 3])
        self.enemies.append(Enemy(x, y, hp, spd, variant))

    def fire_bullet(self):
        if self.bullets_total <= 0 or self.fire_cd > 0:
            return
        self.bullets_total -= 1
        self.fire_cd = self.fire_rate
        bx, by = self.player.x, self.player.y
        # 方向朝向鼠标 或者 朝向最近敌人
        tx, ty = pygame.mouse.get_pos()
        tx, ty = tx // 2, ty // 2
        if self.enemies:
            # 朝向最近敌人
            best = min(self.enemies, key=lambda e: (e.x - bx) ** 2 + (e.y - by) ** 2)
            tx, ty = best.x, best.y
        dx, dy = tx - bx, ty - by
        d = math.hypot(dx, dy) or 1
        spd = 6
        self.bullets.append(Bullet(bx, by, dx / d * spd, dy / d * spd))
        # 粒子
        for _ in range(3):
            self.particles.append(Particle(bx, by, color=YELLOW, life=0.15, size=2))

    def activate_skill(self):
        if self.skill_cd > 0:
            return
        self.skill_cd = 5 - min(3, self.skill_level * 0.5)
        cx, cy = self.player.x, self.player.y
        radius = 50 + self.skill_level * 25
        damage = 30 + self.skill_level * 20
        self.skill_blasts.append(SkillBlast(cx, cy, radius, damage))
        for i in range(36):
            ang = math.radians(i * 10)
            self.particles.append(Particle(cx, cy,
                                            vx=math.cos(ang) * 4,
                                            vy=math.sin(ang) * 4,
                                            life=0.6,
                                            color=(100, 200, 255),
                                            size=4))

    # ========== 主更新 & 绘制 ==========
    def update(self, dt):
        if self.state != STATE_BATTLE:
            return
        self.time += dt
        self.fire_cd = max(0, self.fire_cd - dt)
        self.skill_cd = max(0, self.skill_cd - dt)
        self.shield_timer = max(0, self.shield_timer - dt)

        # 玩家输入
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        self.player.move(dx, dy, dt)

        if keys[pygame.K_SPACE]:
            self.fire_bullet()

        # 敌人生成
        self.enemy_spawn_timer -= dt
        spawn_interval = max(0.5, 2.0 - self.floor * 0.15)
        if self.enemy_spawn_timer <= 0 and self.enemies_killed < self.kill_target:
            self.enemy_spawn_timer = spawn_interval
            if len(self.enemies) < 3 + self.floor:
                self.spawn_enemy()

        # 回血道具随机刷新
        self.heal_spawn_timer -= dt
        if self.heal_spawn_timer <= 0:
            self.heal_spawn_timer = random.uniform(7, 13)  # 7~13秒刷一个
            if len(self.heal_items) < 2 and self.player_hp < self.player_hp_max:
                hx = random.randint(60, WIDTH - 60)
                hy = random.randint(110, 290)
                amt = random.choice([15, 20, 25, 30, 40])
                self.heal_items.append(HealItem(hx, hy, amt))
        # 更新 & 拾取回血道具
        for it in list(self.heal_items):
            it.update(dt)
            if it.life <= 0:
                self.heal_items.remove(it)
                continue
            # 碰到玩家就拾取
            if math.hypot(self.player.x - it.x, self.player.y - it.y) < it.pickup_radius:
                before = self.player_hp
                self.player_hp = min(self.player_hp_max, self.player_hp + it.amount)
                healed = int(self.player_hp - before)
                # 飘字粒子
                for _ in range(12):
                    ang = random.random() * math.tau
                    spd = random.random() * 2 + 0.5
                    self.particles.append(Particle(it.x, it.y - 5,
                                                   vx=math.cos(ang) * spd,
                                                   vy=math.sin(ang) * spd - 1,
                                                   life=0.6,
                                                   color=random.choice(
                                                       [(255, 120, 140), (255, 80, 100), WHITE]),
                                                   size=3))
                self.heal_items.remove(it)

        # 护盾道具随机刷新
        self.shield_spawn_timer -= dt
        if self.shield_spawn_timer <= 0:
            self.shield_spawn_timer = random.uniform(12, 18)
            if len(self.shield_items) < 1:
                sx = random.randint(60, WIDTH - 60)
                sy = random.randint(110, 290)
                dur = random.choice([4, 5, 5, 6, 7])
                self.shield_items.append(ShieldItem(sx, sy, dur))
        # 更新 & 拾取护盾
        for it in list(self.shield_items):
            it.update(dt)
            if it.life <= 0:
                self.shield_items.remove(it)
                continue
            if math.hypot(self.player.x - it.x, self.player.y - it.y) < it.pickup_radius:
                self.shield_timer = max(self.shield_timer, it.duration)
                # 特效：蓝色光环粒子
                for i in range(24):
                    ang = math.radians(i * 15)
                    self.particles.append(Particle(it.x, it.y - 4,
                                                   vx=math.cos(ang) * 3,
                                                   vy=math.sin(ang) * 3,
                                                   life=0.8,
                                                   color=random.choice([
                                                       (100, 220, 255),
                                                       (180, 240, 255),
                                                       WHITE]),
                                                   size=4))
                self.shield_items.remove(it)

        # 更新子弹
        for b in list(self.bullets):
            b.update(dt)
            if b.x < 0 or b.x > WIDTH or b.y < 0 or b.y > HEIGHT:
                self.bullets.remove(b)
                continue
            # 命中敌人
            for e in list(self.enemies):
                if math.hypot(b.x - e.x, b.y - e.y) < 20:
                    e.hp -= b.damage
                    self.bullets.remove(b)
                    for _ in range(6):
                        self.particles.append(Particle(b.x, b.y, color=(255, 200, 50), life=0.3, size=3))
                    break

        # 技能爆炸
        for s in list(self.skill_blasts):
            s.life -= dt
            s.radius_now += (s.target_radius - s.radius_now) * 0.2
            if s.life > 0.9 * s.max_life:  # 只在刚开始命中一次
                for e in list(self.enemies):
                    if not e.hit_by_skill:
                        d = math.hypot(e.x - s.x, e.y - s.y)
                        if d < s.radius_now:
                            e.hp -= s.damage
                            e.hit_by_skill = True
                            for _ in range(8):
                                self.particles.append(Particle(e.x, e.y,
                                                               life=0.4, color=(100, 200, 255), size=4))
            if s.life <= 0:
                self.skill_blasts.remove(s)

        # 更新敌人
        for e in list(self.enemies):
            e.update(dt, self.player)
            # 碰到玩家 扣血
            if math.hypot(e.x - self.player.x, e.y - self.player.y) < 22:
                if self.shield_timer > 0:
                    # 护盾激活：敌人被反弹，不扣血
                    dx, dy = self.player.x - e.x, self.player.y - e.y
                    d = math.hypot(dx, dy) or 1
                    e.x -= dx / d * 0.5
                    e.y -= dy / d * 0.5
                    for _ in range(2):
                        self.particles.append(Particle(self.player.x, self.player.y,
                                                       color=(100, 220, 255), life=0.15, size=3))
                else:
                    self.player_hp -= 18 * dt * e.touch_speed
                    for _ in range(3):
                        self.particles.append(Particle(self.player.x, self.player.y,
                                                       color=RED, life=0.25, size=3))
            if e.hp <= 0:
                self.enemies.remove(e)
                self.enemies_killed += 1
                self.score += 10 * self.floor
                # 掉落 子弹/回血
                if random.random() < 0.3:
                    self.bullets_total += random.randint(3, 8)
                if random.random() < 0.15:
                    self.player_hp = min(self.player_hp_max, self.player_hp + 15)
                # 死亡粒子
                for _ in range(14):
                    ang = random.random() * math.tau
                    spd = random.random() * 3 + 1
                    self.particles.append(Particle(e.x, e.y,
                                                   vx=math.cos(ang) * spd,
                                                   vy=math.sin(ang) * spd,
                                                   life=0.6,
                                                   color=random.choice([RED, PURPLE, YELLOW, ORANGE]),
                                                   size=4))

        # 粒子
        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

        # 死亡
        if self.player_hp <= 0:
            self.state = STATE_DEAD
            for _ in range(30):
                ang = random.random() * math.tau
                spd = random.random() * 4 + 1
                self.particles.append(Particle(self.player.x, self.player.y,
                                               vx=math.cos(ang) * spd,
                                               vy=math.sin(ang) * spd,
                                               life=1.0,
                                               color=random.choice([RED, ORANGE, YELLOW]),
                                               size=5))
        # 过关
        elif self.enemies_killed >= self.kill_target and len(self.enemies) == 0:
            self.state = STATE_WIN_FLOOR
            self.floor_cleared_shown = 0

    def draw(self):
        if self.state == STATE_INTRO:
            self.draw_classroom_bg()
            self.player.draw(canvas)
        else:
            self.draw_abandoned_bg()
            # 技能光环（先画，作为背景圈）
            for s in self.skill_blasts:
                alpha = int(max(0, s.life / s.max_life) * 180)
                sfc = pygame.Surface((s.radius_now * 2, s.radius_now * 2), pygame.SRCALPHA)
                pygame.draw.circle(sfc, (100, 220, 255, alpha),
                                   (s.radius_now, s.radius_now), s.radius_now, 5)
                pygame.draw.circle(sfc, (200, 240, 255, max(0, alpha - 80)),
                                   (s.radius_now, s.radius_now), max(2, s.radius_now - 8))
                canvas.blit(sfc, (s.x - s.radius_now, s.y - s.radius_now))
            #子弹
            for b in self.bullets:
                b.draw(canvas)
            # 回血道具
            for it in self.heal_items:
                it.draw(canvas)
            # 护盾道具
            for it in self.shield_items:
                it.draw(canvas)
            # 敌人
            for e in self.enemies:
                e.draw(canvas)
            # 玩家
            self.player.draw(canvas)
            # 玩家护盾视觉：无敌时的蓝金色护盾圈
            if self.shield_timer > 0:
                px, py = int(self.player.x), int(self.player.y + 10)
                # 脉动效果
                pulse = 1.0 + 0.15 * math.sin(self.time * 10)
                r_inner = int(28 * pulse)
                r_outer = int(36 * pulse)
                # 最后1秒时开始闪烁提醒
                blink_alpha = 220
                if self.shield_timer < 1.0:
                    blink_alpha = int(220 * (0.5 + 0.5 * math.sin(self.time * 20)))
                # 护盾外圈
                sf = pygame.Surface((r_outer * 2, r_outer * 2), pygame.SRCALPHA)
                pygame.draw.circle(sf, (100, 220, 255, blink_alpha),
                                   (r_outer, r_outer), r_outer, 4)
                # 金色内圈
                pygame.draw.circle(sf, (255, 230, 120, min(255, blink_alpha + 30)),
                                   (r_outer, r_outer), r_inner, 2)
                pygame.draw.circle(sf, (200, 240, 255, max(20, blink_alpha - 180)),
                                   (r_outer, r_outer), r_inner - 2)
                # 星闪
                for i in range(8):
                    ang = self.time * 3 + math.radians(i * 45)
                    fx = r_outer + math.cos(ang) * (r_inner - 4)
                    fy = r_outer + math.sin(ang) * (r_inner - 4)
                    pygame.draw.circle(sf, WHITE, (int(fx), int(fy)), 2)
                canvas.blit(sf, (px - r_outer, py - r_outer - 8))
                # 护盾秒数标记（不用emoji避免字体问题）
                shield_txt = font_sm.render(f"SH {self.shield_timer:.1f}s", True, (80, 200, 255))
                canvas.blit(shield_txt, (px - shield_txt.get_width() // 2, py - 42))
            # 粒子
            for p in self.particles:
                p.draw(canvas)
            # HUD
            self.draw_hud()

            if self.state == STATE_DEAD:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                canvas.blit(overlay, (0, 0))
                t1 = font_cn_lg.render("你被怪物击败了...", True, RED)
                canvas.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
                t2 = font_cn.render(f"分数: {self.score}   到达第 {self.floor} 层", True, WHITE)
                canvas.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15)))
                t3 = font_cn.render("按 回车 重新开始  |  Esc 退出", True, YELLOW)
                canvas.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))

            elif self.state == STATE_WIN_FLOOR:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 30, 0, 130))
                canvas.blit(overlay, (0, 0))
                t1 = font_cn_lg.render(f"第 {self.floor} 层通过！", True, GREEN)
                canvas.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
                # 奖励提示
                rewards = [
                    f"  生命上限 +15 （当前 {self.player_hp_max + 15}）",
                    f"  子弹 +40 （当前 {self.bullets_total + 40}）",
                    f"  射速提升！",
                    f"  技能等级提升 Lv{self.skill_level + 1}",
                ]
                for i, r in enumerate(rewards):
                    tr = font_cn.render(r, True, WHITE)
                    canvas.blit(tr, (WIDTH // 2 - 120, HEIGHT // 2 - 5 + i * 22))
                t3 = font_cn.render("按 回车 进入下一层", True, YELLOW)
                canvas.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

            elif self.state == STATE_PAUSE:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                canvas.blit(overlay, (0, 0))
                t1 = font_cn_lg.render("暂停中", True, YELLOW)
                canvas.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                t2 = font_cn.render("按 P 继续", True, WHITE)
                canvas.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    # ========== 输入事件 ==========
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.key == pygame.K_p and self.state == STATE_BATTLE:
                self.state = STATE_PAUSE
            elif event.key == pygame.K_p and self.state == STATE_PAUSE:
                self.state = STATE_BATTLE
            if event.key == pygame.K_RETURN:
                if self.state == STATE_INTRO:
                    self.start_battle()
                elif self.state == STATE_DEAD:
                    self.__init__()  # 重开
                    self.state = STATE_INTRO
                elif self.state == STATE_WIN_FLOOR:
                    self.advance_floor()
            if event.key == pygame.K_q and self.state == STATE_BATTLE:
                self.activate_skill()

    def start_battle(self):
        self.state = STATE_BATTLE
        self.player = Player(WIDTH // 2, HEIGHT // 2 + 30)
        self.bullets = []
        self.enemies = []
        self.skill_blasts = []
        self.heal_items = []
        self.shield_items = []
        self.particles = []
        self.enemy_spawn_timer = 0
        self.heal_spawn_timer = 5.0
        self.shield_spawn_timer = 7.0
        self.enemies_killed = 0
        self.shield_timer = 0.0

    def advance_floor(self):
        self.floor += 1
        self.kill_target = 8 + self.floor * 3
        self.player_hp_max += 15
        self.player_hp = min(self.player_hp_max, self.player_hp + 40)
        self.bullets_total += 40
        self.fire_rate = max(0.1, self.fire_rate * 0.9)
        self.skill_level = min(5, self.skill_level + 1)
        self.start_battle()


# ========== 实体类 ==========
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 130
        self.dir = 1  # 1=右, -1=左
        self.anim = 0
        self.facing = 0  # 朝向角度

    def move(self, dx, dy, dt):
        if dx < 0: self.dir = -1
        elif dx > 0: self.dir = 1
        if dx or dy:
            self.anim += dt * 8
            len = math.hypot(dx, dy) or 1
            self.x += dx / len * self.speed * dt
            self.y += dy / len * self.speed * dt
        # 边界（HUD 占底部）
        self.x = max(18, min(WIDTH - 18, self.x))
        self.y = max(55, min(315, self.y))

    def draw(self, surf):
        # 基于生成的 boy.svg 简化绘制
        # 身体 蓝色T恤
        bx, by = self.x, self.y + 12
        # 阴影
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (bx - 12, by + 18, 24, 5))
        # 裤子
        pygame.draw.rect(surf, (44, 62, 80), (bx - 10, by + 4, 8, 20))
        pygame.draw.rect(surf, (44, 62, 80), (bx + 2, by + 4, 8, 20))
        # T恤
        pygame.draw.ellipse(surf, (52, 152, 219), (bx - 13, by - 6, 26, 18))
        pygame.draw.polygon(surf, (41, 128, 185), [
            (bx - 7, by - 6), (bx, by + 1), (bx + 7, by - 6)])
        # 胸口图案
        pygame.draw.circle(surf, WHITE, (bx, by + 3), 4)
        pygame.draw.line(surf, RED, (bx - 2, by), (bx - 2, by + 6), 1)
        pygame.draw.line(surf, RED, (bx + 2, by), (bx + 2, by + 6), 1)
        # 手臂
        pygame.draw.ellipse(surf, SKIN, (bx - 16, by - 2, 6, 16))
        pygame.draw.ellipse(surf, SKIN, (bx + 10, by - 2, 6, 16))
        # 手
        h_phase = math.sin(self.anim) * 2
        pygame.draw.circle(surf, SKIN, (bx - 13, by + 14 + h_phase), 4)
        pygame.draw.circle(surf, SKIN, (bx + 13, by + 14 - h_phase), 4)
        # 头
        pygame.draw.ellipse(surf, SKIN, (bx - 10, by - 24, 20, 22))
        # 耳朵
        pygame.draw.circle(surf, SKIN, (bx - 10, by - 13), 3)
        pygame.draw.circle(surf, SKIN, (bx + 10, by - 13), 3)
        # 头发
        pygame.draw.ellipse(surf, (61, 43, 31), (bx - 11, by - 28, 22, 11))
        pygame.draw.polygon(surf, (61, 43, 31), [
            (bx - 11, by - 22), (bx - 7, by - 14), (bx - 2, by - 18),
            (bx + 3, by - 12), (bx + 6, by - 20), (bx + 11, by - 15),
            (bx + 11, by - 25)
        ])
        # 眼
        eye_x = 4 if self.dir > 0 else -4
        pygame.draw.ellipse(surf, WHITE, (bx - 6 + eye_x * 0.3, by - 16, 4, 5))
        pygame.draw.ellipse(surf, WHITE, (bx + 2 + eye_x * 0.3, by - 16, 4, 5))
        pygame.draw.circle(surf, (44, 24, 16), (bx - 4 + eye_x * 0.4, by - 14), 2)
        pygame.draw.circle(surf, (44, 24, 16), (bx + 4 + eye_x * 0.4, by - 14), 2)
        # 腮红
        pygame.draw.ellipse(surf, (255, 182, 160, 120), (bx - 9, by - 10, 4, 3))
        pygame.draw.ellipse(surf, (255, 182, 160, 120), (bx + 5, by - 10, 4, 3))
        # 嘴
        pygame.draw.arc(surf, (192, 102, 80), (bx - 4, by - 10, 8, 6), 3.1, 0.1, 1)
        # 鞋
        foot_phase = math.sin(self.anim) * 2
        pygame.draw.ellipse(surf, WHITE, (bx - 12, by + 22, 10, 5))
        pygame.draw.ellipse(surf, (231, 76, 60), (bx - 12, by + 20, 9, 3))
        pygame.draw.ellipse(surf, WHITE, (bx + 2, by + 22, 10, 5))
        pygame.draw.ellipse(surf, (231, 76, 60), (bx + 2, by + 20, 9, 3))


class Bullet:
    def __init__(self, x, y, vx, vy, damage=10):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.rot = math.atan2(vy, vx)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        # 黄色光束弹
        bx, by = int(self.x), int(self.y)
        # 尾迹
        for i in range(4, 0, -1):
            alpha = (4 - i) / 4
            color = (255, int(220 * alpha + 50), 60, int(255 * alpha))
            s = pygame.Surface((12, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(s, color, (0, 0, 12, 6))
            s = pygame.transform.rotate(s, -math.degrees(self.rot))
            px = bx - i * self.vx * 0.3 - s.get_width() // 2
            py = by - i * self.vy * 0.3 - s.get_height() // 2
            surf.blit(s, (px, py))
        # 头部
        pygame.draw.circle(surf, YELLOW, (bx, by), 4)
        pygame.draw.circle(surf, WHITE, (bx, by), 2)


class Enemy:
    def __init__(self, x, y, hp, speed, variant=1):
        self.x, self.y = x, y
        self.hp = hp
        self.hp_max = hp
        self.speed = speed
        self.variant = variant
        self.touch_speed = 1.0
        self.anim = random.random() * math.tau
        self.hit_by_skill = False

    def update(self, dt, player):
        self.anim += dt * 5
        dx, dy = player.x - self.x, player.y - self.y
        d = math.hypot(dx, dy) or 1
        self.x += dx / d * self.speed + math.sin(self.anim) * 0.2
        self.y += dy / d * self.speed + math.cos(self.anim) * 0.2
        self.hit_by_skill = False  # 下一帧可重新吃技能

    def draw(self, surf):
        bx, by = int(self.x), int(self.y)
        phase = math.sin(self.anim) * 2
        variant = self.variant

        # 颜色微调
        if variant == 1:
            body1 = (142, 68, 173)
            body2 = (155, 89, 182)
            belly = (245, 176, 65)
        elif variant == 2:
            body1 = (120, 60, 50)
            body2 = (150, 80, 70)
            belly = (200, 140, 60)
        else:
            body1 = (50, 80, 140)
            body2 = (70, 110, 180)
            belly = (230, 160, 70)

        # 阴影
        pygame.draw.ellipse(surf, (0, 0, 0, 100), (bx - 18, by + 32, 36, 6))
        # 身体
        pygame.draw.ellipse(surf, body1, (bx - 18, by - 5, 36, 44))
        pygame.draw.ellipse(surf, body2, (bx - 14, by - 3, 28, 38))
        pygame.draw.ellipse(surf, belly, (bx - 9, by + 7, 18, 24))
        pygame.draw.ellipse(surf, belly, (bx - 7, by + 5, 6, 10))
        # 腿
        pygame.draw.ellipse(surf, body1, (bx - 10, by + 25, 6, 14))
        pygame.draw.ellipse(surf, body1, (bx + 4, by + 25, 6, 14))
        # 脚+爪
        pygame.draw.ellipse(surf, (28, 40, 51), (bx - 14, by + 36, 10, 5))
        pygame.draw.ellipse(surf, (28, 40, 51), (bx + 4, by + 36, 10, 5))
        for i, px in enumerate((bx - 15, bx - 12, bx - 9)):
            pygame.draw.polygon(surf, WHITE, [(px, by + 36), (px - 1, by + 40), (px + 2, by + 38)])
        for i, px in enumerate((bx + 3, bx + 6, bx + 9)):
            pygame.draw.polygon(surf, WHITE, [(px, by + 36), (px - 1, by + 40), (px + 2, by + 38)])
        # 头
        pygame.draw.ellipse(surf, body1, (bx - 18, by - 28, 36, 34))
        pygame.draw.ellipse(surf, body2, (bx - 15, by - 26, 30, 30))
        # 耳朵
        ear_surf = pygame.Surface((20, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(ear_surf, body1, (0, 2, 14, 28))
        pygame.draw.ellipse(ear_surf, (195, 155, 211), (4, 7, 8, 20))
        surf.blit(pygame.transform.rotate(ear_surf, -20), (bx - 22, by - 35))
        surf.blit(pygame.transform.rotate(ear_surf, 20), (bx + 10, by - 35))
        # 角
        def horn(hx, hy, dir=1):
            pts = [
                (hx, hy),
                (hx - dir * 5, hy - 12),
                (hx - dir * 10, hy - 14),
                (hx - dir * 3, hy - 4),
            ]
            pygame.draw.polygon(surf, YELLOW, pts)
            pygame.draw.circle(surf, WHITE, (hx - dir * 10, hy - 14), 2)
        horn(bx - 13, by - 36, dir=-1)
        horn(bx + 13, by - 36, dir=1)
        # 头顶小刺
        for sx in (-8, 0, 8):
            pygame.draw.polygon(surf, YELLOW,
                                [(bx + sx - 2, by - 40), (bx + sx, by - 50), (bx + sx + 2, by - 40)])
        # 怒眼
        brow_col = (44, 19, 58)
        pygame.draw.line(surf, brow_col, (bx - 16, by - 22), (bx - 4, by - 18), 3)
        pygame.draw.line(surf, brow_col, (bx + 16, by - 22), (bx + 4, by - 18), 3)
        # 眼睛 (红+黄瞳孔)
        eye_rect = pygame.Rect(bx - 12, by - 20, 10, 9)
        eye_rect2 = pygame.Rect(bx + 2, by - 20, 10, 9)
        pygame.draw.rect(surf, BLACK, eye_rect)
        pygame.draw.ellipse(surf, RED, eye_rect)
        pygame.draw.rect(surf, BLACK, eye_rect2)
        pygame.draw.ellipse(surf, RED, eye_rect2)
        pygame.draw.circle(surf, YELLOW, (bx - 7 + phase, by - 15), 3)
        pygame.draw.circle(surf, BLACK, (bx - 7 + phase, by - 15), 2)
        pygame.draw.circle(surf, YELLOW, (bx + 7 + phase, by - 15), 3)
        pygame.draw.circle(surf, BLACK, (bx + 7 + phase, by - 15), 2)
        # 鼻子
        pygame.draw.ellipse(surf, brow_col, (bx - 3, by - 6, 6, 4))
        # 尖牙嘴
        mouth = pygame.Rect(bx - 13, by - 2, 26, 16)
        pygame.draw.ellipse(surf, BLACK, mouth)
        # 上牙
        for i, (tx, th) in enumerate([(-10, 9), (-4, 11), (2, 11), (8, 9)]):
            pygame.draw.polygon(surf, WHITE,
                                [(bx + tx, by - 2), (bx + tx + 2, by - 2 + th), (bx + tx + 4, by - 2)])
        # 下牙
        for i, (tx, th) in enumerate([(-7, 9), (-1, 11), (5, 9)]):
            pygame.draw.polygon(surf, WHITE,
                                [(bx + tx, by + 11), (bx + tx + 2, by + 11 - th), (bx + tx + 4, by + 11)])
        # 小舌头
        pygame.draw.polygon(surf, RED,
                            [(bx - 5, by + 7), (bx, by + 12), (bx + 5, by + 7)])
        # 手臂 + 刺刀（左手臂 举武器）
        # 左手臂
        pygame.draw.ellipse(surf, body2, (bx - 30, by - 12, 8, 28))
        pygame.draw.circle(surf, body1, (bx - 28, by + 14), 6)
        # 刺刀刀柄
        hx, hy = bx - 32, by + 16
        # 刀柄头
        pygame.draw.rect(surf, (93, 64, 55), (hx - 1, hy - 14, 8, 4))
        pygame.draw.rect(surf, (139, 69, 19), (hx, hy - 10, 6, 12))
        pygame.draw.line(surf, (93, 64, 55), (hx, hy - 7), (hx + 6, hy - 5), 1)
        pygame.draw.line(surf, (93, 64, 55), (hx, hy - 3), (hx + 6, hy - 1), 1)
        pygame.draw.line(surf, (93, 64, 55), (hx, hy + 1), (hx + 6, hy + 3), 1)
        # 刀锷
        pygame.draw.rect(surf, (184, 134, 11), (hx - 3, hy + 1, 14, 3))
        pygame.draw.circle(surf, (255, 215, 0), (hx - 1, hy + 2), 1)
        pygame.draw.circle(surf, (255, 215, 0), (hx + 8, hy + 2), 1)
        # 刀身
        blade = pygame.Surface((10, 80), pygame.SRCALPHA)
        pygame.draw.polygon(blade, (189, 195, 199), [(0, 0), (8, 0), (6, 70), (4, 78), (2, 78)])
        pygame.draw.polygon(blade, (213, 219, 219), [(2, 0), (7, 0), (5, 68), (3, 75)])
        pygame.draw.line(blade, (149, 165, 166), (4, 10), (4, 65), 1)
        blade = pygame.transform.rotate(blade, -50)
        surf.blit(blade, (hx - blade.get_width() // 2 + 3, hy - blade.get_height() // 2 - 20))

        # 另一只手 握拳
        pygame.draw.ellipse(surf, body2, (bx + 22, by - 10, 8, 24))
        pygame.draw.circle(surf, body1, (bx + 27, by + 12), 7)

        # HP 条
        if self.hp < self.hp_max:
            bw = 30
            pygame.draw.rect(surf, (40, 10, 10), (bx - bw // 2, by - 48, bw, 4))
            r = max(0, self.hp / self.hp_max)
            pygame.draw.rect(surf, RED, (bx - bw // 2, by - 48, int(bw * r), 4))
            pygame.draw.rect(surf, BLACK, (bx - bw // 2, by - 48, bw, 4), 1)


class SkillBlast:
    def __init__(self, x, y, radius, damage):
        self.x, self.y = x, y
        self.target_radius = radius
        self.radius_now = 8
        self.damage = damage
        self.max_life = 0.6
        self.life = 0.6


class HealItem:
    """随机刷新的回血道具（爱心 / 红色药瓶）"""
    def __init__(self, x, y, amount=25):
        self.x, self.y = x, y
        self.amount = amount
        self.life = 15.0  # 15秒没捡到就消失
        self.anim = random.random() * math.tau
        self.kind = random.choice(['heart', 'potion'])  # 两种外观
        # 浮动参数
        self.base_y = y
        self.pickup_radius = 18

    def update(self, dt):
        self.life -= dt
        self.anim += dt * 4
        self.y = self.base_y + math.sin(self.anim) * 2.5

    def draw(self, surf):
        # 快要消失时闪烁
        blink = 1.0
        if self.life < 3.0:
            blink = 0.5 + 0.5 * math.sin(self.anim * 3)
        alpha = int(255 * blink)

        if self.kind == 'heart':
            # 红色爱心 (两个圆 + 三角)
            hx, hy = int(self.x), int(self.y)
            s = pygame.Surface((28, 28), pygame.SRCALPHA)
            # 光晕
            glow = (255, 230, 230, int(120 * blink))
            pygame.draw.circle(s, glow, (14, 14), 13)
            # 心主体
            c1 = (255, int(70 * blink), int(90 * blink), alpha)
            c2 = (220, int(40 * blink), int(60 * blink), alpha)
            pygame.draw.circle(s, c1, (8, 9), 6)
            pygame.draw.circle(s, c1, (20, 9), 6)
            pts = [(2, 10), (26, 10), (14, 26)]
            pygame.draw.polygon(s, c1, pts)
            # 高光
            hl = (255, 220, 220, int(200 * blink))
            pygame.draw.circle(s, hl, (6, 7), 2)
            # 外描边
            s2 = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(s2, BLACK + (int(180 * blink),), (8, 9), 6, 1)
            pygame.draw.circle(s2, BLACK + (int(180 * blink),), (20, 9), 6, 1)
            pygame.draw.polygon(s2, BLACK + (int(180 * blink),), pts, 1)
            s.blit(s2, (0, 0))
            surf.blit(s, (hx - 14, hy - 14))
            # 回血数值小标
            txt = font_sm.render(f"+{self.amount}", True, (255, 80, 100))
            surf.blit(txt, (hx - txt.get_width() // 2, hy + 14))
        else:
            # 红色药瓶
            hx, hy = int(self.x), int(self.y)
            s = pygame.Surface((24, 30), pygame.SRCALPHA)
            # 光晕
            pygame.draw.circle(s, (255, 230, 230, int(100 * blink)), (12, 15), 13)
            # 瓶盖
            pygame.draw.rect(s, (100, 100, 100, alpha), (6, 0, 12, 5), border_radius=1)
            pygame.draw.rect(s, (60, 60, 60, alpha), (6, 0, 12, 5), 1, border_radius=1)
            # 瓶颈
            pygame.draw.rect(s, (200, 200, 200, alpha), (8, 5, 8, 3))
            # 瓶身（圆角矩形）
            body = (255, int(70 * blink), int(90 * blink), alpha)
            pygame.draw.ellipse(s, body, (2, 8, 20, 20))
            pygame.draw.rect(s, body, (3, 8, 18, 10))
            # 液体高光
            hl = (255, 220, 220, int(180 * blink))
            pygame.draw.ellipse(s, hl, (6, 12, 4, 10))
            # 描边
            pygame.draw.ellipse(s, BLACK + (int(150 * blink),), (2, 8, 20, 20), 1)
            # 十字标识（医疗）
            cross = (255, 255, 255, alpha)
            pygame.draw.rect(s, cross, (10, 14, 4, 10))
            pygame.draw.rect(s, cross, (7, 17, 10, 4))
            surf.blit(s, (hx - 12, hy - 15))
            txt = font_sm.render(f"+{self.amount}", True, (255, 80, 100))
            surf.blit(txt, (hx - txt.get_width() // 2, hy + 15))


class ShieldItem:
    """护盾道具：吃到后 N 秒无敌"""
    def __init__(self, x, y, duration=5.0):
        self.x, self.y = x, y
        self.duration = duration
        self.life = 14.0
        self.anim = random.random() * math.tau
        self.base_y = y
        self.pickup_radius = 20

    def update(self, dt):
        self.life -= dt
        self.anim += dt * 5
        self.y = self.base_y + math.sin(self.anim) * 3

    def draw(self, surf):
        blink = 1.0
        if self.life < 3.0:
            blink = 0.5 + 0.5 * math.sin(self.anim * 3)
        alpha = int(255 * blink)

        hx, hy = int(self.x), int(self.y)
        s = pygame.Surface((40, 44), pygame.SRCALPHA)
        # 光晕
        glow_a = int(110 * blink)
        pygame.draw.circle(s, (100, 220, 255, glow_a), (20, 22), 19)
        pygame.draw.circle(s, (200, 240, 255, int(80 * blink)), (20, 22), 14)
        # 盾牌六边形 + 星
        shield_col = (60, 170, 255, alpha)
        edge_col = (255, 220, 100, alpha)
        # 盾牌形状
        pts = [(20, 2), (34, 8), (34, 22), (20, 38), (6, 22), (6, 8)]
        pygame.draw.polygon(s, shield_col, pts)
        pygame.draw.polygon(s, (30, 130, 220, alpha), pts, 0)
        # 内部高光线条
        pygame.draw.line(s, (180, 230, 255, alpha), (10, 12), (14, 26), 1)
        # 外描边（金色）
        pygame.draw.polygon(s, edge_col, pts, 2)
        # 中间星星
        star_cx, star_cy = 20, 20
        star_pts = []
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            rr = 7 if i % 2 == 0 else 3
            star_pts.append((star_cx + math.cos(ang) * rr, star_cy + math.sin(ang) * rr))
        pygame.draw.polygon(s, edge_col, star_pts)
        pygame.draw.polygon(s, (255, 255, 200, alpha), star_pts, 1)
        # 反射高光
        hl = (255, 255, 255, int(220 * blink))
        pygame.draw.circle(s, hl, (13, 13), 2)
        surf.blit(s, (hx - 20, hy - 22))
        # 秒数小标
        txt = font_sm.render(f"{self.duration:.0f}s", True, (80, 200, 255))
        surf.blit(txt, (hx - txt.get_width() // 2, hy + 20))


class Particle:
    def __init__(self, x, y, vx=0, vy=0, life=0.3, color=WHITE, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= dt

    def draw(self, surf):
        alpha = max(0, int(self.life / self.max_life * 255))
        size = max(1, int(self.size * (self.life / self.max_life)))
        c = (self.color[0], self.color[1], self.color[2], alpha)
        sfc = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(sfc, c, (size * 2, size * 2), size)
        surf.blit(sfc, (self.x - size * 2, self.y - size * 2))


# ========== 主循环 ==========
def main():
    game = Game()
    running = True
    while running:
        dt = 1.0 / FPS
        for event in pygame.event.get():
            game.handle_event(event)
        game.update(dt)
        game.draw()
        # 放大到主画面
        scaled = pygame.transform.scale(canvas, (WIDTH * 2, HEIGHT * 2))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
