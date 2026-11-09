"""Generator Tahap 10: scene wilayah chapter (saat ini Ch1_HutanIndeks.tscn).

Jalankan dari folder proyek:  python tools/gen_region.py
Memakai TileSet yang sudah ada (assets/tilesets/world_tileset.tres, dibuat gen_village.py) dan menulis
scenes/world/Ch1_HutanIndeks.tscn. Hasilnya boleh dirapikan manual di editor Godot (jalan, pohon, musuh).

Tata letak Ch1 (peta 4000 x 1024 px, jalan berkelok dari kiri ke kanan):
  0-500      Gerbang masuk: PlayerStart, papan pulang ke Desa, Bonfire 1
  500-1400   Hutan awal: musuh ringan, peti, herb, Checkpoint 1
  1400-2300  Padang Rak: musuh sedang, puzzle ArrayShelf (Quest Tengah), peti, Bonfire 2
  2540       Gerbang boss (terkunci sampai Quest Tengah selesai)
  2560-3560  Arena Golem Batu (luas) + Checkpoint 2
  3560-4000  Setelah boss: Bonfire 3, Arman (Quest Akhir), papan pulang ke Desa
"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_village import ROOT, TILE, Scene, blue_tiles, components, encode_cells, img, v2  # noqa: E402
import organic  # noqa: E402

MAP_W, MAP_H = 250, 64   # tile -> 4000 x 1024 px
PX_W, PX_H = MAP_W * TILE, MAP_H * TILE


def road_y(x):
    """Titik tengah jalan (px) pada posisi x."""
    return 512 + 96 * math.sin(x / 360.0)


def build_ch1(extra=()):
    """extra = titik objek yang jatuh di luar area jalan pada putaran sebelumnya (dipaksa masuk area)."""
    rng = random.Random(101)
    sc = Scene()
    recorded = []
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
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
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    # ------------------------------------------------------------ titik penting (px)
    def on_road(x, dy=0):
        return (x, round(road_y(x) + dy))

    pts = {
        "start": on_road(110),
        "exit_west": on_road(44),
        "bonfire1": on_road(260, -70),
        "cp1": on_road(1380),
        "station": on_road(2000, -70),
        "bonfire2": on_road(2380, 80),
        "gate": on_road(2540),
        "cp2": on_road(2640),
        "boss": on_road(3100),
        "bonfire3": on_road(3680, -70),
        "arman": on_road(190, 40),
        "exit_east": on_road(3920),
    }
    gate_x = pts["gate"][0]
    wall_east_x = 3580

    # ------------------------------------------------------------ bentuk wilayah ORGANIK (bukan persegi)
    gx, gy = organic.grid(MAP_W, MAP_H)
    skeleton = [(x, y, 0) for x, y in organic.polyline_samples([(x, road_y(x)) for x in range(0, PX_W + 1, 40)], 24)]
    skeleton += [(px, py, 70) for px, py in (pts[k] for k in ("start", "bonfire1", "cp1", "station", "bonfire2", "cp2",
                                                               "bonfire3", "arman", "exit_west", "exit_east"))]
    skeleton += [(pts["boss"][0], pts["boss"][1], 235)]                       # arena boss luas
    skeleton += [(x, y, 40) for x, y in extra]
    # siluet = bentuk Hutan Indeks di Peta Dunia, ditambah koridor jalan supaya semua objek tetap terjangkau
    mask = organic.region_mask("ch1", MAP_W, MAP_H, seed=11) | organic.organic_mask(gx, gy, skeleton, r_base=110, r_amp=30, seed=12)
    mask[:2, :] = mask[:2, :] | (mask[2:3, :] & True)     # tepi kiri/kanan tersambung ke pintu masuk-keluar
    walk = lambda x, y: organic.walkable_at(mask, x, y)   # noqa: E731
    inner = organic.erode(mask, 3)                          # bagian dalam; selisihnya = pita tepi hutan

    # ------------------------------------------------------------ peta tile
    grass = [(1, 10), (2, 10), (3, 10)]
    path = [(6, 10), (7, 10), (8, 10)]
    pads = [pts[k] for k in ("start", "bonfire1", "cp1", "station", "bonfire2", "cp2", "bonfire3", "arman")]
    ground, water = [], []
    water_tile = blue_tiles("tilesets/Water_tiles.png")[0]
    edge = mask & ~organic.erode(mask, 1)                   # satu tile di tepi = pasir/tanah pantai sungai
    for tx in range(MAP_W):
        for ty in range(MAP_H):
            cx, cy = tx * TILE + 8, ty * TILE + 8
            dirt = abs(cy - road_y(cx)) <= 28
            dirt = dirt or any(math.hypot(cx - px, cy - py) <= 46 for px, py in pads)
            dirt = dirt or math.hypot(cx - pts["boss"][0], cy - pts["boss"][1]) <= 170   # lantai arena boss
            dirt = dirt or edge[tx, ty]
            pool = path if dirt else grass
            t = pool[1] if rng.random() < 0.85 else rng.choice(pool)
            ground.append((tx, ty, 0, t[0], t[1]))
            if not mask[tx, ty]:                                # di luar area jalan: sungai/danau (padat)
                water.append((tx, ty, 1, *water_tile))
    ponds_px = []

    # ------------------------------------------------------------ node akar
    sc.node("Ch1_HutanIndeks", "Node2D", script=f"ExtResource(\"{script}\")", chapter="1",
            music_name="\"ch1_hutan_indeks\"", boss_music_name="\"boss\"", map_size=f"Vector2i({PX_W}, {PX_H})",
            boss_scene=f"ExtResource(\"{boss_scene}\")")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=encode_cells(ground), tile_set=f"ExtResource(\"{tileset}\")")
    sc.node("Water", "TileMapLayer", ".", tile_map_data=encode_cells(water), tile_set=f"ExtResource(\"{tileset}\")")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    def sprite(parent, tex_path, size, region=None):
        tex = sc.ext_res("Texture2D", tex_path)
        w, h = size
        props = {"texture": f"ExtResource(\"{tex}\")", "offset": v2(0, -h / 2)}
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
                    position=v2(0, -ch / 2), shape=f"SubResource(\"{sc.rect_shape(cw, ch)}\")")

    def inst(name, scene_id, pos, **props):
        recorded.append(pos)
        sc.node(name, None, "Objects", instance=scene_id, position=v2(*pos), **props)

    # ------------------------------------------------------------ pohon & semak
    cells = {"m1a": ("Trees/Model_01/Size_03.png", (0, 0, 48, 96)), "m1b": ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
             "m2a": ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)), "m2b": ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))}
    trees = {}
    for k, (f, box) in cells.items():
        bb = img("props/" + f).crop(box).getbbox()
        trees[k] = (f, (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3]))

    def keep_clear(x, y):
        if abs(y - road_y(x)) < 62:
            return False                                           # jalan utama selalu lapang
        if any(math.hypot(x - px, y - py) < 78 for px, py in pts.values()):
            return False
        if 2560 <= x <= 3580:
            return False                                           # arena boss luas, tanpa pohon sebaran
        return not any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in ponds_px)

    spots = []
    for ty in range(MAP_H):                  # pita hutan lebat mengikuti tepi organik
        for tx in range(MAP_W):
            if mask[tx, ty] and not inner[tx, ty] and (tx + 2 * ty) % 3 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if abs(y - road_y(x)) > 70 and not any(math.hypot(x - px, y - py) < 78 for px, py in pts.values()):
                    spots.append((x, y))
    for wall_x in (gate_x, wall_east_x):   # dinding arena; celah di jalan
        for y in range(100, 930, 26):
            if abs(y - road_y(wall_x)) > 88 and walk(wall_x, y):
                spots.append((wall_x + rng.randint(-4, 4), y))
    for _ in range(260):           # sebaran hutan
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, 960)
        if walk(x, y) and keep_clear(x, y):
            spots.append((x, y))
    placed = []
    for n, (x, y) in enumerate(spots):
        if any(abs(x - px) < 24 and abs(y - py) < 12 for px, py in placed):
            continue
        placed.append((x, y))
        f, region = trees[rng.choice(list(trees))]
        size = (region[2] - region[0], region[3] - region[1])
        static_prop(f"Pohon{n}", (x, y), f"res://assets/props/{f}", size, region=region, collision=(10, 6))

    veg = sorted([c for c in components(img("props/Vegetation.png").crop((0, 0, 190, 142)), 1)
                  if c[2] - c[0] < 40], key=lambda c: (c[1] // 8, c[0]))[:4]
    for n in range(90):
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, 960)
        if walk(x, y) and veg and (keep_clear(x, y) or abs(y - road_y(x)) > 40):
            region = rng.choice(veg)
            sc.node(f"Semak{n}", "Node2D", "Objects", position=v2(x, y))
            sprite(f"Objects/Semak{n}", "res://assets/props/Vegetation.png", (region[2] - region[0], region[3] - region[1]), region)

    # ------------------------------------------------------------ stasiun & penanda
    inst("Bonfire1", bonfire_scene, pts["bonfire1"])
    inst("Bonfire2", bonfire_scene, pts["bonfire2"])
    inst("Bonfire3", bonfire_scene, pts["bonfire3"])
    inst("Checkpoint1", checkpoint_scene, pts["cp1"])
    inst("Checkpoint2", checkpoint_scene, pts["cp2"])
    inst("StasiunRak", station_scene, pts["station"], puzzle_scene=f"ExtResource(\"{puzzle_scene}\")", chapter="1",
         station_label="\"Rak Benih\"")
    inst("Gerbang", gate_scene, pts["gate"], chapter="1", required_stage="2", gate_height="170.0")
    inst("PulangBarat", exit_scene, pts["exit_west"], to_chapter="0", sign_text="\"Kembali ke Desa\"")
    inst("PulangTimur", exit_scene, pts["exit_east"], to_chapter="2", sign_text="\"Ke Tambang Tumpuk\"")
    inst("Arman", npc_scene, pts["arman"], npc_id="\"arman\"")

    # ------------------------------------------------------------ musuh (id, x, dy dari jalan)
    enemies = [
        ("skeleton", 700, -70), ("skeleton", 820, 80), ("orc", 960, -50), ("orc", 1100, 90), ("skeleton_rogue", 1240, 10),
        ("orc_rogue", 1560, 100), ("skeleton", 1690, -130), ("orc_warrior", 1840, 110), ("orc_shaman", 1930, -110),
        ("skeleton_rogue", 2090, 40), ("orc", 2190, -90), ("skeleton_mage", 2260, 120),
    ]
    for i, (eid, x, dy) in enumerate(enemies):
        x, y = on_road(x, dy)
        inst(f"Musuh{i + 1}", enemy_scene, (x, max(150, min(880, y))), enemy_id=f"\"{eid}\"")

    # ------------------------------------------------------------ peti & collectible
    chests = [(900, -190), (1700, 200), (2300, -170)]
    for i, (x, dy) in enumerate(chests):
        inst(f"Peti{i + 1}", chest_scene, on_road(x, dy), roll_count="2")
    herbs = [(380, 110), (640, -120), (1000, 150), (1320, -100), (1620, -60), (1960, 160), (2230, 60), (3300, 140)]
    for i, (x, dy) in enumerate(herbs):
        inst(f"Herb{i + 1}", collect["Herb"], on_road(x, dy))
    for i, (x, dy) in enumerate([(560, 60), (1180, -40), (1780, 40), (2150, -30)]):
        inst(f"Koin{i + 1}", collect["GoldCoin"], on_road(x, dy))
    inst("Potion1", collect["Potion"], on_road(1460, 170))

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*pts["start"]))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*pts["boss"]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Arman", "Marker2D", "NPCSpawns", position=v2(*pts["arman"]), **{"metadata/npc_id": "\"arman\""})
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(*pts['start'])}\n")
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Ch1_HutanIndeks.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    outside = [p for p in recorded if not walk(*p)]
    organic.save_preview(os.path.join(ROOT, "tools/preview_ch1.png"), mask, recorded)
    print("Ch1_HutanIndeks.tscn:", len(placed), "pohon,", len(enemies), "musuh,", len(chests), "peti,", len(outside), "objek di luar area")
    return outside


if __name__ == "__main__":
    extra = []
    for _ in range(4):   # ulangi sampai semua objek berada di dalam area jalan
        out = build_ch1(extra)
        if not out:
            break
        extra += out
