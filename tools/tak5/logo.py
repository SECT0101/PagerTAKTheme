#!/usr/bin/env python3
"""TAK.5 Pineapple Edition shield logos on the community TAK shield template."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from brand import camo, wordmark, font, noise, fill_mask
from character import character, bez

R = 2  # px per unit
W, H = 1000, 1100


def P(seq): return [(x * R, y * R) for x, y in seq]


def shield_poly():
    right = bez((890, 150), (906, 560), (770, 880), (500, 1066), 60)
    left = [(1000 - x, y) for x, y in right[::-1]]
    return [(500, 26), (890, 150)] + right[1:] + left[1:-1] + [(110, 150)]


def mask_of(poly):
    m = Image.new("L", (W * R, H * R), 0)
    ImageDraw.Draw(m).polygon(P(poly), fill=255)
    return m


def erode(m, r):
    return m.filter(ImageFilter.GaussianBlur(r * R)).point(lambda v: 255 if v > 250 else 0)


def brushed(color, seed=1):
    n = noise(W * R, H * R, 3, seed, stretch=(0.05, 1.0), octaves=2)
    base = np.zeros((H * R, W * R, 3), np.float32) + color
    base *= (1 + 0.07 * n)[..., None]
    return Image.fromarray(base.clip(0, 255).astype(np.uint8))


def grunge(seed=2):
    n = noise(W * R, H * R, 30, seed, octaves=4)
    base = np.zeros((H * R, W * R, 3), np.float32) + (88, 90, 92)
    base *= (1 + 0.22 * n)[..., None]
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    for _ in range(120):
        x, y = rng.integers(0, W * R), rng.integers(0, H * R)
        L, a = rng.integers(30, 260), rng.uniform(-1.2, 1.2)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(200, 200, 200, int(rng.integers(20, 70))), width=1)
    return img.convert("RGB")


def shield(field, art, wm_kwargs, subtitle="PINEAPPLE EDITION", border=(16, 16, 18), bevel=(190, 194, 198), art_box=(500, 360, 600), art_on_top=True, sub_color=(236, 236, 230)):
    img = Image.new("RGBA", (W * R, H * R), (0, 0, 0, 0))
    outer = mask_of(shield_poly())
    # silver bevel ring, black border, field
    img.paste(Image.new("RGBA", img.size, bevel + (255,)), (0, 0), outer)
    img.paste(Image.new("RGBA", img.size, border + (255,)), (0, 0), erode(outer, 7))
    fm = erode(outer, 44)
    img.paste(Image.new("RGBA", img.size, bevel + (255,)), (0, 0), erode(outer, 40))
    img.paste(field.convert("RGBA"), (0, 0), fm)
    # soft light on the field
    glow = Image.new("RGBA", img.size, (255, 255, 255, 0))
    ImageDraw.Draw(glow).ellipse([W * R * 0.15, -H * R * 0.15, W * R * 0.85, H * R * 0.55], fill=(255, 255, 255, 46))
    glow = glow.filter(ImageFilter.GaussianBlur(80 * R))
    glow.putalpha(ImageChops.multiply(glow.split()[3], fm))
    img.alpha_composite(glow)
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sm = ImageChops.subtract(fm, erode(fm, 40).filter(ImageFilter.GaussianBlur(26 * R)))
    shade.putalpha(sm.point(lambda v: int(v * 0.45)))
    img.alpha_composite(shade)
    # center seam lines (TAK template detail)
    d = ImageDraw.Draw(img, "RGBA")
    d.line(P([(500, 70), (500, 210)]), fill=(0, 0, 0, 120), width=4 * R)
    d.line(P([(500, 900), (500, 1010)]), fill=(0, 0, 0, 120), width=4 * R)
    # art
    if art is not None:
        cx, cy, hgt = art_box
        a = art.copy()
        w = int(a.size[0] * hgt / a.size[1])
        a = a.resize((w * R, hgt * R), Image.LANCZOS)
        sh = Image.new("RGBA", a.size, (0, 0, 0, 0))
        sh.putalpha(a.split()[3].filter(ImageFilter.GaussianBlur(10 * R)).point(lambda v: int(v * 0.5)))
        img.alpha_composite(sh, (int((cx - w / 2 + 8) * R), int((cy - hgt / 2 + 12) * R)))
        img.alpha_composite(a, (int((cx - w / 2) * R), int((cy - hgt / 2) * R)))
    # banner
    d = ImageDraw.Draw(img, "RGBA")
    by0, by1 = 618, 872
    ban = [(40, by0), (960, by0), (990, by0 + 30), (960, by1), (40, by1), (10, by0 + 30)]
    d.polygon(P(ban), fill=bevel + (255,))
    ban2 = [(48, by0 + 8), (952, by0 + 8), (978, by0 + 30), (952, by1 - 8), (48, by1 - 8), (22, by0 + 30)]
    d.polygon(P(ban2), fill=(10, 10, 12, 255))
    wm = wordmark(**wm_kwargs)
    th = 188 * R
    wm = wm.resize((int(wm.size[0] * th / wm.size[1]), th), Image.LANCZOS)
    img.alpha_composite(wm, ((W * R - wm.size[0]) // 2 - 10 * R, int((by0 + 10) * R)))
    if subtitle:
        f = font("saira", 34 * R)
        d.text((W * R // 2, int((by1 - 30) * R)), subtitle, font=f, fill=sub_color + (255,), anchor="mm")
    return img.crop(img.getbbox())


if __name__ == "__main__":
    head = character("head")
    opts = []
    opts.append(("1_multicam", shield(camo(W * R, H * R, "multicam", 3), head, dict(fontname="anton", height=220, camo_kind="woodland", seed=5), art_box=(500, 340, 560))))
    opts.append(("2_coyote", shield(brushed((150, 122, 84), 4), head, dict(fontname="saira", height=220, camo_kind="multicam", seed=6), art_box=(500, 340, 560))))
    opts.append(("3_nightops", shield(grunge(5), head, dict(fontname="blackops", height=220, camo_kind="woodland", seed=8), art_box=(500, 340, 560))))
    bust = character("bust", "od")
    bust = bust.crop((0, 0, bust.size[0], int(bust.size[1] * 0.80)))
    bust = bust.crop(bust.getbbox())
    opts.append(("4_woodland_operator", shield(camo(W * R, H * R, "woodland", 9), bust, dict(fontname="russo", height=220, camo_kind="coyote", seed=7), art_box=(500, 318, 590))))
    for n, im in opts:
        im.save("shield_%s.png" % n)
    print("ok")
