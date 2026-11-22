#!/usr/bin/env python3
"""TAK THE PLANET! pieces for the TAK5 theme and art:
the two-tone stencil slogan (white "TAK THE" + woodland-camo "PLANET!"), an amber/coyote
color split for the glitch frames, and a wireframe globe centered on Tennessee with CoT
links. Coastlines: Natural Earth 1:110m land (public domain), data/ne_110m_land.geojson.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from brand import font, text_mask, shear, distress, fill_mask, camo

HERE = os.path.dirname(os.path.abspath(__file__))
AMBER, WHITE = (255, 200, 40), (236, 236, 228)


# ------------------------------------------------------------------ "TAK THE PLANET!" mark
def planet_mark(height=200, two_line=False, seed=21, outline=None):
    """Family style: white distressed 'TAK THE' + woodland-camo 'PLANET!' (Black Ops One, italic)."""
    f = font("blackops", height)
    a = text_mask("TAK THE", f, pad=0)
    b = text_mask("PLANET!", f, pad=0)
    gap = int(height * 0.28)
    if two_line:
        W = max(a.size[0], b.size[0]) + height
        H = a.size[1] + b.size[1] + int(height * 0.35)
        MA, MB = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
        MA.paste(a, (int(height * 0.25), 0))
        MB.paste(b, (int(height * 0.05), a.size[1] + int(height * 0.3)))
    else:
        W = a.size[0] + gap + b.size[0] + height
        H = max(a.size[1], b.size[1]) + int(height * 0.3)
        MA, MB = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
        MA.paste(a, (int(height * 0.1), int(height * 0.1)))
        MB.paste(b, (int(height * 0.1) + a.size[0] + gap, int(height * 0.1)))
    MA, MB = shear(MA, 0.2), shear(MB, 0.2)
    sc = height / 300
    MA, MB = distress(MA, seed, 1.0, sc), distress(MB, seed + 9, 1.0, sc)
    out = Image.new("RGBA", MA.size, (0, 0, 0, 0))
    if outline:
        both = ImageChops.lighter(MA, MB).filter(ImageFilter.MaxFilter(int(9 * sc) | 1))
        out.alpha_composite(fill_mask(both, outline))
    out.alpha_composite(fill_mask(MA, WHITE))
    out.alpha_composite(fill_mask(MB, camo(MB.size[0], MB.size[1], "woodland", seed + 20)))
    return out.crop(out.getbbox())


def chroma_split(img, shift, a=(255, 200, 40), b=(206, 164, 104), alpha=0.6):
    """Hackers-style color split, in amber + coyote instead of pink/cyan."""
    al = img.split()[3]
    out = Image.new("RGBA", (img.size[0] + 2 * shift, img.size[1]), (0, 0, 0, 0))
    for col, dx in ((a, 0), (b, 2 * shift)):
        L = Image.new("RGBA", img.size, col + (0,))
        L.putalpha(al.point(lambda v: int(v * alpha)))
        out.alpha_composite(L, (dx, 0))
    out.alpha_composite(img, (shift, 0))
    return out


# ------------------------------------------------------------------ globe
_land = None


def land_mask(w=2048):
    """Equirectangular land mask from Natural Earth 110m (public domain)."""
    global _land
    if _land is not None:
        return _land
    gj = json.load(open(os.path.join(HERE, "data", "ne_110m_land.geojson")))
    h = w // 2
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for feat in gj["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for k, ring in enumerate(poly):
                pts = [((lon + 180) / 360 * w, (90 - lat) / 180 * h) for lon, lat in ring]
                d.polygon(pts, fill=255 if k == 0 else 0)
    _land = np.asarray(m) > 127
    return _land


def ortho_inv(x, y, lat0, lon0):
    """Inverse orthographic: unit-disk x,y -> lat, lon (deg); NaN outside."""
    rho = np.sqrt(x * x + y * y)
    c = np.arcsin(np.clip(rho, 0, 1))
    p0 = math.radians(lat0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arcsin(np.cos(c) * math.sin(p0) + np.where(rho > 0, y * np.sin(c) * math.cos(p0) / rho, 0))
        lon = math.radians(lon0) + np.arctan2(x * np.sin(c), rho * np.cos(c) * math.cos(p0) - y * np.sin(c) * math.sin(p0))
    lat, lon = np.degrees(lat), (np.degrees(lon) + 540) % 360 - 180
    out = rho > 1
    lat[out] = np.nan
    lon[out] = np.nan
    return lat, lon


def ortho_fwd(lat, lon, lat0, lon0):
    p, l, p0, l0 = map(math.radians, (lat, lon, lat0, lon0))
    cosc = math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)
    x = math.cos(p) * math.sin(l - l0)
    y = math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0)
    return x, y, cosc > 0


def globe(r, lat0=28, lon0=-86, land_col=(150, 122, 84), sea=(10, 22, 20), grid=(64, 255, 140), rim=(255, 200, 40),
          links=True, glow=True, shade3d=False):
    """Wireframe-and-land globe, r px radius, RGBA (2r+pad square)."""
    pad = int(r * 0.18)
    N = 2 * (r + pad)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    x = (xx - N / 2) / r
    y = -(yy - N / 2) / r
    lat, lon = ortho_inv(x, y, lat0, lon0)
    inside = ~np.isnan(lat)
    lm = land_mask()
    H, W = lm.shape
    li = np.clip(((90 - np.nan_to_num(lat)) / 180 * H).astype(int), 0, H - 1)
    lj = np.clip(((np.nan_to_num(lon) + 180) / 360 * W).astype(int), 0, W - 1)
    land = inside & lm[li, lj]
    img = np.zeros((N, N, 4), np.float32)
    rho = np.sqrt(x * x + y * y)
    limb = np.clip(1 - rho, 0, 1) ** 0.35
    img[inside, :3] = np.array(sea, np.float32)
    img[land, :3] = np.array(land_col, np.float32)
    img[inside, :3] *= (0.45 + 0.55 * limb[inside])[:, None]
    img[inside, 3] = 255
    # coastline: land edges
    lmask = Image.fromarray((land * 255).astype(np.uint8))
    edge = np.asarray(ImageChops.subtract(lmask.filter(ImageFilter.MaxFilter(3)), lmask)) > 0
    img[edge & inside, :3] = np.array(rim, np.float32) * 0.85
    # graticule every 30 deg (lat) / 30 deg (lon), thin
    step = 30
    lw = 1.2 * 90 / r * 1.0
    with np.errstate(invalid="ignore"):
        dlat = np.abs(((lat + step / 2) % step) - step / 2)
        dlon = np.abs(((lon + step / 2) % step) - step / 2) * np.cos(np.radians(np.nan_to_num(lat)))
    g = inside & ((dlat < lw) | (dlon < lw))
    img[g, :3] = img[g, :3] * 0.35 + np.array(grid, np.float32) * 0.65
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGBA")
    if shade3d:
        from shade import shade_ellipsoid
        out = shade_ellipsoid(out, N / 2, N / 2, r, r, ambient=0.55, diffuse=0.75, spec=0.35, shin=18, rim=0.5)
    d = ImageDraw.Draw(out, "RGBA")
    # CoT links from Tennessee to a few far points (great circles)
    home = (36.0, -86.6)
    if links:
        for dest in ((51.5, -0.1), (21.3, -157.9), (64.8, -147.7), (-15.8, -47.9), (35.7, 139.7)):
            pts = []
            for t in np.linspace(0, 1, 60):
                la, lo = slerp(home, dest, t)
                px, py, vis = ortho_fwd(la, lo, lat0, lon0)
                pts.append((N / 2 + px * r * (1 + 0.12 * math.sin(math.pi * t)), N / 2 - py * r * (1 + 0.12 * math.sin(math.pi * t)), vis))
            seg = []
            for px, py, vis in pts:
                if vis:
                    seg.append((px, py))
                elif len(seg) > 1:
                    d.line(seg, fill=rim + (200,), width=max(1, r // 60))
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                d.line(seg, fill=rim + (200,), width=max(1, r // 60))
                ex, ey = seg[-1]
                d.ellipse([ex - r / 40, ey - r / 40, ex + r / 40, ey + r / 40], fill=(255, 64, 80, 230))
    # Tennessee self marker (TAK chevron)
    px, py, vis = ortho_fwd(*home, lat0, lon0)
    if vis:
        cx, cy, s = N / 2 + px * r, N / 2 - py * r, r / 9
        d.polygon([(cx, cy - s), (cx + 0.72 * s, cy + 0.85 * s), (cx, cy + 0.45 * s), (cx - 0.72 * s, cy + 0.85 * s)], fill=AMBER + (255,), outline=(20, 16, 8, 255))
    # rim + glow
    d.ellipse([N / 2 - r, N / 2 - r, N / 2 + r, N / 2 + r], outline=rim + (230,), width=max(1, r // 45))
    if glow:
        gl = Image.new("RGBA", out.size, (0, 0, 0, 0))
        ImageDraw.Draw(gl).ellipse([N / 2 - r, N / 2 - r, N / 2 + r, N / 2 + r], outline=grid + (160,), width=max(2, r // 18))
        gl = gl.filter(ImageFilter.GaussianBlur(r / 14))
        gl.alpha_composite(out)
        out = gl
    return out


def slerp(a, b, t):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    p1 = np.array([math.cos(la1) * math.cos(lo1), math.cos(la1) * math.sin(lo1), math.sin(la1)])
    p2 = np.array([math.cos(la2) * math.cos(lo2), math.cos(la2) * math.sin(lo2), math.sin(la2)])
    om = math.acos(np.clip(p1 @ p2, -1, 1))
    p = (math.sin((1 - t) * om) * p1 + math.sin(t * om) * p2) / math.sin(om)
    return math.degrees(math.asin(p[2])), math.degrees(math.atan2(p[1], p[0]))
