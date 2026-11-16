"""TileSet Pohon Dunia Ch5: assets/tilesets/akar_tileset.tres (FILE BARU, aset asli tidak diubah).

Sumber (Ninja Adventure, CC0):
  sumber 0 = assets/tilesets/akar_floor.png  : blok terrain rumput Ninja TilesetFloor (0,7) apa adanya (rumput di luar, jalan tanah
             di dalam); pemetaan sudut (marching squares) = CORNER_TILES.
  sumber 1 = assets/tilesets/akar_relief.png : Ninja TilesetRelief diwarnai ulang jadi KULIT KAYU (puncak coklat kayu, dinding coklat tua)
             = AKAR RAKSASA Pohon Dunia & batas wilayah, BERTABRAKAN. Koordinat tile sama dengan TilesetRelief.
  sumber 2 = assets/tilesets_biome/TilesetWater.png : blok AIR UNGU (13,6) (pemetaan sudut sama, bit = titik sudut air)
             + papan jembatan kayu. Tanpa tabrakan: air ditutup TileMapLayer penghalang tak terlihat (block_tileset).
Jalankan:  python tools/gen_akar_tileset.py
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

# TilesetRelief: puncak pasir -> kayu akar, dinding cokelat -> kulit kayu tua
RELIEF_RECOLOR = {(255, 203, 141): (150, 108, 74), (242, 173, 125): (126, 88, 60), (189, 121, 89): (92, 62, 44),
                  (150, 83, 64): (66, 44, 34)}

GRASS = [(0, 5)] * 7 + [(1, 5), (2, 5), (3, 5), (4, 5)]
DIRT = [(1, 1)]
DIRT_DETAIL = [(0, 4), (1, 4)]
WATER_CORNER = {k: (v[0] + 13, v[1] + 6) for k, v in CORNER_TILES.items()}   # blok air ungu di (13,6)
PLANK = [(5, 13), (6, 13), (7, 13)]
FLOOR_TILES = sorted({(x, y) for x in range(11) for y in range(6)})
RELIEF_TILES = [(x, y) for x in range(1, 7) for y in range(5, 8)]
WATER_TILES = sorted(set(WATER_CORNER.values()) | set(PLANK))


def recolor(im, table):
    a = np.array(im)
    for src, dst in table.items():
        m = (a[:, :, 0] == src[0]) & (a[:, :, 1] == src[1]) & (a[:, :, 2] == src[2])
        a[m, 0:3] = dst
    return Image.fromarray(a)


def main():
    Image.open(os.path.join(BIOME, "TilesetFloor.png")).convert("RGBA").crop((0, 7 * 16, 11 * 16, 13 * 16)).save(
        os.path.join(TS, "akar_floor.png"))
    recolor(Image.open(os.path.join(BIOME, "TilesetRelief.png")).convert("RGBA"), RELIEF_RECOLOR).save(os.path.join(TS, "akar_relief.png"))
    sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[gd_resource type="TileSet" load_steps=7 format=3]', "",
             '[ext_resource type="Texture2D" path="res://assets/tilesets/akar_floor.png" id="tex_0"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets/akar_relief.png" id="tex_1"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets_biome/TilesetWater.png" id="tex_2"]', "",
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
    lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
              "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")', 'sources/1 = SubResource("src_1")',
              'sources/2 = SubResource("src_2")']
    with open(os.path.join(TS, "akar_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("akar_tileset.tres:", len(FLOOR_TILES), "lantai,", len(RELIEF_TILES), "akar,", len(WATER_TILES), "air ungu/jembatan")


if __name__ == "__main__":
    main()
