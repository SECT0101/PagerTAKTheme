#!/usr/bin/env python3
"""Project shields for SECT0101's TAK projects, on the same template as the
TAK.5 Pineapple Edition shield, each with the project's name on the banner:
PagerTAK (gold, Tac-Pine), OpenWrt-TAK (gunmetal, router) and LiveU-TAK
(silver, camera).

usage: family.py OUT_DIR
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter
from shade import shade_layer, drop_shadow
from logo3d import shield3d
from brand import wordmark, font, text_mask, fill_mask, shear, distress, camo

S = 1200                                   # art canvas size


def layer():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def shape(draw_fn, col):
    m = Image.new("L", (S, S), 0)
    draw_fn(ImageDraw.Draw(m))
    L = layer()
    L.paste(Image.new("RGBA", (S, S), col + (255,)), (0, 0), m)
    return L


def put(img, L, radius=14, depth=2.6, shadow=True, **kw):
    if shadow:
        drop_shadow(img, L, (10, 16), blur=14, alpha=0.5)
    img.alpha_composite(shade_layer(L, radius=radius, depth=depth, **kw))


def arcs(img, cx, cy, rs, col, start, end, w=34):
    for r in rs:
        put(img, shape(lambda d, r=r: d.arc([cx - r, cy - r, cx + r, cy + r], start, end, fill=255, width=w), col),
            radius=6, depth=2.0, spec=0.5)


def router_art():
    """Field router / gateway: rugged box, four antennas, link LEDs, signal arcs."""
    img = layer()
    body_col, dark, coy = (58, 62, 58), (30, 32, 30), (176, 146, 98)
    for x, tilt in ((300, -70), (470, -25), (730, 25), (900, 70)):       # antennas
        put(img, shape(lambda d, x=x, t=tilt: d.line([(x, 640), (x + t, 250)], fill=255, width=46), dark), radius=10)
        put(img, shape(lambda d, x=x, t=tilt: d.ellipse([x + t - 30, 222, x + t + 30, 282], fill=255), dark), radius=10)
    put(img, shape(lambda d: d.rounded_rectangle([150, 600, 1050, 900], 60, fill=255), body_col), radius=22, depth=3.0, spec=0.45)
    put(img, shape(lambda d: d.rounded_rectangle([200, 650, 1000, 720], 24, fill=255), coy), radius=10, shadow=False)
    for i, c in enumerate([(64, 255, 140)] * 4 + [(255, 200, 40)]):                       # LEDs
        put(img, shape(lambda d, i=i: d.ellipse([250 + i * 120, 770, 300 + i * 120, 820], fill=255), c), radius=8, shadow=False, spec=0.9)
    put(img, shape(lambda d: d.rounded_rectangle([860, 760, 990, 830], 14, fill=255), dark), radius=6, shadow=False)
    arcs(img, 600, 300, (90, 170, 250), (232, 196, 96), 215, 325)
    return img.crop(img.getbbox())


def video_art():
    """Field video: camera with a bonded-cellular transmitter, antennas and signal arcs."""
    img = layer()
    body, dark, coy, lens = (54, 58, 54), (28, 30, 28), (176, 146, 98), (20, 24, 30)
    put(img, shape(lambda d: d.rounded_rectangle([150, 470, 760, 860], 70, fill=255), body), radius=24, depth=3.0, spec=0.45)
    put(img, shape(lambda d: d.polygon([(740, 560), (1020, 430), (1020, 900), (740, 770)], fill=255), dark), radius=18)
    put(img, shape(lambda d: d.ellipse([930, 470, 1080, 860], fill=255), lens), radius=26, spec=0.9, shin=40)
    put(img, shape(lambda d: d.ellipse([960, 560, 1050, 770], fill=255), (60, 90, 120)), radius=16, shadow=False, spec=1.0, shin=50)
    put(img, shape(lambda d: d.rounded_rectangle([200, 380, 560, 480], 30, fill=255), coy), radius=12)      # transmitter on top
    for x in (250, 360, 470):
        put(img, shape(lambda d, x=x: d.line([(x, 390), (x - 40, 170)], fill=255, width=34), dark), radius=8)
    put(img, shape(lambda d: d.ellipse([230, 540, 330, 640], fill=255), (255, 64, 80)), radius=10, shadow=False, spec=0.9)  # REC
    put(img, shape(lambda d: d.rounded_rectangle([380, 560, 700, 780], 24, fill=255), (40, 70, 60)), radius=8, shadow=False)
    arcs(img, 330, 230, (110, 190), (232, 196, 96), 200, 300)
    return img.crop(img.getbbox())


def name_mark(first, second, fontname="blackops", height=260, camo_kind="woodland", seed=8, first_color=(245, 245, 240), fit=4.6):
    """Project wordmark in the TAK.5 style: distressed italic white word, camo second word,
    underline with the square dot. Padded so it fits the shield banner (width/height <= fit)."""
    f = font(fontname, height)
    a, b = text_mask(first, f, pad=0), text_mask(second, f, pad=0)
    gap = int(height * 0.12)
    W = a.size[0] + gap + b.size[0] + int(height * 0.5)
    H = int(max(a.size[1], b.size[1]) * 1.45)
    x0, y0 = int(height * 0.12), int(height * 0.08)
    MA, MB, ML = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    MA.paste(a, (x0, y0)); MB.paste(b, (x0 + a.size[0] + gap, y0))
    ly, lt = y0 + a.size[1] + int(height * 0.08), max(3, int(height * 0.035))
    d = ImageDraw.Draw(ML); ds = int(height * 0.13)
    dx1 = x0 + a.size[0] + gap - int(height * 0.04); dx0 = dx1 - ds
    d.rectangle([dx0, ly + lt + int(height * 0.02) - ds, dx1, ly + lt + int(height * 0.02)], fill=255)
    d.rectangle([x0 + int(height * 0.04), ly, dx0 - int(height * 0.05), ly + lt], fill=255)
    MA, MB, ML = [distress(shear(m, 0.2), seed + k, 1.0, height / 300) for k, m in enumerate((MA, MB, ML))]
    src = camo(MA.size[0], MA.size[1], camo_kind, seed=seed + 20)
    out = Image.new("RGBA", MA.size, (0, 0, 0, 0))
    out.alpha_composite(fill_mask(MA, first_color))
    out.alpha_composite(fill_mask(ML, src)); out.alpha_composite(fill_mask(MB, src))
    out = out.crop(out.getbbox())
    if out.size[0] / out.size[1] > fit:                      # pad height so the banner scales it to fit
        h = int(out.size[0] / fit)
        pad = Image.new("RGBA", (out.size[0], h), (0, 0, 0, 0))
        pad.alpha_composite(out, (0, (h - out.size[1]) // 2))
        out = pad
    return out


def main():
    import character3d
    out = sys.argv[1] if len(sys.argv) > 1 else "../../art/family"
    os.makedirs(out, exist_ok=True)
    bust = character3d.render("bust", "od")
    bust = bust.crop((0, 0, bust.size[0], int(bust.size[1] * 0.80)))
    bust = bust.crop(bust.getbbox())
    for name, art, box, wm, kw in (
            ("pagertak_shield.png", bust, (500, 330, 600), name_mark("PAGER", "TAK"),
             dict(rim="gold", subtitle="PINEAPPLE EDITION", sub_col=(232, 196, 96))),
            ("openwrt_tak_shield.png", router_art(), (500, 360, 520), name_mark("OPENWRT", "TAK", camo_kind="woodland"),
             dict(rim="gunmetal", subtitle="TAK GATEWAY", sub_col=(150, 220, 255), field_kind="woodland")),
            ("liveu_tak_shield.png", video_art(), (500, 350, 480), name_mark("LIVEU", "TAK", camo_kind="multicam"),
             dict(rim="silver", subtitle="VIDEO TO TAK", sub_col=(255, 96, 96), field_kind="coyote"))):
        shield3d(art, box, wm, **kw).save(os.path.join(out, name))
        print("wrote", name)


if __name__ == "__main__":
    main()
