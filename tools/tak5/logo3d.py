#!/usr/bin/env python3
"""TAK.5 Pineapple Edition shields v2: multicam field (option 1) + wordmark D,
character B, bevelled metal badge look."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from brand import camo, wordmark, font, noise
from shade import shade_layer, drop_shadow
from logo import shield_poly, mask_of, erode, P, W, H, R


def solid(mask, col):
    L = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    L.paste(Image.new("RGBA", mask.size, col + (255,)), (0, 0), mask)
    return L


def brushed_metal(mask, base=(176, 180, 184), seed=1):
    n = noise(mask.size[0], mask.size[1], 3, seed, stretch=(0.04, 1.0), octaves=2)
    a = np.zeros((mask.size[1], mask.size[0], 3), np.float32) + base
    a *= (1 + 0.06 * n)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(mask)
    return img


def shield3d(art, art_box, wm, rim="silver", subtitle="PINEAPPLE EDITION", sub_col=(236, 236, 228), field_kind="multicam", banner_col=(12, 12, 14), rim_w=10, border_w=36):
    outer = mask_of(shield_poly())
    img = Image.new("RGBA", outer.size, (0, 0, 0, 0))
    drop_shadow(img, solid(outer, (0, 0, 0)), (10 * R, 16 * R), blur=18 * R, alpha=0.45)
    # metal rim
    rim_col = {"silver": (178, 182, 186), "gold": (200, 160, 70), "gunmetal": (96, 100, 106)}[rim]
    ring = brushed_metal(outer, rim_col)
    ring = shade_layer(ring, radius=10 * R, depth=3.0, ambient=0.55, diffuse=0.8, spec=0.9, shin=30)
    img.alpha_composite(ring)
    # black border, bevelled
    bmask = erode(outer, rim_w)
    border = shade_layer(solid(bmask, (22, 22, 24)), radius=14 * R, depth=2.5, ambient=0.7, diffuse=0.6, spec=0.5, shin=24)
    img.alpha_composite(border)
    # inner metal lip
    lip = erode(outer, rim_w + border_w)
    img.alpha_composite(shade_layer(brushed_metal(lip, rim_col, 2), radius=4 * R, depth=3, ambient=0.6, diffuse=0.7, spec=0.8, shin=30))
    # field
    fm = erode(outer, rim_w + border_w + 6)
    field = camo(W * R, H * R, field_kind, 3).convert("RGBA")
    field.putalpha(fm)
    img.alpha_composite(field)
    # lighting on field: top glow + inner shadow
    glow = Image.new("RGBA", img.size, (255, 255, 255, 0))
    ImageDraw.Draw(glow).ellipse([W * R * 0.1, -H * R * 0.2, W * R * 0.75, H * R * 0.5], fill=(255, 255, 255, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(90 * R))
    glow.putalpha(ImageChops.multiply(glow.split()[3], fm))
    img.alpha_composite(glow)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sm = ImageChops.subtract(fm, erode(fm, 26).filter(ImageFilter.GaussianBlur(20 * R)))
    sh.putalpha(sm.point(lambda v: int(v * 0.7)))
    img.alpha_composite(sh)
    # center seam (template detail)
    d = ImageDraw.Draw(img, "RGBA")
    d.line(P([(500, 96), (500, 230)]), fill=(0, 0, 0, 110), width=4 * R)
    d.line(P([(500, 880), (500, 1000)]), fill=(0, 0, 0, 110), width=4 * R)
    # art
    if art is not None:
        cx, cy, hgt = art_box
        w = int(art.size[0] * hgt / art.size[1])
        a = art.resize((w * R, hgt * R), Image.LANCZOS)
        drop_shadow(img, Image.new("RGBA", img.size, (0, 0, 0, 0)), (0, 0))
        tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tmp.alpha_composite(a, (int((cx - w / 2) * R), int((cy - hgt / 2) * R)))
        drop_shadow(img, tmp, (8 * R, 14 * R), blur=14 * R, alpha=0.55)
        img.alpha_composite(tmp)
    # banner: silver edge, black face, bevel
    by0, by1 = 618, 872
    ban = [(36, by0), (964, by0), (994, by0 + 32), (964, by1), (36, by1), (6, by0 + 32)]
    bm = Image.new("L", img.size, 0)
    ImageDraw.Draw(bm).polygon(P(ban), fill=255)
    tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    drop_shadow(img, solid(bm, (0, 0, 0)), (6 * R, 12 * R), blur=12 * R, alpha=0.55)
    img.alpha_composite(shade_layer(brushed_metal(bm, rim_col, 5), radius=8 * R, depth=3, ambient=0.55, diffuse=0.8, spec=0.9, shin=30))
    face = erode(bm, 8)
    img.alpha_composite(shade_layer(solid(face, banner_col), radius=18 * R, depth=2.0, ambient=0.75, diffuse=0.5, spec=0.45, shin=18))
    # wordmark D with emboss
    th = 186 * R
    wmr = wm.resize((int(wm.size[0] * th / wm.size[1]), th), Image.LANCZOS)
    t = Image.new("RGBA", img.size, (0, 0, 0, 0))
    t.alpha_composite(wmr, ((W * R - wmr.size[0]) // 2 - 6 * R, int((by0 + 12) * R)))
    drop_shadow(img, t, (4 * R, 6 * R), blur=5 * R, alpha=0.8)
    img.alpha_composite(shade_layer(t, radius=3 * R, depth=2.0, ambient=0.8, diffuse=0.35, spec=0.3, shin=20))
    if subtitle:
        f = font("saira", 34 * R)
        d = ImageDraw.Draw(img, "RGBA")
        d.text((W * R // 2 + 2 * R, int((by1 - 28) * R) + 3 * R), subtitle, font=f, fill=(0, 0, 0, 200), anchor="mm")
        d.text((W * R // 2, int((by1 - 28) * R)), subtitle, font=f, fill=sub_col + (255,), anchor="mm")
    return img.crop(img.getbbox())


if __name__ == "__main__":
    # TAK.5 Pineapple Edition shield (gold rim, multicam field, wordmark D, Tac-Pine B)
    import sys
    import character3d
    out = sys.argv[1] if len(sys.argv) > 1 else "../../art/tak5/tak5_pineapple_edition_shield.png"
    wm = wordmark("blackops", 260, "woodland", seed=8)
    bust = character3d.render("bust", "od")
    bust = bust.crop((0, 0, bust.size[0], int(bust.size[1] * 0.80)))
    bust = bust.crop(bust.getbbox())
    shield3d(bust, (500, 330, 600), wm, rim="gold", subtitle="PINEAPPLE EDITION", sub_col=(232, 196, 96)).save(out)
    print("shield ->", out)
