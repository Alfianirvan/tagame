"""Helper bentuk wilayah ORGANIK (tidak persegi) untuk semua generator scene.

Ide: wilayah yang bisa dijalani = area di sekitar "kerangka" (jalan, pad bonfire/checkpoint, arena boss)
yang tepinya dibuat berkelok oleh noise halus, mirip jalur berliku di peta_dunia.png.
Di luar area itu diisi penghalang sesuai biome (air, tebing, dsb.) oleh masing-masing generator.

Dipakai oleh gen_village.py, gen_region.py, gen_ch2.py ... gen_ch5.py.
"""
import numpy as np
from PIL import Image

TILE = 16


def grid(map_w, map_h):
    """Koordinat pusat tiap tile (px): gx, gy berukuran (map_w, map_h)."""
    gx = (np.arange(map_w) * TILE + 8)[:, None] * np.ones((1, map_h))
    gy = (np.arange(map_h) * TILE + 8)[None, :] * np.ones((map_w, 1))
    return gx, gy


def smooth_noise(gx, gy, seed, scales=(420.0, 170.0, 70.0), amps=(1.0, 0.55, 0.3)):
    """Noise halus ~[-1, 1] dari jumlah gelombang sinus berfase acak (tanpa library tambahan)."""
    rng = np.random.RandomState(seed)
    out = np.zeros(gx.shape)
    for sc, amp in zip(scales, amps):
        for _ in range(3):
            ang = rng.uniform(0, 2 * np.pi)
            ph = rng.uniform(0, 2 * np.pi)
            out += amp * np.sin((gx * np.cos(ang) + gy * np.sin(ang)) / sc * 2 * np.pi + ph)
    return out / (sum(amps) * 1.6)


def polyline_samples(points, step=20.0):
    """Titik-titik rapat sepanjang polyline [(x, y), ...] -> array (N, 2)."""
    out = []
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        n = max(1, int(np.hypot(x1 - x0, y1 - y0) / step))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(tuple(points[-1]))
    return np.array(out, float)


def organic_mask(gx, gy, skeleton, r_base, r_amp, seed):
    """Mask bool (True = bisa dijalani).

    skeleton: list (x, y, r_ekstra); jarak ke tiap titik dikurangi r_ekstra (pad/arena lebih lebar).
    r_base  : lebar dasar dari kerangka (px); r_amp: simpangan noise (px).
    """
    sk = np.array(skeleton, float)
    best = np.full(gx.shape, 1e9)
    for i in range(0, len(sk), 64):
        chunk = sk[i:i + 64]
        d = np.hypot(gx[..., None] - chunk[:, 0], gy[..., None] - chunk[:, 1]) - chunk[:, 2]
        best = np.minimum(best, d.min(axis=-1))
    mask = best <= r_base + r_amp * smooth_noise(gx, gy, seed)
    return remove_specks(mask)


def remove_specks(mask, min_cells=40):
    """Buang pulau kecil (< min_cells tile) supaya tepi tidak berbintik."""
    seen = np.zeros(mask.shape, bool)
    out = mask.copy()
    w, h = mask.shape
    for sx in range(w):
        for sy in range(h):
            if not mask[sx, sy] or seen[sx, sy]:
                continue
            stack, comp = [(sx, sy)], []
            seen[sx, sy] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[nx, ny] and not seen[nx, ny]:
                        seen[nx, ny] = True
                        stack.append((nx, ny))
            if len(comp) < min_cells:
                for x, y in comp:
                    out[x, y] = False
    return out


def erode(mask, n=1):
    """Kikis tepi mask sebanyak n tile (4 arah)."""
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1, constant_values=False)
        m = m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m


def dilate(mask, n=1):
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1, constant_values=False)
        m = m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def walkable_at(mask, x, y):
    """True bila titik px (x, y) berada di tile yang bisa dijalani."""
    tx, ty = int(x // TILE), int(y // TILE)
    if 0 <= tx < mask.shape[0] and 0 <= ty < mask.shape[1]:
        return bool(mask[tx, ty])
    return False


def save_preview(path, mask, points=(), scale=2):
    """Gambar pratinjau (hijau = jalan, biru = penghalang, titik merah = objek) untuk dicek mata."""
    w, h = mask.shape
    im = np.zeros((h, w, 3), np.uint8)
    im[...] = (40, 80, 150)
    im[mask.T] = (90, 170, 80)
    for x, y in points:
        tx, ty = int(x // TILE), int(y // TILE)
        if 0 <= tx < w and 0 <= ty < h:
            im[ty, tx] = (230, 40, 40) if mask[tx, ty] else (255, 255, 0)
    Image.fromarray(im).resize((w * scale, h * scale), Image.NEAREST).save(path)


def region_mask(name, map_w, map_h, seed=1, wobble=0.12):
    """Siluet wilayah dari Peta Dunia (tools/region_masks/<name>.png, dibuat extract_regions.py),
    diregangkan ke ukuran scene (map_w x map_h tile). True = daratan wilayah."""
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "region_masks", name + ".png")
    m = np.array(Image.open(path).convert("L")) > 127
    m = ~remove_specks(~m, 60)                           # tutup lubang kecil (bekas label/penanda)
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((map_w, map_h), Image.BICUBIC)
    val = np.array(im).T.astype(float) / 255.0           # (map_w, map_h)
    gx, gy = grid(map_w, map_h)
    val = val + wobble * smooth_noise(gx, gy, seed, scales=(300.0, 120.0, 55.0))
    return remove_specks(val > 0.5)
