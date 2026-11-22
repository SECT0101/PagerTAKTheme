#!/usr/bin/env python3
"""TAK5 Pager Theme asset generator.

Copies Hak5's reference `wargames` theme layout (same file names and sizes) and
redraws the artwork in a tactical TAK style with hacker accents.
Usage: build_tak5.py <wargames_dir> <out_theme_dir> <fonts_dir>
"""
import math, os, random, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageChops

SRC, OUT, FONTS = sys.argv[1], sys.argv[2], sys.argv[3]
S = 2  # supersample factor

# ---------------------------------------------------------------- colors
# Color scheme: TAK5_SCHEME = cyan | nvg | coyote | white
SCHEMES = {
    #          primary          bright           grid minor     grid major     topo           dim             base top       key mid        dialog dark   dialog mid
    "cyan":   ((128, 224, 255), (0, 240, 255),   (12, 36, 48),  (20, 66, 82),  (16, 54, 46),  (92, 120, 132), (6, 16, 28),   (6, 52, 70),   (2, 10, 18),  (10, 60, 86)),
    "nvg":    ((132, 232, 150), (90, 255, 160),  (12, 38, 22),  (22, 70, 40),  (18, 54, 30),  (96, 128, 104), (6, 20, 12),   (8, 58, 30),   (2, 12, 6),   (10, 64, 34)),
    "coyote": ((216, 186, 134), (240, 212, 156), (38, 32, 22),  (70, 58, 40),  (50, 42, 28),  (132, 118, 96), (20, 17, 12),  (60, 48, 30),  (12, 10, 6),  (70, 56, 34)),
    "white":  ((214, 220, 216), (250, 252, 250), (30, 34, 36),  (56, 62, 66),  (38, 44, 44),  (120, 126, 128), (16, 18, 20), (52, 58, 62),  (8, 10, 12),  (56, 62, 66)),
}
SCHEME = os.environ.get("TAK5_SCHEME", "coyote")
(FRIEND, CYAN, GRID_MIN, GRID_MAJ, TOPO, DIM, BASE_TOP, KEY_MID, DLG_D, DLG_M) = SCHEMES[SCHEME]
BG0 = (3, 8, 14) if SCHEME == "cyan" else tuple(max(0, c // 3) for c in BASE_TOP)
NAVY = (6, 20, 40)
AMBER = (255, 200, 40)
HOSTILE = (255, 64, 80)
NEUTRAL = (64, 255, 140)
MAGENTA = (206, 164, 104)   # coyote tan (was magenta; no pink in TAK5)
PURPLE = (182, 154, 112)     # coyote light
WHITE = (225, 240, 245)
WORDMARK = os.environ.get("TAK5_WORDMARK", "wordmark.png")


def F(name, size):
    files = {
        "mono": "ShareTechMono-Regular.ttf",
        "tech": "ShareTech-Regular.ttf",
        "vt": "VT323-Regular.ttf",
        "orb": "Orbitron%5Bwght%5D.ttf",
    }
    f = ImageFont.truetype(os.path.join(FONTS, files[name]), size * S)
    if name == "orb":
        try:
            f.set_variation_by_axes([800])
        except Exception:
            pass
    return f


def canvas(w, h, color=(0, 0, 0, 0)):
    return Image.new("RGBA", (w * S, h * S), color)


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


# ---------------------------------------------------------------- noise / layers
def smooth_noise(w, h, seed, octaves=((6, 1.0), (12, 0.5), (24, 0.25))):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    for cells, amp in octaves:
        small = rng.random((max(2, int(cells * h / w)) + 1, cells + 1)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp
    acc -= acc.min()
    acc /= acc.max()
    return acc


def topo_layer(w, h, seed, color=TOPO, levels=14, alpha=150):
    W, H = w * S, h * S
    n = smooth_noise(W, H, seed)
    v = n * levels
    frac = np.abs(v - np.round(v))
    gy, gx = np.gradient(v)
    g = np.sqrt(gx * gx + gy * gy) + 1e-6
    line = np.clip(1.4 - frac / g, 0, 1)
    major = (np.round(v).astype(int) % 5 == 0)
    a = (line * np.where(major, alpha, alpha * 0.55)).astype(np.uint8)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


def gradient(w, h, top, bottom, horizontal=False):
    W, H = w * S, h * S
    t = np.linspace(0, 1, W if horizontal else H, dtype=np.float32)
    top, bottom = np.array(top, np.float32), np.array(bottom, np.float32)
    col = top[None, :] * (1 - t[:, None]) + bottom[None, :] * t[:, None]
    if horizontal:
        arr = np.repeat(col[None, :, :], H, 0)
    else:
        arr = np.repeat(col[:, None, :], W, 1)
    a = np.full((H, W, 1), 255, np.float32)
    return Image.fromarray(np.concatenate([arr, a], 2).astype(np.uint8), "RGBA")


def grid(img, step=12, major=5, cmin=GRID_MIN, cmaj=GRID_MAJ, ox=0, oy=0, labels=False, lab_color=DIM):
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    st = step * S
    i = 0
    for x in range(ox * S % st, W, st):
        k = (x // st)
        if k % major == 0:
            d.line([(x, 0), (x, H)], fill=rgba(cmaj, 200), width=S)
        else:
            for y in range(0, H, 4 * S):
                d.line([(x, y), (x, y + S)], fill=rgba(cmin, 200), width=1)
    for y in range(oy * S % st, H, st):
        k = (y // st)
        if k % major == 0:
            d.line([(0, y), (W, y)], fill=rgba(cmaj, 200), width=S)
        else:
            for x in range(0, W, 4 * S):
                d.line([(x, y), (x + S, y)], fill=rgba(cmin, 200), width=1)
    if labels:
        f = F("mono", 7)
        for n, x in enumerate(range(0, W, st * major)):
            if x:
                d.text((x + 2 * S, H - 10 * S), "%02d" % (40 + n), font=f, fill=rgba(lab_color, 170))
        for n, y in enumerate(range(0, H, st * major)):
            if y:
                d.text((2 * S, y + 1 * S), "%02d" % (88 - n), font=f, fill=rgba(lab_color, 170))
    return img


def scanlines(im, strength=0.82):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    a[1::2, :, :3] *= strength
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def vignette(img, strength=0.55):
    W, H = img.size
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    m = 1 - np.clip((r - 0.6) / 0.9, 0, 1) * strength
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= m[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def glow(layer, radius=4, boost=1.6):
    g = layer.filter(ImageFilter.GaussianBlur(radius * S))
    a = np.asarray(g).astype(np.float32)
    a[..., 3] = np.clip(a[..., 3] * boost, 0, 255)
    return Image.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"), layer)


def text_layer(size, xy, text, font, color, anchor="la"):
    L = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(L, "RGBA").text((xy[0] * S, xy[1] * S), text, font=font, fill=rgba(color), anchor=anchor)
    return L


def neon_text(img, xy, text, font, color, chroma=1.0, glow_r=3, anchor="la"):
    """Text with glow and a magenta/cyan chromatic split (the hacker touch)."""
    if chroma:
        off = int(round(1.5 * S * chroma))
        m = text_layer(img.size, xy, text, font, MAGENTA, anchor)
        c = text_layer(img.size, xy, text, font, CYAN, anchor)
        m = ImageChops.offset(m, -off, 0)
        c = ImageChops.offset(c, off, 0)
        for L in (m, c):
            a = np.asarray(L).copy()
            a[..., 3] = (a[..., 3] * 0.55).astype(np.uint8)
            img.alpha_composite(Image.fromarray(a, "RGBA"))
    t = text_layer(img.size, xy, text, font, color, anchor)
    img.alpha_composite(glow(t, glow_r, 1.2) if glow_r else t)
    return img


def plain_text(img, xy, text, font, color, alpha=255, anchor="la"):
    ImageDraw.Draw(img, "RGBA").text((xy[0] * S, xy[1] * S), text, font=font, fill=rgba(color, alpha), anchor=anchor)


# ---------------------------------------------------------------- symbology
def sym(d, kind, cx, cy, r, color, alpha=255, width=2, fill=None):
    cx, cy, r = cx * S, cy * S, r * S
    col = rgba(color, alpha)
    fl = rgba(fill, alpha) if fill else None
    w = width * S
    if kind == "friend":  # rectangle 1.5:1
        d.rectangle([cx - r * 1.2, cy - r * 0.8, cx + r * 1.2, cy + r * 0.8], outline=col, width=w, fill=fl)
    elif kind == "hostile":
        d.polygon([(cx, cy - r * 1.15), (cx + r * 1.15, cy), (cx, cy + r * 1.15), (cx - r * 1.15, cy)], outline=col, width=w, fill=fl)
    elif kind == "neutral":
        d.rectangle([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], outline=col, width=w, fill=fl)
    elif kind == "unknown":
        q = r * 0.55
        for dx, dy in ((0, -q), (q, 0), (0, q), (-q, 0)):
            d.ellipse([cx + dx - q, cy + dy - q, cx + dx + q, cy + dy + q], outline=col, width=w)
    elif kind == "infantry":  # friend frame with X
        d.rectangle([cx - r * 1.2, cy - r * 0.8, cx + r * 1.2, cy + r * 0.8], outline=col, width=w, fill=fl)
        d.line([(cx - r * 1.2, cy - r * 0.8), (cx + r * 1.2, cy + r * 0.8)], fill=col, width=w)
        d.line([(cx - r * 1.2, cy + r * 0.8), (cx + r * 1.2, cy - r * 0.8)], fill=col, width=w)


def chevron(d, cx, cy, r, color, alpha=255, angle=0, fill=True):
    """ATAK-style self marker arrow."""
    pts = [(0, -1.0), (0.72, 0.85), (0, 0.45), (-0.72, 0.85)]
    a = math.radians(angle)
    P = []
    for x, y in pts:
        X = x * math.cos(a) - y * math.sin(a)
        Y = x * math.sin(a) + y * math.cos(a)
        P.append(((cx + X * r) * S, (cy + Y * r) * S))
    if fill:
        d.polygon(P, fill=rgba(color, alpha))
    else:
        d.polygon(P, outline=rgba(color, alpha), width=2 * S)


def hexagon(d, cx, cy, r, color, alpha=255, width=2, fill=None):
    P = [((cx + r * math.cos(math.radians(60 * i + 30))) * S, (cy + r * math.sin(math.radians(60 * i + 30))) * S) for i in range(6)]
    d.polygon(P, outline=rgba(color, alpha), width=width * S, fill=rgba(fill, alpha) if fill else None)


def brackets(d, x0, y0, x1, y1, color, alpha=255, L=10, w=2):
    x0, y0, x1, y1, L, w = x0 * S, y0 * S, x1 * S, y1 * S, L * S, w * S
    c = rgba(color, alpha)
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=c, width=w)
        d.line([(x, y), (x, y + sy * L)], fill=c, width=w)


def radar(img, cx, cy, r, color, angle=-40, sweep=70, rings=4, alpha=255, ticks=True):
    W, H = img.size
    L = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L, "RGBA")
    for i in range(1, rings + 1):
        rr = r * i / rings * S
        d.ellipse([cx * S - rr, cy * S - rr, cx * S + rr, cy * S + rr], outline=rgba(color, int(alpha * (0.35 + 0.15 * (i == rings)))), width=S)
    d.line([(cx * S - r * S, cy * S), (cx * S + r * S, cy * S)], fill=rgba(color, int(alpha * 0.25)), width=1)
    d.line([(cx * S, cy * S - r * S), (cx * S, cy * S + r * S)], fill=rgba(color, int(alpha * 0.25)), width=1)
    if ticks:
        for deg in range(0, 360, 10):
            a = math.radians(deg)
            r0 = r * (0.94 if deg % 30 else 0.88)
            d.line([((cx + r0 * math.cos(a)) * S, (cy + r0 * math.sin(a)) * S), ((cx + r * math.cos(a)) * S, (cy + r * math.sin(a)) * S)], fill=rgba(color, int(alpha * 0.5)), width=S)
    # sweep wedge with fading tail
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = (np.degrees(np.arctan2(y - cy * S, x - cx * S)) - angle) % 360
    dist = np.sqrt((x - cx * S) ** 2 + (y - cy * S) ** 2)
    tail = np.where(ang > 360 - sweep, (ang - (360 - sweep)) / sweep, 0)
    a = (tail ** 2.2) * (dist < r * S) * alpha * 0.55
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a.astype(np.uint8)
    L = Image.alpha_composite(Image.fromarray(arr, "RGBA"), L)
    ex, ey = cx + r * math.cos(math.radians(angle)), cy + r * math.sin(math.radians(angle))
    ImageDraw.Draw(L, "RGBA").line([(cx * S, cy * S), (ex * S, ey * S)], fill=rgba(color, alpha), width=2 * S)
    img.alpha_composite(glow(L, 2, 1.0))
    return img


def hexdump(img, x, y, rows, color, alpha=60, seed=1, size=7, cols=8):
    rnd = random.Random(seed)
    f = F("mono", size)
    for i in range(rows):
        line = "%04X " % (0x1000 + i * 16 * rnd.randint(1, 3)) + " ".join("%02X" % rnd.randint(0, 255) for _ in range(cols))
        plain_text(img, (x, y + i * (size + 2)), line, f, color, alpha)


def glitch(img, seed, n=6, maxshift=14, region=None):
    rnd = random.Random(seed)
    W, H = img.size
    a = np.asarray(img).copy()
    x0, y0, x1, y1 = region if region else (0, 0, W // S, H // S)
    for _ in range(n):
        h = rnd.randint(2, 9) * S
        yy = rnd.randint(y0 * S, max(y0 * S, y1 * S - h))
        sh = rnd.randint(-maxshift, maxshift) * S
        a[yy:yy + h, x0 * S:x1 * S] = np.roll(a[yy:yy + h, x0 * S:x1 * S], sh, axis=1)
    return Image.fromarray(a, "RGBA")


def base_map(w, h, seed=1, tint=None, topo=True, grid_on=True, glow_c=None, labels=False, dim=1.0):
    img = gradient(w, h, BASE_TOP, BG0)
    if glow_c:
        g = canvas(w, h)
        ImageDraw.Draw(g, "RGBA").ellipse([w * S * 0.15, -h * S * 0.6, w * S * 1.2, h * S * 0.9], fill=rgba(glow_c, 40))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(40 * S)))
    if topo:
        img.alpha_composite(topo_layer(w, h, seed, tint or TOPO, alpha=int(150 * dim)))
    if grid_on:
        g = canvas(w, h)
        grid(g, labels=labels)
        if dim != 1.0:
            a = np.asarray(g).copy()
            a[..., 3] = (a[..., 3] * dim).astype(np.uint8)
            g = Image.fromarray(a, "RGBA")
        img.alpha_composite(g)
    return img


def scatter_symbols(img, region, n, seed, alpha=70, kinds=("friend", "hostile", "neutral", "unknown", "infantry")):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img, "RGBA")
    cols = {"friend": FRIEND, "infantry": FRIEND, "hostile": HOSTILE, "neutral": NEUTRAL, "unknown": AMBER}
    x0, y0, x1, y1 = region
    for _ in range(n):
        k = rnd.choice(kinds)
        sym(d, k, rnd.randint(x0, x1), rnd.randint(y0, y1), rnd.randint(4, 7), cols[k], alpha, 1)


# ---------------------------------------------------------------- output
def save(img, rel, size=None, colors=96, scan=True, mask_from=None):
    """Downsample, optionally scanline, quantize to palette PNG and save."""
    out = os.path.join(OUT, "assets", rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ref = os.path.join(SRC, "assets", rel)
    if size is None:
        size = Image.open(ref).size if os.path.exists(ref) else (img.size[0] // S, img.size[1] // S)
    im = img.resize(size, Image.LANCZOS) if img.size != size else img
    if scan:
        im = scanlines(im)
    if os.path.exists(ref) and Image.open(ref).convert("RGBA").getextrema()[3][0] == 255:
        flat = Image.new("RGBA", im.size, (0, 0, 0, 255))
        flat.alpha_composite(im)
        im = flat
    if mask_from is not None:
        m = Image.open(mask_from).convert("RGBA").split()[3]
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (r, g, b, ImageChops.multiply(a, m)))
    q = im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    q.save(out, optimize=True)
    return out


def retint(rel, dark, mid, light, overlay_grid=False, keep_extremes=False, colors=64):
    """Recolor a reference asset by luminance, keeping its exact geometry and alpha."""
    src = Image.open(os.path.join(SRC, "assets", rel)).convert("RGBA")
    r, g, b, a = src.split()
    L = src.convert("L")
    L = ImageOps.autocontrast(L, cutoff=0.5)
    col = ImageOps.colorize(L, dark, light, mid=mid).convert("RGBA")
    if keep_extremes:
        s = np.asarray(src).astype(int)
        sat = s[..., :3].max(2) - s[..., :3].min(2)
        lum = s[..., :3].mean(2)
        keep = (sat < 25) & ((lum > 235) | (lum < 12))
        c = np.asarray(col).copy()
        c[keep] = s[keep]
        col = Image.fromarray(c.astype(np.uint8), "RGBA")
    if overlay_grid:
        big = col.resize((col.size[0] * S, col.size[1] * S), Image.NEAREST)
        gl = canvas(*col.size)
        grid(gl, step=10, cmin=tuple(min(255, v + 18) for v in dark), cmaj=tuple(min(255, v + 34) for v in dark))
        ga = np.asarray(gl).copy()
        ga[..., 3] = (ga[..., 3] * 0.45).astype(np.uint8)
        big.alpha_composite(Image.fromarray(ga, "RGBA"))
        col = big.resize(col.size, Image.LANCZOS)
    col.putalpha(a)
    out = os.path.join(OUT, "assets", rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    col.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(out, optimize=True)


MASCOT = os.environ.get("TAK5_MASCOT", "tacpine.png")


def paste_mascot(img, x, y, h, glow_c=None):
    m = Image.open(MASCOT).convert("RGBA")
    m = m.crop(m.getbbox())
    w = round(m.size[0] * h / m.size[1])
    m = m.resize((w * S, h * S), Image.LANCZOS)
    if glow_c:
        a = m.split()[3].filter(ImageFilter.GaussianBlur(5 * S))
        g = Image.new("RGBA", m.size, rgba(glow_c, 0))
        g.putalpha(a.point(lambda v: int(v * 0.5)))
        img.alpha_composite(g, (x * S, y * S))
    img.alpha_composite(m, (x * S, y * S))
    return w



def paste_art(img, art, x, y, h=None, w=None):
    """Paste RGBA art at theme coords, scaled to height h or width w (theme px)."""
    if h:
        w = round(art.size[0] * h / art.size[1])
    else:
        h = round(art.size[1] * w / art.size[0])
    img.alpha_composite(art.resize((w * S, h * S), Image.LANCZOS), (int(x * S), int(y * S)))


_PLANET = {}


def planet_art(kind):
    """TAK THE PLANET! slogan / globe, made once per build."""
    import planet
    if kind not in _PLANET:
        if kind == "mark2":
            _PLANET[kind] = planet.planet_mark(220, two_line=True, outline=(200, 194, 172))
        elif kind == "mark1":
            _PLANET[kind] = planet.planet_mark(220, two_line=False, outline=(200, 194, 172))
        elif kind == "globe":
            _PLANET[kind] = planet.globe(420, lat0=40, lon0=-90)
    return _PLANET[kind]


def boot_finale(glitched):
    """Last boot frames: TAK THE PLANET! with Tac-Pine standing on the globe."""
    import planet
    img = base_map(W, H, 9, dim=0.85)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([14 * S, 210 * S, 230 * S, 214 * S], outline=rgba(GRID_MAJ, 255), width=S)
    d.rectangle([15 * S, 211 * S, 229 * S, 213 * S], fill=rgba(NEUTRAL))
    plain_text(img, (234, 207), "SA LINK 100%", F("mono", 9), NEUTRAL)
    brackets(d, 4, 4, 476, 218, FRIEND, 170, 12, 1)
    paste_art(img, planet_art("globe"), 296, 100, h=250)   # top of the globe, rest below the screen
    paste_mascot(img, 368, 4, 120, FRIEND)
    mark = planet.chroma_split(planet_art("mark2"), 18) if glitched else planet_art("mark2")
    paste_art(img, mark, 14, 28 if glitched else 30, w=236)
    plain_text(img, (16, 156), "> SA LINK ESTABLISHED // 5 NODES", F("mono", 10), NEUTRAL, 230)
    plain_text(img, (16, 172), "> TAK.5 PINEAPPLE EDITION", F("mono", 10), AMBER, 230)
    if glitched:
        img = glitch(img, 3, n=10, maxshift=16)
    return img

# =================================================================== screens
W, H = 480, 222
STATUS_FADE = None


def title_bg(title, seed, tint=None, extra=None):
    img = base_map(W, H, seed, tint=tint, dim=0.55)
    d = ImageDraw.Draw(img, "RGBA")
    # header rule under title area
    d.line([(8 * S, 38 * S), (200 * S, 38 * S)], fill=rgba(FRIEND, 120), width=S)
    d.line([(200 * S, 38 * S), (210 * S, 30 * S)], fill=rgba(FRIEND, 120), width=S)
    d.line([(210 * S, 30 * S), (W * S, 30 * S)], fill=rgba(GRID_MAJ, 160), width=S)
    if title:
        neon_text(img, (8, 4), title, F("tech", 25), FRIEND, chroma=0.6, glow_r=2)
    plain_text(img, (472, 212), "TAK.5", F("orb", 7), DIM, 140, anchor="rs")
    if extra:
        extra(img)
    return vignette(img, 0.45)


def build_logo(img, x, y, size=46, chroma=1.0, sub=True, glow_r=4):
    """TAK.5 wordmark (Hak5-style: white TAK, line + dot, camo 5)."""
    wm = Image.open(WORDMARK).convert("RGBA")
    h = int(size * 1.3)
    w = round(wm.size[0] * h / wm.size[1])
    wm = wm.resize((w * S, h * S), Image.LANCZOS)
    sh = Image.new("RGBA", wm.size, (0, 0, 0, 0))
    sh.putalpha(wm.split()[3].filter(ImageFilter.GaussianBlur(2 * S)).point(lambda v: int(v * 0.8)))
    img.alpha_composite(sh, ((x + 2) * S, (y + 3) * S))
    img.alpha_composite(wm, (x * S, y * S))
    if sub:
        plain_text(img, (x + 2, y + h + 6), "TEAM AWARENESS // PAGER", F("mono", 10), AMBER, 230)
    return w


def emblem(img, cx, cy, r=34, color=FRIEND):
    L = canvas(W, H)
    d = ImageDraw.Draw(L, "RGBA")
    hexagon(d, cx, cy, r, color, 230, 2)
    hexagon(d, cx, cy, r - 6, color, 90, 1)
    chevron(d, cx, cy + 2, r * 0.55, AMBER, 255)
    for k in range(6):
        a = math.radians(60 * k + 30)
        d.line([((cx + (r + 3) * math.cos(a)) * S, (cy + (r + 3) * math.sin(a)) * S), ((cx + (r + 9) * math.cos(a)) * S, (cy + (r + 9) * math.sin(a)) * S)], fill=rgba(color, 200), width=2 * S)
    img.alpha_composite(glow(L, 3, 1.3))


def boot_frames():
    lines = [
        ("> TAK.5 SA KERNEL ......... LOADED", FRIEND),
        ("> GPS NMEA ............... LOCK", NEUTRAL),
        ("> COT ROUTER ............. ONLINE", NEUTRAL),
        ("> TLS 8089 ............... READY", NEUTRAL),
        ("> PINEAP ................. ARMED", AMBER),
        ("> TAK THE PLANET", AMBER),
    ]
    fmono = F("mono", 10)
    frames = []
    for i in range(6):
        img = base_map(W, H, 7, dim=0.25 + 0.15 * min(i, 4))
        d = ImageDraw.Draw(img, "RGBA")
        if i >= 1:
            radar(img, 368, 112, 92, NEUTRAL, angle=-90 + i * 62, alpha=200)
            scatter_symbols(img, (290, 40, 450, 190), 6, 3, alpha=150 if i > 2 else 80)
            chevron(d, 368, 112, 9, AMBER, 255, angle=20)
        n = min(len(lines), 1 + i)
        up = 14 if n > 5 else 0  # make room above the progress bar for the last line
        for k in range(n):
            t, c = lines[k]
            plain_text(img, (14, 136 + k * 14 - up), t, fmono, c, 220)
        if i < 5:
            plain_text(img, (14, 136 + n * 14), "_", fmono, CYAN, 255)
        else:  # TAK THE PLANET is typed last, cursor still blinking
            plain_text(img, (15 + fmono.getlength(lines[-1][0]) / S, 136 + (n - 1) * 14 - up), "_", fmono, AMBER, 255)
        if i >= 2:
            build_logo(img, 14, 22, 40, chroma=2.6 if i == 2 else (1.4 if i == 3 else 0.8), sub=i >= 3)
        if i >= 3:
            paste_mascot(img, 186, 6, 120, FRIEND)
        else:
            hexdump(img, 14, 18, 9, FRIEND, 90 if i else 55, seed=i)
        # progress
        p = [0.08, 0.25, 0.48, 0.70, 0.90, 1.0][i]
        d.rectangle([14 * S, 210 * S, 230 * S, 214 * S], outline=rgba(GRID_MAJ, 255), width=S)
        d.rectangle([15 * S, 211 * S, (15 + 214 * p) * S, 213 * S], fill=rgba(AMBER if p < 1 else NEUTRAL))
        plain_text(img, (234, 207), "SA LINK %3d%%" % int(p * 100), F("mono", 9), AMBER if p < 1 else NEUTRAL)
        brackets(d, 4, 4, 476, 218, FRIEND, 170, 12, 1)
        if i == 2:
            img = glitch(img, 11, n=9, maxshift=18)
        if i == 3:
            img = glitch(img, 5, n=3, maxshift=6, region=(0, 20, 260, 90))
        save(vignette(img, 0.5), "boot_animation/init-%d.png" % (i + 1), size=(W, H))
    for n, glitched in ((7, True), (8, False)):
        save(vignette(boot_finale(glitched), 0.5), "boot_animation/init-%d.png" % n, size=(W, H))


def dashboard():
    img = base_map(W, H, 21, dim=1.0, labels=True)
    d = ImageDraw.Draw(img, "RGBA")
    # range rings centered on the menu cluster
    radar(img, 340, 128, 118, FRIEND, angle=-130, sweep=55, alpha=110, ticks=True)
    scatter_symbols(img, (250, 40, 470, 210), 9, 42, alpha=55)
    # route/track line
    pts = [(250, 205), (286, 176), (318, 186), (356, 158), (402, 166), (448, 138), (476, 140)]
    for a, b in zip(pts, pts[1:]):
        d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=rgba(NEUTRAL, 90), width=S)
    # left emblem + logo
    paste_mascot(img, 4, 22, 112, FRIEND)
    build_logo(img, 112, 34, 34, chroma=1.0, sub=False)
    paste_art(img, planet_art("mark1"), 113, 85, w=128)
    plain_text(img, (114, 100), "16S  COT//SA  NET:TLS", F("mono", 8), DIM, 220)
    # label plate where the firmware prints the selected item name (16,171)
    P = canvas(W, H)
    pd = ImageDraw.Draw(P, "RGBA")
    pd.polygon([(0, 164 * S), (226 * S, 164 * S), (240 * S, 178 * S), (226 * S, 208 * S), (0, 208 * S)], fill=rgba((2, 6, 10), 235))
    pd.line([(0, 164 * S), (226 * S, 164 * S), (240 * S, 178 * S)], fill=rgba(AMBER, 230), width=S)
    pd.line([(0, 208 * S), (226 * S, 208 * S)], fill=rgba(AMBER, 120), width=S)
    pd.rectangle([4 * S, 168 * S, 8 * S, 204 * S], fill=rgba(AMBER, 230))
    img.alpha_composite(P)
    plain_text(img, (222, 213), "SEL//", F("mono", 6), AMBER, 160, anchor="rs")
    save(vignette(img, 0.4), "dashboard/tak5_bg.png", size=(W, H))


def dash_tiles():
    # unselected tile (native colors) – dark diamond, friend outline
    img = canvas(63, 62)
    d = ImageDraw.Draw(img, "RGBA")
    c = (31.5, 31)
    P = [(c[0] * S, 1 * S), (62 * S, c[1] * S), (c[0] * S, 61 * S), (1 * S, c[1] * S)]
    d.polygon(P, fill=rgba((6, 22, 34), 235), outline=rgba(FRIEND, 255), width=2 * S)
    P2 = [(c[0] * S, 7 * S), (56 * S, c[1] * S), (c[0] * S, 55 * S), (7 * S, c[1] * S)]
    d.polygon(P2, outline=rgba(FRIEND, 70), width=S)
    save(img, "dashboard/item_bg.png", size=(63, 62), scan=False)
    # highlight – amber glow ring
    img = canvas(71, 72)
    L = canvas(71, 72)
    d = ImageDraw.Draw(L, "RGBA")
    c = (35.5, 36)
    P = [(c[0] * S, 2 * S), (69 * S, c[1] * S), (c[0] * S, 70 * S), (2 * S, c[1] * S)]
    d.polygon(P, outline=rgba(AMBER, 255), width=2 * S)
    for (x, y) in P:
        d.rectangle([x - 2 * S, y - 2 * S, x + 2 * S, y + 2 * S], fill=rgba(AMBER, 255))
    img.alpha_composite(glow(L, 2, 1.4))
    save(img, "dashboard/highlight.png", size=(71, 72), scan=False)


def radar_screen(rel, color, title=None):
    img = base_map(W, H, 33 if color == NEUTRAL else 34, dim=0.6)
    radar(img, 30, 250, 230, color, angle=-58, sweep=80, rings=6, alpha=200)
    scatter_symbols(img, (40, 60, 240, 210), 7, 9 if color == NEUTRAL else 12, alpha=90)
    plain_text(img, (472, 212), "TAK.5", F("orb", 7), DIM, 140, anchor="rs")
    save(vignette(img, 0.45), rel, size=(W, H))


def payloads_bg():
    img = base_map(W, H, 51, dim=0.4, tint=(40, 32, 18))
    g = gradient(W, H, (44, 34, 18), (4, 8, 14), horizontal=True)
    a = np.asarray(g).copy()
    a[..., 3] = 150
    img.alpha_composite(Image.fromarray(a, "RGBA"))
    # data-package cube, wireframe
    L = canvas(W, H)
    d = ImageDraw.Draw(L, "RGBA")
    cx, cy, s = 70, 135, 46
    top = [(cx, cy - s), (cx + s, cy - s / 2), (cx, cy), (cx - s, cy - s / 2)]
    left = [(cx - s, cy - s / 2), (cx, cy), (cx, cy + s), (cx - s, cy + s / 2)]
    right = [(cx, cy), (cx + s, cy - s / 2), (cx + s, cy + s / 2), (cx, cy + s)]
    for poly, al in ((top, 120), (left, 70), (right, 40)):
        d.polygon([(x * S, y * S) for x, y in poly], fill=rgba(MAGENTA, al), outline=rgba(MAGENTA, 255), width=2 * S)
    # zip zipper on front
    for k in range(6):
        y = cy + 6 + k * 6
        d.line([((cx - 4) * S, y * S), ((cx + 4) * S, (y + 3) * S)], fill=rgba(WHITE, 220), width=S)
    d.text((cx * S, (cy - s / 2) * S), "</>", font=F("mono", 14), fill=rgba(WHITE, 230), anchor="mm")
    img.alpha_composite(glow(L, 4, 1.3))
    hexdump(img, 140, 60, 14, MAGENTA, 50, seed=8, size=8, cols=10)
    img = glitch(img, 3, n=5, maxshift=10, region=(0, 80, 140, 200))
    neon_text(img, (8, 4), "Payloads", F("tech", 25), FRIEND, chroma=0.7, glow_r=2)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(8 * S, 38 * S), (200 * S, 38 * S)], fill=rgba(MAGENTA, 150), width=S)
    plain_text(img, (472, 212), "TAK.5", F("orb", 7), DIM, 140, anchor="rs")
    save(vignette(img, 0.4), "payloads_dashboard/payloads_bg.png", size=(W, H))


def recon_dashboard():
    img = title_bg("Recon", 61)
    d = ImageDraw.Draw(img, "RGBA")
    fr = rgba(GRID_MAJ, 255)
    d.rectangle([10 * S, 43 * S, 470 * S, 216 * S], outline=rgba(FRIEND, 110), width=S, fill=rgba((2, 6, 10), 150))
    brackets(d, 10, 43, 470, 216, FRIEND, 255, 8, 2)
    for y in (90, 139):
        for x in range(24, 430, 8):
            d.line([(x * S, y * S), ((x + 4) * S, y * S)], fill=rgba(GRID_MAJ, 255), width=S)
    d.line([(12 * S, 180 * S), (468 * S, 180 * S)], fill=rgba(FRIEND, 110), width=S)
    f = F("mono", 13)
    plain_text(img, (102, 199), "^ Type v", f, DIM, 255, anchor="mm")
    # settings glyph (sliders)
    for k, (y, kx) in enumerate(((193, 197), (199, 203), (205, 199))):
        d.line([(191 * S, y * S), (209 * S, y * S)], fill=rgba(FRIEND), width=S)
        d.rectangle([(kx - 1) * S, (y - 2) * S, (kx + 1) * S, (y + 2) * S], fill=rgba(FRIEND))
    plain_text(img, (216, 199), "Settings", f, FRIEND, 255, anchor="lm")
    plain_text(img, (370, 199), "< Views >", f, DIM, 255, anchor="mm")
    plain_text(img, (464, 190), "NOW", F("mono", 11), AMBER, 255, anchor="rm")
    save(img, "recon/recon_dashboard.png", size=(W, H))


def lists():
    save(title_bg("PineAP", 71), "pineap_bg.png", size=(W, H))
    save(title_bg("Settings", 72), "settings_bg.png", size=(W, H))
    save(title_bg(None, 73), "blank_recon_bg.png", size=(W, H))

    def pill(img):
        ImageDraw.Draw(img, "RGBA").rounded_rectangle([1 * S, 1 * S, 44 * S, 12 * S], radius=6 * S, fill=rgba((40, 52, 60), 255))
    save(title_bg(None, 74, extra=pill), "recon/recon_list_bg.png", size=(W, H))

    img = title_bg(None, 75)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([1 * S, 1 * S, 478 * S, 220 * S], outline=rgba(FRIEND, 150), width=S)
    brackets(d, 1, 1, 478, 220, AMBER, 255, 10, 2)
    save(img, "payloadlog/payload_log_bg.png", size=(W, H))


def lock_screens():
    for rel, msg in (("lock_screen.png", None), ("buttons_locked.png", "Double Tap Power to Unlock")):
        img = base_map(W, H, 81, dim=0.5)
        d = ImageDraw.Draw(img, "RGBA")
        L = canvas(W, H)
        ld = ImageDraw.Draw(L, "RGBA")
        cx, cy = 240, 112 if msg is None else 96
        hexagon(ld, cx, cy, 70, FRIEND, 160, 2)
        hexagon(ld, cx, cy, 62, FRIEND, 60, 1)
        ld.arc([(cx - 22) * S, (cy - 44) * S, (cx + 22) * S, (cy + 2) * S], 180, 360, fill=rgba(AMBER), width=7 * S)
        ld.line([((cx - 22) * S, (cy - 22) * S), ((cx - 22) * S, (cy - 6) * S)], fill=rgba(AMBER), width=7 * S)
        ld.line([((cx + 22) * S, (cy - 22) * S), ((cx + 22) * S, (cy - 6) * S)], fill=rgba(AMBER), width=7 * S)
        ld.rounded_rectangle([(cx - 32) * S, (cy - 8) * S, (cx + 32) * S, (cy + 36) * S], radius=5 * S, fill=rgba(AMBER))
        ld.ellipse([(cx - 6) * S, (cy + 4) * S, (cx + 6) * S, (cy + 16) * S], fill=rgba(BG0))
        ld.rectangle([(cx - 2) * S, (cy + 12) * S, (cx + 2) * S, (cy + 26) * S], fill=rgba(BG0))
        img.alpha_composite(glow(L, 4, 1.3))
        plain_text(img, (14, 14), "TAK.5 // SECURE", F("mono", 11), FRIEND, 230)
        paste_mascot(img, 30, 50 if msg is None else 40, 120 if msg is None else 108, FRIEND)
        plain_text(img, (466, 14), "LOCKED", F("mono", 11), HOSTILE, 230, anchor="ra")
        brackets(d, 4, 4, 476, 218, FRIEND, 170, 12, 1)
        if msg is None:
            paste_art(img, planet_art("mark1"), 145, 192, w=190)
        if msg:
            neon_text(img, (240, 188), msg, F("mono", 19), WHITE, chroma=0.8, glow_r=2, anchor="mm")
        save(vignette(img, 0.5), rel, size=(W, H))


def battery_alerts():
    for rel, title, col in (("low_battery_alert.png", "LOW BATTERY", AMBER), ("critical_battery_alert.png", "CONNECT POWER", HOSTILE)):
        img = base_map(W, H, 91, dim=0.4)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([2 * S, 2 * S, 477 * S, 219 * S], outline=rgba(col, 255), width=3 * S)
        for x in range(0, W + 40, 22):  # hazard stripes top & bottom
            d.polygon([(x * S, 6 * S), ((x + 11) * S, 6 * S), ((x + 3) * S, 14 * S), ((x - 8) * S, 14 * S)], fill=rgba(col, 120))
            d.polygon([(x * S, 208 * S), ((x + 11) * S, 208 * S), ((x + 3) * S, 216 * S), ((x - 8) * S, 216 * S)], fill=rgba(col, 120))
        neon_text(img, (240, 44), title, F("orb", 26), col, chroma=0.8, glow_r=3, anchor="mm")
        L = canvas(W, H)
        ld = ImageDraw.Draw(L, "RGBA")
        cx, cy = 240, 140
        ld.polygon([(cx * S, (cy - 58) * S), ((cx + 66) * S, (cy + 54) * S), ((cx - 66) * S, (cy + 54) * S)], outline=rgba(col), width=4 * S)
        ld.rounded_rectangle([(cx - 16) * S, (cy - 18) * S, (cx + 16) * S, (cy + 40) * S], radius=3 * S, outline=rgba(col), width=3 * S)
        ld.rectangle([(cx - 7) * S, (cy - 24) * S, (cx + 7) * S, (cy - 18) * S], fill=rgba(col))
        lvl = 0.35 if col == AMBER else 0.12
        ld.rectangle([(cx - 11) * S, (cy + 35 - 50 * lvl) * S, (cx + 11) * S, (cy + 35) * S], fill=rgba(col))
        ld.polygon([((cx + 3) * S, (cy - 10) * S), ((cx - 7) * S, (cy + 12) * S), ((cx + 1) * S, (cy + 12) * S), ((cx - 4) * S, (cy + 32) * S), ((cx + 8) * S, (cy + 6) * S), ((cx) * S, (cy + 6) * S)], fill=rgba(WHITE))
        img.alpha_composite(glow(L, 4, 1.3))
        save(vignette(img, 0.4), rel, size=(W, H))


def spinners():
    for i in range(4):
        rel = "spinner/spinner%d.png" % (i + 1)
        w, h = Image.open(os.path.join(SRC, "assets", rel)).size
        img = canvas(w, h)
        d = ImageDraw.Draw(img, "RGBA")
        cx, cy, r = w / 2, h / 2, 70
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=rgba((3, 12, 18), 230))
        radar(img, cx, cy, r, NEUTRAL, angle=-90 + i * 90, sweep=90, rings=3, alpha=230)
        rnd = random.Random(i)
        sym(d, "hostile", cx + 32, cy - 22, 5, HOSTILE, 220 if i in (0, 1) else 90, 1)
        sym(d, "friend", cx - 30, cy + 26, 5, FRIEND, 220 if i in (2, 3) else 90, 1)
        chevron(d, cx, cy, 8, AMBER, 255)
        save(img, rel, size=(w, h), scan=False, colors=64)


def launch_anim():
    for i, rel in enumerate(("launch_payload_dialog/animation/anim_frame_1.png", "launch_payload_dialog/animation/anim_frame_2.png")):
        w, h = Image.open(os.path.join(SRC, "assets", rel)).size
        img = canvas(w, h)
        L = canvas(w, h)
        d = ImageDraw.Draw(L, "RGBA")
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 6
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], outline=rgba(HOSTILE), width=3 * S)
        d.ellipse([(cx - r * 0.55) * S, (cy - r * 0.55) * S, (cx + r * 0.55) * S, (cy + r * 0.55) * S], outline=rgba(HOSTILE, 160), width=2 * S)
        g = 6 if i == 0 else 12
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.line([((cx + dx * (r + 4)) * S, (cy + dy * (r + 4)) * S), ((cx + dx * g) * S, (cy + dy * g) * S)], fill=rgba(HOSTILE), width=2 * S)
        d.ellipse([(cx - 3) * S, (cy - 3) * S, (cx + 3) * S, (cy + 3) * S], fill=rgba(AMBER))
        img.alpha_composite(glow(L, 2, 1.2))
        save(img, rel, size=(w, h), scan=False, colors=48)


def pager_portal():
    specs = [
        ("pager_portal/pager_portal_dashboard_alert_payloads.png", NEUTRAL, None),
        ("pager_portal/pager_portal_dashboard_bg2.png", AMBER, "DOWNLOAD, UPDATE, AND MANAGE"),
        ("pager_portal/pager_portal_dashboard_payloads.png", PURPLE, None),
        ("pager_portal/pager_portal_dashboard_recon_payloads.png", HOSTILE, None),
        ("pager_portal/pager_portal_dashboard_themes.png", FRIEND, None),
    ]
    for k, (rel, col, txt) in enumerate(specs):
        img = base_map(W, H, 100 + k, dim=0.45, tint=tuple(int(c * 0.22) for c in col))
        L = canvas(W, H)
        d = ImageDraw.Draw(L, "RGBA")
        cx, cy = 92, 126
        # orbit ring (sat uplink) + data package with down arrow
        d.ellipse([(cx - 78) * S, (cy - 70) * S, (cx + 78) * S, (cy - 18) * S], outline=rgba(col, 255), width=4 * S)
        d.ellipse([(cx - 6 + 64) * S, (cy - 54) * S, (cx + 6 + 64) * S, (cy - 42) * S], fill=rgba(WHITE))
        d.polygon([((cx - 22) * S, (cy - 52) * S), ((cx + 22) * S, (cy - 52) * S), ((cx + 22) * S, (cy + 20) * S), ((cx + 46) * S, (cy + 20) * S), ((cx) * S, (cy + 80) * S), ((cx - 46) * S, (cy + 20) * S), ((cx - 22) * S, (cy + 20) * S)], fill=rgba(col, 220), outline=rgba(WHITE, 200), width=2 * S)
        for j in range(4):
            y = cy - 40 + j * 14
            d.line([((cx - 12) * S, y * S), ((cx + 12) * S, y * S)], fill=rgba(BG0, 200), width=2 * S)
        img.alpha_composite(glow(L, 4, 1.2))
        img = glitch(img, k, n=4, maxshift=8, region=(0, 40, 190, 210))
        if txt:
            plain_text(img, (472, 56), txt, F("mono", 11), col, 255, anchor="ra")
        plain_text(img, (472, 212), "TAK.5 // DATA PACKAGES", F("mono", 8), DIM, 170, anchor="rs")
        save(vignette(img, 0.45), rel, size=(W, H))


def power_menu():
    w, h = 295, 222
    img = gradient(w, h, BASE_TOP, BG0)
    img.alpha_composite(topo_layer(w, h, 120, alpha=90))
    radar(img, -10, 111, 280, NEUTRAL, angle=-15, sweep=50, rings=7, alpha=150)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(293 * S, 0), (293 * S, h * S)], fill=rgba(NEUTRAL, 220), width=2 * S)
    save(img, "power_menu_bg.png", size=(w, h))


def upgrade():
    for rel, txt, col in (("upgrade/checking_for_update-min.png", "Checking for updates", FRIEND), ("upgrade/downloading_upgrade.png", "Downloading Upgrade", AMBER), ("upgrade/validating_upgrade.png", "Validating Upgrade", NEUTRAL)):
        img = base_map(W, H, 130, dim=0.6, tint=tuple(int(c * 0.25) for c in col))
        d = ImageDraw.Draw(img, "RGBA")
        radar(img, 240, 111, 100, col, angle=-30, sweep=60, rings=4, alpha=120, ticks=False)
        d.rounded_rectangle([100 * S, 70 * S, 380 * S, 150 * S], radius=6 * S, fill=rgba((2, 8, 12), 235), outline=rgba(col), width=2 * S)
        brackets(d, 94, 64, 386, 156, col, 255, 10, 2)
        neon_text(img, (240, 102), txt, F("mono", 18), WHITE, chroma=0.7, glow_r=2, anchor="mm")
        plain_text(img, (240, 132), "TAK.5 // DO NOT POWER OFF", F("mono", 9), col, 230, anchor="mm")
        save(vignette(img, 0.4), rel, size=(W, H))


def retints():
    TEAL_D, TEAL_M, TEAL_L = DLG_D, DLG_M, CYAN
    # dialogs keep their exact layout, recolored
    retint("alert_dialog_bg_term_blue.png", DLG_D, DLG_M, FRIEND, overlay_grid=True)
    retint("alert_dialog_bg_term_error.png", (14, 2, 6), (90, 14, 26), (255, 90, 100), overlay_grid=True)
    retint("alert_dialog_bg_term_warning.png", (14, 9, 0), (96, 64, 4), (255, 210, 70), overlay_grid=True)
    retint("confirmation_dialog_bg_term.png", (0, 12, 6), (8, 80, 44), (90, 255, 150), overlay_grid=True)
    retint("optiondialog/option_dialog_bg_narrow.png", DLG_D, KEY_MID, FRIEND, overlay_grid=True)
    retint("optiondialog/option_dialog_bg_windowed.png", DLG_D, KEY_MID, FRIEND, overlay_grid=True)
    retint("optiondialog/option_dialog_bg_windowed_green.png", (0, 12, 6), (6, 66, 38), (90, 255, 150), overlay_grid=True)
    retint("optiondialog/option_dialog_bg_windowed_purple.png", (12, 9, 4), (74, 58, 34), (206, 164, 104), overlay_grid=True)
    retint("optiondialog/option_dialog_bg_windowed_red.png", (14, 2, 6), (84, 12, 22), (255, 90, 100), overlay_grid=True)
    retint("edit_string_dialog_bg.png", DLG_D, GRID_MAJ, tuple(c // 2 for c in FRIEND), overlay_grid=True)
    retint("launch_payload_dialog/launch_payload_bg.png", DLG_D, KEY_MID, (255, 200, 40), overlay_grid=True)
    retint("messagebox.png", (0, 10, 6), (8, 70, 42), (90, 255, 150))
    retint("confirmation_dialog/generic_confirmation_button_deselected.png", (0, 8, 4), (4, 40, 24), (90, 255, 150))
    retint("confirmation_dialog/generic_confirmation_button_selected.png", (0, 10, 6), (10, 90, 50), (180, 255, 200))
    retint("payload_dialog_option_bg.png", TEAL_D, TEAL_M, TEAL_L)
    retint("payload_dialog_selected_box.png", (40, 28, 0), (255, 200, 40), (255, 240, 160))
    retint("optiondialog/button_bg.png", TEAL_D, TEAL_M, TEAL_L)
    retint("optiondialog/button_outline.png", (40, 28, 0), (255, 200, 40), (255, 240, 160))
    for rel in ("payloadlog/payload_complete_indicator.png", "payloadlog/payload_running_indicator.png",
                "payloadlog/payload_error_indicator.png", "payloadlog/payload_stopped_indicator.png"):
        col = {"complete": (64, 255, 140), "running": (255, 200, 40), "error": (255, 64, 80), "stopped": (128, 150, 160)}[rel.split("_")[1]]
        retint(rel, (0, 0, 0), tuple(int(c * 0.45) for c in col), col)
    # keyboards – identical key geometry, tactical colors
    for k in ("hex", "ip", "lower", "numeric", "symbols", "upper"):
        retint("keyboard/keyboard_layout_%s.png" % k, (0, 0, 0), KEY_MID, CYAN)
    for k in ("_hex-bg.png", "_key-bg.png", "_spacebar-4x.png"):
        retint("keyboard/" + k, (0, 0, 0), KEY_MID, CYAN)
    for k in ("divider.png", "divleft.png", "divright.png"):
        retint(k, (0, 0, 0), GRID_MAJ, FRIEND)


def main():
    # 1) start from a byte-for-byte copy of the reference layout
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    # 2) draw
    boot_frames()
    dashboard()
    dash_tiles()
    radar_screen("alerts_dashboard/alerts_bg.png", NEUTRAL)
    radar_screen("payloads_dashboard/recon_payloads_bg.png", HOSTILE)
    payloads_bg()
    recon_dashboard()
    lists()
    lock_screens()
    battery_alerts()
    spinners()
    launch_anim()
    pager_portal()
    power_menu()
    upgrade()
    retints()
    print("art done")


if __name__ == "__main__":
    main()
