"""Menyiapkan sprite monster Ninja Adventure (Slime, Slime2, Slime3, Mushroom, Mushroom2) agar dibaca EnemySprites:
assets/enemies/ninja/<Nama>/{Idle,Run,Death}/<Aksi>-Sheet.png, frame 32x32 (= skala 2 dari 16x16 asli, nearest).
Jalankan: python tools/make_enemy_ninja.py
"""
import os

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "assets", "ninja", "monsters")
OUT = os.path.join(ROOT, "assets", "enemies", "ninja")
# nama: (file, baris idle, baris jalan)
MON = {"Slime": ("Slime/Slime.png", 1, 0), "Slime2": ("Slime2/Slime2.png", 1, 0), "Slime3": ("Slime3/Slime3.png", 1, 0),
       "Mushroom": ("Mushroom/mushroom.png", 0, 1), "Mushroom2": ("Mushroom2/Mushroom2.png", 0, 1)}


def row(im, r):
    return [im.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16)).resize((32, 32), Image.NEAREST) for c in range(4)]


def save_strip(frames, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    strip = Image.new("RGBA", (32 * len(frames), 32), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (i * 32, 0))
    strip.save(path)


for name, (rel, r_idle, r_run) in MON.items():
    im = Image.open(os.path.join(SRC, rel)).convert("RGBA")
    base = row(im, r_idle)
    save_strip(base, os.path.join(OUT, name, "Idle", "Idle-Sheet.png"))
    save_strip(row(im, r_run), os.path.join(OUT, name, "Run", "Run-Sheet.png"))
    death = []
    for k, (sc, al) in enumerate(((1.0, 1.0), (1.1, 0.9), (0.85, 0.7), (0.55, 0.45), (0.25, 0.2))):
        f = base[0]
        w = max(2, int(32 * sc))
        h = max(2, int(32 * (sc if sc < 1 else 0.9)))
        g = f.resize((w, h), Image.NEAREST)
        a = g.split()[3].point(lambda v: int(v * al))
        g.putalpha(a)
        canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        canvas.alpha_composite(g, ((32 - w) // 2, 32 - h))
        death.append(canvas)
    save_strip(death, os.path.join(OUT, name, "Death", "Death-Sheet.png"))
print("selesai ->", OUT)
