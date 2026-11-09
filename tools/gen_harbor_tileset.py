"""TileSet pantai & dermaga untuk Ch3 (Pelabuhan Antre). FILE BARU; aset asli tidak diubah.
Jalankan:  python tools/gen_harbor_tileset.py
  assets/tilesets/harbor_tiles.png     atlas 7 tile: 0-2 pasir, 3-5 papan dermaga, 6 air (padat)
  assets/tilesets/harbor_tileset.tres
Pasir & air dari Pixel Crawler, papan kayu dari Ninja Adventure (CC0).
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_village import ROOT, blue_tiles, img  # noqa: E402

OUT = os.path.join(ROOT, "assets", "tilesets")


def crop(rel, tx, ty):
    return img(rel).crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16))


water = blue_tiles("tilesets/Water_tiles.png")[0]
TILES = [crop("tilesets/Floors_Tiles.png", 7, 23), crop("tilesets/Floors_Tiles.png", 6, 23),
         crop("tilesets/Floors_Tiles.png", 8, 23),
         crop("tilesets_biome/TilesetWater.png", 5, 14), crop("tilesets_biome/TilesetWater.png", 6, 14),
         crop("tilesets_biome/TilesetWater.png", 8, 14), crop("tilesets/Water_tiles.png", *water)]
atlas = Image.new("RGBA", (16 * len(TILES), 16))
for i, t in enumerate(TILES):
    atlas.paste(t, (i * 16, 0))
atlas.save(os.path.join(OUT, "harbor_tiles.png"))

sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
lines = ['[gd_resource type="TileSet" load_steps=3 format=3]\n',
         '[ext_resource type="Texture2D" path="res://assets/tilesets/harbor_tiles.png" id="tex_0"]\n',
         '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")',
         "texture_region_size = Vector2i(16, 16)"]
for i in range(len(TILES)):
    lines.append(f"{i}:0/0 = 0")
    if i == 6:
        lines.append(f"{i}:0/0/physics_layer_0/polygon_0/points = {sq}")
lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
          "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")']
with open(os.path.join(OUT, "harbor_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("harbor_tiles.png + harbor_tileset.tres dibuat")
