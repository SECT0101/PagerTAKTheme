#!/usr/bin/env python3
"""Tac-Pine 3D-ish render (character B: helmet + NVGs, coyote Pager EUD on chest).

Same design as character.py, but every part is drawn on its own layer and lit:
ellipsoid shading for the fruit / helmet / mask, bevel shading for gear,
per-scale pillow shading, specular metal, and soft contact shadows.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import character as C
from character import (k, pts, box, bez, thick_line, egg_x, egg_poly, egg_mask, scale_shape,
                       CX, CY, RX, RY, K, RES, INK, GOLD, GOLD_L, GOLD_D, GOLD_DD, LEAF, LEAF_L, LEAF_D,
                       METAL, METAL_L, METAL_D, ANT, ANT_L, COY, COY_L, COY_D, OD, OD_D, OD_L, AMBER, NEON, WHITE)
from shade import shade_layer, shade_ellipsoid, drop_shadow, gradient_fill

SZ = 1000 * K


def new():
    return Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))


def put(img, layer, shadow=True, off=(5, 8), blur=7, alpha=0.42):
    if shadow:
        drop_shadow(img, layer, (int(k(off[0])), int(k(off[1]))), blur=k(blur), alpha=alpha)
    img.alpha_composite(layer)


# ------------------------------------------------------------------ fruit
_sprites = {}


def scale_sprite(w, h):
    key = (round(w), round(h))
    if key in _sprites:
        return _sprites[key]
    W, H = int(k(w + 8)), int(k(h + 8))
    m = Image.new("L", (W, H), 0)
    poly = [(k(x), k(y)) for x, y in scale_shape((w + 8) / 2, (h + 8) / 2, w, h)]
    ImageDraw.Draw(m).polygon(poly, fill=255)
    spr = gradient_fill(m, (250, 214, 96), (196, 132, 30))
    # puffy 3D scale
    spr = shade_layer(spr, radius=k(w) / 4, depth=2.2, ambient=0.62, diffuse=0.6, spec=0.18, shin=10, spec_col=(255, 236, 170))
    d = ImageDraw.Draw(spr, "RGBA")
    d.polygon(poly, outline=(110, 66, 14, 255), width=int(k(2.5)))
    # dark crease at the base where the next row tucks under
    d.arc([k(w * 0.18 + 4), k(h * 0.62 + 4), k(w * 0.82 + 4), k(h * 1.02 + 4)], 20, 160, fill=(96, 56, 10, 200), width=int(k(3)))
    _sprites[key] = spr
    return spr


def fruit_layer():
    L = new()
    d = ImageDraw.Draw(L, "RGBA")
    d.polygon(pts(egg_poly()), fill=(150, 96, 22, 255))
    sw, sh, dy = 66, 66, 38
    row, y = 0, CY - RY - 20
    while y < CY + RY + 40:
        off = (sw / 2) if row % 2 else 0
        x = CX - 260 + off
        while x < CX + 260:
            hx = egg_x(min(max(y, CY - RY + 1), CY + RY - 1))
            rel = (x - CX) / (hx + 1e-6) if hx else 2
            if abs(rel) < 1.15:
                f = max(0.45, math.cos(min(1.0, abs(rel)) * 1.25))
                spr = scale_sprite(sw * f * 1.22, sh * (0.95 + 0.15 * f))
                L.alpha_composite(spr, (int(k(x) - spr.size[0] / 2), int(k(y) - spr.size[1] / 2)))
            x += sw
        y += dy
        row += 1
    m = egg_mask(L.size)
    L.putalpha(ImageChops.multiply(L.split()[3], m))
    L = shade_ellipsoid(L, k(CX - 10), k(CY - 20), k(RX + 10), k(RY + 20), ambient=0.48, diffuse=0.72, spec=0.25, shin=10, rim=0.35)
    # deep rim occlusion
    occ = Image.new("RGBA", L.size, (40, 18, 0, 0))
    rm = ImageChops.subtract(m, egg_mask(L.size, grow=-30).filter(ImageFilter.GaussianBlur(k(22))))
    occ.putalpha(rm.point(lambda v: int(v * 0.6)))
    L.alpha_composite(occ)
    ImageDraw.Draw(L, "RGBA").polygon(pts(egg_poly()), outline=INK, width=int(k(7)))
    return L


def leaves_layer():
    L = new()
    C.draw_leaves(L)
    # gradient: darker at the base
    a = np.asarray(L).astype(np.float32)
    H = a.shape[0]
    y = np.arange(H, dtype=np.float32)[:, None]
    top, base = k(CY - RY - 250), k(CY - RY + 22)
    t = np.clip((y - top) / (base - top), 0, 1)
    a[..., :3] *= (1.15 - 0.45 * t)[..., None]
    L = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return shade_layer(L, radius=k(7), depth=2.2, ambient=0.6, diffuse=0.6, spec=0.45, shin=20, spec_col=(220, 255, 200))


def eyes_layer():
    L = new()
    C.draw_eyes(L)
    L = shade_layer(L, radius=k(14), depth=1.6, ambient=0.72, diffuse=0.38, spec=0.5, shin=30)
    d = ImageDraw.Draw(L, "RGBA")
    for side in (-1, 1):  # glossy catch-light
        ex, ey = CX + side * 78, CY + 62
        d.ellipse(box(ex - 30, ey - 6, ex - 14, ey + 6), fill=(255, 255, 255, 200))
    return L


def mask_layer():
    L = new()
    C.draw_mask(L)
    L = shade_ellipsoid(L, k(CX - 20), k(CY + 40), k(RX + 30), k(RY + 10), ambient=0.75, diffuse=0.65, spec=0.8, shin=36, spec_col=(255, 255, 255), rim=0.5)
    return shade_layer(L, radius=k(4), depth=2.0, ambient=0.9, diffuse=0.25, spec=0.25, shin=30)


def antennas_layer(upper, lower):
    L = new()
    C.draw_antennas(L, upper=upper, lower=lower)
    return shade_layer(L, radius=k(9), depth=3.0, ambient=0.55, diffuse=0.9, spec=0.8, shin=40)


def helmet_layer():
    L = new()
    C.draw_helmet(L)
    L = shade_ellipsoid(L, k(CX - 30), k(CY - 120), k(240), k(190), ambient=0.5, diffuse=0.75, spec=0.35, shin=14, spec_col=(230, 240, 210), rim=0.4)
    return shade_layer(L, radius=k(5), depth=2.5, ambient=0.72, diffuse=0.4, spec=0.2, shin=20)


def headset_layer(helmet=True):
    L = new()
    (C.draw_headset_cups_on_helmet if helmet else C.draw_headset)(L)
    return shade_layer(L, radius=k(14), depth=2.5, ambient=0.55, diffuse=0.75, spec=0.35, shin=20)


def back_layer():
    """Manpack + whip (behind everything)."""
    L = new()
    d = ImageDraw.Draw(L, "RGBA")
    thick_line(d, [(CX + 200, 600), (CX + 258, 330), (CX + 330, 120)], 9, METAL_D, ow=5)
    d.ellipse(box(CX + 318, 106, CX + 344, 132), fill=AMBER, outline=INK, width=int(k(4)))
    d.rounded_rectangle(box(CX + 150, 590, CX + 300, 830), radius=k(24), fill=(56, 60, 58, 255), outline=INK, width=int(k(7)))
    d.rounded_rectangle(box(CX + 200, 612, CX + 286, 668), radius=k(8), fill=(34, 38, 37, 255), outline=INK, width=int(k(4)))
    L = shade_layer(L, radius=k(16), depth=2.5, ambient=0.5, diffuse=0.8, spec=0.3, shin=20)
    d = ImageDraw.Draw(L, "RGBA")
    for i in range(3):
        d.rectangle(box(CX + 210, 624 + i * 14, CX + 270 - i * 14, 632 + i * 14), fill=NEON)
    for i, r in enumerate((34, 58, 82)):
        d.arc(box(CX + 331 - r, 119 - r, CX + 331 + r, 119 + r), 280, 10, fill=NEON[:3] + (230 - 60 * i,), width=int(k(7)))
    return L


def torso_layer(shirt):
    L = new()
    d = ImageDraw.Draw(L, "RGBA")
    d.rounded_rectangle(box(CX - 196, 600, CX + 196, 960), radius=k(70), fill=shirt, outline=INK, width=int(k(8)))
    for side in (-1, 1):
        thick_line(d, [(CX + side * 170, 650), (CX + side * 250, 760), (CX + side * 226, 880)], 52, shirt, ow=8)
    # fabric folds
    for side in (-1, 1):
        d.arc(box(CX + side * 200 - 40, 700, CX + side * 200 + 40, 780), 200 if side < 0 else -20, 300 if side < 0 else 80, fill=tuple(int(c * 0.7) for c in shirt[:3]) + (200,), width=int(k(5)))
    return shade_layer(L, radius=k(34), depth=2.2, ambient=0.5, diffuse=0.75, spec=0.08, shin=8)


def carrier_layer(car, car_d):
    L = new()
    d = ImageDraw.Draw(L, "RGBA")
    d.rounded_rectangle(box(CX - 160, 640, CX + 160, 955), radius=k(36), fill=car, outline=INK, width=int(k(8)))
    for side in (-1, 1):
        d.rounded_rectangle(box(CX + side * 120 - 26, 596, CX + side * 120 + 26, 668), radius=k(10), fill=car_d, outline=INK, width=int(k(6)))
    for i in range(4):
        y = 870 + i * 20
        d.rectangle(box(CX - 140, y, CX + 140, y + 8), fill=car_d)
    # cordura texture
    a = np.asarray(L).astype(np.float32)
    rng = np.random.default_rng(3)
    n = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) - 128
    a[..., :3] += (n * 0.5)[..., None]
    L = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return shade_layer(L, radius=k(16), depth=2.4, ambient=0.5, diffuse=0.75, spec=0.1, shin=10)


def pouches_layer(car, car_d):
    L = new()
    d = ImageDraw.Draw(L, "RGBA")
    for i in range(3):
        x = CX - 132 + i * 92
        d.rounded_rectangle(box(x, 846, x + 80, 950), radius=k(10), fill=car_d, outline=INK, width=int(k(5)))
        d.rounded_rectangle(box(x + 6, 852, x + 74, 878), radius=k(6), fill=car, outline=INK, width=int(k(3)))
    for side in (-1, 1):  # gloves
        d.ellipse(box(CX + side * 226 - 32, 852, CX + side * 226 + 32, 916), fill=(54, 50, 44, 255), outline=INK, width=int(k(6)))
    return shade_layer(L, radius=k(12), depth=2.4, ambient=0.5, diffuse=0.8, spec=0.12, shin=10)


def pager_layer():
    L = new()
    p = C.pager(208, 140)
    p = shade_layer(p, radius=k(10), depth=2.6, ambient=0.55, diffuse=0.7, spec=0.45, shin=26)
    # glass reflection on the screen
    g = Image.new("RGBA", p.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g, "RGBA")
    s = K
    gd.polygon([(38 * s, 34 * s), (110 * s, 34 * s), (70 * s, 100 * s), (38 * s, 100 * s)], fill=(255, 255, 255, 34))
    p.alpha_composite(g)
    L.alpha_composite(p, (int(k(CX - 124)), int(k(670))))
    d = ImageDraw.Draw(L, "RGBA")
    for side in (-1, 1):
        d.rectangle(box(CX + side * 70 - 12, 812, CX + side * 70 + 12, 846), fill=COY_D, outline=INK, width=int(k(4)))
    return L


def gear_layer():
    L = new()
    C.draw_ptt(L)
    C.draw_yagi(L)
    return shade_layer(L, radius=k(8), depth=2.5, ambient=0.55, diffuse=0.8, spec=0.5, shin=30)


def render(variant="helmet", carrier="od"):
    cmap = {"coyote": (COY, COY_D, OD), "od": (OD, OD_D, (110, 98, 72, 255)), "black": ((48, 50, 52, 255), (30, 32, 34, 255), (70, 76, 60, 255))}
    car, car_d, shirt = cmap[carrier]
    img = new()
    body = variant in ("helmet", "bust", "operator")
    helmet = variant in ("helmet", "bust", "head")
    if body:
        if variant in ("helmet", "operator"):
            put(img, back_layer(), shadow=False)
        put(img, torso_layer(shirt), shadow=False)
        put(img, carrier_layer(car, car_d))
        put(img, pouches_layer(car, car_d))
    put(img, antennas_layer(upper=not helmet, lower=True))
    put(img, leaves_layer(), off=(3, 6), blur=5)
    put(img, fruit_layer(), off=(6, 12), blur=12, alpha=0.5)
    put(img, eyes_layer(), shadow=False)
    put(img, mask_layer(), off=(4, 10), blur=8, alpha=0.5)
    if helmet:
        put(img, helmet_layer(), off=(4, 12), blur=10, alpha=0.55)
    put(img, headset_layer(helmet), off=(4, 8), blur=6)
    if body:
        put(img, pager_layer(), off=(5, 10), blur=8, alpha=0.55)
        if variant in ("helmet", "operator"):
            put(img, gear_layer())
    out = img.resize((1000 * RES, 1000 * RES), Image.LANCZOS)
    return out.crop(out.getbbox())


if __name__ == "__main__":
    import sys, time
    t = time.time()
    v = sys.argv[1] if len(sys.argv) > 1 else "helmet"
    im = render(v)
    im.save("char3d_%s.png" % v)
    print(v, im.size, round(time.time() - t, 1), "s")
