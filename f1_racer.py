import math
import random
import sys

import pygame

pygame.init()

# Tiny NES-like resolution scaled up for chunky retro pixels
GAME_W, GAME_H = 160, 240
SCALE  = 3
WIN_W  = GAME_W * SCALE
WIN_H  = GAME_H * SCALE

screen = pygame.display.set_mode((WIN_W, WIN_H))
canvas = pygame.Surface((GAME_W, GAME_H))
pygame.display.set_caption("F1 RACER")
clock  = pygame.time.Clock()
FPS    = 30

# ── Retro palette ─────────────────────────────────────────────────────────────
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (210,  35,  35)
YELLOW = (240, 200,   0)
GRASS  = ( 30, 130,  30)
ROAD   = ( 65,  65,  65)
KERB_R = (210,  30,  30)
KERB_W = (240, 240, 240)
BLUE   = ( 40,  80, 200)
ORANGE = (220, 100,   0)
TEAL   = (  0, 160, 160)
PURPLE = (140,  40, 200)
LTGRAY = (160, 160, 160)

# ── Road geometry ─────────────────────────────────────────────────────────────
ROAD_L  = 28
ROAD_R  = 132
LANE_W  = (ROAD_R - ROAD_L) // 3
KERB_W_ = 7

def lane_cx(n):
    return ROAD_L + n * LANE_W + LANE_W // 2


# ── Draw a pixel F1 car centred at (x, y) ─────────────────────────────────────
def draw_car(s, cx, cy, color, flip=False):
    x, y = int(cx) - 5, int(cy) - 8
    # wheels
    for wx, wy in [(x - 2, y + 2), (x + 9, y + 2), (x - 2, y + 9), (x + 9, y + 9)]:
        pygame.draw.rect(s, BLACK,  (wx, wy, 3, 5))
        pygame.draw.rect(s, LTGRAY, (wx, wy + 1, 3, 3))
    # body
    pygame.draw.rect(s, color, (x + 1, y + 1,  9, 14))
    # cockpit / visor
    pygame.draw.rect(s, BLACK, (x + 3, y + 4,  5,  6))
    pygame.draw.rect(s, (80, 180, 255), (x + 4, y + 5, 3, 4))  # visor glint
    # front wing  (top when going down)
    wing_y = y if not flip else y + 14
    pygame.draw.rect(s, color,  (x - 1, wing_y,    13, 2))
    pygame.draw.rect(s, BLACK,  (x,     wing_y + 1,  11, 1))
    # rear wing
    rwing_y = y + 14 if not flip else y
    pygame.draw.rect(s, color,  (x - 1, rwing_y,    13, 2))
    pygame.draw.rect(s, BLACK,  (x,     rwing_y,     11, 1))


# ── Scrolling road ────────────────────────────────────────────────────────────
def draw_road(s, sc):
    s.fill(GRASS)
    pygame.draw.rect(s, ROAD, (ROAD_L, 0, ROAD_R - ROAD_L, GAME_H))

    # alternating kerb stripes on both sides
    seg = 14
    cycle = seg * 2
    for i in range(GAME_H // seg + 3):
        ky  = i * seg - int(sc) % cycle
        col = KERB_R if i % 2 == 0 else KERB_W
        pygame.draw.rect(s, col, (ROAD_L - KERB_W_, ky, KERB_W_, seg))
        pygame.draw.rect(s, col, (ROAD_R,            ky, KERB_W_, seg))

    # lane dividers — dashed white
    for lx in [ROAD_L + LANE_W, ROAD_L + LANE_W * 2]:
        dash_cycle = 20
        y = -(int(sc) % dash_cycle)
        while y < GAME_H:
            pygame.draw.rect(s, WHITE, (lx - 1, y, 2, 10))
            y += dash_cycle


# ── Title screen ──────────────────────────────────────────────────────────────
def title_screen():
    font_lg = pygame.font.SysFont(None, 26)
    font_sm = pygame.font.SysFont(None, 14)
    tick = 0
    sc   = 0.0
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
        sc += 3
        draw_road(canvas, sc)

        # dark overlay
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        canvas.blit(overlay, (0, 0))

        # title box
        bx, by, bw, bh = 12, GAME_H // 2 - 44, GAME_W - 24, 88
        pygame.draw.rect(canvas, BLACK,       (bx, by, bw, bh))
        pygame.draw.rect(canvas, RED,         (bx, by, bw, bh), 2)
        pygame.draw.rect(canvas, YELLOW,      (bx + 2, by + 2, bw - 4, bh - 4), 1)

        draw_car(canvas, GAME_W // 2 - 22, by + 14, RED)
        draw_car(canvas, GAME_W // 2 + 12, by + 14, BLUE)

        t1 = font_lg.render("F1  RACER", True, YELLOW)
        t2 = font_sm.render("ARROW KEYS  /  WASD", True, WHITE)
        blink = YELLOW if (tick // 15) % 2 == 0 else (100, 80, 0)
        t3 = font_sm.render("PRESS SPACE TO START", True, blink)

        canvas.blit(t1, (GAME_W // 2 - t1.get_width() // 2, by + 28))
        canvas.blit(t2, (GAME_W // 2 - t2.get_width() // 2, by + 50))
        canvas.blit(t3, (GAME_W // 2 - t3.get_width() // 2, by + 66))

        screen.blit(pygame.transform.scale(canvas, (WIN_W, WIN_H)), (0, 0))
        pygame.display.flip()
        tick += 1


# ── Main game loop ────────────────────────────────────────────────────────────
def play():
    """Run one race. Returns "retry" or "menu" once the player chooses after a crash."""
    font_sm = pygame.font.SysFont(None, 14)
    font_md = pygame.font.SysFont(None, 22)

    px = float(GAME_W // 2)
    py = float(GAME_H - 28)

    enemies      = []  # each: [x, y, color]
    score        = 0
    frame        = 0
    scroll       = 0.0
    e_speed      = 2.5
    p_speed      = 2
    alive        = True
    boom_timer   = 0
    boom_frame   = 0
    crash_x      = 0
    crash_y      = 0

    ENEMY_COLORS = [BLUE, YELLOW, ORANGE, TEAL, PURPLE, WHITE]
    CAR_HW, CAR_HH = 8, 8  # hit-box half-width / half-height

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and not alive and boom_timer == 0:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "menu"

        # ── Update ────────────────────────────────────────────────────────────
        if alive:
            frame  += 1
            score  += 1

            e_speed     = 2.5 + (score // 250) * 0.35
            p_speed     = 2   + (score // 500)
            spawn_every = max(20, 55 - (score // 120) * 3)

            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: px -= p_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: px += p_speed
            px = max(ROAD_L + 7.0, min(ROAD_R - 7.0, px))

            if frame % spawn_every == 0:
                col = random.choice(ENEMY_COLORS)
                lane = random.randint(0, 2)
                enemies.append([float(lane_cx(lane)), -18.0, col])

            scroll += e_speed

            for e in enemies:
                e[1] += e_speed

            # collision
            for e in enemies:
                if abs(e[0] - px) < CAR_HW and abs(e[1] - py) < CAR_HH * 2:
                    alive      = False
                    boom_timer = 35
                    crash_x, crash_y = px, py
                    break

            enemies = [e for e in enemies if e[1] < GAME_H + 24]

        elif boom_timer > 0:
            boom_timer  -= 1
            boom_frame  += 1

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_road(canvas, scroll)

        for e in enemies:
            draw_car(canvas, e[0], e[1], e[2], flip=True)

        if alive:
            draw_car(canvas, px, py, RED)
        elif boom_timer > 0:
            # explosion: expanding coloured squares
            for i in range(8):
                angle  = i / 8.0
                ex = crash_x + math.cos(angle * 6.28) * (boom_frame * 1.5)
                ey = crash_y + math.sin(angle * 6.28) * (boom_frame * 1.2)
                sz = max(1, 5 - boom_frame // 8)
                col = [RED, YELLOW, ORANGE, WHITE][i % 4]
                pygame.draw.rect(canvas, col, (int(ex) - sz, int(ey) - sz, sz * 2, sz * 2))

        # HUD bar
        pygame.draw.rect(canvas, BLACK, (ROAD_L, 0, ROAD_R - ROAD_L, 12))
        hud = font_sm.render(f"SCORE {score:05d}   SPD {int(e_speed * 8):02d}", True, YELLOW)
        canvas.blit(hud, (ROAD_L + 2, 2))

        # Game over overlay
        if not alive and boom_timer == 0:
            ov = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            canvas.blit(ov, (0, 0))

            bx, by, bw, bh = 15, GAME_H // 2 - 38, GAME_W - 30, 76
            pygame.draw.rect(canvas, BLACK, (bx, by, bw, bh))
            pygame.draw.rect(canvas, RED,   (bx, by, bw, bh), 2)

            t1 = font_md.render("GAME OVER",         True, RED)
            t2 = font_sm.render(f"SCORE  {score:05d}", True, WHITE)
            t3 = font_sm.render("R = RETRY   Q = MENU", True, YELLOW)

            canvas.blit(t1, (GAME_W // 2 - t1.get_width() // 2, by + 8))
            canvas.blit(t2, (GAME_W // 2 - t2.get_width() // 2, by + 30))
            canvas.blit(t3, (GAME_W // 2 - t3.get_width() // 2, by + 48))

        screen.blit(pygame.transform.scale(canvas, (WIN_W, WIN_H)), (0, 0))
        pygame.display.flip()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    title_screen()
    while True:
        if play() == "menu":
            title_screen()
