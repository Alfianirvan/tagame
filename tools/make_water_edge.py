"""Autotile tepi air (sungai/laut) buatan sendiri: assets/tilesets/water_edge.png + dua TileSet.

Tiap tile = sel AIR; indeks tile = bitmask 8 tetangga yang berupa DARAT: N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128
-> koordinat atlas (idx % 16, idx // 16), atlas 256x256 (16x16 tile). Bagian darat tile TRANSPARAN (lantai di bawahnya
yang terlihat: rumput / kanopi hutan), jadi warna tepi selalu cocok. Di sisi air digambar buih putih, di sisi darat tepi
tanah cokelat 3 px yang menjorok ke dalam sel air. Sudut dibulatkan dari mask kontinu 48x48 (tanpa kotak polos).
  water_edge_tileset.tres        : tiap tile bertabrakan (air tak bisa dilewati)
  water_edge_nocol_tileset.tres  : tanpa tabrakan (di bawah jembatan)
Jalankan:  python tools/make_water_edge.py
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
TS = os.path.join(ROOT, "assets", "tilesets")

DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]   # N NE E SE S SW W NW
FOAM, FOAM2 = (214, 234, 248), (128, 180, 230)
LIP_DARK, LIP_MID, LIP_LIGHT = (92, 58, 32), (146, 96, 54), (172, 120, 70)


def box_blur(a, r):
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    out = np.zeros_like(a)
    for dy in range(k):
        for dx in range(k):
            out += p[dy:dy + a.shape[0], dx:dx + a.shape[1]]
    return out / (k * k)


def tile_image(idx, water_px):
    land = np.zeros((48, 48), float)
    for bit, (dx, dy) in enumerate(DIRS):
        if idx & (1 << bit):
            land[(1 + dy) * 16:(2 + dy) * 16, (1 + dx) * 16:(2 + dx) * 16] = 1.0
    # tepi tanah menjorok 3 px ke dalam sel air
    grown = land.copy()
    for _ in range(3):
        g = grown.copy()
        g[1:, :] = np.maximum(g[1:, :], grown[:-1, :]); g[:-1, :] = np.maximum(g[:-1, :], grown[1:, :])
        g[:, 1:] = np.maximum(g[:, 1:], grown[:, :-1]); g[:, :-1] = np.maximum(g[:, :-1], grown[:, 1:])
        grown = g
    m = box_blur(box_blur(grown, 2), 2) > 0.5
    ys, xs = np.mgrid[0:48, 0:48]
    land_pts = np.stack([xs[m], ys[m]], 1).astype(float)
    water_pts = np.stack([xs[~m], ys[~m]], 1).astype(float)
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = out.load()
    for y in range(16):
        for x in range(16):
            X, Y = x + 16, y + 16
            if m[Y, X]:
                if len(water_pts) == 0:
                    continue
                d = np.sqrt(((water_pts - [X, Y]) ** 2).sum(1)).min()
                if d <= 1.2:
                    px[x, y] = LIP_DARK + (255,)
                elif d <= 2.4:
                    px[x, y] = LIP_MID + (255,)
                elif d <= 3.6:
                    px[x, y] = LIP_LIGHT + (255,)
            else:
                base = water_px[x, y]
                if len(land_pts) == 0:
                    px[x, y] = base
                    continue
                d = np.sqrt(((land_pts - [X, Y]) ** 2).sum(1)).min()
                px[x, y] = FOAM + (255,) if d <= 1.4 else FOAM2 + (255,) if d <= 2.6 else base
    return out


def write_tileset(name, collide):
    poly = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[gd_resource type="TileSet" format=3]', "",
             '[ext_resource type="Texture2D" path="res://assets/tilesets/water_edge.png" id="tex_0"]', "",
             '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")']
    for idx in range(256):
        lines.append(f"{idx % 16}:{idx // 16}/0 = 0")
        if collide:
            lines.append(f"{idx % 16}:{idx // 16}/0/physics_layer_0/polygon_0/points = {poly}")
    lines += ["", "[resource]"]
    if collide:
        lines += ["physics_layer_0/collision_layer = 1", "physics_layer_0/collision_mask = 0"]
    lines += ['sources/0 = SubResource("src_0")', ""]
    open(os.path.join(TS, name), "w", encoding="utf-8", newline="\n").write("\n".join(lines))


def main():
    water = Image.open(os.path.join(TS, "Water_tiles.png")).convert("RGBA").crop((6 * 16, 12 * 16, 7 * 16, 13 * 16))
    wpx = water.load()
    atlas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for idx in range(256):
        atlas.paste(tile_image(idx, wpx), ((idx % 16) * 16, (idx // 16) * 16))
    atlas.save(os.path.join(TS, "water_edge.png"))
    write_tileset("water_edge_tileset.tres", True)
    write_tileset("water_edge_nocol_tileset.tres", False)
    print("water_edge.png + 2 tileset dibuat")


if __name__ == "__main__":
    main()
