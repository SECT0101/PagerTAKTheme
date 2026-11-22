#!/usr/bin/env python3
"""Menu selector: a small TAK.5 shield (replaces wargames' ship sprite).

payloads_dashboard/arrow.png (20 x 18) is the cursor next to the highlighted
item in the payload menus; alerts_dashboard/sub.png (26 x 9) is the one in the
alerts and Pager Portal menus. Both are drawn as pixel art from the same shield
outline as the full logo, the big one with a "5" on it.

usage: selector.py THEME_DIR
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from logo import shield_poly

SS = 16                                    # supersampling for the outline
OUTLINE = (16, 16, 18, 255)
FIELD = (150, 122, 84, 255)               # coyote, as the full shield
LIGHT = (216, 186, 134, 255)
SHADE = (104, 84, 56, 255)
MARK = (240, 238, 228, 255)
FIVE = ["111",
        "100",
        "110",
        "001",
        "110"]


def shield_mask(w, h):
    poly = shield_poly()
    xs = [x for x, _ in poly]
    ys = [y for _, y in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).polygon([((x - x0) / (x1 - x0) * (w * SS - 1), (y - y0) / (y1 - y0) * (h * SS - 1)) for x, y in poly], fill=255)
    small = np.array(m.resize((w, h), Image.BOX)) > 110
    return small


def erode(a):
    b = a.copy()
    b[1:, :] &= a[:-1, :]
    b[:-1, :] &= a[1:, :]
    b[:, 1:] &= a[:, :-1]
    b[:, :-1] &= a[:, 1:]
    return b


def draw(W, H, sw, sh, five=True):
    outer = shield_mask(sw, sh)
    inner = erode(outer)
    img = np.zeros((sh, sw, 4), np.uint8)
    img[outer] = OUTLINE
    img[inner] = FIELD
    core = erode(inner)
    for y in range(sh):                                     # bevel: light top-left edge, shade bottom-right
        for x in range(sw):
            if inner[y, x] and not core[y, x]:
                img[y, x] = LIGHT if (x < sw / 2 and y < sh * 0.7) or y <= 2 else SHADE
    ox, oy = sw // 2 - 1, 5
    for r, row in enumerate(FIVE if five else []):
        for c, v in enumerate(row):
            if v == "1":
                img[oy + r, ox + c] = MARK
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(Image.fromarray(img, "RGBA"), ((W - sw) // 2, 0))
    return out


def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else "../../themes/tak5"
    for rel, args in (("payloads_dashboard/arrow.png", (20, 18, 16, 18, True)),
                      ("alerts_dashboard/sub.png", (26, 9, 8, 9, False))):
        path = os.path.join(theme, "assets", rel)
        im = draw(*args)
        im.save(path, optimize=True)
        print("wrote", path, im.size)


if __name__ == "__main__":
    main()
