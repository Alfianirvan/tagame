"""Generator Tahap 10: scene Ch3_PelabuhanAntre.tscn (pantai berpasir, dermaga kayu, laut, kapal).

Jalankan dari folder proyek:  python tools/gen_harbor_tileset.py && python tools/gen_ch3.py
Memakai TileSet pantai (assets/tilesets/harbor_tileset.tres). Hasilnya boleh dirapikan manual di editor Godot.

Tata letak Ch3 (peta 5400 x 1024 px, jalan papan kayu berkelok di pantai; laut di selatan):
  0-500      Gerbang masuk: PlayerStart, papan kembali ke Tambang, Dadang (Quest Awal/Akhir), Bonfire 1
  500-1800   Pantai awal: musuh ringan-sedang, peti, Checkpoint 1
  1800-3100  Dermaga pelanggan: musuh sedang-berat, puzzle QueueCustomers (Quest Tengah), Bonfire 2
  3300       Gerbang boss (terkunci sampai Quest Tengah selesai)
  3320-4500  Arena Kapten Bajak Laut (geladak papan luas) + Checkpoint 2
  4500-5400  Setelah boss: Bonfire 3, dermaga panjang + Kapal Dadang ke Gua Rantai
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
import organic  # noqa: E402

from gen_village import ROOT, TILE, Scene, components, encode_cells, img, v2  # noqa: E402

MAP_W, MAP_H = 338, 64   # tile -> 5408 x 1024 px
PX_W, PX_H = MAP_W * TILE, MAP_H * TILE


def road_y(x):
    return 400 + 70 * math.sin(x / 340.0)


def shore_y(x):
    """Garis pantai: di bawah ini laut."""
    return 740 + 45 * math.sin(x / 230.0 + 1.0)


def build_ch3(extra=()):
    rng = random.Random(303)
    sc = Scene()
    recorded = []
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/harbor_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKapten.tscn")
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    gate_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionGate.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/QueueCustomers.tscn")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    def on_road(x, dy=0):
        return (x, round(road_y(x) + dy))

    pier_x = 5200
    pts = {
        "start": on_road(110), "exit_west": on_road(44), "dadang": on_road(190, 40),
        "bonfire1": on_road(280, -70), "cp1": on_road(1800), "station": on_road(2600, -70),
        "bonfire2": on_road(3050, 80), "gate": on_road(3300), "cp2": on_road(3400), "boss": on_road(3900),
        "bonfire3": on_road(4650, -70), "exit_east": (pier_x, 850),
    }
    gate_x = pts["gate"][0]
    wall_east_x = 4500
    pads = [pts[k] for k in ("start", "bonfire1", "cp1", "station", "bonfire2", "cp2", "bonfire3", "dadang")]

    # ------------------------------------------------------------ tile: pasir, papan jalan/dermaga, laut (padat)
    # dermaga: lajur papan dari jalan ke laut; yang terakhir (pier_x) adalah dermaga Kapal Dadang
    piers = [(1350, 24), (2300, 24), (2950, 24), (4100, 24), (pier_x, 40)]
    # bentuk organik: daratan sempit berkelok mengikuti jalan; di luarnya laut (utara & selatan)
    gx, gy = organic.grid(MAP_W, MAP_H)
    skeleton = [(x, y, 0) for x, y in organic.polyline_samples([(x, road_y(x)) for x in range(0, PX_W + 1, 40)], 24)]
    skeleton += [(px, py, 70) for px, py in pads]
    skeleton += [(pts["boss"][0], pts["boss"][1], 230), (pts["exit_west"][0], pts["exit_west"][1], 60)]
    skeleton += [(x, y, 40) for x, y in extra]
    mask = organic.region_mask("ch3", MAP_W, MAP_H, seed=33) | organic.organic_mask(gx, gy, skeleton, r_base=110, r_amp=30, seed=34)
    for tx in range(MAP_W):
        for ty in range(MAP_H):
            cx, cy = tx * TILE + 8, ty * TILE + 8
            if any(abs(cx - px) <= hw and road_y(px) - 10 <= cy <= 880 for px, hw in piers):
                mask[tx, ty] = True
    walk = lambda x, y: organic.walkable_at(mask, x, y)   # noqa: E731
    ground = []
    for tx in range(MAP_W):
        for ty in range(MAP_H):
            cx, cy = tx * TILE + 8, ty * TILE + 8
            on_pier = any(abs(cx - px) <= hw and road_y(px) - 10 <= cy <= 880 for px, hw in piers)
            sea = not mask[tx, ty]
            if sea:
                ground.append((tx, ty, 0, 6, 0))
                continue
            wood = on_pier or abs(cy - road_y(cx)) <= 22
            wood = wood or any(math.hypot(cx - px, cy - py) <= 40 for px, py in pads)
            wood = wood or math.hypot(cx - pts["boss"][0], cy - pts["boss"][1]) <= 190   # geladak arena boss
            if wood:
                idx = 3 if rng.random() < 0.7 else rng.choice([4, 5])
            else:
                idx = 0 if rng.random() < 0.8 else rng.choice([1, 2])
            ground.append((tx, ty, 0, idx, 0))

    # ------------------------------------------------------------ node akar
    sc.node("Ch3_PelabuhanAntre", "Node2D", script=f"ExtResource(\"{script}\")", chapter="3",
            music_name="\"ch3_pelabuhan_antre\"", boss_music_name="\"boss\"", map_size=f"Vector2i({PX_W}, {PX_H})",
            boss_scene=f"ExtResource(\"{boss_scene}\")")
    sc.node("Suasana", "CanvasModulate", ".", color="Color(0.95, 0.98, 1.04, 1)")   # nuansa laut tipis
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=encode_cells(ground), tile_set=f"ExtResource(\"{tileset}\")")
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

    sand_set = {(c[0], c[1]) for c in ground if c[3] <= 2}

    def on_sand(x, y):
        return (int(x // TILE), int(y // TILE)) in sand_set

    def keep_clear(x, y):
        if abs(y - road_y(x)) < 50:
            return False
        if any(math.hypot(x - px, y - py) < 70 for px, py in pts.values()):
            return False
        if gate_x <= x <= wall_east_x:
            return False
        return on_sand(x, y) and on_sand(x, y - 14) and on_sand(x + 10, y) and on_sand(x - 10, y)

    # ------------------------------------------------------------ batu, palem, kapal
    rocks = sorted(components(img("props/Rocks.png").crop((0, 15, 100, 75)), 1, 30), key=lambda c: -(c[2] - c[0]) * (c[3] - c[1]))
    rocks = [(c[0], c[1] + 15, c[2], c[3] + 15) for c in rocks][:7]
    n = 0
    for _ in range(45):
        x, y = rng.randint(40, PX_W - 40), rng.randint(130, 900)
        if keep_clear(x, y):
            region = rng.choice(rocks)
            size = (region[2] - region[0], region[3] - region[1])
            static_prop(f"Batu{n}", (x, y), "res://assets/props/Rocks.png", size, region=region,
                        collision=(max(6, size[0] - 8), 6))
            n += 1
    palm_bb = img("tilesets_biome/TilesetDesert.png").crop((160, 160, 192, 192)).getbbox()
    palm = (160 + palm_bb[0], 160 + palm_bb[1], 160 + palm_bb[2], 160 + palm_bb[3])
    inner = organic.erode(mask, 3)
    palm_spots = []
    for ty in range(MAP_H):   # pita palem mengikuti tepi daratan (hanya sisi utara; sisi selatan = pantai terbuka)
        for tx in range(MAP_W):
            if mask[tx, ty] and not inner[tx, ty] and ty * TILE < road_y(tx * TILE) and (tx + 2 * ty) % 4 == 0:
                palm_spots.append((tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14))
    for wall_x in (gate_x, wall_east_x):   # dinding arena dari palem; celah di jalan
        for y in range(150, 700, 26):
            if abs(y - road_y(wall_x)) > 88:
                palm_spots.append((wall_x + rng.randint(-4, 4), y))
    for _ in range(70):
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, 700)
        if keep_clear(x, y):
            palm_spots.append((x, y))
    placed = []
    palms = 0
    for x, y in palm_spots:
        if any(abs(x - px) < 24 and abs(y - py) < 12 for px, py in placed):
            continue
        if not on_sand(x, y):
            continue
        placed.append((x, y))
        static_prop(f"Palem{palms}", (x, y), "res://assets/tilesets_biome/TilesetDesert.png",
                    (palm[2] - palm[0], palm[3] - palm[1]), region=palm, collision=(10, 6))
        palms += 1
    boat_bb = img("tilesets_biome/Boat.png").getbbox()
    boats = 0
    for bx in (700, 1700, 2650, 3600, 4350, 4850, 5330):
        by = round(shore_y(bx) + 120)
        static_prop(f"Kapal{boats}", (bx, by), "res://assets/tilesets_biome/Boat.png",
                    (boat_bb[2] - boat_bb[0], boat_bb[3] - boat_bb[1]), region=boat_bb, collision=(66, 12))
        boats += 1

    # ------------------------------------------------------------ stasiun & penanda
    for i, k in enumerate(("bonfire1", "bonfire2", "bonfire3")):
        inst(f"Bonfire{i + 1}", bonfire_scene, pts[k])
    inst("Checkpoint1", checkpoint_scene, pts["cp1"])
    inst("Checkpoint2", checkpoint_scene, pts["cp2"])
    inst("StasiunAntrean", station_scene, pts["station"], puzzle_scene=f"ExtResource(\"{puzzle_scene}\")", chapter="3",
         station_label="\"Antrean Pelanggan\"")
    inst("Gerbang", gate_scene, pts["gate"], chapter="3", required_stage="2", gate_height="170.0")
    inst("PulangBarat", exit_scene, pts["exit_west"], to_chapter="2", sign_text="\"Kembali ke Tambang Tumpuk\"")
    inst("PulangTimur", exit_scene, pts["exit_east"], to_chapter="4", sign_text="\"Naik Kapal Dadang ke Gua Rantai\"")
    inst("Dadang", npc_scene, pts["dadang"], npc_id="\"dadang\"")

    # ------------------------------------------------------------ musuh (id, x, dy dari jalan): lebih berat dari Ch2
    enemies = [
        ("skeleton", 620, -90), ("orc", 740, 100), ("skeleton_rogue", 880, -60), ("orc_rogue", 1020, 130),
        ("orc_warrior", 1180, -100), ("skeleton_warrior", 1330, 120), ("skeleton_rogue", 1500, -70), ("orc_rogue", 1650, 90),
        ("orc_warrior", 1950, -110), ("skeleton_warrior", 2080, 130), ("orc_shaman", 2200, -80), ("skeleton_mage", 2330, 140),
        ("orc_warrior", 2450, -30), ("skeleton_warrior", 2800, 110), ("orc_shaman", 2900, -120), ("skeleton_mage", 3000, 40),
    ]
    for i, (eid, x, dy) in enumerate(enemies):
        x, y = on_road(x, dy)
        inst(f"Musuh{i + 1}", enemy_scene, (x, max(180, min(660, y))), enemy_id=f"\"{eid}\"")

    # ------------------------------------------------------------ peti & collectible
    for i, (x, dy) in enumerate([(1000, -190), (2100, 220), (2900, -200)]):
        inst(f"Peti{i + 1}", chest_scene, on_road(x, dy), roll_count="2")
    for i, (x, dy) in enumerate([(540, 150), (900, -150), (1400, 160), (1750, -130), (2000, 170), (2550, -150), (3100, 150), (3950, 140), (4250, -150)]):
        inst(f"Herb{i + 1}", collect["Herb"], on_road(x, dy))
    for i, (x, dy) in enumerate([(600, 50), (1100, -60), (1550, 60), (2250, -40), (2650, 70), (4750, 60)]):
        inst(f"Koin{i + 1}", collect["GoldCoin"], on_road(x, dy))
    for i, (x, dy) in enumerate([(1850, 190), (2850, -190)]):
        inst(f"Potion{i + 1}", collect["Potion"], on_road(x, dy))
    for i, (x, dy) in enumerate([(1250, 200), (3600, -170), (4400, 180)]):
        inst(f"Bijih{i + 1}", collect["Ore"], on_road(x, dy))

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*pts["start"]))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*pts["boss"]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Dadang", "Marker2D", "NPCSpawns", position=v2(*pts["dadang"]), **{"metadata/npc_id": "\"dadang\""})
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(*pts['start'])}\n")
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Ch3_PelabuhanAntre.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    if os.environ.get("PREVIEW"):   # gambar pratinjau peta (tile saja) untuk pengecekan cepat tanpa editor
        atlas = Image.open(os.path.join(ROOT, "assets/tilesets/harbor_tiles.png")).convert("RGBA")
        pv = Image.new("RGBA", (PX_W, PX_H))
        for tx, ty, _, idx, _ in ground:
            pv.paste(atlas.crop((idx * 16, 0, idx * 16 + 16, 16)), (tx * 16, ty * 16))
        pv.convert("RGB").resize((PX_W // 4, PX_H // 4), Image.NEAREST).save(os.environ["PREVIEW"])
    outside = [p for p in recorded if not walk(*p)]
    organic.save_preview(os.path.join(ROOT, "tools/preview_ch3.png"), mask, recorded)
    print("Ch3_PelabuhanAntre.tscn:", n, "batu,", palms, "palem,", boats, "kapal,", len(enemies), "musuh,", len(outside), "objek di luar")
    return outside


if __name__ == "__main__":
    extra = []
    for _ in range(4):   # ulangi sampai semua objek berada di dalam area daratan
        out = build_ch3(extra)
        if not out:
            break
        extra += out
