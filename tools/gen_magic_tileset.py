"""TileSet hutan ajaib untuk Ch5 (Pohon Dunia) dari Ninja Adventure (CC0). FILE BARU; aset asli tidak diubah.
Jalankan:  python tools/gen_magic_tileset.py
  assets/tilesets/magic_tiles.png     atlas 8 tile: 0-2 tanah merah muda, 3-4 jalan tanah, 5 lantai arena, 6 air ungu (padat)
  assets/tilesets/magic_tileset.tres
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


F, W = "TilesetFloor.png", "TilesetWater.png"
TILES = [flatten(tile(F, 17, 4)), tile(F, 12, 4), tile(F, 11, 4),     # tanah merah muda
         tile(F, 12, 15), tile(F, 14, 18),                           # jalan tanah
         tile(F, 11, 19),                                            # lantai arena (tanah terang)
         tile(W, 14, 7)]                                             # air ungu (padat)
atlas = Image.new("RGBA", (16 * len(TILES), 16))
for i, t in enumerate(TILES):
    atlas.paste(t, (i * 16, 0))
atlas.save(os.path.join(OUT, "magic_tiles.png"))
sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
lines = ['[gd_resource type="TileSet" load_steps=3 format=3]\n',
         '[ext_resource type="Texture2D" path="res://assets/tilesets/magic_tiles.png" id="tex_0"]\n',
         '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")',
         "texture_region_size = Vector2i(16, 16)"]
for i in range(len(TILES)):
    lines.append(f"{i}:0/0 = 0")
    if i == 6:
        lines.append(f"{i}:0/0/physics_layer_0/polygon_0/points = {sq}")
lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
          "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")']
with open(os.path.join(OUT, "magic_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("magic_tiles.png + magic_tileset.tres dibuat")
