"""TileSet ngarai Ch2 (Tambang Tumpuk): assets/tilesets/canyon_tileset.tres (FILE BARU, aset asli tidak diubah).

Dua sumber atlas langsung dari Ninja Adventure (CC0) yang sudah ada di proyek:
  sumber 0 = assets/tilesets_biome/TilesetFloor.png  : pasir oranye + jalan pasir terang bertepi (blok terrain 11x6 di kiri atas),
             tanpa tabrakan. Pemetaan sudut (marching squares) ada di CORNER_TILES.
  sumber 1 = assets/tilesets_biome/TilesetRelief.png : dataran tinggi (puncak 3x3) + dinding tebing berbibir (3x3), BERTABRAKAN.
Jalankan:  python tools/gen_canyon_tileset.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "tilesets", "canyon_tileset.tres")

# (TL, TR, BL, BR) sudut "jalan terang" -> koordinat atlas TilesetFloor
CORNER_TILES = {
    (1, 1, 1, 1): (1, 1), (0, 0, 1, 1): (1, 0), (1, 1, 0, 0): (1, 2), (0, 1, 0, 1): (0, 1), (1, 0, 1, 0): (2, 1),
    (0, 0, 0, 1): (0, 0), (0, 0, 1, 0): (2, 0), (0, 1, 0, 0): (0, 2), (1, 0, 0, 0): (2, 2),
    (0, 1, 1, 1): (9, 2), (1, 0, 1, 1): (10, 2), (1, 1, 0, 1): (9, 3), (1, 1, 1, 0): (10, 3),
    (1, 0, 0, 1): (1, 1), (0, 1, 1, 0): (1, 1),
}
SAND = [(0, 5), (0, 5), (0, 5), (0, 5), (0, 5), (0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]   # pasir oranye (+ sedikit retak/kerikil)
LIGHT_DETAIL = [(0, 4), (1, 4)]
FLOOR_TILES = sorted(set(CORNER_TILES.values()) | set(SAND) | set(LIGHT_DETAIL))
RELIEF_TILES = [(x, y) for x in range(1, 7) for y in range(5, 8)]


def main():
    sq = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[gd_resource type="TileSet" load_steps=5 format=3]', "",
             '[ext_resource type="Texture2D" path="res://assets/tilesets_biome/TilesetFloor.png" id="tex_0"]',
             '[ext_resource type="Texture2D" path="res://assets/tilesets_biome/TilesetRelief.png" id="tex_1"]', "",
             '[sub_resource type="TileSetAtlasSource" id="src_0"]', 'texture = ExtResource("tex_0")',
             "texture_region_size = Vector2i(16, 16)"]
    lines += [f"{x}:{y}/0 = 0" for x, y in FLOOR_TILES]
    lines += ["", '[sub_resource type="TileSetAtlasSource" id="src_1"]', 'texture = ExtResource("tex_1")',
              "texture_region_size = Vector2i(16, 16)"]
    for x, y in RELIEF_TILES:
        lines += [f"{x}:{y}/0 = 0", f"{x}:{y}/0/physics_layer_0/polygon_0/points = {sq}"]
    lines += ["", "[resource]", "tile_size = Vector2i(16, 16)", "physics_layer_0/collision_layer = 1",
              "physics_layer_0/collision_mask = 0", 'sources/0 = SubResource("src_0")', 'sources/1 = SubResource("src_1")']
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("canyon_tileset.tres:", len(FLOOR_TILES), "tile lantai,", len(RELIEF_TILES), "tile tebing")


if __name__ == "__main__":
    main()
