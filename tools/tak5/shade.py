"""Cheap 3D lighting for flat vector layers (PIL + numpy).

shade_layer(): normals from a blurred alpha height-field (pillow / bevel look)
shade_ellipsoid(): exact normals of an ellipsoid (fruit, helmet dome)
drop_shadow(): soft contact shadow under a part
"""
import numpy as np
from PIL import Image, ImageFilter

LIGHT = np.array([-0.55, -0.70, 0.95], np.float32)
LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1], np.float32)
HALF /= np.linalg.norm(HALF)


def _apply(arr, nx, ny, nz, mask, ambient, diffuse, spec, shin, spec_col=(255, 255, 255), rim=0.0):
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    sp = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1) ** shin * spec
    shade = ambient + diffuse * lam
    rgb = arr[..., :3].astype(np.float32) * shade[..., None]
    rgb += sp[..., None] * np.array(spec_col, np.float32)
    if rim:
        r = np.clip(1 - nz, 0, 1) ** 2 * rim * np.clip(nx * 0.5 + ny * 0.8 + 0.4, 0, 1)
        rgb += r[..., None] * 120
    out = arr.copy()
    out[..., :3] = np.where(mask[..., None], rgb.clip(0, 255), arr[..., :3]).astype(np.uint8)
    return out


def shade_layer(layer, radius=10, depth=2.5, ambient=0.50, diffuse=0.75, spec=0.35, shin=24, spec_col=(255, 255, 255), rim=0.0):
    bbox = layer.getbbox()
    if not bbox:
        return layer
    pad = int(radius * 3)
    x0, y0 = max(0, bbox[0] - pad), max(0, bbox[1] - pad)
    x1, y1 = min(layer.size[0], bbox[2] + pad), min(layer.size[1], bbox[3] + pad)
    crop = layer.crop((x0, y0, x1, y1))
    arr = np.asarray(crop).copy()
    a = crop.split()[3]
    h = np.asarray(a.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255
    gy, gx = np.gradient(h)
    k = depth * radius
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / L, ny / L, nz / L
    out = _apply(arr, nx, ny, nz, arr[..., 3] > 0, ambient, diffuse, spec, shin, spec_col, rim)
    res = layer.copy()
    res.paste(Image.fromarray(out, "RGBA"), (x0, y0))
    return res


def shade_ellipsoid(layer, cx, cy, rx, ry, ambient=0.42, diffuse=0.85, spec=0.45, shin=18, spec_col=(255, 245, 210), rim=0.6, flatten=1.0):
    arr = np.asarray(layer).copy()
    H, W = arr.shape[:2]
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (x - cx) / rx
    ny = (y - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 0.985)
    nz = np.sqrt(1 - r2) * flatten
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    out = _apply(arr, nx / L, ny / L, nz / L, arr[..., 3] > 0, ambient, diffuse, spec, shin, spec_col, rim)
    return Image.fromarray(out, "RGBA")


def drop_shadow(dst, layer, offset=(6, 10), blur=10, alpha=0.45):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * alpha)))
    dst.alpha_composite(sh, offset)


def gradient_fill(mask, top, bottom, angle_y=True):
    """Vertical gradient clipped to mask (an L image)."""
    W, H = mask.size
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    top, bottom = np.array(top[:3], np.float32), np.array(bottom[:3], np.float32)
    rgb = top * (1 - t[..., None]) + bottom * t[..., None]
    rgb = np.repeat(rgb, W, axis=1)
    out = np.dstack([rgb, np.asarray(mask, np.float32)]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")
