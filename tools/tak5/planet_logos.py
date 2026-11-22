#!/usr/bin/env python3
"""TAK THE PLANET! logos, in the same style as the TAK.5 Pineapple Edition shield:
  tak_the_planet_tab.png     curved tab above the TAK.5 shield (unit-tab style)
  tak_the_planet_shield.png  family shield: Tac-Pine in front of the globe
  tak_the_planet_patch.png   round patch (stickers, profile pictures)

usage: planet_logos.py OUT_DIR   (reads ../../art/tak5/ for the shield and Tac-Pine)
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from brand import font, distress, fill_mask, camo, noise
from shade import shade_layer, drop_shadow
import logo3d
import planet

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GOLD = (200, 160, 70)
WHITE = (236, 236, 228)


def brushed(mask, base, seed=1):
    n = noise(mask.size[0], mask.size[1], 3, seed, stretch=(0.04, 1.0), octaves=2)
    a = np.zeros((mask.size[1], mask.size[0], 3), np.float32) + base
    a *= (1 + 0.06 * n)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(mask)
    return img


def erode(m, r):
    return m.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v > 250 else 0)


def arc_text(size, cx, cy, radius, text, fnt, start_deg, spacing=1.0, inside=False, fills=None, seed=3, rough=0.8):
    """Characters along a circle. start_deg = angle of the text center (deg, 0 = up). inside=True reads along the bottom."""
    L = Image.new("RGBA", size, (0, 0, 0, 0))
    widths = [fnt.getlength(c) * spacing for c in text]
    total = sum(widths)
    ang_total = math.degrees(total / radius)
    a = start_deg - ang_total / 2 if not inside else start_deg + ang_total / 2
    for i, ch in enumerate(text):
        w = widths[i]
        da = math.degrees(w / radius)
        mid = a + (da / 2 if not inside else -da / 2)
        if ch.strip():
            l, t, r, b = fnt.getbbox(ch)
            m = Image.new("L", (int(r - l + 40), int(b - t + 40)), 0)
            ImageDraw.Draw(m).text((20 - l, 20 - t), ch, font=fnt, fill=255)
            if rough:
                m = distress(m, seed + i, rough, fnt.size / 300)
            src = fills[i] if fills else WHITE
            g = fill_mask(m, src if isinstance(src, tuple) else src.resize(m.size))
            rot = -mid if not inside else 180 - mid
            g = g.rotate(rot, resample=Image.BICUBIC, expand=True)
            rad = math.radians(mid)
            x = cx + radius * math.sin(rad)
            y = cy - radius * math.cos(rad)
            L.alpha_composite(g, (int(x - g.size[0] / 2), int(y - g.size[1] / 2)))
        a += da if not inside else -da
    return L


def planet_fills(text, size=400, seed=40):
    """White for 'TAK THE ', woodland camo for 'PLANET!'."""
    cm = camo(size, size, "woodland", seed)
    k = text.index("PLANET")
    return [WHITE] * k + [cm] * (len(text) - k)


# ---------------- 5a: tab over the existing TAK.5 shield
def tab_over_shield():
    sh = Image.open(os.path.join(REPO, "art/tak5/tak5_pineapple_edition_shield.png")).convert("RGBA")
    W0, H0 = sh.size
    top = 380
    img = Image.new("RGBA", (W0 + 200, H0 + top), (0, 0, 0, 0))
    cx = img.size[0] // 2
    img.alpha_composite(sh, ((img.size[0] - W0) // 2, top))
    R_out, R_in = 1560, 1330
    cy = top + R_in - 60                               # tab sits just above the shield's peak
    span = 31
    def band(ro, ri, sp):
        m = Image.new("L", img.size, 0)
        pts = [(cx + ro * math.sin(math.radians(t)), cy - ro * math.cos(math.radians(t))) for t in np.linspace(-sp, sp, 90)]
        pts += [(cx + ri * math.sin(math.radians(t)), cy - ri * math.cos(math.radians(t))) for t in np.linspace(sp, -sp, 90)]
        ImageDraw.Draw(m).polygon(pts, fill=255)
        return m
    outer = band(R_out, R_in, span)
    face = band(R_out - 22, R_in + 22, span - 0.9)
    drop_shadow(img, Image.merge("RGBA", [outer] * 4), (12, 18), blur=18, alpha=0.55)
    img.alpha_composite(shade_layer(brushed(outer, GOLD, 4), radius=10, depth=3, ambient=0.55, diffuse=0.8, spec=0.9, shin=30))
    f = Image.new("RGBA", img.size, (0, 0, 0, 0))
    f.paste(Image.new("RGBA", img.size, (12, 12, 14, 255)), (0, 0), face)
    img.alpha_composite(shade_layer(f, radius=22, depth=2.0, ambient=0.75, diffuse=0.5, spec=0.45, shin=18))
    text = "TAK THE PLANET!"
    txt = arc_text(img.size, cx, cy, (R_out + R_in) / 2 - 4, text, font("blackops", 150), 0, spacing=1.04, fills=planet_fills(text))
    drop_shadow(img, txt, (6, 8), blur=5, alpha=0.8)
    img.alpha_composite(shade_layer(txt, radius=3, depth=2.0, ambient=0.85, diffuse=0.3, spec=0.25, shin=20))
    return img.crop(img.getbbox())


# ---------------- art: 3D globe with Tac-Pine in front
def globe_with_pine(r=520):
    g = planet.globe(r, lat0=30, lon0=-86, shade3d=True, glow=False)
    pine = Image.open(os.path.join(REPO, "art/tak5/tac-pine.png")).convert("RGBA")
    pine = pine.crop((0, 0, pine.size[0], int(pine.size[1] * 0.80)))
    pine = pine.crop(pine.getbbox())
    ph = int(g.size[1] * 0.78)
    pine = pine.resize((int(pine.size[0] * ph / pine.size[1]), ph), Image.LANCZOS)
    W = max(g.size[0], pine.size[0])
    out = Image.new("RGBA", (W, int(g.size[1] * 1.12)), (0, 0, 0, 0))
    out.alpha_composite(g, ((W - g.size[0]) // 2, 0))
    px, py = (W - pine.size[0]) // 2, out.size[1] - pine.size[1]
    drop_shadow(out, Image.new("RGBA", out.size, (0, 0, 0, 0)), (0, 0))
    tmp = Image.new("RGBA", out.size, (0, 0, 0, 0))
    tmp.alpha_composite(pine, (px, py))
    drop_shadow(out, tmp, (10, 14), blur=16, alpha=0.6)
    out.alpha_composite(tmp)
    return out.crop(out.getbbox())


# ---------------- 5b: family shield
def family_shield():
    art = globe_with_pine()
    wm = planet.planet_mark(260, two_line=True)
    return logo3d.shield3d(art, (500, 330, 600), wm, rim="gold", subtitle="TAK.5 PINEAPPLE EDITION", sub_col=(232, 196, 96))


# ---------------- 5c: round patch
def round_patch(D=1800):
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    c = D / 2
    def disc(r):
        m = Image.new("L", (D, D), 0)
        ImageDraw.Draw(m).ellipse([c - r, c - r, c + r, c + r], fill=255)
        return m
    R = D / 2 - 30
    drop_shadow(img, Image.merge("RGBA", [disc(R)] * 4), (14, 22), blur=22, alpha=0.5)
    img.alpha_composite(shade_layer(brushed(disc(R), GOLD, 7), radius=14, depth=3, ambient=0.55, diffuse=0.8, spec=0.9, shin=30))
    band = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    band.paste(Image.new("RGBA", (D, D), (14, 14, 16, 255)), (0, 0), disc(R - 34))
    img.alpha_composite(shade_layer(band, radius=20, depth=2.2, ambient=0.75, diffuse=0.5, spec=0.4, shin=18))
    ri = R - 250
    img.alpha_composite(shade_layer(brushed(disc(ri + 18), GOLD, 8), radius=6, depth=3, ambient=0.6, diffuse=0.7, spec=0.8, shin=30))
    field = camo(D, D, "multicam", 3).convert("RGBA")
    field.putalpha(disc(ri))
    img.alpha_composite(field)
    sh = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    sm = ImageChops.subtract(disc(ri), erode(disc(ri), 40).filter(ImageFilter.GaussianBlur(30)))
    sh.putalpha(sm.point(lambda v: int(v * 0.7)))
    img.alpha_composite(sh)
    # art clipped to the field
    art = globe_with_pine(int(ri * 0.62))
    ah = int(ri * 1.85)
    art = art.resize((int(art.size[0] * ah / art.size[1]), ah), Image.LANCZOS)
    tmp = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    tmp.alpha_composite(art, (int(c - art.size[0] / 2), int(c - ri * 0.82)))
    tmp.putalpha(ImageChops.multiply(tmp.split()[3], disc(ri)))
    drop_shadow(img, tmp, (10, 14), blur=14, alpha=0.5)
    img.alpha_composite(tmp)
    # ring text
    rt = R - 145
    top = "TAK THE PLANET!"
    t1 = arc_text((D, D), c, c, rt, top, font("blackops", 150), 0, spacing=1.05, fills=planet_fills(top))
    t2 = arc_text((D, D), c, c, rt + 8, "TAK.5  PINEAPPLE EDITION", font("saira", 112), 180, spacing=1.08, inside=True,
                  fills=[(232, 196, 96)] * 24, rough=0)
    for t in (t1, t2):
        drop_shadow(img, t, (5, 7), blur=5, alpha=0.8)
        img.alpha_composite(shade_layer(t, radius=3, depth=2.0, ambient=0.85, diffuse=0.3, spec=0.25, shin=20))
    d = ImageDraw.Draw(img, "RGBA")
    for ang in (-100, 100):  # star separators
        x, y = c + rt * math.sin(math.radians(ang)), c - rt * math.cos(math.radians(ang))
        pts = []
        for k in range(10):
            rr = 44 if k % 2 == 0 else 18
            a = math.radians(k * 36 - 90)
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        d.polygon(pts, fill=(232, 196, 96, 255))
    return img.crop(img.getbbox())


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "art", "tak5")
    os.makedirs(out, exist_ok=True)
    tab_over_shield().save(os.path.join(out, "tak_the_planet_tab.png"))
    family_shield().save(os.path.join(out, "tak_the_planet_shield.png"))
    round_patch().save(os.path.join(out, "tak_the_planet_patch.png"))
    print("TAK THE PLANET! logos ->", out)
