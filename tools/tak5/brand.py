#!/usr/bin/env python3
"""TAK.5 brand kit: camo textures and Hak5-style 'TAK.5' wordmarks."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONTS = os.environ.get("TAK5_FONTS", "fonts")


def font(name, size):
    files = {
        "anton": "Anton-Regular.ttf",
        "saira": "SairaCondensed-Black.ttf",
        "sairax": "SairaExtraCondensed-Black.ttf",
        "russo": "RussoOne-Regular.ttf",
        "blackops": "BlackOpsOne-Regular.ttf",
        "teko": "Teko%5Bwght%5D.ttf",
        "oswald": "Oswald%5Bwght%5D.ttf",
        "mono": "ShareTechMono-Regular.ttf",
        "tech": "ShareTech-Regular.ttf",
    }
    f = ImageFont.truetype(os.path.join(FONTS, files[name]), size)
    if name in ("teko", "oswald"):
        try:
            f.set_variation_by_axes([700])
        except Exception:
            pass
    return f


# ------------------------------------------------------------------ noise
def noise(w, h, scale, seed, stretch=(1.0, 1.0), octaves=3):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cw = max(2, int(w / scale * stretch[0] * (2 ** o)))
        ch = max(2, int(h / scale * stretch[1] * (2 ** o)))
        small = rng.random((ch, cw)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.45
    acc /= tot
    acc = (acc - acc.mean()) / (acc.std() + 1e-6)
    return acc


CAMO = {
    # name: base, [(color, scale, threshold, stretch)]
    "woodland": ((150, 140, 100), [((70, 88, 46), 120, -0.2, (1.6, 1)), ((104, 76, 46), 90, 0.45, (1.8, 1)), ((28, 28, 24), 60, 1.0, (2.2, 1))]),
    "multicam": ((186, 168, 128), [((128, 132, 90), 90, 0.0, (1, 1.8)), ((132, 102, 70), 70, 0.55, (1, 1.6)), ((92, 72, 50), 50, 1.0, (1, 1.4)), ((240, 228, 196), 40, 1.6, (1, 1))]),
    "coyote": ((150, 122, 84), [((126, 100, 66), 80, 0.1, (1.5, 1)), ((176, 150, 108), 60, 0.8, (1.5, 1)), ((96, 76, 50), 40, 1.3, (1.5, 1))]),
    "night": ((40, 44, 46), [((62, 68, 64), 90, 0.0, (1.6, 1)), ((24, 26, 28), 60, 0.6, (1.8, 1)), ((88, 96, 90), 40, 1.4, (1, 1))]),
}


def camo(w, h, kind="woodland", seed=7, digital=0):
    base, layers = CAMO[kind]
    img = np.zeros((h, w, 3), np.float32)
    img[:] = base
    for i, (col, sc, th, st) in enumerate(layers):
        n = noise(w, h, sc, seed + i * 17, stretch=st)
        if digital:
            n = np.asarray(Image.fromarray(n).resize((max(1, w // digital), max(1, h // digital)), Image.BILINEAR).resize((w, h), Image.NEAREST))
        img[n > th] = col
    out = Image.fromarray(img.astype(np.uint8), "RGB")
    if not digital:
        out = out.filter(ImageFilter.ModeFilter(5))
    return out


# ------------------------------------------------------------------ distress
def distress(mask, seed=3, amount=1.0, scale=1.0):
    """Organic worn edges plus speckle wear, like a screen-printed patch."""
    w, h = mask.size
    r = max(1.0, 2.2 * scale)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    n = noise(w, h, 5 * scale, seed, octaves=2)
    m = m + n * 0.16 * amount
    out = (m > 0.5).astype(np.float32)
    sp = noise(w, h, 2.2 * scale, seed + 1, octaves=1)
    out *= (sp > -2.3 / amount)
    blobs = noise(w, h, 14 * scale, seed + 2, octaves=2)
    out *= ~((blobs < -2.0 / amount) & (sp < -0.8))
    im = Image.fromarray((out * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.6 * scale))
    return im.point(lambda v: 255 if v > 127 else 0)


def shear(img, k=0.2):
    w, h = img.size
    extra = int(abs(k) * h)
    return img.transform((w + extra, h), Image.AFFINE, (1, k, -extra if k > 0 else 0, 0, 1, 0), Image.BICUBIC)


def text_mask(text, fnt, pad=20):
    l, t, r, b = fnt.getbbox(text)
    m = Image.new("L", (r - l + pad * 2, b - t + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - l, pad - t), text, font=fnt, fill=255)
    return m


def fill_mask(mask, source):
    """Fill a mask with an RGB(A) source (color tuple or image)."""
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    if isinstance(source, tuple):
        src = Image.new("RGBA", mask.size, source + (255,) if len(source) == 3 else source)
    else:
        src = source.convert("RGBA").resize(mask.size) if source.size != mask.size else source.convert("RGBA")
    out.paste(src, (0, 0), mask)
    return out


def wordmark(fontname="anton", height=300, camo_kind="woodland", tak_color=(245, 245, 240), five_scale=1.42,
             italic=0.2, rough=1.0, seed=5, dot=True, outline=None, five_camo=True, five_color=None):
    """Hak5-style 'TAK.5': distressed italic TAK, underline ending in a square dot, oversized camo 5."""
    f = font(fontname, height)
    tak = text_mask("TAK", f, pad=0)
    f5 = font(fontname, int(height * five_scale))
    five = text_mask("5", f5, pad=0)
    gap = int(height * 0.10)
    W = tak.size[0] + gap + five.size[0] + int(height * 0.9)
    H = int(five.size[1] * 1.25)
    base_y = int(H * 0.08) + five.size[1]          # bottom of the 5
    tak_y = base_y - int(five.size[1] * 0.12) - tak.size[1]  # TAK sits a little above the 5's foot
    x0 = int(height * 0.1)
    M_tak = Image.new("L", (W, H), 0)
    M_tak.paste(tak, (x0, tak_y))
    # underline + square dot (the Hak5 "dot")
    M_line = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(M_line)
    gap = int(height * 0.24)
    ly = tak_y + tak.size[1] + int(height * 0.07)
    lt = max(3, int(height * 0.035))
    x5 = x0 + tak.size[0] + gap
    if dot:
        ds = int(height * 0.13)                       # the period / Hak5 dot
        dx1 = x5 - int(height * 0.035)
        dx0 = dx1 - ds
        dy1 = ly + lt + int(height * 0.02)
        ld.rectangle([dx0, dy1 - ds, dx1, dy1], fill=255)
        ld.rectangle([x0 + int(height * 0.04), ly, dx0 - int(height * 0.05), ly + lt], fill=255)
        M_tak.paste(Image.new("L", (1, 1), 0), (0, 0))
    M_five = Image.new("L", (W, H), 0)
    M_five.paste(five, (x5, base_y - five.size[1]))
    # italic shear + distress
    sk = lambda m: shear(m, italic)
    M_tak, M_line, M_five = sk(M_tak), sk(M_line), sk(M_five)
    sc = height / 300
    if rough:
        M_tak = distress(M_tak, seed, rough, sc)
        M_five = distress(M_five, seed + 9, rough, sc)
        M_line = distress(M_line, seed + 4, rough * 0.6, sc)
    size = M_tak.size
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    five_src = camo(size[0], size[1], camo_kind, seed=seed + 20) if five_camo else Image.new("RGB", size, five_color)
    if outline:
        both = ImageChops.lighter(ImageChops.lighter(M_tak, M_five), M_line)
        o = both.filter(ImageFilter.MaxFilter(int(9 * sc) | 1))
        out.alpha_composite(fill_mask(o, outline))
    out.alpha_composite(fill_mask(M_tak, tak_color))
    out.alpha_composite(fill_mask(M_line, five_src if five_camo else five_color))
    out.alpha_composite(fill_mask(M_five, five_src if five_camo else five_color))
    return out.crop(out.getbbox())
