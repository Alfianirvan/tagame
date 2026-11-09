"""TileSet salju & es untuk Ch4 (Gua Rantai) dari Ninja Adventure (CC0). FILE BARU; aset asli tidak diubah.
Jalankan:  python tools/gen_snow_tileset.py
  assets/tilesets/snow_tiles.png     atlas 12 tile: 0-2 salju, 3-5 es, 6-7 jalan tanah, 8-12 tebing (padat)
  assets/tilesets/snow_tileset.tres
"""
import os
from collections import Counter

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIOME = os.path.join(ROOT, "assets", "tilesets_biome")
OUT = os.path.join(ROOT, "assets", "tilesets")


def tile(name, tx, ty):
    return Image.open(os.path.join(BIOME, name)).convert("RGBA").crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16))


def flatten(im):
    px = im.load()
    dom = Counter(px[x, y] for x in range(16) for y in range(16)).most_common(1)[0][0]
    return Image.new("RGBA", (16, 16), dom)


F, R = "TilesetFloor.png", "TilesetRelief.png"
TILES = [flatten(tile(F, 6, 18)), tile(F, 1, 18), tile(F, 0, 18),        # salju
         flatten(tile(F, 6, 25)), tile(F, 5, 22), tile(F, 6, 22),        # es
         tile(F, 12, 15), tile(F, 14, 18),                               # jalan tanah
         tile(R, 5, 1), tile(R, 6, 1), tile(R, 5, 2), tile(R, 5, 0), tile(R, 4, 1)]   # tebing batu
SOLID_FROM = 8

atlas = Image.new("RGBA", (16 * len(TILES), 16))
for i, t in enumerate(TILES):
    atlas.paste(t, (i * 16, 0))
atlas.save(os.path.join(OUT, "snow_tiles.png"))
sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
lines = ['[gd_resource type="TileSet" load_steps=3 format=3]\n',
         '[ext_resource type="Texture2D" path="res://assets/tilesets/snow_tiles.png" id="tex_0"]\n',
         '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")',
         "texture_region_size = Vector2i(16, 16)"]
for i in range(len(TILES)):
    lines.append(f"{i}:0/0 = 0")
    if i >= SOLID_FROM:
        lines.append(f"{i}:0/0/physics_layer_0/polygon_0/points = {sq}")
lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
          "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")']
with open(os.path.join(OUT, "snow_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("snow_tiles.png + snow_tileset.tres dibuat")
