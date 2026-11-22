#!/usr/bin/env python3
"""Home-menu icons in the theme's own color.

The stock dashboard icons are magenta (and the Pager Portal logo orange) in the
PNG files. The firmware recolors them at runtime, so the Pager never shows
those colors, but the files are repainted coyote tan so the theme has no pink
anywhere (repo previews, file browsers). Only the color changes; the shapes
and transparency stay the same.

usage: icons.py THEME_DIR
"""
import os
import sys
from PIL import Image

TAN = (216, 186, 134)
ICONS = ["alerts", "payloads", "pineap", "recon", "settings", "pagerportal_logo"]


def main():
    theme = sys.argv[1] if len(sys.argv) > 1 else "../../themes/tak5"
    for name in ICONS:
        path = os.path.join(theme, "assets", "dashboard", name + ".png")
        im = Image.open(path).convert("RGBA")
        solid = Image.new("RGBA", im.size, TAN + (255,))
        solid.putalpha(im.getchannel("A"))
        solid.save(path, optimize=True)
        print("recolored", path)


if __name__ == "__main__":
    main()
