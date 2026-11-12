"""Generator Ch1_HutanIndeks.tscn versi 2: bentuk, ukuran, dan arah jalan mengikuti Peta Dunia (docs/layout/region_layout.json).

Jalankan dari folder proyek:  python tools/gen_ch1_v2.py
Menulis scenes/world/Ch1_HutanIndeks.tscn (cadangan lama: C:\\TA GAME\\_backup_scenes_organik\\) dan
tools/preview_ch1_v2.png (gambaran seluruh peta untuk dibandingkan dengan docs/layout/Ch1_HutanIndeks_layout.png).
Skala: 1 piksel peta 270x480 = 1 tile 16x16 (peta 203x144 tile = 3248x2304 px).

Layer TileMapLayer : Ground (rumput), Path (jalan tanah), Water (laut di luar mask, bertabrakan), River (sungai tanpa
                     tabrakan; tabrakan lewat StaticBody + celah jembatan), Forest (tajuk padat bertabrakan untuk sisa area).
Node               : Decor (jembatan), Objects (y-sort: bangunan, pohon, NPC, musuh, Bonfire, dst).
Setelah ini jalankan tools/add_decor.py untuk dekorasi perkemahan (stasiun, barel, peti) dan landasan tempa.
"""
import base64
import json
import math
import os
import random
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_village import A, ROOT, TILE, Scene, blue_tiles, components, img, v2  # noqa: E402
import organic  # noqa: E402

LAYOUT = json.load(open(os.path.join(ROOT, "docs/layout/region_layout.json"), encoding="utf-8"))["Ch1_HutanIndeks"]
W, H = LAYOUT["ukuran_tile"]            # 203 x 144
PX_W, PX_H = LAYOUT["ukuran_px"]        # 3248 x 2304
BACKUP = r"C:\TA GAME\_backup_scenes_organik\Ch1_HutanIndeks_sebelum_layout.tscn"


def tpx(p):
    return (p[0] * TILE + 8, p[1] * TILE + 8)


# ---------------------------------------------------------------- bantuan numpy
def dist_to(gx, gy, pts):
    """Jarak (px) tiap sel ke titik terdekat dari `pts` (N,2)."""
    pts = np.asarray(pts, float)
    best = np.full(gx.shape, 1e9)
    for i in range(0, len(pts), 48):
        c = pts[i:i + 48]
        d = np.hypot(gx[..., None] - c[:, 0], gy[..., None] - c[:, 1])
        best = np.minimum(best, d.min(axis=-1))
    return best


def dilate(m, n):
    out = m.copy()
    for _ in range(n):
        s = out.copy()
        s[1:, :] |= out[:-1, :]
        s[:-1, :] |= out[1:, :]
        s[:, 1:] |= out[:, :-1]
        s[:, :-1] |= out[:, 1:]
        out = s
    return out


def erode(m, n):
    return ~dilate(~m, n)


def b64cells(cells):
    out = bytearray(struct.pack("<H", 0))
    for x, y, src, ax, ay in cells:
        out += struct.pack("<hhHHHH", x, y, src, ax, ay, 0)
    return 'PackedByteArray("%s")' % base64.b64encode(bytes(out)).decode()


# ---------------------------------------------------------------- tileset tanpa tabrakan untuk sungai
def make_nocol_tileset():
    src = open(os.path.join(A, "tilesets/world_tileset.tres"), encoding="utf-8").read().replace("\r\n", "\n")
    src = re.sub(r'^\[gd_resource type="TileSet" format=3 uid="[^"]*"\]', '[gd_resource type="TileSet" format=3]', src)
    src = re.sub(r"(?m)^.*physics_layer_0.*\n", "", src)
    src = re.sub(r'(?m)^(physics_layer_0/[^\n]*\n)', "", src)
    src = re.sub(r' uid="[^"]*"( path="res://assets/tilesets/)', r"\1", src)
    open(os.path.join(A, "tilesets/world_tileset_nocol.tres"), "w", encoding="utf-8", newline="\n").write(src)


def make_bridge():
    """Jembatan kayu 64x56 (papan melintang + pagar tepi), gambar baru buatan sendiri."""
    im = Image.new("RGBA", (64, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, 56, 7):
        d.rectangle([4, y + 1, 59, y + 6], fill=(150, 98, 52, 255), outline=(70, 42, 20, 255))
        d.line([(6, y + 3), (57, y + 3)], fill=(176, 122, 70, 255))
    for x in (0, 60):
        d.rectangle([x, 0, x + 3, 55], fill=(110, 70, 36, 255), outline=(60, 36, 16, 255))
        for y in (4, 26, 48):
            d.rectangle([x - 1, y, x + 4, y + 4], fill=(130, 84, 44, 255), outline=(60, 36, 16, 255))
    im.save(os.path.join(A, "props/bridge_wood.png"))


# ---------------------------------------------------------------- bangun
def build():
    rng = random.Random(1001)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T       # [tx, ty]
    assert mask.shape == (W, H), mask.shape
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    road = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)

    def road_index(pt):
        return int(np.argmin(np.hypot(road[:, 0] - pt[0], road[:, 1] - pt[1])))

    def road_at(frac_from, frac_to, t):
        a, b = road_index(P[frac_from]), road_index(P[frac_to])
        return road[int(a + (b - a) * t)]

    def tangent(i):
        a, b = road[max(0, i - 3)], road[min(len(road) - 1, i + 3)]
        return math.atan2(b[1] - a[1], b[0] - a[0])

    # ------------------------------------------------------------ area yang bisa dijelajahi
    pads = {"village_center": 175, "journey_start": 30, "puzzle": 55, "bonfire_village": 75, "bonfire_preboss": 40,
            "boss_arena": 85, "exit": 40, "entry": 40}
    skeleton = [(x, y, 0) for x, y in road]
    skeleton += [(P[k][0], P[k][1], r) for k, r in pads.items()]
    # 3 jalan cabang pendek: tegak lurus jalan, berhenti 8 tile sebelum tepi wilayah
    mask_d = dilate(mask, 2)
    branches = []
    for frac_from, frac_to, t, side in (("journey_start", "puzzle", 0.35, 1), ("puzzle", "bonfire_preboss", 0.45, -1),
                                         ("bonfire_preboss", "exit", 0.55, 1)):
        base = road_at(frac_from, frac_to, t)
        th = tangent(road_index(base)) + side * math.pi / 2
        pts = [tuple(base)]
        for step in range(1, 40):
            x, y = base[0] + math.cos(th) * step * 16, base[1] + math.sin(th) * step * 16
            tx, ty = int(x // TILE), int(y // TILE)
            if not (0 <= tx < W and 0 <= ty < H) or not erode(mask, 8)[tx, ty] or step > 26:
                break
            pts.append((x, y))
        branches.append(pts)
        skeleton += [(x, y, -125) for x, y in pts]
        skeleton += [(pts[-1][0], pts[-1][1], 20)]
    gx2, gy2 = gx, gy
    corridor = organic.organic_mask(gx2, gy2, skeleton, r_base=205, r_amp=42, seed=21) & mask_d
    road_cells = dist_to(gx, gy, road) <= 34
    corridor |= road_cells
    # leher sempit di gerbang desa: di utara gerbang koridor menyempit ke sekitar jalan (gerbang jadi pendek, desa lega di selatan)
    gate_village = tuple(int(v) for v in road[road_index(P["journey_start"])])
    gate_th = tangent(road_index(gate_village))
    along = (gx - gate_village[0]) * math.cos(gate_th) + (gy - gate_village[1]) * math.sin(gate_th)
    neck = (along > -14) & (along < 360) & (dist_to(gx, gy, road) > 96)
    corridor &= ~neck
    # leher sempit juga di gerbang arena boss (gerbang pendek, bukan memotong seluruh padang)
    i_pre0, i_boss0 = road_index(P["bonfire_preboss"]), road_index(P["boss_arena"])
    ga = tuple(road[int(i_pre0 + (i_boss0 - i_pre0) * 0.6)])
    ga_th = tangent(road_index(ga))
    along2 = (gx - ga[0]) * math.cos(ga_th) + (gy - ga[1]) * math.sin(ga_th)
    corridor &= ~((along2 > -14) & (along2 < 70) & (dist_to(gx, gy, road) > 96))
    forest_cells = mask & ~corridor
    sea_cells = ~mask & ~corridor
    # ------------------------------------------------------------ sungai + jembatan di entry & exit
    rivers = []
    for key, rows in (("entry", (-5, -3)), ("exit", (3, 5))):
        ty0 = int(P[key][1] // TILE) + rows[0]
        ty1 = int(P[key][1] // TILE) + rows[1]
        mid = (ty0 + ty1) / 2 * TILE + 8
        ri = int(np.argmin(np.abs(road[:, 1] - mid)))
        bx = float(road[ri][0])
        txc = int(bx // TILE)
        run_l = txc
        while run_l > 0 and corridor[run_l - 1, ty0:ty1 + 1].all():
            run_l -= 1
        run_r = txc
        while run_r < W - 1 and corridor[run_r + 1, ty0:ty1 + 1].all():
            run_r += 1
        rivers.append({"rows": (ty0, ty1), "cols": (run_l, run_r), "bx": bx, "key": key})

    river_cells = np.zeros_like(mask)
    for r in rivers:
        river_cells[r["cols"][0]:r["cols"][1] + 1, r["rows"][0]:r["rows"][1] + 1] = True

    # ------------------------------------------------------------ peta tile
    grass = [(1, 10), (2, 10), (3, 10)]
    dirt = [(6, 10), (7, 10), (8, 10)]
    d_road = dist_to(gx, gy, road)
    plaza = [P["village_center"], P["boss_arena"], P["puzzle"], P["bonfire_village"], P["bonfire_preboss"], P["journey_start"], P["entry"], P["exit"]]
    plaza_r = [95, 150, 50, 36, 40, 36, 40, 40]
    is_dirt = d_road <= 30 + 6 * organic.smooth_noise(gx, gy, 5)
    for (px, py), rr in zip(plaza, plaza_r):
        is_dirt |= np.hypot(gx - px, gy - py) <= rr
    ground, path_cells, water, riverc, forest = [], [], [], [], []
    water_tile = blue_tiles("tilesets/Water_tiles.png")[0]
    for tx in range(W):
        for ty in range(H):
            t = grass[1] if rng.random() < 0.85 else rng.choice(grass)
            ground.append((tx, ty, 0, t[0], t[1]))
            if is_dirt[tx, ty] and corridor[tx, ty] and not river_cells[tx, ty]:
                d = dirt[1] if rng.random() < 0.85 else rng.choice(dirt)
                path_cells.append((tx, ty, 0, d[0], d[1]))
            if sea_cells[tx, ty]:
                water.append((tx, ty, 1, *water_tile))
            if river_cells[tx, ty]:
                riverc.append((tx, ty, 1, *water_tile))
            if forest_cells[tx, ty]:
                forest.append((tx, ty, 1, tx % 25, ty % 25))

    # ------------------------------------------------------------ scene
    sc = Scene()
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    ts_nocol = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset_nocol.tres")
    ts_forest = sc.ext_res("TileSet", "res://assets/tilesets/forest_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossGolem.tscn")
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    gate_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionGate.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/ArrayShelf.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    sc.node("Ch1_HutanIndeks", "Node2D", script=f'ExtResource("{script}")', chapter="1",
            music_name='"ch1_hutan_indeks"', boss_music_name='"boss"', map_size=f"Vector2i({PX_W}, {PX_H})",
            boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{tileset}")')
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(path_cells), tile_set=f'ExtResource("{tileset}")')
    sc.node("Water", "TileMapLayer", ".", tile_map_data=b64cells(water), tile_set=f'ExtResource("{tileset}")')
    sc.node("River", "TileMapLayer", ".", tile_map_data=b64cells(riverc), tile_set=f'ExtResource("{ts_nocol}")')
    sc.node("Forest", "TileMapLayer", ".", tile_map_data=b64cells(forest), tile_set=f'ExtResource("{ts_forest}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    def sprite(parent, tex_path, size, region=None, **extra):
        tex = sc.ext_res("Texture2D", tex_path)
        w, h = size
        props = {"texture": f'ExtResource("{tex}")', "offset": v2(0, -h / 2)}
        props.update(extra)
        if region:
            props["region_enabled"] = "true"
            props["region_rect"] = f"Rect2({region[0]}, {region[1]}, {region[2] - region[0]}, {region[3] - region[1]})"
        sc.node("Sprite2D", "Sprite2D", parent, **props)

    def static_prop(name, pos, tex_path, size, region=None, collision=None):
        sc.node(name, "StaticBody2D", "Objects", position=v2(*pos), collision_layer=1, collision_mask=0)
        sprite(f"Objects/{name}", tex_path, size, region)
        if collision:
            cw, ch = collision
            sc.node("CollisionShape2D", "CollisionShape2D", f"Objects/{name}",
                    position=v2(0, -ch / 2), shape=f'SubResource("{sc.rect_shape(cw, ch)}")')

    def free_sprite(name, pos, tex_path, size, region=None):
        sc.node(name, "Node2D", "Objects", position=v2(*pos))
        sprite(f"Objects/{name}", tex_path, size, region)

    recorded = []

    def inst(name, scene_id, pos, **props):
        tx_, ty_ = int(pos[0] // TILE), int(pos[1] // TILE)
        if not (0 <= tx_ < W and 0 <= ty_ < H and corridor[tx_, ty_]):      # jatuh di hutan/laut: geser ke dekat jalan
            j = int(np.argmin(np.hypot(road[:, 0] - pos[0], road[:, 1] - pos[1])))
            vx, vy = pos[0] - road[j][0], pos[1] - road[j][1]
            n_ = max(1.0, math.hypot(vx, vy))
            pos = (round(road[j][0] + vx / n_ * min(n_, 36)), round(road[j][1] + vy / n_ * min(n_, 36)))
        recorded.append(pos)
        sc.node(name, None, "Objects", instance=scene_id, position=v2(*pos), **props)

    def in_corridor(x, y, margin=0):
        tx, ty = int(x // TILE), int(y // TILE)
        if not (0 <= tx < W and 0 <= ty < H):
            return False
        if margin:
            return bool(erode(corridor, margin)[tx, ty]) if False else bool(corridor[tx, ty])
        return bool(corridor[tx, ty])

    def road_dist(x, y):
        return float(np.min(np.hypot(road[:, 0] - x, road[:, 1] - y)))

    # ------------------------------------------------------------ titik penting
    bf_village, bf_pre = P["bonfire_village"], P["bonfire_preboss"]
    i_exit, i_boss, i_pre = road_index(P["exit"]), road_index(P["boss_arena"]), road_index(P["bonfire_preboss"])
    i_js, i_puz = road_index(P["journey_start"]), road_index(P["puzzle"])

    def at(i_a, i_b, t, side=0.0, dist=0.0):
        i = int(i_a + (i_b - i_a) * t)
        th = tangent(i)
        x, y = road[i]
        return (round(x + math.cos(th + math.pi / 2) * side * dist), round(y + math.sin(th + math.pi / 2) * side * dist))

    bf3 = at(i_boss, i_exit, 0.62, 1, 56)
    cp1 = at(i_puz, i_pre, 0.55, 1, 48)
    cp2 = at(i_boss, i_exit, 0.30, -1, 52)
    gate_arena = tuple(int(v) for v in ga)
    start = tuple(int(v) for v in road[min(len(road) - 1, road_index(P["entry"]) + 3)])

    # ------------------------------------------------------------ pohon, semak (dibuat di akhir agar tahu posisi bangunan)
    cells = {"m1a": ("Trees/Model_01/Size_03.png", (0, 0, 48, 96)), "m1b": ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
             "m2a": ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)), "m2b": ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))}
    trees = {}
    for k, (f, box) in cells.items():
        bb = img("props/" + f).crop(box).getbbox()
        trees[k] = (f, (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3]))
    veg = sorted([c for c in components(img("props/Vegetation.png").crop((0, 0, 190, 142)), 1) if c[2] - c[0] < 40],
                 key=lambda c: (c[1] // 8, c[0]))[:4]

    # ------------------------------------------------------------ Dusun Larik
    vc = P["village_center"]
    house_names = {"RumahArman": "house_brown", "RumahPenebang": "house_log", "Lumbung": "house_dark",
                   "RumahWarga": "house_green", "RumahPenjaga": "house_plank"}
    anchor = ((vc[0] * 1 + bf_village[0] * 1.6) / 2.6, (vc[1] * 1 + bf_village[1] * 1.6) / 2.6)   # pusat dusun: antara pusat desa & bonfire desa
    placed_b = []
    house_pos = {}
    extra = {}
    # kandidat: kisi 24 px di sekitar pusat dusun; harus di dalam koridor (juga 50 px ke samping & 70 px ke atas), jauh dari jalan
    cands = []
    for gxp in range(-560, 641, 24):
        for gyp in range(-300, 361, 24):
            x, y = anchor[0] + gxp, anchor[1] + gyp
            ok = all(in_corridor(x + ox, y + oy) for ox, oy in ((0, 0), (-50, 0), (50, 0), (0, -20), (-50, -20), (50, -20), (0, 18)))
            behind_gate = ((x - gate_village[0]) * math.cos(gate_th) + (y - gate_village[1]) * math.sin(gate_th)) < -30   # bangunan di selatan gerbang desa (atap boleh menjorok ke hutan leher)
            if ok and behind_gate and road_dist(x, y) > 76 and road_dist(x, y - 62) > 46 and math.hypot(gxp, gyp * 1.3) < 640:
                cands.append((math.hypot(gxp, gyp * 1.3) + rng.random() * 40, x, y))
    cands.sort()
    plan = ["Penggergajian"] + list(house_names) + ["DapurUmum"]
    gaps = {"Penggergajian": 175, "DapurUmum": 135}
    for name in plan:
        for _, x, y in cands:
            if any(math.hypot(x - bx, y - by) < gaps.get(name, 140) for bx, by in placed_b):
                continue
            if name == "Penggergajian" and not all(in_corridor(x + ox, y + oy) for ox, oy in ((-112, 0), (112, 0), (-112, -60), (112, -60))):
                continue
            if name in house_names:
                house_pos[name] = (round(x), round(y))
            else:
                extra[name] = (round(x), round(y))
            placed_b.append((x, y))
            break
    for name, pos in house_pos.items():
        static_prop(name, pos, f"res://assets/props/buildings/{house_names[name]}.png", (128, 138), collision=(116, 44))
    if "Penggergajian" in extra:
        static_prop("Penggergajian", extra["Penggergajian"], "res://assets/props/stations/Sawmill/Base.png", (256, 144), collision=(220, 40))
    farm = components(img("props/Farm.png"), 1, 6)
    farm = sorted(farm, key=lambda c: (c[1] // 16, c[0]))
    furn = sorted(components(img("props/Furniture.png"), 1, 6), key=lambda c: (c[1] // 16, c[0]))
    cook = img("props/stations/Cooking Station/Cooking Station.png")
    if "DapurUmum" in extra:
        dx, dy = extra["DapurUmum"]
        for nm, box, off in (("DapurGrill", (211, 17, 282, 64), (0, 0)), ("DapurKompor", (144, 101, 192, 128), (-62, 18))):
            bb = cook.crop(box).getbbox()
            region = (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3])
            static_prop(nm, (dx + off[0], dy + off[1]), "res://assets/props/stations/Cooking Station/Cooking Station.png",
                        (region[2] - region[0], region[3] - region[1]), region=region, collision=(region[2] - region[0] - 8, 14))
    # ladang & kebun sayur di sekitar Lumbung (peti tanaman + orang-orangan sawah)
    if "Lumbung" in house_pos:
        lx, ly = house_pos["Lumbung"]
        for i, idx in enumerate((3, 27, 38, 24, 81)):
            c = farm[idx]
            fx, fy = lx - 120 + i * 40, ly + 52 + (i % 2) * 8
            if in_corridor(fx, fy) and road_dist(fx, fy) > 46:
                static_prop(f"TanamanLumbung{i}", (fx, fy), "res://assets/props/Farm.png", (c[2] - c[0], c[3] - c[1]), region=c,
                            collision=(c[2] - c[0] - 6, 8))
        c = farm[18]
        sx_, sy_ = lx + 100, ly + 40
        if in_corridor(sx_, sy_) and road_dist(sx_, sy_) > 50:
            static_prop("OrangOrangSawah", (sx_, sy_), "res://assets/props/Farm.png", (c[2] - c[0], c[3] - c[1]), region=c,
                        collision=(10, 6))
    # lampu & pagar mengelilingi desa
    lamp = furn[54]
    for i, (ox, oy) in enumerate(((-68, -34), (72, -30), (-60, 52), (66, 58))):
        x, y = vc[0] + ox, vc[1] + oy
        if road_dist(x, y) > 34 and in_corridor(x, y):
            static_prop(f"Lampu{i}", (x, y), "res://assets/props/Furniture.png", (lamp[2] - lamp[0], lamp[3] - lamp[1]), region=lamp, collision=(8, 6))
    fence = furn[50]
    fw = fence[2] - fence[0]
    fcount = 0
    for ang in range(0, 360, 9):
        x = vc[0] + math.cos(math.radians(ang)) * 330
        y = vc[1] + math.sin(math.radians(ang)) * 260
        if road_dist(x, y) < 70 or not in_corridor(x, y) or any(math.hypot(x - hx, y - hy) < 105 for hx, hy in placed_b):
            continue
        static_prop(f"Pagar{fcount}", (round(x), round(y)), "res://assets/props/Furniture.png", (fw, fence[3] - fence[1]), region=fence,
                    collision=(fw, 8))
        fcount += 1

    # ------------------------------------------------------------ pohon & semak
    inner = erode(corridor, 2)
    keypts = [P[k] for k in P] + [cp1, cp2, bf3, gate_arena, start]
    placed_t = []
    tnum = 0

    def tree_at(x, y, collide):
        nonlocal tnum
        f, region = trees[rng.choice(list(trees))]
        size = (region[2] - region[0], region[3] - region[1])
        if collide:
            static_prop(f"Pohon{tnum}", (x, y), f"res://assets/props/{f}", size, region=region, collision=(10, 6))
        else:
            free_sprite(f"Pohon{tnum}", (x, y), f"res://assets/props/{f}", size, region)
        tnum += 1

    def okay(x, y, gap=24):
        if any(abs(x - px) < gap and abs(y - py) < 12 for px, py in placed_t):
            return False
        if any(math.hypot(x - kx, y - ky) < 70 for kx, ky in keypts):
            return False
        if any(math.hypot(x - bx, y - by) < 110 for bx, by in placed_b):
            return False
        return True

    for ty in range(H):                    # pita pohon di tepi koridor (bertabrakan) + hutan di sisi hutan (tanpa tabrakan)
        for tx in range(W):
            if corridor[tx, ty] and not inner[tx, ty] and (tx + 2 * ty) % 3 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if road_dist(x, y) > 56 and okay(x, y):
                    placed_t.append((x, y))
                    tree_at(x, y, True)
    near_forest = dilate(corridor, 4) & forest_cells
    for ty in range(H):
        for tx in range(W):
            if near_forest[tx, ty] and (tx * 5 + ty * 3) % 4 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if okay(x, y, 20):
                    placed_t.append((x, y))
                    tree_at(x, y, False)
    for _ in range(170):                   # pohon tersebar di dalam koridor
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, PX_H - 60)
        if inner[int(x // TILE), int(y // TILE)] and road_dist(x, y) > 75 and okay(x, y, 30):
            placed_t.append((x, y))
            tree_at(x, y, True)
    for n in range(190):
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, PX_H - 60)
        if corridor[int(x // TILE), int(y // TILE)] and veg and road_dist(x, y) > 44 and okay(x, y, 10):
            region = rng.choice(veg)
            free_sprite(f"Semak{n}", (x, y), "res://assets/props/Vegetation.png", (region[2] - region[0], region[3] - region[1]), region)

    # ------------------------------------------------------------ stasiun & penanda
    inst("Bonfire1", bonfire_scene, bf_village)
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf3)
    inst("Checkpoint1", checkpoint_scene, cp1)
    inst("Checkpoint2", checkpoint_scene, cp2)
    inst("StasiunRak", station_scene, P["puzzle"], puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="1",
         station_label='"Rak Benih"')
    # gerbang melintang selebar koridor (tegak lurus arah jalan di titik itu)
    def gate_span(pt):
        i = road_index(pt)
        th = tangent(i)
        n = (math.cos(th + math.pi / 2), math.sin(th + math.pi / 2))
        total = 0
        for sgn in (1, -1):
            d = 0
            while d < 700:
                x, y = pt[0] + n[0] * d * sgn, pt[1] + n[1] * d * sgn
                if not in_corridor(x, y):
                    break
                d += 8
            total += d
        return th, total + 24

    th, span = gate_span(gate_village)
    inst("GerbangDesa", gate_scene, gate_village, chapter="1", required_stage="1", gate_height=f"{span:.1f}",
         rotation=f"{th:.4f}", locked_text='"Gerbang desa terkunci.\\nBantu Arman dulu."')
    th2, span2 = gate_span(gate_arena)
    inst("Gerbang", gate_scene, gate_arena, chapter="1", required_stage="2", gate_height=f"{span2:.1f}", rotation=f"{th2:.4f}")
    inst("PulangBarat", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="0", sign_text='"Kembali ke Desa Algoria"')
    inst("PulangTimur", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="2", sign_text='"Ke Tambang Tumpuk"')

    # ------------------------------------------------------------ NPC: Arman, 3 warga, pedagang
    def near_house(name, dx, dy):
        hx, hy = house_pos.get(name, (vc[0] + dx, vc[1] + dy))
        return (hx + dx, hy + dy)

    arman_pos = near_house("RumahArman", 62, 26)
    inst("Arman", npc_scene, arman_pos, npc_id='"arman"')
    inst("Penjaga", npc_scene, near_house("Lumbung", -48, 40) if "Lumbung" in house_pos else (vc[0] - 60, vc[1] + 40), npc_id='"penjaga"',
         dialog_id='"ch1_penjaga"', villager_chapter="1")
    inst("Penebang", npc_scene, (extra["Penggergajian"][0] - 40, extra["Penggergajian"][1] + 34) if "Penggergajian" in extra else (vc[0] + 90, vc[1] - 60),
         npc_id='"penebang"', dialog_id='"ch1_penebang"', villager_chapter="1")
    inst("Sari", npc_scene, (extra["DapurUmum"][0] + 20, extra["DapurUmum"][1] + 40) if "DapurUmum" in extra else (vc[0] - 90, vc[1] - 40),
         npc_id='"sari"', dialog_id='"ch1_sari"', villager_chapter="1")
    inst("Pedagang", npc_scene, (bf_village[0] + 46, bf_village[1] + 20), npc_id='"pedagang"', opens_shop="true")
    inst("PedagangAkhir", npc_scene, (bf3[0] + 52, bf3[1] + 18), npc_id='"pedagang"', opens_shop="true")

    # interior rumah Arman
    if "RumahArman" in house_pos:
        hx, hy = house_pos["RumahArman"]
        sc.node("PintuArman", "Area2D", "Objects", position=v2(hx, hy + 14), script=f'ExtResource("{door_script}")',
                interior_scene='"res://scenes/world/Interior_RumahArman.tscn"', hint_text='"E: Masuk rumah Arman"')
        sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuArman", position=v2(0, 0),
                shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    # ------------------------------------------------------------ musuh, peti, collectible (dari scene lama)
    old = open(BACKUP, encoding="utf-8").read()
    enemies = re.findall(r'\[node name="Musuh\d+"[^\]]*\]\nposition = [^\n]*\n(?:damage_scale = ([^\n]*)\n)?enemy_id = "([^"]*)"', old)
    route = [(i_js, i_puz), (i_puz, i_pre), (i_pre, i_boss)]
    for k, (ds, eid) in enumerate(enemies):
        seg = route[0] if k < len(enemies) * 0.4 else route[1] if k < len(enemies) * 0.85 else route[2]
        t = ((k % 5) + 0.6) / 5.4
        side = 1 if k % 2 == 0 else -1
        x, y = 0, 0
        for attempt in range(12):                       # cari titik bebas pohon/bangunan supaya musuh tidak muncul di dalam tabrakan
            x, y = at(seg[0], seg[1], t + attempt * 0.013, side, rng.randint(40, 120))
            clear = in_corridor(x, y) and road_dist(x, y) >= 24
            clear = clear and not any(abs(x - px) < 32 and abs(y - py) < 24 for px, py in placed_t)
            clear = clear and not any(math.hypot(x - bx, y - by) < 120 for bx, by in placed_b)
            if clear:
                break
        else:
            x, y = at(seg[0], seg[1], t)
        extra_props = {"damage_scale": ds} if ds else {}
        inst(f"Musuh{k + 1}", enemy_scene, (x, y), enemy_id=f'"{eid}"', **extra_props)
    ends = [b[-1] for b in branches]
    for i, e in enumerate(ends):
        inst(f"Peti{i + 1}", chest_scene, (round(e[0]), round(e[1])), roll_count="2")
        inst(f"Herb{i * 3 + 1}", collect["Herb"], (round(e[0] + 26), round(e[1] + 12)))
        inst(f"Herb{i * 3 + 2}", collect["Herb"], (round(e[0] - 24), round(e[1] + 16)))
        inst(f"Ore{i + 1}", collect["Ore"], (round(e[0] + 2), round(e[1] + 30)))
    for i in range(8):
        i0, i1 = ((i_js, i_puz), (i_puz, i_pre), (i_pre, i_boss))[i % 3]
        x, y = at(i0, i1, 0.15 + 0.7 * rng.random(), rng.choice((-1, 1)), rng.randint(60, 150))
        if in_corridor(x, y):
            inst(f"Herb{10 + i}", collect["Herb"], (x, y))
    for i in range(4):
        x, y = at(i_js, i_exit, 0.1 + 0.8 * rng.random(), rng.choice((-1, 1)), rng.randint(30, 90))
        if in_corridor(x, y):
            inst(f"Koin{i + 1}", collect["GoldCoin"], (x, y))
    inst("Potion1", collect["Potion"], at(i_puz, i_pre, 0.8, -1, 70))

    # ------------------------------------------------------------ sungai: tabrakan + jembatan
    for r in rivers:
        y0, y1 = r["rows"][0] * TILE, (r["rows"][1] + 1) * TILE
        x0, x1 = r["cols"][0] * TILE, (r["cols"][1] + 1) * TILE
        bx = r["bx"]
        sc.node(f"TepiSungai_{r['key']}", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
        for nm, (a, b) in (("Kiri", (x0, bx - 32)), ("Kanan", (bx + 32, x1))):
            if b - a > 4:
                sc.node(nm, "CollisionShape2D", f"TepiSungai_{r['key']}", position=v2((a + b) / 2, (y0 + y1) / 2),
                        shape=f'SubResource("{sc.rect_shape(b - a, y1 - y0)}")')
        tex = sc.ext_res("Texture2D", "res://assets/props/bridge_wood.png")
        sc.node(f"Jembatan_{r['key']}", "Sprite2D", "Decor", position=v2(bx, (y0 + y1) / 2), texture=f'ExtResource("{tex}")')

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Arman", "Marker2D", "NPCSpawns", position=v2(*arman_pos), **{"metadata/npc_id": '"arman"'})
    sc.node("FinalNPCs", "Node2D", ".")
    sc.node("Arman", "Marker2D", "FinalNPCs", position=v2(*at(i_boss, i_exit, 0.5, -1, 64)), **{"metadata/npc_id": '"arman"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')

    out = os.path.join(ROOT, "scenes/world/Ch1_HutanIndeks.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ pratinjau (bandingkan dengan docs/layout)
    render_preview(mask, corridor, forest_cells, river_cells, is_dirt, road, P, house_pos, extra, rivers,
                   [("Bonfire", bf_village), ("Bonfire", bf_pre), ("Bonfire", bf3), ("CP", cp1), ("CP", cp2),
                    ("Gerbang", gate_village), ("Gerbang", gate_arena), ("Start", start)])
    outside = [p for p in recorded if not corridor[int(p[0] // TILE), int(p[1] // TILE)]]
    print("Ch1_HutanIndeks.tscn:", tnum, "pohon,", len(enemies), "musuh, bangunan", list(house_pos) + list(extra),
          "| objek di luar koridor:", len(outside), "| koridor", int(corridor.sum()), "tile, hutan", int(forest_cells.sum()), "tile")
    return outside


def render_preview(mask, corridor, forest, river, dirt, road, P, house_pos, extra, rivers, marks):
    Z = 5
    im = Image.new("RGB", (W * Z, H * Z), (40, 70, 140))
    px = im.load()
    for tx in range(W):
        for ty in range(H):
            c = (40, 70, 140)
            if mask[tx, ty]:
                c = (24, 64, 34) if forest[tx, ty] else (96, 150, 70)
            if corridor[tx, ty] and dirt[tx, ty]:
                c = (170, 140, 96)
            if river[tx, ty]:
                c = (70, 130, 200)
            for dx in range(Z):
                for dy in range(Z):
                    px[tx * Z + dx, ty * Z + dy] = c
    d = ImageDraw.Draw(im)
    for name, (x, y) in {**house_pos, **extra}.items():
        d.rectangle([x / TILE * Z - 12, y / TILE * Z - 12, x / TILE * Z + 12, y / TILE * Z + 2], fill=(150, 90, 50), outline=(0, 0, 0))
    for r in rivers:
        d.line([(r["bx"] / TILE * Z - 8, (r["rows"][0] + 1) * Z), (r["bx"] / TILE * Z + 8, (r["rows"][0] + 1) * Z)], fill=(200, 150, 80), width=5)
    for k, (x, y) in P.items():
        d.ellipse([x / TILE * Z - 5, y / TILE * Z - 5, x / TILE * Z + 5, y / TILE * Z + 5], fill=(255, 220, 60), outline=(0, 0, 0))
        d.text((x / TILE * Z + 8, y / TILE * Z - 5), k, fill=(255, 255, 255))
    for k, (x, y) in marks:
        d.rectangle([x / TILE * Z - 3, y / TILE * Z - 3, x / TILE * Z + 3, y / TILE * Z + 3], fill=(255, 90, 40))
        d.text((x / TILE * Z + 5, y / TILE * Z - 4), k, fill=(255, 200, 200))
    im.save(os.path.join(ROOT, "tools/preview_ch1_v2.png"))


if __name__ == "__main__":
    make_nocol_tileset()
    make_bridge()
    build()
