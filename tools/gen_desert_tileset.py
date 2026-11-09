"""Membuat TileSet gurun untuk Ch2 (Tambang Tumpuk) dari Ninja Adventure (CC0).
Jalankan:  python tools/gen_desert_tileset.py
Menulis FILE BARU (aset asli tidak diubah):
  assets/tilesets/desert_tiles.png      atlas 10 tile 16x16 (pasir, tanah gelap, tebing)
  assets/tilesets/desert_tileset.tres   TileSet; tile tebing (indeks 5-9) bertabrakan
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
    """Ganti piksel selain warna dominan dengan warna dominan (pasir polos tanpa tepi)."""
    px = im.load()
    dom = Counter(px[x, y] for x in range(16) for y in range(16)).most_common(1)[0][0]
    out = Image.new("RGBA", (16, 16), dom)
    return out


TILES = [
    flatten(tile("TilesetFloor.png", 6, 4)),   # 0 pasir polos
    tile("TilesetFloor.png", 1, 4),            # 1 pasir + kerikil
    tile("TilesetFloor.png", 0, 4),            # 2 pasir retak
    tile("TilesetFloor.png", 12, 15),          # 3 tanah gelap A (jalan tambang)
    tile("TilesetFloor.png", 14, 18),          # 4 tanah gelap B
    tile("TilesetRelief.png", 5, 6),           # 5 tebing A
    tile("TilesetRelief.png", 6, 6),           # 6 tebing B
    tile("TilesetRelief.png", 5, 7),           # 7 tebing C (kaki tebing)
    tile("TilesetRelief.png", 5, 5),           # 8 tebing D
    tile("TilesetRelief.png", 4, 6),           # 9 tebing E
]
SOLID_FROM = 5

atlas = Image.new("RGBA", (16 * len(TILES), 16))
for i, t in enumerate(TILES):
    atlas.paste(t, (i * 16, 0))
atlas.save(os.path.join(OUT, "desert_tiles.png"))

sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
lines = ['[gd_resource type="TileSet" load_steps=3 format=3]\n',
         '[ext_resource type="Texture2D" path="res://assets/tilesets/desert_tiles.png" id="tex_0"]\n',
         '[sub_resource type="TileSetAtlasSource" id="src_0"]',
         'texture = ExtResource("tex_0")', "texture_region_size = Vector2i(16, 16)"]
for i in range(len(TILES)):
    lines.append(f"{i}:0/0 = 0")
    if i >= SOLID_FROM:
        lines.append(f"{i}:0/0/physics_layer_0/polygon_0/points = {sq}")
lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
          "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")']
with open(os.path.join(OUT, "desert_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("desert_tiles.png + desert_tileset.tres dibuat")
