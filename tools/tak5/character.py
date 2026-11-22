#!/usr/bin/env python3
"""Tac-Pine v2 - tactical take on the Hak5 pineapple: scaled fruit, angry eyes,
spiked muzzle mask, four antennas, plus tactical kit and a coyote WiFi Pineapple
Pager chest-mounted as his EUD.

character(variant=...) returns an RGBA image (1000x1000 design units * RES).
Variants: 'operator', 'helmet', 'bust', 'head'.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

RES = 2          # output pixels per design unit
SS = 2           # extra supersampling
K = RES * SS
FONTS = os.environ.get("TAK5_FONTS", "fonts")

INK = (16, 14, 12, 255)
GOLD = (236, 186, 52, 255)
GOLD_L = (255, 226, 120, 255)
GOLD_D = (176, 118, 26, 255)
GOLD_DD = (120, 76, 18, 255)
LEAF = (64, 170, 52, 255)
LEAF_L = (130, 220, 80, 255)
LEAF_D = (24, 104, 36, 255)
METAL = (72, 74, 80, 255)
METAL_L = (132, 136, 144, 255)
METAL_D = (38, 40, 44, 255)
ANT = (28, 28, 32, 255)
ANT_L = (86, 88, 96, 255)
COY = (150, 122, 84, 255)        # coyote brown
COY_L = (182, 154, 112, 255)
COY_D = (104, 82, 54, 255)
OD = (84, 92, 56, 255)
OD_D = (58, 64, 38, 255)
OD_L = (118, 126, 82, 255)
SCREEN = (8, 30, 40, 255)
FRIEND = (128, 224, 255, 255)
AMBER = (255, 200, 40, 255)
HOSTILE = (255, 64, 80, 255)
NEON = (64, 255, 140, 255)
WHITE = (250, 250, 246, 255)


def k(v):
    return v * K


def pts(seq):
    return [(k(x), k(y)) for x, y in seq]


def box(x0, y0, x1, y1):
    return [k(x0), k(y0), k(x1), k(y1)]


def bez(p0, p1, p2, p3=None, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        out.append((x, y))
    return out


def thick_line(d, seq, width, fill, outline=INK, ow=6):
    """Line with an ink outline (draw twice) and round caps."""
    if outline:
        d.line(pts(seq), fill=outline, width=int(k(width + ow * 2)), joint="curve")
        for p in (seq[0], seq[-1]):
            r = (width + ow * 2) / 2
            d.ellipse(box(p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=outline)
    d.line(pts(seq), fill=fill, width=int(k(width)), joint="curve")
    for p in (seq[0], seq[-1]):
        r = width / 2
        d.ellipse(box(p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=fill)


# ------------------------------------------------------------------ fruit
CX, CY = 500, 380        # fruit center
RX, RY = 196, 238


def egg_x(y):
    """Half width of the egg-shaped fruit at height y (wider low)."""
    t = (y - CY) / RY
    if abs(t) >= 1:
        return 0
    return RX * math.sqrt(1 - t * t) * (1 + 0.10 * t)


def egg_poly(n=160):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        y = CY - RY * math.cos(a)
        x = CX + egg_x(y) * math.copysign(1, math.sin(a) or 1) if abs(math.sin(a)) > 1e-6 else CX
        out.append((CX + egg_x(y) * (1 if math.sin(a) >= 0 else -1), y))
    return out


def egg_mask(size, grow=0):
    m = Image.new("L", size, 0)
    poly = egg_poly()
    if grow:
        poly = [(CX + (x - CX) * (1 + grow / RX), CY + (y - CY) * (1 + grow / RY)) for x, y in poly]
    ImageDraw.Draw(m).polygon(pts(poly), fill=255)
    return m


def scale_shape(cx, cy, w, h):
    """Pointed-top pineapple scale (tip up, round bottom)."""
    left = bez((cx, cy - h / 2), (cx - w * 0.30, cy - h * 0.18), (cx - w * 0.62, cy + h * 0.28), (cx, cy + h / 2), 16)
    right = bez((cx, cy + h / 2), (cx + w * 0.62, cy + h * 0.28), (cx + w * 0.30, cy - h * 0.18), (cx, cy - h / 2), 16)
    return left + right[1:]


def draw_fruit(img, y_cut=None):
    """Scaled pineapple body. Scales above y_cut only (the mask covers the rest)."""
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.polygon(pts(egg_poly()), fill=GOLD_D)
    sw, sh, dy = 66, 66, 38
    row = 0
    y = CY - RY - 20
    while y < CY + RY + 40:
        off = (sw / 2) if row % 2 else 0
        x = CX - 260 + off
        while x < CX + 260:
            hx = egg_x(min(max(y, CY - RY + 1), CY + RY - 1))
            rel = (x - CX) / (hx + 1e-6) if hx else 2
            if abs(rel) < 1.15:
                # foreshorten toward the edges for roundness
                f = max(0.45, math.cos(min(1.0, abs(rel)) * 1.25))
                w = sw * f
                poly = scale_shape(x, y, w, sh * (0.85 + 0.15 * f))
                shade = 1 - 0.45 * min(1, abs(rel)) ** 2 - 0.2 * max(0, (y - CY) / RY)
                base = tuple(int(c * shade) for c in GOLD[:3]) + (255,)
                d.polygon(pts(poly), fill=base, outline=GOLD_DD, width=int(k(3)))
                # lower shadow + highlight streak
                inner = scale_shape(x, y + sh * 0.18, w * 0.62, sh * 0.42)
                d.polygon(pts(inner), fill=tuple(int(c * shade * 0.78) for c in GOLD[:3]) + (255,))
                d.line(pts([(x - w * 0.1, y - sh * 0.32), (x - w * 0.16, y - sh * 0.02)]), fill=tuple(min(255, int(c * (shade + 0.25))) for c in GOLD_L[:3]) + (230,), width=int(k(4)))
            x += sw
        y += dy
        row += 1
    m = egg_mask((W, H))
    a = ImageChops.multiply(layer.split()[3], m)
    layer.putalpha(a)
    # rim shading
    rim = Image.new("RGBA", (W, H), (60, 30, 0, 0))
    rm = ImageChops.subtract(m, egg_mask((W, H), grow=-26).filter(ImageFilter.GaussianBlur(k(18))))
    rim.putalpha(rm.point(lambda v: int(v * 0.55)))
    layer.alpha_composite(rim)
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon(pts(egg_poly()), outline=INK, width=int(k(8)))


def draw_leaves(img, top_y=None):
    d = ImageDraw.Draw(img, "RGBA")
    base = (CX, CY - RY + 22)
    blades = [
        (-150, -120, -40, 0.95, LEAF_D), (150, -110, 40, 0.95, LEAF_D),
        (-110, -190, -20, 1.0, LEAF), (110, -185, 22, 1.0, LEAF),
        (-60, -230, -10, 1.0, LEAF), (66, -228, 10, 1.0, LEAF),
        (-175, -40, -60, 0.8, LEAF), (178, -48, 60, 0.8, LEAF),
        (0, -250, 0, 1.0, LEAF_L), (-24, -205, -30, 0.9, LEAF_L), (30, -200, 30, 0.9, LEAF_L),
    ]
    for dx, dy, curl, wf, col in blades:
        tip = (base[0] + dx, base[1] + dy)
        ctrl = (base[0] + dx * 0.25 + curl * 0.2, base[1] + dy * 0.75)
        w = 26 * wf
        nx, ny = dy, -dx
        L = math.hypot(nx, ny) or 1
        nx, ny = nx / L * w, ny / L * w
        left = bez((base[0] - nx, base[1] - ny), (ctrl[0] - nx * 0.8, ctrl[1] - ny * 0.8), (tip[0] + curl * 0.3, tip[1]), n=24)
        right = bez((tip[0] + curl * 0.3, tip[1]), (ctrl[0] + nx * 0.8, ctrl[1] + ny * 0.8), (base[0] + nx, base[1] + ny), n=24)
        d.polygon(pts(left + right), fill=col, outline=INK, width=int(k(6)))
        mid = bez(base, ctrl, (tip[0] + curl * 0.3, tip[1]), n=20)
        d.line(pts(mid[2:-3]), fill=tuple(int(c * 0.7) for c in col[:3]) + (255,), width=int(k(4)))


def draw_eyes(img):
    d = ImageDraw.Draw(img, "RGBA")
    for side in (-1, 1):
        ex, ey = CX + side * 78, CY + 62
        rx, ry = 66, 44
        ell = [(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 80)]
        # angry lid: line high at outer edge, low at inner edge
        y_out, y_in = ey - ry * 0.55, ey - ry * 0.05
        def lid(x):
            t = (x - (ex + side * rx)) / (-2 * rx * side)  # 0 at outer, 1 at inner
            return y_out + (y_in - y_out) * t
        poly = [(x, max(y, lid(x))) for x, y in ell]
        d.polygon(pts(poly), fill=WHITE, outline=INK, width=int(k(8)))
        # heavy brow
        bx0, bx1 = ex + side * (rx + 10), ex - side * (rx - 6)
        d.polygon(pts([(bx0, lid(ex + side * rx) - 10), (bx1, lid(ex - side * rx) - 4), (bx1, lid(ex - side * rx) + 12), (bx0, lid(ex + side * rx) + 4)]), fill=INK)
        # square pupil, inner-low
        px = ex - side * 24
        d.rectangle(box(px - 10, ey + 2, px + 10, ey + 24), fill=INK)
        d.rectangle(box(px - 4, ey + 6, px + 1, ey + 11), fill=WHITE)


def draw_mask(img):
    """Spiked muzzle mask covering the lower fruit."""
    W, H = img.size
    top = CY + 112
    poly = []
    for x in np.linspace(CX - egg_x(top) - 10, CX + egg_x(top) + 10, 40):
        u = (x - CX) / (egg_x(top) + 10)
        poly.append((x, top + 16 * u * u - 8 * (1 - u * u)))
    yb = np.linspace(top, CY + RY + 6, 30)
    right = [(CX + egg_x(min(y, CY + RY - 1)) + 10, y) for y in yb]
    bottom = [(CX + egg_x(CY + RY - 1) * 0.0, CY + RY + 8)]
    left = [(CX - egg_x(min(y, CY + RY - 1)) - 10, y) for y in yb[::-1]]
    shape = poly + right + bottom + left
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L, "RGBA")
    d.polygon(pts(shape), fill=METAL)
    # cylindrical shading
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh, "RGBA")
    sd.ellipse(box(CX - 140, top + 6, CX + 40, top + 70), fill=(255, 255, 255, 50))
    sh = sh.filter(ImageFilter.GaussianBlur(k(14)))
    mm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mm).polygon(pts(shape), fill=255)
    sh.putalpha(ImageChops.multiply(sh.split()[3], mm))
    L.alpha_composite(sh)
    d = ImageDraw.Draw(L, "RGBA")
    # grille teeth
    gx0, gx1, gy0, gy1 = CX - 92, CX + 92, top + 50, top + 104
    d.rounded_rectangle(box(gx0, gy0, gx1, gy1), radius=k(14), fill=METAL_D, outline=INK, width=int(k(6)))
    n = 9
    for i in range(n):
        x = gx0 + 14 + i * (gx1 - gx0 - 28) / (n - 1)
        d.rounded_rectangle(box(x - 6, gy0 + 8, x + 6, gy1 - 8), radius=k(4), fill=METAL_L, outline=INK, width=int(k(3)))
    d.line(pts([(gx0 + 6, (gy0 + gy1) / 2), (gx1 - 6, (gy0 + gy1) / 2)]), fill=INK, width=int(k(5)))
    # rivets along top band
    for x in np.linspace(CX - 150, CX + 150, 9):
        y = top + 26 + 10 * ((x - CX) / 150) ** 2
        d.ellipse(box(x - 6, y - 6, x + 6, y + 6), fill=METAL_L, outline=INK, width=int(k(2)))
    # ethernet port (Hak5 nod)
    px, py = CX + 128, top + 92
    d.rectangle(box(px - 22, py - 14, px + 22, py + 14), fill=INK)
    d.rectangle(box(px - 16, py - 8, px + 16, py + 8), fill=METAL_D)
    d.rectangle(box(px - 8, py + 2, px + 8, py + 10), fill=INK)
    d.polygon(pts(shape), outline=INK, width=int(k(8)))
    img.alpha_composite(L)
    # spikes along the top edge
    d = ImageDraw.Draw(img, "RGBA")
    for i, x in enumerate(np.linspace(CX - egg_x(top) + 6, CX + egg_x(top) - 6, 9)):
        u = (x - CX) / egg_x(top)
        y = top + 16 * u * u - 8 * (1 - u * u)
        ang = math.radians(-90 + 55 * u)
        L = 34 if i % 2 == 0 else 24
        b = 13
        tip = (x + L * math.cos(ang), y + L * math.sin(ang))
        nx, ny = -math.sin(ang) * b, math.cos(ang) * b
        d.polygon(pts([(x + nx, y + ny), tip, (x - nx, y - ny)]), fill=METAL_L, outline=INK, width=int(k(4)))
    # side spikes
    for side in (-1, 1):
        for j, y in enumerate((top + 40, top + 80, top + 118)):
            x = CX + side * (egg_x(min(y, CY + RY - 1)) + 8)
            tip = (x + side * 30, y + 6)
            d.polygon(pts([(x, y - 12), tip, (x, y + 12)]), fill=METAL_L, outline=INK, width=int(k(4)))


def draw_antennas(img, upper=True, lower=True):
    d = ImageDraw.Draw(img, "RGBA")
    specs = []
    if upper:
        specs += [(-1, CY - 70, (-60, -24), (-34, -220)), (1, CY - 70, (60, -24), (34, -220))]
    if lower:
        specs += [(-1, CY + 40, (-60, 10), (-150, 120)), (1, CY + 40, (60, 10), (150, 120))]
    for side, y, elbow, shaft in specs:
        x = CX + side * egg_x(y) - side * 6
        e = (x + elbow[0], y + elbow[1])
        tip = (e[0] + shaft[0], e[1] + shaft[1])
        # connector stub
        thick_line(d, [(x, y), e], 26, ANT, ow=6)
        # elbow joint
        d.ellipse(box(e[0] - 20, e[1] - 20, e[0] + 20, e[1] + 20), fill=ANT, outline=INK, width=int(k(6)))
        # shaft, tapering, with bands
        thick_line(d, [e, tip], 22, ANT, ow=6)
        for t in (0.28, 0.55):
            bx, by = e[0] + shaft[0] * t, e[1] + shaft[1] * t
            L = math.hypot(*shaft)
            nx, ny = -shaft[1] / L * 15, shaft[0] / L * 15
            d.line(pts([(bx - nx, by - ny), (bx + nx, by + ny)]), fill=ANT_L, width=int(k(5)))
        hl = [(e[0] + shaft[0] * 0.08 - side * 4, e[1] + shaft[1] * 0.08), (e[0] + shaft[0] * 0.9 - side * 4, e[1] + shaft[1] * 0.9)]
        d.line(pts(hl), fill=ANT_L, width=int(k(4)))


def draw_headset(img):
    d = ImageDraw.Draw(img, "RGBA")
    # band over the crown
    band = bez((CX - 196, CY - 10), (CX - 210, CY - 300), (CX + 210, CY - 300), (CX + 196, CY - 10), 50)
    thick_line(d, band, 18, OD_D, ow=6)
    for side in (-1, 1):
        x = CX + side * (egg_x(CY - 6) + 2)
        d.rounded_rectangle(box(x - 34, CY - 66, x + 34, CY + 54), radius=k(26), fill=OD, outline=INK, width=int(k(7)))
        d.rounded_rectangle(box(x - 18, CY - 44, x + 18, CY + 32), radius=k(14), fill=OD_D)
        d.ellipse(box(x - 8, CY - 18, x + 8, CY - 2), fill=AMBER)
    # boom mic to the mask
    x = CX - egg_x(CY) - 2
    boom = bez((x, CY + 30), (x - 10, CY + 150), (CX - 160, CY + 175), (CX - 112, CY + 162), 30)
    thick_line(d, boom, 10, METAL_D, ow=5)
    d.ellipse(box(CX - 126, CY + 148, CX - 96, CY + 178), fill=INK)


def draw_helmet(img):
    d = ImageDraw.Draw(img, "RGBA")
    # high-cut helmet riding on the upper fruit; leaves erupt from the top
    shell = box(CX - 214, CY - 252, CX + 214, CY + 70)
    d.chord(shell, 180, 360, fill=OD, outline=INK, width=int(k(8)))
    d.rectangle(box(CX - 210, CY - 98, CX + 210, CY - 72), fill=OD_D, outline=INK, width=int(k(6)))
    for side in (-1, 1):  # ARC rails
        x = CX + side * 178
        d.rounded_rectangle(box(x - 22, CY - 140, x + 22, CY - 76), radius=k(6), fill=OD_D, outline=INK, width=int(k(5)))
    # NVG shroud + mount arm + tubes (flipped up)
    d.rounded_rectangle(box(CX - 40, CY - 210, CX + 40, CY - 150), radius=k(10), fill=METAL_D, outline=INK, width=int(k(6)))
    d.rounded_rectangle(box(CX - 70, CY - 300, CX + 70, CY - 222), radius=k(18), fill=METAL, outline=INK, width=int(k(6)))
    for side in (-1, 1):
        d.ellipse(box(CX + side * 34 - 26, CY - 290, CX + side * 34 + 26, CY - 238), fill=METAL_D, outline=INK, width=int(k(5)))
        d.ellipse(box(CX + side * 34 - 12, CY - 276, CX + side * 34 + 12, CY - 252), fill=(40, 120, 70, 255))
    # IR strobe + velcro
    d.rounded_rectangle(box(CX + 76, CY - 200, CX + 132, CY - 160), radius=k(6), fill=COY, outline=INK, width=int(k(4)))
    d.ellipse(box(CX - 140, CY - 190, CX - 108, CY - 158), fill=METAL_D, outline=INK, width=int(k(4)))
    d.ellipse(box(CX - 131, CY - 181, CX - 117, CY - 167), fill=AMBER)


def pager(w=200, h=136, color=COY, color_l=COY_L, color_d=COY_D, angle=0):
    """WiFi Pineapple Pager style device, chest-mounted as an EUD."""
    s = K
    img = Image.new("RGBA", (int((w + 40) * s), int((h + 40) * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    o = 20
    b = lambda x0, y0, x1, y1: [(x0 + o) * s, (y0 + o) * s, (x1 + o) * s, (y1 + o) * s]
    d.rounded_rectangle(b(0, 0, w, h), radius=22 * s, fill=color, outline=INK, width=int(7 * s))
    d.rounded_rectangle(b(6, 6, w - 6, h * 0.5), radius=16 * s, fill=color_l)
    # screen bezel + screen
    sx0, sy0, sx1, sy1 = 18, 14, w - 18, h * 0.58
    d.rounded_rectangle(b(sx0 - 6, sy0 - 6, sx1 + 6, sy1 + 6), radius=10 * s, fill=(30, 26, 22, 255))
    d.rectangle(b(sx0, sy0, sx1, sy1), fill=SCREEN)
    for gx in np.arange(sx0, sx1, 16):
        d.line([((gx + o) * s, (sy0 + o) * s), ((gx + o) * s, (sy1 + o) * s)], fill=(20, 80, 96, 255), width=int(1.5 * s))
    for gy in np.arange(sy0, sy1, 16):
        d.line([((sx0 + o) * s, (gy + o) * s), ((sx1 + o) * s, (gy + o) * s)], fill=(20, 80, 96, 255), width=int(1.5 * s))
    cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2 + 2
    d.polygon([((cx + o) * s, (cy - 14 + o) * s), ((cx + 10 + o) * s, (cy + 10 + o) * s), ((cx + o) * s, (cy + 5 + o) * s), ((cx - 10 + o) * s, (cy + 10 + o) * s)], fill=AMBER)
    d.rectangle(b(sx0 + 12, sy0 + 10, sx0 + 30, sy0 + 22), outline=FRIEND, width=int(2.5 * s))
    q = (sx1 - 26, sy1 - 18)
    d.polygon([((q[0] + o) * s, (q[1] - 9 + o) * s), ((q[0] + 9 + o) * s, (q[1] + o) * s), ((q[0] + o) * s, (q[1] + 9 + o) * s), ((q[0] - 9 + o) * s, (q[1] + o) * s)], outline=HOSTILE, width=int(2.5 * s))
    d.rectangle(b(sx0, sy0, sx1, sy0 + 7), fill=(10, 50, 60, 255))
    # buttons: two pills left, d-pad right
    by = h * 0.80
    for i in range(2):
        d.rounded_rectangle(b(22 + i * 34, by - 7, 48 + i * 34, by + 7), radius=7 * s, fill=color_d, outline=INK, width=int(3 * s))
    dx = w - 50
    d.ellipse(b(dx - 24, by - 24, dx + 24, by + 24), fill=color_d, outline=INK, width=int(3 * s))
    for (ax, ay) in ((0, -13), (13, 0), (0, 13), (-13, 0)):
        d.ellipse(b(dx + ax - 5, by + ay - 5, dx + ax + 5, by + ay + 5), fill=color_l)
    d.ellipse(b(dx - 6, by - 6, dx + 6, by + 6), fill=(255, 200, 40, 255))
    # lanyard loop / antenna nub
    d.rounded_rectangle(b(w - 40, -10, w - 20, 4), radius=4 * s, fill=color_d, outline=INK, width=int(3 * s))
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    return img


def draw_body(img, carrier=COY, carrier_d=COY_D, shirt=OD, manpack=True):
    d = ImageDraw.Draw(img, "RGBA")
    if manpack:
        # manpack radio on the back with whip
        thick_line(d, [(CX + 200, 600), (CX + 258, 330), (CX + 330, 120)], 9, METAL_D, ow=5)
        d.ellipse(box(CX + 318, 106, CX + 344, 132), fill=AMBER, outline=INK, width=int(k(4)))
        for i, r in enumerate((34, 58, 82)):
            d.arc(box(CX + 331 - r, 119 - r, CX + 331 + r, 119 + r), 280, 10, fill=NEON[:3] + (230 - 60 * i,), width=int(k(7)))
        d.rounded_rectangle(box(CX + 150, 590, CX + 300, 830), radius=k(24), fill=(56, 60, 58, 255), outline=INK, width=int(k(7)))
        d.rounded_rectangle(box(CX + 200, 612, CX + 286, 668), radius=k(8), fill=(34, 38, 37, 255), outline=INK, width=int(k(4)))
        for i in range(3):
            d.rectangle(box(CX + 210, 624 + i * 14, CX + 270 - i * 14, 632 + i * 14), fill=NEON)
    # torso / shirt
    d.rounded_rectangle(box(CX - 196, 600, CX + 196, 960), radius=k(70), fill=shirt, outline=INK, width=int(k(8)))
    # arms
    for side in (-1, 1):
        thick_line(d, [(CX + side * 170, 650), (CX + side * 250, 760), (CX + side * 226, 880)], 52, shirt, ow=8)
    # plate carrier
    d.rounded_rectangle(box(CX - 160, 640, CX + 160, 955), radius=k(36), fill=carrier, outline=INK, width=int(k(8)))
    for side in (-1, 1):
        d.rounded_rectangle(box(CX + side * 120 - 26, 596, CX + side * 120 + 26, 668), radius=k(10), fill=carrier_d, outline=INK, width=int(k(6)))
    # MOLLE rows
    for i in range(4):
        y = 870 + i * 20
        d.rectangle(box(CX - 140, y, CX + 140, y + 8), fill=carrier_d)
    # admin/mag pouches
    for i in range(3):
        x = CX - 132 + i * 92
        d.rounded_rectangle(box(x, 846, x + 80, 950), radius=k(10), fill=carrier_d, outline=INK, width=int(k(5)))
        d.rectangle(box(x + 8, 856, x + 72, 872), fill=carrier)
    # hands
    for side in (-1, 1):
        d.ellipse(box(CX + side * 226 - 32, 852, CX + side * 226 + 32, 916), fill=(48, 44, 40, 255), outline=INK, width=int(k(6)))


def draw_hood(img):
    d = ImageDraw.Draw(img, "RGBA")
    hood = bez((CX - 250, 960), (CX - 330, 300), (CX - 180, 70), (CX, 90), 40) + bez((CX, 90), (CX + 180, 70), (CX + 330, 300), (CX + 250, 960), 40)
    d.polygon(pts(hood), fill=(44, 46, 50, 255), outline=INK, width=int(k(8)))
    inner = bez((CX - 220, 700), (CX - 270, 330), (CX - 150, 130), (CX, 140), 40) + bez((CX, 140), (CX + 150, 130), (CX + 270, 330), (CX + 220, 700), 40)
    d.polygon(pts(inner), fill=(20, 22, 24, 255))


def draw_hoodie_body(img):
    d = ImageDraw.Draw(img, "RGBA")
    hood_c = (44, 46, 50, 255)
    d.rounded_rectangle(box(CX - 210, 600, CX + 210, 960), radius=k(70), fill=hood_c, outline=INK, width=int(k(8)))
    for side in (-1, 1):
        thick_line(d, [(CX + side * 180, 650), (CX + side * 262, 760), (CX + side * 232, 880)], 56, hood_c, ow=8)
    # drawstrings
    for side in (-1, 1):
        d.line(pts([(CX + side * 40, 640), (CX + side * 46, 720)]), fill=(200, 200, 196, 255), width=int(k(5)))
    # kangaroo pocket
    d.rounded_rectangle(box(CX - 120, 860, CX + 120, 960), radius=k(20), outline=INK, width=int(k(5)))
    # coyote chest harness straps
    for side in (-1, 1):
        thick_line(d, [(CX + side * 136, 604), (CX - side * 50, 850)], 24, COY, ow=5)
    thick_line(d, [(CX - 170, 830), (CX + 170, 830)], 22, COY, ow=5)
    for side in (-1, 1):
        d.ellipse(box(CX + side * 232 - 32, 852, CX + side * 232 + 32, 916), fill=(30, 30, 32, 255), outline=INK, width=int(k(6)))


def draw_ptt(img):
    d = ImageDraw.Draw(img, "RGBA")
    # coiled cord from carrier strap to handset in the left hand
    seq = []
    x0, y0, x1, y1 = CX - 120, 660, CX - 236, 846
    for i in range(241):
        u = i / 240
        bx, by = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        a = u * 2 * math.pi * 8
        seq.append((bx + 10 * math.cos(a), by + 10 * math.sin(a)))
    d.line(pts(seq), fill=INK, width=int(k(5)))
    d.rounded_rectangle(box(CX - 270, 818, CX - 200, 930), radius=k(14), fill=(56, 60, 58, 255), outline=INK, width=int(k(7)))
    d.rectangle(box(CX - 256, 836, CX - 214, 856), fill=AMBER)


def draw_yagi(img):
    """Little handheld yagi in the right hand (fox-hunt / recon)."""
    d = ImageDraw.Draw(img, "RGBA")
    hx, hy = CX + 226, 884
    boom_end = (hx + 150, hy - 150)
    thick_line(d, [(hx, hy), boom_end], 12, METAL_D, ow=5)
    for t in np.linspace(0.25, 1.0, 5):
        bx, by = hx + (boom_end[0] - hx) * t, hy + (boom_end[1] - hy) * t
        L = 46 - 18 * t
        d.line(pts([(bx - L * 0.7, by - L * 0.7), (bx + L * 0.7, by + L * 0.7)]), fill=INK, width=int(k(12)))
        d.line(pts([(bx - L * 0.7, by - L * 0.7), (bx + L * 0.7, by + L * 0.7)]), fill=METAL_L, width=int(k(6)))


def character(variant="operator", carrier="coyote"):
    W = H = 1000 * K
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cmap = {
        "coyote": (COY, COY_D, OD),
        "od": (OD, OD_D, (110, 98, 72, 255)),
        "black": ((48, 50, 52, 255), (30, 32, 34, 255), (70, 76, 60, 255)),
    }
    car, car_d, shirt = cmap[carrier]
    body = variant in ("operator", "helmet", "bust")
    if variant == "hacker":
        draw_hood(img)
        draw_hoodie_body(img)
    if body:
        draw_body(img, car, car_d, shirt, manpack=variant != "bust")
    draw_antennas(img, upper=variant != "helmet", lower=True)
    if variant == "helmet":
        draw_leaves(img)
        draw_fruit(img)
        draw_helmet(img)
        draw_antennas(img, upper=False, lower=False)
    else:
        draw_leaves(img)
        draw_fruit(img)
    draw_eyes(img)
    draw_mask(img)
    if variant in ("operator", "helmet", "bust", "hacker"):
        draw_headset(img) if variant not in ("helmet", "hacker") else None
        # the Pager EUD on the chest (MOLLE chest mount)
        p = pager(208, 140)
        img.alpha_composite(p, (int(k(CX - 124)), int(k(670))))
        d = ImageDraw.Draw(img, "RGBA")
        for side in (-1, 1):  # mount straps
            d.rectangle(box(CX + side * 70 - 12, 812, CX + side * 70 + 12, 846), fill=COY_D, outline=INK, width=int(k(4)))
    if variant in ("operator", "helmet", "hacker"):
        draw_yagi(img)
    if variant in ("operator", "helmet"):
        draw_ptt(img)
    if variant == "helmet":
        draw_headset_cups_on_helmet(img)
    out = img.resize((1000 * RES, 1000 * RES), Image.LANCZOS)
    return out.crop(out.getbbox())


def draw_headset_cups_on_helmet(img):
    d = ImageDraw.Draw(img, "RGBA")
    for side in (-1, 1):
        x = CX + side * (egg_x(CY - 30) + 6)
        d.rounded_rectangle(box(x - 34, CY - 80, x + 34, CY + 40), radius=k(26), fill=OD, outline=INK, width=int(k(7)))
        d.rounded_rectangle(box(x - 18, CY - 58, x + 18, CY + 18), radius=k(14), fill=OD_D)
        thick_line(d, [(x, CY - 80), (x - side * 4, CY - 112)], 12, OD_D, ow=5)
    x = CX - egg_x(CY) - 6
    boom = bez((x, CY + 20), (x - 10, CY + 150), (CX - 160, CY + 175), (CX - 112, CY + 162), 30)
    thick_line(d, boom, 10, METAL_D, ow=5)
    d.ellipse(box(CX - 126, CY + 148, CX - 96, CY + 178), fill=INK)


if __name__ == "__main__":
    import sys
    v = sys.argv[1] if len(sys.argv) > 1 else "operator"
    character(v).save("char_%s.png" % v)
