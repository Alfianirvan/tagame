"""Membuat tekstur TANAH TERKUTUK (file baru, aset asli tidak diubah) dari CraftPix Cursed Land:
warna dasar ungu-cokelat (warna lantai Ground.png) + bercak (spots.png) + retakan/akar (details.png) + urat merah
(objects/Veins_*) yang menjalar keluar dari tengah, dengan tepi organik bergerigi per 2 px (gaya pixel art).

Hasil (assets/props/generated/):
  cursed_arena.png  - sekeliling arena Golem (pusat hutan)
  cursed_desa4.png  - di dalam kubah segel Desa 4 (memudar setelah Kristal diletakkan)
Jalankan:  python tools/make_cursed_ground.py
"""
import math
import os
import random

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CL = os.path.join(ROOT, "assets", "craftpix", "cursed_land")
OUT = os.path.join(ROOT, "assets", "props", "generated")

BASE = np.array([157, 98, 89])        # lantai gelap Ground.png
DARK = np.array([140, 86, 80])
LIGHT = np.array([205, 150, 115])     # lantai terang Ground.png (dipakai bercak)


def blobs(path):
    """Potong semua gumpalan terpisah (komponen alfa) dari sebuah lembar sprite."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)[:, :, 3] > 0
    h, w = a.shape
    seen = np.zeros_like(a)
    out = []
    for y in range(h):
        for x in range(w):
            if a[y, x] and not seen[y, x]:
                st = [(y, x)]
                seen[y, x] = True
                xs, ys = [x], [y]
                while st:
                    cy, cx = st.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                st.append((ny, nx))
                                xs.append(nx)
                                ys.append(ny)
                box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
                if (box[2] - box[0]) * (box[3] - box[1]) >= 9:
                    out.append(im.crop(box))
    return out


def value_noise(w, h, cell, seed):
    r = np.random.RandomState(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = r.rand(gh, gw)
    ys, xs = np.mgrid[0:h, 0:w] / cell
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def make(name, w, h, seed, veins=6, edge=0.18):
    rnd = random.Random(seed)
    cx, cy = w / 2, h / 2
    ys, xs = np.mgrid[0:h, 0:w]
    # jarak elips ternormalisasi + noise -> tepi organik
    d = np.hypot((xs - cx) / (w / 2), (ys - cy) / (h / 2))
    n = value_noise(w, h, 28, seed) * 0.75 + value_noise(w, h, 10, seed + 1) * 0.25
    d2 = d + (n - 0.5) * 0.28
    inside = (d2 < 1.0 - edge * 0.2) & (d < 1.0)   # tanpa pulau-pulau kecil di sudut
    # warna dasar dengan noise gelap-terang lembut, dikuantisasi agar tetap "pixel art"
    shade = value_noise(w, h, 18, seed + 2)
    col = np.where(shade[..., None] < 0.38, DARK, BASE).astype(np.uint8)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = col
    # tepi bergerigi per 2 px
    blocky = inside[::2, ::2].repeat(2, 0).repeat(2, 1)[:h, :w]
    img[..., 3] = np.where(blocky, 255, 0)
    canvas = Image.fromarray(img, "RGBA")
    mask = Image.fromarray((blocky * 255).astype(np.uint8), "L")

    def stamp(piece, x, y, tint=None):
        if tint is not None:
            arr = np.array(piece).astype(int)
            arr[..., :3] = np.clip(arr[..., :3] * 0 + tint, 0, 255)
            piece = Image.fromarray(arr.astype(np.uint8), "RGBA")
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.alpha_composite(piece, (int(x - piece.width / 2), int(y - piece.height / 2)))
        # hanya di dalam bentuk tanah
        la = np.array(layer)
        la[..., 3] = (la[..., 3].astype(int) * (np.array(mask) > 0)).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(la, "RGBA"))

    spots = blobs(os.path.join(CL, "spots.png"))
    details = blobs(os.path.join(CL, "details.png"))
    area = w * h
    for _ in range(int(area / 1400)):              # bercak terang
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if inside[int(y), int(x)]:
            stamp(rnd.choice(spots), x, y, LIGHT if rnd.random() < 0.7 else BASE + 18)
    for _ in range(int(area / 2600)):              # retakan, akar kecil, tulang kecil
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if inside[int(y), int(x)]:
            stamp(rnd.choice(details), x, y)
    # urat merah menjalar dari tengah ke luar
    vein_files = [f"Veins_shadow1_{k}.png" for k in (1, 2, 3, 4)]
    for k in range(veins):
        v = Image.open(os.path.join(CL, "objects", rnd.choice(vein_files))).convert("RGBA")
        v = v.crop(v.getbbox())
        if rnd.random() < 0.5:
            v = v.transpose(Image.FLIP_LEFT_RIGHT)
        if rnd.random() < 0.5:
            v = v.transpose(Image.FLIP_TOP_BOTTOM)
        ang = (k + rnd.uniform(-0.3, 0.3)) / veins * math.tau
        r = rnd.uniform(0.38, 0.6)
        stamp(v, cx + math.cos(ang) * r * w / 2, cy + math.sin(ang) * r * h / 2)
    os.makedirs(OUT, exist_ok=True)
    canvas.save(os.path.join(OUT, name + ".png"))
    print(name, canvas.size)


if __name__ == "__main__":
    make("cursed_arena", 640, 500, 51, veins=8)
    make("cursed_desa4", 300, 224, 52, veins=4)
