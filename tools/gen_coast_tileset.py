"""TileSet pesisir Ch3 (Pelabuhan Antre): assets/tilesets/coast_tileset.tres (FILE BARU, aset asli tidak diubah).

Sumber (Ninja Adventure, CC0):
  sumber 0 = assets/tilesets/coast_floor.png  : blok terrain rumput Ninja TilesetFloor (0,7) yang TANAH-nya diwarnai ulang
             jadi PASIR PANTAI (warna pasir sama dengan tepi air Ninja TilesetWater). Rumput di luar, pasir di dalam;
             pemetaan sudut (marching squares) = CORNER_TILES dari gen_canyon_tileset (blok berbentuk sama).
  sumber 1 = assets/tilesets/coast_relief.png : Ninja TilesetRelief dengan puncak dataran diwarnai rumput (tebing batu pasir
             berpuncak rumput), BERTABRAKAN. Koordinat tile sama dengan TilesetRelief (puncak (1-3,5-6), dinding (4-6,5-7)).
  sumber 2 = assets/tilesets_biome/TilesetWater.png : blok air bertepi pasir (0,0) (pemetaan sudut sama, bit = titik sudut AIR)
             + papan dermaga kayu. Tanpa tabrakan: air ditutup TileMapLayer penghalang tak terlihat (block_tileset).
Jalankan:  python tools/gen_coast_tileset.py
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

# tanah cokelat blok rumput -> pasir pantai
DIRT_TO_SAND = {(211, 134, 95): (255, 203, 141), (189, 121, 89): (248, 192, 130), (173, 112, 75): (236, 172, 112),
                (230, 165, 120): (255, 222, 178)}
# puncak dataran TilesetRelief (pasir) -> rumput tua (lebih gelap dari rumput lantai supaya batas wilayah terbaca)
TOP_TO_GRASS = {(255, 203, 141): (104, 146, 58), (242, 173, 125): (86, 124, 50), (189, 121, 89): (66, 98, 44)}

GRASS = [(0, 5)] * 7 + [(1, 5), (2, 5), (3, 5), (4, 5)]      # rumput polos (+ sedikit rumput tinggi)
SAND = [(1, 1)]                                              # pasir polos (dalam blok)
SAND_DETAIL = [(0, 4), (1, 4)]                               # pasir berkerikil/kerang
WATER_CORNER = CORNER_TILES                                  # blok air (0,0) TilesetWater, bit = titik sudut air
WATER_FULL = (1, 1)
PLANK = [(5, 13), (6, 13), (7, 13)]                          # papan dermaga (vertikal)
FLOOR_TILES = sorted({(x, y) for x in range(11) for y in range(6)})
RELIEF_TILES = [(x, y) for x in range(1, 7) for y in range(5, 8)]
WATER_TILES = sorted(set(CORNER_TILES.values()) | {(0, 5)} | set(PLANK))


def recolor(im, table, box=None):
    a = np.array(im)
    region = a if box is None else a[box[1]:box[3], box[0]:box[2]]
    for src, dst in table.items():
        m = (region[:, :, 0] == src[0]) & (region[:, :, 1] == src[1]) & (region[:, :, 2] == src[2])
        region[m, 0:3] = dst
    return Image.fromarray(a)


def main():
    floor = Image.open(os.path.join(BIOME, "TilesetFloor.png")).convert("RGBA").crop((0, 7 * 16, 11 * 16, 13 * 16))
    recolor(floor, DIRT_TO_SAND).save(os.path.join(TS, "coast_floor.png"))
    relief = Image.open(os.path.join(BIOME, "TilesetRelief.png")).convert("RGBA")
    recolor(relief, TOP_TO_GRASS, (16, 80, 64, 112)).save(os.path.join(TS, "coast_relief.png"))

    sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[gd_resource type="TileSet" load_steps=7 format=3]', "",
             '[ext_resource type="Texture2D" path="res://assets/tilesets/coast_floor.png" id="tex_0"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets/coast_relief.png" id="tex_1"]',
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
    with open(os.path.join(TS, "coast_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("coast_tileset.tres:", len(FLOOR_TILES), "lantai,", len(RELIEF_TILES), "tebing,", len(WATER_TILES), "air/dermaga")


if __name__ == "__main__":
    main()
