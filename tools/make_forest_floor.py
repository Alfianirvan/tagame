"""Membuat 'lantai hutan lebat' untuk area tak bisa dijalani Ch1 (menggantikan danau biru) agar mirip Peta Dunia.

Menghasilkan:
  assets/tilesets/forest_floor.png     400x400, tajuk pohon pixel-art yang tersambung mulus (torus) -> dipotong jadi tile 16x16
  assets/tilesets/forest_tileset.tres  salinan world_tileset.tres; sumber 1 (air) diganti tekstur hutan, SEMUA tile 25x25 punya tabrakan
Lalu menambal scenes/world/Ch1_HutanIndeks.tscn: layer Water memakai tileset hutan dan tile (x mod 25, y mod 25),
sehingga tajuk menyambung antar-tile. Tabrakan tetap (area ini tidak bisa dijalani). Aman dijalankan ulang.

Jalankan dari folder proyek:  python tools/make_forest_floor.py
"""
import base64
import os
import random
import re
import struct

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TS = os.path.join(ROOT, "assets", "tilesets")
SIZE = 400
N = 25

PAL = {
    "base": (22, 58, 32, 255),
    "outline": (14, 40, 24, 255),
    "dark": (30, 78, 40, 255),
    "mid": (44, 106, 50, 255),
    "light": (70, 144, 66, 255),
    "hi": (104, 180, 88, 255),
}


SHADES = [  # (gelap, tengah, terang, kilau) beberapa nuansa hijau supaya kanopi tidak seragam
    ((26, 70, 36, 255), (40, 98, 46, 255), (62, 132, 60, 255), (96, 170, 80, 255)),
    ((24, 64, 34, 255), (36, 90, 44, 255), (54, 120, 56, 255), (84, 156, 74, 255)),
    ((32, 78, 40, 255), (50, 112, 50, 255), (76, 146, 64, 255), (110, 182, 86, 255)),
]


def make_canopy():
    rng = random.Random(7)
    big = Image.new("RGBA", (SIZE * 3, SIZE * 3), PAL["base"])
    d = ImageDraw.Draw(big)
    crowns = [(rng.uniform(0, SIZE), rng.uniform(0, SIZE), rng.randint(7, 12), rng.choice(SHADES)) for _ in range(900)]
    crowns.sort(key=lambda c: c[1])
    for ox in (0, SIZE, 2 * SIZE):
        for oy in (0, SIZE, 2 * SIZE):
            for x, y, r, (dark, mid, light, hi) in crowns:
                cx, cy = x + ox, y + oy
                d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=PAL["outline"])
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dark)
                d.ellipse([cx - r + 1, cy - r, cx + r - 2, cy + r - 3], fill=mid)
                d.ellipse([cx - r + 3, cy - r + 2, cx + r - 5, cy + r - 7], fill=light)
                for _ in range(max(2, r // 3)):
                    px = cx + rng.randint(-r // 2, r // 3)
                    py = cy + rng.randint(-r // 2, 0)
                    d.rectangle([px, py, px + 1, py], fill=hi)
    return big.crop((SIZE, SIZE, SIZE * 2, SIZE * 2))


def make_tileset():
    src = open(os.path.join(TS, "world_tileset.tres"), encoding="utf-8").read().replace("\r\n", "\n")
    src = re.sub(r'^\[gd_resource type="TileSet" format=3 uid="[^"]*"\]', '[gd_resource type="TileSet" format=3]', src)
    src = src.replace('path="res://assets/tilesets/Water_tiles.png"', 'path="res://assets/tilesets/forest_floor.png"')
    src = re.sub(r'(\[ext_resource type="Texture2D") uid="[^"]*"( path="res://assets/tilesets/forest_floor.png")', r"\1\2", src)
    i = src.index('[sub_resource type="TileSetAtlasSource" id="src_1"]')
    j = src.find("[sub_resource", i + 10)
    j = j if j > 0 else src.find("[resource", i)
    poly = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"
    lines = ['[sub_resource type="TileSetAtlasSource" id="src_1"]', 'texture = ExtResource("tex_1")']
    for y in range(N):
        for x in range(N):
            lines.append(f"{x}:{y}/0 = 0")
            lines.append(f"{x}:{y}/0/physics_layer_0/polygon_0/points = {poly}")
    block = "\n".join(lines) + "\n\n"
    out = src[:i] + block + src[j:]
    open(os.path.join(TS, "forest_tileset.tres"), "w", encoding="utf-8", newline="\n").write(out)


def patch_scene():
    path = os.path.join(ROOT, "scenes", "world", "Ch1_HutanIndeks.tscn")
    raw = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    t = raw.replace("\r\n", "\n")
    m = re.search(r'(\[node name="Water" type="TileMapLayer"[^\]]*\]\n)(.*?)(\n\n)', t, re.S)
    body = m.group(2)
    data = re.search(r'tile_map_data = PackedByteArray\("([^"]*)"\)', body)
    if data:
        b = base64.b64decode(data.group(1))
    else:
        arr = re.search(r"tile_map_data = PackedByteArray\(([^)]*)\)", body).group(1)
        b = bytes(int(v) for v in arr.split(","))
    cells = [struct.unpack("<hhHHHH", b[2 + k * 12: 14 + k * 12]) for k in range((len(b) - 2) // 12)]
    out = bytearray(struct.pack("<H", 0))
    for x, y, _src, _ax, _ay, _alt in cells:
        out += struct.pack("<hhHHHH", x, y, 1, x % N, y % N, 0)
    enc = base64.b64encode(bytes(out)).decode()
    body = re.sub(r'tile_map_data = PackedByteArray\([^)]*\)', f'tile_map_data = PackedByteArray("{enc}")', body, count=1)
    if 'id="forest_ts"' not in t:
        last = [mm for mm in re.finditer(r"(?m)^\[ext_resource[^\n]*\n", t)][-1]
        t = t[: last.end()] + '[ext_resource type="TileSet" path="res://assets/tilesets/forest_tileset.tres" id="forest_ts"]\n' + t[last.end():]
        m = re.search(r'(\[node name="Water" type="TileMapLayer"[^\]]*\]\n)(.*?)(\n\n)', t, re.S)
    body = re.sub(r"tile_set = ExtResource\(\"[^\"]*\"\)", 'tile_set = ExtResource("forest_ts")', body, count=1)
    t = t[: m.start(2)] + body + t[m.end(2):]
    open(path, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    return len(cells)


if __name__ == "__main__":
    make_canopy().save(os.path.join(TS, "forest_floor.png"))
    make_tileset()
    print("sel hutan:", patch_scene())
