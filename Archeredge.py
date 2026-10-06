import pygame
import sys
import math
import random

# Init
pygame.init()
pygame.mixer.init()

W, H = 1100, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("🏹  ArcherEdge")

clock = pygame.time.Clock()
FPS   = 60

# Colours 
SKY_TOP     = (20,  10,  40)
SKY_BOT     = (80,  40, 120)
GRASS_TOP   = (34, 139,  34)
GRASS_BOT   = (20,  80,  20)
GOLD        = (255, 215,   0)
GOLD_LIGHT  = (255, 240, 120)
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
RED         = (220,  30,  30)
ORANGE      = (255, 140,   0)
ACCENT      = (  0, 200, 255)
DARK_PANEL  = ( 10,   5,  30, 200)
ARROW_CLR   = (180, 120,  40)
FEATHER_CLR = (220, 60,  60)

# Official WA archery ring colours (inner → outer, each ring 2 zones)
RING_COLORS = [
    (255, 215,   0),  # 10 – inner gold
    (255, 215,   0),  # 9  – gold
    (220,  20,  60),  # 8  – inner red
    (220,  20,  60),  # 7  – red
    (30,  144, 255),  # 6  – inner blue
    (30,  144, 255),  # 5  – blue
    (  0, 0  ,   0),  # 4  – inner black   (drawn white text)
    ( 30,  30,  30),  # 3  – black
    (240, 240, 240),  # 2  – inner white
    (200, 200, 200),  # 1  – white
]
RING_SCORES = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Fonts
def load_font(size, bold=False):
    for name in ["Georgia", "Palatino Linotype", "DejaVu Serif", "serif"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

def load_worldstar(size):
    """Try Worldstar, fall back to Impact-style bold fonts."""
    for name in ["Worldstar", "Impact", "Arial Black", "Anton", "Haettenschweiler"]:
        try:
            f = pygame.font.SysFont(name, size, bold=True)
            return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_title = load_worldstar(160)   # ARCHEREDGE title
font_huge  = load_font(90, bold=True)
font_big   = load_font(56, bold=True)
font_med   = load_font(32, bold=True)
font_small = load_font(22)
font_tiny  = load_font(16)

# helpers
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))

def draw_gradient_rect(surf, c1, c2, rect, vertical=True):
    x, y, w, h = rect
    for i in range(h if vertical else w):
        t = i / max(h-1, 1) if vertical else i / max(w-1, 1)
        clr = lerp_color(c1, c2, t)
        if vertical:
            pygame.draw.line(surf, clr, (x, y+i), (x+w-1, y+i))
        else:
            pygame.draw.line(surf, clr, (x+i, y), (x+i, y+h-1))

def draw_text_shadow(surf, text, font, color, pos, shadow=(2,2), scolor=(0,0,0)):
    s = font.render(text, True, scolor)
    surf.blit(s, (pos[0]+shadow[0], pos[1]+shadow[1]))
    s = font.render(text, True, color)
    surf.blit(s, pos)

def centered_text(surf, text, font, color, cy, shadow=True):
    s  = font.render(text, True, color)
    x  = (W - s.get_width()) // 2
    if shadow:
        sd = font.render(text, True, BLACK)
        surf.blit(sd, (x+2, cy+2))
    surf.blit(s, (x, cy))

# stars
stars = [(random.randint(0,W), random.randint(0, int(H*0.65)),
          random.uniform(0.3,1.0), random.randint(1,3)) for _ in range(280)]

def draw_bg(surf):
    draw_gradient_rect(surf, SKY_TOP, SKY_BOT, (0, 0, W, H//2+60))
    draw_gradient_rect(surf, GRASS_TOP, GRASS_BOT, (0, H//2+60, W, H//2-60))
    for sx, sy, br, sz in stars:
        c = int(br * 255)
        pygame.draw.circle(surf, (c, c, c), (sx, sy), sz)

# target
TARGET_OUTER_R = 130          # total radius
NUM_RINGS      = 10

def ring_radius(ring_idx):
    """ring_idx 0 = innermost (10pts), 9 = outermost (1pt)"""
    return int(TARGET_OUTER_R * (ring_idx+1) / NUM_RINGS)

def draw_target(surf, cx, cy):
    for i in range(NUM_RINGS-1, -1, -1):
        r   = ring_radius(i)
        clr = RING_COLORS[i]
        pygame.draw.circle(surf, clr, (cx, cy), r)
        pygame.draw.circle(surf, BLACK, (cx, cy), r, 1)

    # cross-hair on X ring
    pygame.draw.line(surf, BLACK, (cx-8, cy), (cx+8, cy), 2)
    pygame.draw.line(surf, BLACK, (cx, cy-8), (cx, cy+8), 2)

    # zone labels (optional small numbers)
    for i, sc in enumerate(RING_SCORES):
        r   = ring_radius(i)
        rp  = ring_radius(i-1) if i > 0 else 0
        mid = (r + rp)//2
        if mid > 6:
            col = WHITE if sc <= 4 else BLACK
            lbl = font_tiny.render(str(sc), True, col)
            surf.blit(lbl, (cx - lbl.get_width()//2, cy - mid - lbl.get_height()//2))

def score_for_hit(dx, dy, cx, cy):
    dist = math.hypot(dx - cx, dy - cy)
    for i, sc in enumerate(RING_SCORES):
        if dist <= ring_radius(i):
            return sc
    return 0

#   Crosshair (free-roaming, follows mouse)

def draw_reticle(surf, mx, my, wobble=0):
    ox = mx + random.randint(-wobble, wobble) if wobble else mx
    oy = my + random.randint(-wobble, wobble) if wobble else my
    r   = 22
    gap = 6
    pygame.draw.circle(surf, RED, (ox, oy), r, 2)
    pygame.draw.line(surf, RED, (ox-r-14, oy), (ox-gap, oy), 2)
    pygame.draw.line(surf, RED, (ox+gap,  oy), (ox+r+14, oy), 2)
    pygame.draw.line(surf, RED, (ox, oy-r-14), (ox, oy-gap), 2)
    pygame.draw.line(surf, RED, (ox, oy+gap),  (ox, oy+r+14), 2)
    pygame.draw.circle(surf, RED, (ox, oy), 3)


#   Arrow (embedded in target after shot)
class Arrow:
    def __init__(self, x, y, score):
        self.x = x
        self.y = y
        self.score = score
        self.angle = random.uniform(-0.3, 0.3)   # slight random tilt
        self.alpha = 255

    def draw(self, surf):
        length = 28
        tip_x = self.x
        tip_y = self.y
        tail_x = tip_x - int(math.sin(self.angle) * length) + int(math.cos(self.angle+math.pi/2)*0)
        tail_y = tip_y + length
        pygame.draw.line(surf, ARROW_CLR, (tip_x, tip_y), (tail_x, tail_y), 3)
        # fletch
        for side in (-1, 1):
            fx = tail_x + side * 5
            fy = tail_y - 8
            pygame.draw.line(surf, FEATHER_CLR, (tail_x, tail_y), (fx, fy), 2)


#   particle effect
class Particle:
    def __init__(self, x, y, color):
        self.x  = float(x)
        self.y  = float(y)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.r  = random.randint(3, 7)
        self.color = color
        self.life  = random.randint(25, 50)
        self.max_life = self.life

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        c = tuple(min(255, v) for v in self.color)
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*c, alpha), (self.r, self.r), self.r)
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))

#   floating score pop
class ScorePop:
    def __init__(self, x, y, score):
        color_map = {10: GOLD, 9: GOLD, 8: RED, 7: RED,
                     6: ACCENT, 5: ACCENT, 4: WHITE, 3: WHITE, 2: WHITE, 1: (180,180,180)}
        self.text  = f"+{score}"
        self.color = color_map.get(score, WHITE)
        self.x = float(x)
        self.y = float(y)
        self.life  = 70
        self.max_life = 70

    def update(self):
        self.y    -= 1.2
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        s = font_med.render(self.text, True, self.color)
        ts = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        ts.fill((0,0,0,0))
        ts.blit(s, (0,0))
        ts.set_alpha(alpha)
        surf.blit(ts, (int(self.x - s.get_width()//2), int(self.y)))

#   Button(arrow icon prefix instead of emoji squares)
class Button:
    def __init__(self, x, y, w, h, text, color=GOLD, hover_color=GOLD_LIGHT, small=False):
        self.rect  = pygame.Rect(x, y, w, h)
        self.text  = text
        self.color = color
        self.hover = hover_color
        self.small = small   # use smaller font so text fits

    def draw(self, surf, mx, my):
        hot = self.rect.collidepoint(mx, my)
        clr = self.hover if hot else self.color
        pygame.draw.rect(surf, clr, self.rect, border_radius=12)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=12)

        f   = font_small if self.small else font_med
        lbl = f.render(self.text, True, BLACK)
        tx  = self.rect.centerx - lbl.get_width()//2
        ty  = self.rect.centery - lbl.get_height()//2
        surf.blit(lbl, (tx, ty))

        # Draw a small arrow icon to the left of the text
        ax  = tx - 22
        ay  = self.rect.centery
        arrow_col = (60, 30, 0) if not hot else (0, 0, 0)
        pygame.draw.line(surf, arrow_col, (ax-10, ay), (ax+4, ay), 3)
        pygame.draw.polygon(surf, arrow_col, [
            (ax+4,  ay),
            (ax-4, ay-6),
            (ax-4, ay+6)
        ])
        return hot

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)

#   Main Menu
def main_menu():
    btn_play   = Button(W//2-140, 360, 280, 55, "PLAY")
    btn_quit   = Button(W//2-140, 440, 280, 55, "QUIT",
                        color=(180,30,30), hover_color=(220,60,60))

    tick   = 0
    while True:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()
        tick  += 1

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_play.clicked(mx, my):    return "play"
                if btn_quit.clicked(mx, my):    pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:    return "play"
                if e.key == pygame.K_ESCAPE:    pygame.quit(); sys.exit()

        # --- draw ---
        draw_bg(screen)

        # decorative target in background
        draw_target(screen, W//2, H//2 + 60)

        # dark overlay
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        screen.blit(ov, (0, 0))

        # ARCHEREDGE title (Worldstar / Impact font)
        title_y = 100 + int(math.sin(tick*0.04)*8)

        # Glow layers
        for glow_r, glow_a in [(6, 40), (3, 80)]:
            gs = font_title.render("ARCHEREDGE", True, GOLD)
            gsurf = pygame.Surface(gs.get_size(), pygame.SRCALPHA)
            gsurf.blit(gs, (0, 0))
            gsurf.set_alpha(glow_a)
            screen.blit(gsurf,
                        (W//2 - gs.get_width()//2 + glow_r,
                         title_y + glow_r))

        # Shadow
        sh = font_title.render("ARCHEREDGE", True, (60, 30, 0))
        screen.blit(sh, (W//2 - sh.get_width()//2 + 4, title_y + 4))
        # Main title
        ts = font_title.render("ARCHEREDGE", True, GOLD)
        screen.blit(ts, (W//2 - ts.get_width()//2, title_y))

        btn_play.draw(screen, mx, my)
        btn_quit.draw(screen, mx, my)

        note = font_tiny.render("Use mouse to aim  •  Hold LMB to charge  •  10 arrows per round", True, (160,160,200))
        screen.blit(note, (W//2 - note.get_width()//2, H-40))

        pygame.mouse.set_visible(False)
        draw_reticle(screen, mx, my)

        pygame.display.flip()


def game_over_screen(total_score, arrows_used, hit_log):
    btn_play  = Button(W//2-230, H-110, 210, 55, "PLAY AGAIN")
    btn_menu  = Button(W//2+20,  H-110, 210, 55, "MAIN MENU")

    grade_map = [(100,"S – PERFECT!",GOLD), (90,"A – EXCELLENT",GOLD_LIGHT),
                 (70,"B – GREAT",(100,220,100)), (50,"C – GOOD",(100,180,255)),
                 (1,"D – KEEP TRYING",(200,120,120)), (0,"F – MISS!",(180,180,180))]
    grade_lbl = "F – MISS!"
    grade_clr = (180,180,180)
    pct = (total_score / (10*10)) * 100
    for threshold, lbl, clr in grade_map:
        if pct >= threshold:
            grade_lbl, grade_clr = lbl, clr
            break

    while True:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_play.clicked(mx, my):  return "play"
                if btn_menu.clicked(mx, my):  return "menu"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:  return "menu"
                if e.key == pygame.K_r:        return "play"

        draw_bg(screen)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))

        centered_text(screen, "ROUND OVER", font_big, WHITE, 50)
        centered_text(screen, grade_lbl, font_big, grade_clr, 120)

        # score panel
        panel = pygame.Surface((420, 200), pygame.SRCALPHA)
        panel.fill((0,0,20,200))
        screen.blit(panel, (W//2-210, 210))
        pygame.draw.rect(screen, GOLD, (W//2-210, 210, 420, 200), 2, border_radius=8)

        lines = [
            (f"Total Score:  {total_score} / 100", GOLD),
            (f"Arrows Shot:  {arrows_used}", WHITE),
            (f"Accuracy:     {pct:.0f}%", grade_clr),
        ]
        for i, (txt, clr) in enumerate(lines):
            lbl = font_med.render(txt, True, clr)
            screen.blit(lbl, (W//2 - lbl.get_width()//2, 230 + i*56))

        # per-arrow breakdown
        if hit_log:
            bx = W//2 - (len(hit_log)*38)//2
            for idx, sc in enumerate(hit_log):
                col = GOLD if sc == 10 else RED if sc >= 7 else ACCENT if sc >= 5 else WHITE
                box = pygame.Rect(bx + idx*38, 440, 32, 32)
                pygame.draw.rect(screen, col, box, border_radius=5)
                pygame.draw.rect(screen, BLACK, box, 1, border_radius=5)
                n = font_small.render(str(sc), True, BLACK if sc >= 5 else WHITE)
                screen.blit(n, (box.centerx - n.get_width()//2,
                                box.centery - n.get_height()//2))

        hint = font_tiny.render("R = play again   ESC = menu", True, (140,140,180))
        screen.blit(hint, (W//2 - hint.get_width()//2, H-45))

        btn_play.draw(screen, mx, my)
        btn_menu.draw(screen, mx, my)
        pygame.mouse.set_visible(False)
        draw_reticle(screen, mx, my)
        pygame.display.flip()


#   Gameplay
TOTAL_ARROWS  = 10
WOBBLE_BASE   = 2      # aim wobble pixels

def play_game():
    pygame.mouse.set_visible(False)

    # Target follows cursor on a parallax-ed "range"
    # The board is drawn at screen centre; the BG shifts slightly
    tx, ty = W//2, H//2 + 20     # target centre (fixed on screen)

    arrows_left = TOTAL_ARROWS
    total_score = 0
    hit_log     = []
    embedded    = []          # Arrow objects stuck in target
    particles   = []
    pops        = []

    charge_start = None        # for power/wobble mechanic
    charging     = False
    charge       = 0.0         # 0..1
    CHARGE_MAX   = 1.5         # seconds to full charge

    # camera offset (parallax)
    cam_ox = cam_oy = 0.0

    tick = 0

    # HUD panel surface
    def draw_hud():
        # Top bar
        hud = pygame.Surface((W, 60), pygame.SRCALPHA)
        hud.fill((0, 0, 15, 180))
        screen.blit(hud, (0, 0))

        # Arrows remaining (as ▼ icons)
        lbl = font_small.render("ARROWS:", True, GOLD)
        screen.blit(lbl, (20, 18))
        for i in range(TOTAL_ARROWS):
            clr = ARROW_CLR if i < arrows_left else (60, 40, 20)
            pygame.draw.polygon(screen, clr, [
                (165 + i*24, 18),
                (157 + i*24, 42),
                (173 + i*24, 42)
            ])

        # Score
        sc_lbl = font_med.render(f"SCORE: {total_score}", True, GOLD)
        screen.blit(sc_lbl, (W//2 - sc_lbl.get_width()//2, 12))

        # Charge bar
        if charging:
            bw = 200
            bx = W - bw - 20
            by = 15
            bh = 28
            pygame.draw.rect(screen, (40, 40, 60), (bx, by, bw, bh), border_radius=6)
            bar_w = int(bw * charge)
            bar_c = lerp_color(ACCENT, RED, charge)
            pygame.draw.rect(screen, bar_c, (bx, by, bar_w, bh), border_radius=6)
            pygame.draw.rect(screen, WHITE, (bx, by, bw, bh), 2, border_radius=6)
            clbl = font_tiny.render("HOLD to charge • RELEASE to shoot", True, WHITE)
            screen.blit(clbl, (bx + bw//2 - clbl.get_width()//2, by + bh + 4))
        else:
            hint = font_tiny.render("Hold LMB to charge, release to shoot", True, (140,140,180))
            screen.blit(hint, (W - hint.get_width() - 10, 38))

    while True:
        dt = clock.tick(FPS) / 1000.0
        tick += 1
        mx, my = pygame.mouse.get_pos()

        # Camera parallax (screen follows cursor gently)
        target_ox = (mx - W//2) * -0.12
        target_oy = (my - H//2) * -0.08
        cam_ox += (target_ox - cam_ox) * 0.08
        cam_oy += (target_oy - cam_oy) * 0.08

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu", total_score, arrows_left, hit_log

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if arrows_left > 0:
                    charging     = True
                    charge_start = pygame.time.get_ticks() / 1000.0
                    charge       = 0.0

            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if charging and arrows_left > 0:
                    charging = False
                    # wobble proportional to charge (steady aim = less wobble)
                    wobble = int(WOBBLE_BASE + charge * 18)
                    hit_x  = mx + random.randint(-wobble, wobble)
                    hit_y  = my + random.randint(-wobble, wobble)

                    sc = score_for_hit(hit_x, hit_y, tx, ty)
                    total_score += sc
                    arrows_left -= 1
                    hit_log.append(sc)

                    embedded.append(Arrow(hit_x, hit_y, sc))

                    # particles
                    ring_clr = RING_COLORS[max(0, min(9, 10-sc))] if sc > 0 else (150,150,150)
                    for _ in range(16):
                        particles.append(Particle(hit_x, hit_y, ring_clr))

                    if sc > 0:
                        pops.append(ScorePop(hit_x, hit_y - 20, sc))

                    charge = 0.0

        # update charge
        if charging:
            now    = pygame.time.get_ticks() / 1000.0
            charge = min(1.0, (now - charge_start) / CHARGE_MAX)

        # update effects
        particles = [p for p in particles if p.life > 0]
        for p in particles: p.update()
        pops = [p for p in pops if p.life > 0]
        for p in pops: p.update()

        # ── Draw ─────────────────────────────────────────────────────────────
        ox, oy = int(cam_ox), int(cam_oy)

        # Background with parallax
        screen.fill(SKY_TOP)
        draw_gradient_rect(screen, SKY_TOP, SKY_BOT, (0, 0, W, H//2+60+oy))
        draw_gradient_rect(screen, GRASS_TOP, GRASS_BOT, (0, H//2+60+oy, W, H))
        for sx, sy, br, sz in stars:
            c = int(br * 255)
            pygame.draw.circle(screen, (c, c, c), (sx+ox//2, sy+oy//2), sz)

        # Target stand
        pygame.draw.rect(screen, (100, 60, 20),
                         (tx+ox-8, ty+oy+TARGET_OUTER_R, 16, 80))
        pygame.draw.rect(screen, (80, 50, 10),
                         (tx+ox-40, ty+oy+TARGET_OUTER_R+75, 80, 10))

        # Target board
        draw_target(screen, tx+ox, ty+oy)

        # Embedded arrows
        for a in embedded:
            # offset arrow position relative to target + parallax
            ax = a.x + ox
            ay = a.y + oy
            length = 28
            tail_x = ax
            tail_y = ay + length
            pygame.draw.line(screen, ARROW_CLR, (ax, ay), (tail_x, tail_y), 3)
            for side in (-1, 1):
                pygame.draw.line(screen, FEATHER_CLR, (tail_x, tail_y),
                                 (tail_x + side*5, tail_y - 8), 2)

        # Particles & pops
        for p in particles: p.draw(screen)
        for p in pops:      p.draw(screen)

        # Wobble for reticle (if charging)
        wob = int(charge * 5) if charging else 0
        draw_reticle(screen, mx, my, wobble=wob)

        draw_hud()

        pygame.display.flip()

        # Round end
        if arrows_left == 0 and not particles:
            return "over", total_score, TOTAL_ARROWS - arrows_left, hit_log

    return "over", total_score, TOTAL_ARROWS, hit_log

# main loop
def main():
    state = "menu"
    while True:
        if state == "menu":
            choice = main_menu()
            if choice == "play":
                state = "play"

        elif state == "play":
            result = play_game()
            outcome   = result[0]
            tot_score = result[1]
            used      = result[2]
            log       = result[3]
            if outcome == "over":
                state = "over"
                _score = tot_score
                _used  = used
                _log   = log
            elif outcome == "menu":
                state = "menu"

        elif state == "over":
            nxt = game_over_screen(_score, _used, _log)
            state = nxt if nxt in ("play","menu") else "menu"

if __name__ == "__main__":
    main()
