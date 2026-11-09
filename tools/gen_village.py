"""Generator Tahap 3: sprite rumah gabungan, TileSet (.tres), dan scene Village.tscn.

Jalankan dari folder proyek:  python tools/gen_village.py
Membuat (menimpa) file berikut:
  assets/props/buildings/house_brown.png, house_green.png   (gabungan dari Walls/Roofs/Props, file BARU)
  assets/props/papan_peta.png                                (papan Peta Dunia buatan sendiri)
  assets/tilesets/world_tileset.tres
  scenes/world/Village.tscn
File aset asli tidak diubah. Setelah scene dibuat, rapikan manual di editor Godot.
"""
import os
import random
import struct
import sys
from collections import deque

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
TILE = 16
MAP_W, MAP_H = 50, 40  # dalam tile -> 800 x 640 px (desa awal kecil di tepi pantai)


def img(rel):
    return Image.open(os.path.join(A, rel)).convert("RGBA")


def components(im, grow=1, min_n=20):
    """Kotak pembatas komponen piksel yang terhubung (alpha > 0)."""
    a = np.array(im)[:, :, 3] > 0
    h, w = a.shape
    seen = np.zeros_like(a)
    out = []
    for y in range(h):
        for x in range(w):
            if a[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = 1
                x0 = x1 = x
                y0 = y1 = y
                n = 0
                while q:
                    cy, cx = q.popleft()
                    n += 1
                    x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                    for dy in range(-grow, grow + 1):
                        for dx in range(-grow, grow + 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = 1
                                q.append((ny, nx))
                if n > min_n:
                    out.append((x0, y0, x1 + 1, y1 + 1))
    return out


# ------------------------------------------------------------------ 1. Sprite rumah

def make_house(roof_box, roof_sheet, wall_x, name):
    roof = img(roof_sheet).crop(roof_box)
    walls = img("props/buildings/Walls.png")
    props = img("props/buildings/Props.png")
    wall_w, wall_h = 128, 55
    wall = Image.new("RGBA", (wall_w, wall_h))
    for i in range(4):  # 4 panel lebar (32 px) berselang-seling
        sx = wall_x[i % 2]
        wall.alpha_composite(walls.crop((sx, 185, sx + 32, 240)), (i * 32, 0))
    door = props.crop((101, 29, 123, 64))
    window = props.crop((132, 99, 156, 124))
    wall.alpha_composite(door, ((wall_w - door.width) // 2, wall_h - door.height - 1))
    wall.alpha_composite(window, (14, 14))
    wall.alpha_composite(window, (wall_w - window.width - 14, 14))
    overlap = 6
    out = Image.new("RGBA", (wall_w, roof.height + wall_h - overlap))
    out.alpha_composite(wall, (0, roof.height - overlap))
    # isi celah (gable & bawah tepi atap) dengan warna dinding: tiap baris antara piksel atap paling kiri-kanan
    wp = np.array(wall)
    solid = wp[wp[:, :, 3] == 255][:, :3]
    fill_color = tuple(int(v) for v in solid[len(solid) // 2:].mean(axis=0)) + (255,)
    ra = np.array(roof)
    fill = Image.new("RGBA", roof.size)
    fpx = fill.load()
    for y in range(roof.height):
        xs = np.where(ra[y, :, 3] > 0)[0]
        if len(xs):
            for x in range(xs.min(), xs.max() + 1):
                fpx[x, y] = fill_color
    out.alpha_composite(fill, (0, 0))
    out.alpha_composite(roof, (0, 0))  # atap di atas dinding
    path = os.path.join(A, "props/buildings", name)
    out.save(path)
    return out.size


def make_board():
    """Papan Peta Dunia sederhana 24x32: dua tiang kayu + papan."""
    im = Image.new("RGBA", (24, 32))
    px = im.load()
    dark, mid, light = (60, 36, 20, 255), (122, 80, 44, 255), (176, 124, 72, 255)
    for y in range(12, 32):
        for x in (4, 5, 18, 19):
            px[x, y] = mid
        px[3, y] = dark if y < 31 else px[3, y]
        px[6, y] = dark
        px[17, y] = dark
        px[20, y] = dark
    for y in range(2, 16):
        for x in range(1, 23):
            edge = y in (2, 15) or x in (1, 22)
            px[x, y] = dark if edge else (light if y < 4 or y > 13 else mid)
    for x in range(5, 19, 3):  # garis "tulisan"
        for y in (6, 9):
            px[x, y] = dark
            px[x + 1, y] = dark
    im.save(os.path.join(A, "props/papan_peta.png"))


# ------------------------------------------------------------------ 2. TileSet

def opaque_tiles(rel):
    im = np.array(img(rel))
    tiles = []
    for ty in range(im.shape[0] // TILE):
        for tx in range(im.shape[1] // TILE):
            cell = im[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE, 3]
            if (cell == 255).all():
                tiles.append((tx, ty))
    return tiles


def blue_tiles(rel):
    """Tile penuh yang dominan biru (air), diurutkan dari yang paling seragam."""
    im = np.array(img(rel))
    found = []
    for tx, ty in opaque_tiles(rel):
        px = im[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE, :3].reshape(-1, 3).astype(float)
        mean = px.mean(axis=0)
        if mean[2] > mean[0] + 80 and mean[1] < mean[2]:
            found.append((px.std(), (tx, ty)))
    return [t for _, t in sorted(found)]


SOURCES = [  # (id, file, solid/collision)
    (0, "tilesets/Floors_Tiles.png", False),
    (1, "tilesets/Water_tiles.png", True),
    (2, "tilesets/Wall_Tiles.png", True),
    (3, "tilesets/Wall_Variations.png", True),
]
SQUARE = "PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)"


def make_tileset():
    avail = {sid: opaque_tiles(f) for sid, f, _ in SOURCES}
    lines = []
    steps = 1 + len(SOURCES) * 2
    lines.append(f"[gd_resource type=\"TileSet\" load_steps={steps} format=3]\n")
    for sid, f, _ in SOURCES:
        lines.append(f"[ext_resource type=\"Texture2D\" path=\"res://assets/{f}\" id=\"tex_{sid}\"]")
    lines.append("")
    for sid, f, solid in SOURCES:
        lines.append(f"[sub_resource type=\"TileSetAtlasSource\" id=\"src_{sid}\"]")
        lines.append(f"texture = ExtResource(\"tex_{sid}\")")
        lines.append("texture_region_size = Vector2i(16, 16)")
        for tx, ty in avail[sid]:
            lines.append(f"{tx}:{ty}/0 = 0")
            if solid:
                lines.append(f"{tx}:{ty}/0/physics_layer_0/polygon_0/points = {SQUARE}")
        lines.append("")
    lines.append("[resource]")
    lines.append("tile_size = Vector2i(16, 16)")
    lines.append("physics_layer_0/collision_layer = 1")
    lines.append("physics_layer_0/collision_mask = 0")
    for sid, _, _ in SOURCES:
        lines.append(f"sources/{sid} = SubResource(\"src_{sid}\")")
    with open(os.path.join(A, "tilesets/world_tileset.tres"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return avail


def encode_cells(cells):
    """Format tile_map_data TileMapLayer: header 2 byte + 12 byte/sel (x,y,source,ax,ay,alt)."""
    data = bytearray(struct.pack("<H", 0))
    for x, y, src, ax, ay in cells:
        data += struct.pack("<hhHHHH", x, y, src, ax, ay, 0)
    return "PackedByteArray(" + ", ".join(str(b) for b in data) + ")"


# ------------------------------------------------------------------ 3. Scene builder

class Scene:
    def __init__(self):
        self.ext = {}   # path -> id
        self.sub = []   # (id, teks)
        self.nodes = []
        self._n = 0

    def ext_res(self, res_type, path):
        if path not in self.ext:
            self.ext[path] = (f"ext_{len(self.ext)}", res_type)
        return self.ext[path][0]

    def add_sub(self, kind, body):
        self._n += 1
        sid = f"sub_{self._n}"
        self.sub.append(f"[sub_resource type=\"{kind}\" id=\"{sid}\"]\n{body}\n")
        return sid

    def rect_shape(self, w, h):
        return self.add_sub("RectangleShape2D", f"size = Vector2({w}, {h})")

    def circle_shape(self, r):
        return self.add_sub("CircleShape2D", f"radius = {r}")

    def node(self, name, kind, parent=None, **props):
        head = f"[node name=\"{name}\" type=\"{kind}\""
        if parent is not None:
            head += f" parent=\"{parent}\""
        if "instance" in props:
            head = f"[node name=\"{name}\" parent=\"{parent}\" instance=ExtResource(\"{props.pop('instance')}\")"
        out = [head + "]"]
        for k, v in props.items():
            out.append(f"{k} = {v}")
        self.nodes.append("\n".join(out) + "\n")

    def render(self):
        steps = 1 + len(self.ext) + len(self.sub)
        head = [f"[gd_scene load_steps={steps} format=3]\n"]
        for path, (eid, typ) in self.ext.items():
            head.append(f"[ext_resource type=\"{typ}\" path=\"{path}\" id=\"{eid}\"]")
        head.append("")
        return "\n".join(head) + "\n" + "\n".join(self.sub) + "\n" + "\n".join(self.nodes)


def v2(x, y):
    return f"Vector2({x}, {y})"


def build_village(avail):
    """Desa Algoria: desa awal kecil di tepi pantai. Joko, rumah Raka, Bonfire, gerbang timur ke Hutan Indeks."""
    import math
    rng = random.Random(10)
    sc = Scene()
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Village.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")

    # ---- Peta tile: rumput + jalan tanah (timur-barat) + pantai pasir + laut
    grass = [(1, 10), (2, 10), (3, 10)]
    path_tiles = [(6, 10), (7, 10), (8, 10)]
    sand = [(6, 23), (7, 23), (8, 23)]
    road_h = range(18, 20)
    road_v = range(24, 26)   # jalan kecil ke Bonfire
    ground, water = [], []
    water_solid = blue_tiles("tilesets/Water_tiles.png")
    # ---- bentuk pulau organik (bukan persegi): sekitar jalan, rumah, bonfire, gerbang; sisanya laut
    import organic
    gx, gy = organic.grid(MAP_W, MAP_H)
    skeleton = [(x, y, 0) for x, y in organic.polyline_samples([(40, 300), (400, 300), (780, 312)], 20)]
    skeleton += [(250, 250, 130), (520, 250, 130), (400, 410, 60), (250, 290, 40), (768, 312, 40)]
    mask = organic.region_mask("village", MAP_W, MAP_H, seed=7) | organic.organic_mask(gx, gy, skeleton, r_base=90, r_amp=25, seed=8)
    edge = mask & ~organic.erode(mask, 1)
    inner = organic.erode(mask, 3)
    for x in range(MAP_W):
        for y in range(MAP_H):
            on_road = y in road_h or (x in road_v and 19 <= y <= 25)
            if edge[x, y]:
                t = sand[1] if rng.random() < 0.85 else rng.choice(sand)
            elif on_road:
                t = path_tiles[1] if rng.random() < 0.85 else rng.choice(path_tiles)
            else:
                t = grass[1] if rng.random() < 0.85 else rng.choice(grass)
            ground.append((x, y, 0, t[0], t[1]))
            if not mask[x, y]:
                water.append((x, y, 1, *water_solid[0]))

    sc.node("Village", "Node2D", script=f"ExtResource(\"{script}\")")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=encode_cells(ground), tile_set=f"ExtResource(\"{tileset}\")")
    sc.node("Water", "TileMapLayer", ".", tile_map_data=encode_cells(water), tile_set=f"ExtResource(\"{tileset}\")")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    def sprite(parent, tex_path, size, region=None, extra_offset=(0, 0)):
        tex = sc.ext_res("Texture2D", tex_path)
        w, h = size
        props = {"texture": f"ExtResource(\"{tex}\")",
                 "offset": v2(extra_offset[0], -h / 2 + extra_offset[1])}
        if region:
            props["region_enabled"] = "true"
            props["region_rect"] = f"Rect2({region[0]}, {region[1]}, {region[2] - region[0]}, {region[3] - region[1]})"
        sc.node("Sprite2D", "Sprite2D", parent, **props)

    def static_prop(name, pos, tex_path, size, region=None, collision=None):
        """collision = (lebar, tinggi) kotak di atas titik kaki; None = tanpa tabrakan."""
        sc.node(name, "StaticBody2D", "Objects", position=v2(*pos), collision_layer=1, collision_mask=0)
        sprite(f"Objects/{name}", tex_path, size, region)
        if collision:
            cw, ch = collision
            sc.node("CollisionShape2D", "CollisionShape2D", f"Objects/{name}",
                    position=v2(0, -ch / 2), shape=f"SubResource(\"{sc.rect_shape(cw, ch)}\")")

    # ---- Rumah: Joko (cokelat) dan rumah Raka (hijau)
    hb = make_house((0, 6, 128, 95), "props/buildings/Roofs.png", (384, 432), "house_brown.png")
    hg = make_house((128, 6, 256, 95), "props/buildings/Roofs.png", (96, 144), "house_green.png")
    static_prop("RumahJoko", (250, 250), "res://assets/props/buildings/house_brown.png", hb, collision=(120, 40))
    static_prop("RumahRaka", (520, 250), "res://assets/props/buildings/house_green.png", hg, collision=(120, 40))

    # ---- Bonfire (titik simpan desa)
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    sc.node("Bonfire", None, "Objects", instance=bonfire_scene, position=v2(400, 410))

    # ---- Gerbang timur ke Hutan Indeks (terkunci sampai prolog Joko selesai)
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    sc.node("GerbangHutan", None, "Objects", instance=exit_scene, position=v2(768, 312),
            to_chapter="1", sign_text="\"Jalan ke Hutan Indeks\"")

    # ---- Pohon (batas atas/kiri/kanan + sebaran) dan semak
    cells = {"m1a": ("Trees/Model_01/Size_03.png", (0, 0, 48, 96)),
             "m1b": ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
             "m2a": ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)),
             "m2b": ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))}
    trees = {}
    for k, (f, box) in cells.items():
        bbox = img("props/" + f).crop(box).getbbox()
        trees[k] = (f, (box[0] + bbox[0], box[1] + bbox[1], box[0] + bbox[2], box[1] + bbox[3]))
    keep_out = [(180, 150, 330, 330), (450, 150, 600, 330), (0, 270, 800, 340), (330, 330, 470, 440),
                (700, 270, 800, 340)]

    def free(x, y):
        return organic.walkable_at(mask, x, y) and not any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in keep_out)

    W, H = MAP_W * TILE, MAP_H * TILE
    spots = []
    for ty in range(MAP_H):  # pita pohon mengikuti tepi organik (sisakan jalan)
        for tx in range(MAP_W):
            if mask[tx, ty] and not inner[tx, ty] and (tx + 2 * ty) % 3 == 0:
                x, y = tx * TILE + 8 + rng.randint(-4, 4), ty * TILE + 14
                if not (255 <= y <= 355) and not (330 <= y <= 450 and 330 <= x <= 470):
                    spots.append((x, y))
    for _ in range(40):  # sebaran di dalam
        x, y = rng.randint(30, W - 30), rng.randint(70, 430)
        if free(x, y):
            spots.append((x, y))
    placed = []
    for n, (x, y) in enumerate(spots):
        if any(abs(x - px) < 26 and abs(y - py) < 14 for px, py in placed):
            continue
        placed.append((x, y))
        k = rng.choice(list(trees))
        f, region = trees[k]
        size = (region[2] - region[0], region[3] - region[1])
        static_prop(f"Pohon{n}", (x, y), f"res://assets/props/{f}", size, region=region, collision=(10, 6))

    veg = sorted([c for c in components(img("props/Vegetation.png").crop((0, 0, 190, 142)), 1)
                  if c[2] - c[0] < 40], key=lambda c: (c[1] // 8, c[0]))[:4]
    for n in range(14):
        x, y = rng.randint(30, W - 30), rng.randint(70, 430)
        if free(x, y) and veg:
            region = rng.choice(veg)
            size = (region[2] - region[0], region[3] - region[1])
            sc.node(f"Semak{n}", "Node2D", "Objects", position=v2(x, y))
            sprite(f"Objects/Semak{n}", "res://assets/props/Vegetation.png", size, region)

    # ---- Marker: hanya Joko di desa awal (Arman di pintu Ch1, Lilbah di Ch2, Dadang di Ch3)
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Joko", "Marker2D", "NPCSpawns", position=v2(250, 290), **{"metadata/npc_id": "\"joko\""})
    sc.node("Joko", None, "Objects", instance=npc_scene, position=v2(250, 290), npc_id="\"joko\"", has_new_quest="true")
    sc.node("PlayerStart", "Marker2D", ".", position=v2(400, 340))
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(400, 340)}\n")

    # ---- Batas map (tak terlihat)
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (W / 2, -t / 2, W + 2 * t, t), "Bawah": (W / 2, H + t / 2, W + 2 * t, t),
                             "Kiri": (-t / 2, H / 2, t, H), "Kanan": (W + t / 2, H / 2, t, H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Village.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    organic.save_preview(os.path.join(ROOT, "tools/preview_village.png"), mask, [(250, 290), (400, 340), (400, 410), (768, 312), (250, 250), (520, 250)])
    print("pohon:", len(placed), "| rumah:", hb, hg)


if __name__ == "__main__":
    avail = make_tileset()
    print({k: len(v) for k, v in avail.items()}, "tile padat per sumber")
    build_village(avail)
