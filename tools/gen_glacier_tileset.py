"""TileSet gletser Ch4 (Gua Rantai): assets/tilesets/glacier_tileset.tres (FILE BARU, aset asli tidak diubah).

Sumber (Ninja Adventure, CC0):
  sumber 0 = assets/tilesets/glacier_floor.png  : blok terrain SALJU Ninja TilesetFloor (0,14) (salju di luar, jalan salju padat
             bertepi abu di dalam); pemetaan sudut (marching squares) = CORNER_TILES (blok berbentuk sama dengan blok rumput).
  sumber 1 = assets/tilesets/glacier_relief.png : Ninja TilesetRelief diwarnai ulang: puncak dataran = salju, dinding = batu kelabu
             kebiruan, BERTABRAKAN. Koordinat tile sama dengan TilesetRelief (puncak (1-3,5-6), dinding (4-6,5-7)).
  sumber 2 = assets/tilesets_biome/TilesetWater.png : blok air bertepi SALJU (13,0) (pemetaan sudut sama, bit = titik sudut air)
             + papan jembatan kayu. Tanpa tabrakan: air ditutup TileMapLayer penghalang tak terlihat (block_tileset).
  sumber 3 = assets/tilesets/glacier_ice.png    : blok LANTAI ES Ninja TilesetFloor (0,21) (salju di luar, es di dalam) untuk
             arena Ksatria Rantai; pemetaan sudut = CORNER_TILES (bit = titik sudut es). Bisa dilalui.
Jalankan:  python tools/gen_glacier_tileset.py
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_canyon_tileset import CORNER_TILES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = os.path.join(ROOT, "assets", "tilesets")
BIOME = os.path.join(ROOT, "assets", "tilesets_biome")

# TilesetRelief: puncak pasir -> salju, dinding cokelat -> batu kelabu kebiruan
RELIEF_RECOLOR = {(255, 203, 141): (184, 198, 222), (242, 173, 125): (160, 176, 204), (189, 121, 89): (122, 136, 160),
                  (150, 83, 64): (86, 96, 122)}

SNOW = [(0, 5)] * 6 + [(1, 5), (2, 5), (3, 5), (4, 5)]      # salju polos (+ sedikit detail)
PATH = [(1, 1)]                                             # jalan salju padat (dalam blok)
PATH_DETAIL = [(0, 4), (1, 4)]
WATER_CORNER = {k: (v[0] + 13, v[1]) for k, v in CORNER_TILES.items()}   # blok air bertepi salju di kolom 13
PLANK = [(5, 13), (6, 13), (7, 13)]                         # papan jembatan (vertikal)
PLANK_H = [(5, 12), (6, 12)]                                # papan jembatan (horizontal)
FLOOR_TILES = sorted({(x, y) for x in range(11) for y in range(6)})
ICE = (1, 1)                                                # es polos (dalam blok es)
ICE_TILES = sorted({(x, y) for x in range(11) for y in range(5)})
RELIEF_TILES = [(x, y) for x in range(1, 7) for y in range(5, 8)]
WATER_TILES = sorted(set(WATER_CORNER.values()) | set(PLANK) | set(PLANK_H))


def recolor(im, table):
    a = np.array(im)
    for src, dst in table.items():
        m = (a[:, :, 0] == src[0]) & (a[:, :, 1] == src[1]) & (a[:, :, 2] == src[2])
        a[m, 0:3] = dst
    return Image.fromarray(a)


def main():
    floor = Image.open(os.path.join(BIOME, "TilesetFloor.png")).convert("RGBA").crop((0, 14 * 16, 11 * 16, 20 * 16))
    floor.save(os.path.join(TS, "glacier_floor.png"))
    Image.open(os.path.join(BIOME, "TilesetFloor.png")).convert("RGBA").crop((0, 21 * 16, 11 * 16, 26 * 16)).save(
        os.path.join(TS, "glacier_ice.png"))
    relief = Image.open(os.path.join(BIOME, "TilesetRelief.png")).convert("RGBA")
    recolor(relief, RELIEF_RECOLOR).save(os.path.join(TS, "glacier_relief.png"))

    sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[gd_resource type="TileSet" load_steps=9 format=3]', "",
             '[ext_resource type="Texture2D" path="res://assets/tilesets/glacier_floor.png" id="tex_0"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets/glacier_relief.png" id="tex_1"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets_biome/TilesetWater.png" id="tex_2"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets/glacier_ice.png" id="tex_3"]', "",
             '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")',
             "texture_region_size = Vector2i(16, 16)"]
    lines += [f"{x}:{y}/0 = 0" for x, y in FLOOR_TILES]
    lines += ["", '[sub_resource type="TileSetAtlasSource" id="src_1"]', 'texture = ExtResource("tex_1")',
              "texture_region_size = Vector2i(16, 16)"]
    for x, y in RELIEF_TILES:
        lines += [f"{x}:{y}/0 = 0", f"{x}:{y}/0/physics_layer_0/polygon_0/points = {sq}"]
    lines += ["", '[sub_resource type="TileSetAtlasSource" id="src_2"]', 'texture = ExtResource("tex_2")',
              "texture_region_size = Vector2i(16, 16)"]
    lines += [f"{x}:{y}/0 = 0" for x, y in WATER_TILES]
    lines += ["", '[sub_resource type="TileSetAtlasSource" id="src_3"]', 'texture = ExtResource("tex_3")',
              "texture_region_size = Vector2i(16, 16)"]
    lines += [f"{x}:{y}/0 = 0" for x, y in ICE_TILES]
    lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
              "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")', 'sources/1 = SubResource("src_1")',
              'sources/2 = SubResource("src_2")', 'sources/3 = SubResource("src_3")']
    with open(os.path.join(TS, "glacier_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("glacier_tileset.tres:", len(FLOOR_TILES), "lantai,", len(RELIEF_TILES), "tebing,", len(WATER_TILES), "air/jembatan")


if __name__ == "__main__":
    main()
