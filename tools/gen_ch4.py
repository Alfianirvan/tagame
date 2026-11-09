"""Generator Tahap 10: scene Ch4_GuaRantai.tscn (pegunungan bersalju, celah gunung, gua es).

Jalankan dari folder proyek:  python tools/gen_snow_tileset.py && python tools/gen_ch4.py
Memakai TileSet salju (assets/tilesets/snow_tileset.tres). Hasilnya boleh dirapikan manual di editor Godot.

Tata letak Ch4 (peta 5800 x 1024 px, jalan setapak berkelok di celah gunung):
  0-500      Gerbang masuk: PlayerStart, papan kembali ke Pelabuhan, Megas (Quest Awal/Akhir), Bonfire 1
  500-1900   Lereng salju: musuh sedang, peti, bijih, Checkpoint 1
  1900-3300  Mulut gua: musuh berat, puzzle LinkedPortals (Quest Tengah), Bonfire 2
  3450       Gerbang boss (terkunci sampai Quest Tengah selesai)
  3470-4650  Arena Ksatria Rantai (lantai es luas) + Checkpoint 2
  4650-5800  Setelah boss: Bonfire 3, papan jembatan es ke Pohon Dunia
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_village import ROOT, TILE, Scene, components, encode_cells, img, v2  # noqa: E402
import organic  # noqa: E402

MAP_W, MAP_H = 362, 64   # tile -> 5792 x 1024 px
PX_W, PX_H = MAP_W * TILE, MAP_H * TILE


def road_y(x):
    return 512 + 100 * math.sin(x / 300.0 + 0.5)


def build_ch4(extra=()):
    rng = random.Random(404)
    sc = Scene()
    recorded = []
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/snow_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKsatria.tscn")
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    gate_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionGate.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/LinkedPortals.tscn")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    def on_road(x, dy=0):
        return (x, round(road_y(x) + dy))

    pts = {
        "start": on_road(110), "exit_west": on_road(44), "megas": on_road(190, 40),
        "bonfire1": on_road(280, -70), "cp1": on_road(1900), "station": on_road(2800, -70),
        "bonfire2": on_road(3250, 80), "gate": on_road(3450), "cp2": on_road(3550), "boss": on_road(4060),
        "bonfire3": on_road(4800, -70), "exit_east": on_road(5700),
    }
    gate_x = pts["gate"][0]
    wall_east_x = 4650
    pads = [pts[k] for k in ("start", "bonfire1", "cp1", "station", "bonfire2", "cp2", "bonfire3", "megas")]

    # ------------------------------------------------------------ tile: pasir, jalan tanah gelap, tebing
    def blob_cells():
        """Gumpalan tebing di luar jalan (batu besar di ngarai)."""
        cells = set()
        for _ in range(95):
            bx, by = rng.randint(8, MAP_W - 8), rng.randint(10, MAP_H - 12)
            w, h = rng.randint(2, 5), rng.randint(2, 3)
            cx, cy = bx * TILE, by * TILE
            if any(abs(cy + h * 8 - road_y(cx)) < 110 for cx in (cx, cx + w * 16)):
                continue
            if any(math.hypot(cx - px, cy - py) < 150 for px, py in pads):
                continue
            if gate_x - 40 <= cx <= wall_east_x + 40:
                continue          # arena luas tanpa gumpalan
            for x in range(bx, bx + w):
                for y in range(by, by + h):
                    cells.add((x, y))
        return cells

    blobs = blob_cells()
    cliff_ids = [8, 9, 12]
    # bentuk organik: celah gunung berkelok mengikuti jalan; di luarnya tebing/gunung padat
    gx, gy = organic.grid(MAP_W, MAP_H)
    skeleton = [(x, y, 0) for x, y in organic.polyline_samples([(x, road_y(x)) for x in range(0, PX_W + 1, 40)], 24)]
    skeleton += [(px, py, 70) for px, py in pads] + [(pts["boss"][0], pts["boss"][1], 230), (pts["exit_east"][0], pts["exit_east"][1], 60)]
    skeleton += [(pts["exit_west"][0], pts["exit_west"][1], 60)] + [(x, y, 40) for x, y in extra]
    mask = organic.region_mask("ch4", MAP_W, MAP_H, seed=44) | organic.organic_mask(gx, gy, skeleton, r_base=110, r_amp=30, seed=45)
    walk = lambda x, y: organic.walkable_at(mask, x, y)   # noqa: E731
    ground = []
    for tx in range(MAP_W):
        top, bottom = -1, MAP_H
        for ty in range(MAP_H):
            cx, cy = tx * TILE + 8, ty * TILE + 8
            wall = False
            if abs(cx - gate_x) <= 16 or abs(cx - wall_east_x) <= 16:   # dinding arena (2 tile) dengan celah di jalan
                wall = abs(cy - road_y(cx)) > 88
            cliff = (not mask[tx, ty]) or (tx, ty) in blobs or wall
            if cliff:
                below = (tx, ty + 1) in blobs or (ty + 1 < MAP_H and mask[tx, ty] and not mask[tx, ty + 1]) or (ty > 0 and mask[tx, ty - 1] and not mask[tx, ty])
                idx = 10 if below and rng.random() < 0.4 else rng.choice(cliff_ids)
                ground.append((tx, ty, 0, idx, 0))
                continue
            dirt = abs(cy - road_y(cx)) <= 28
            dirt = dirt or any(math.hypot(cx - px, cy - py) <= 46 for px, py in pads)
            ice = math.hypot(cx - pts["boss"][0], cy - pts["boss"][1]) <= 190   # lantai es arena boss
            if ice:
                idx = 3 if rng.random() < 0.8 else rng.choice([4, 5])
            elif dirt:
                idx = 6 if rng.random() < 0.75 else 7
            else:
                idx = 0 if rng.random() < 0.88 else rng.choice([1, 2])
            ground.append((tx, ty, 0, idx, 0))

    # ------------------------------------------------------------ node akar
    sc.node("Ch4_GuaRantai", "Node2D", script=f"ExtResource(\"{script}\")", chapter="4",
            music_name="\"ch4_gua_rantai\"", boss_music_name="\"boss\"", map_size=f"Vector2i({PX_W}, {PX_H})",
            boss_scene=f"ExtResource(\"{boss_scene}\")")
    sc.node("Suasana", "CanvasModulate", ".", color="Color(0.88, 0.95, 1.1, 1)")   # nuansa kebiruan dingin
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

    cliff_set = {(c[0], c[1]) for c in ground if c[3] >= 8}

    def on_cliff(x, y):
        return (int(x // TILE), int(y // TILE)) in cliff_set

    def keep_clear(x, y):
        if abs(y - road_y(x)) < 55:
            return False
        if any(math.hypot(x - px, y - py) < 70 for px, py in pts.values()):
            return False
        if gate_x <= x <= wall_east_x:
            return False
        return not on_cliff(x, y) and not on_cliff(x, y - 20)

    # ------------------------------------------------------------ batu coklat (Pixel Crawler Rocks) & palem oasis
    rocks = sorted(components(img("props/Rocks.png").crop((97, 15, 192, 75)), 1, 30), key=lambda c: -(c[2] - c[0]) * (c[3] - c[1]))
    rocks = [(c[0] + 97, c[1] + 15, c[2] + 97, c[3] + 15) for c in rocks][:7]
    n = 0
    for _ in range(130):
        x, y = rng.randint(40, PX_W - 40), rng.randint(120, 900)
        if keep_clear(x, y):
            region = rng.choice(rocks)
            size = (region[2] - region[0], region[3] - region[1])
            static_prop(f"Batu{n}", (x, y), "res://assets/props/Rocks.png", size, region=region,
                        collision=(max(6, size[0] - 8), 6))
            n += 1
    snow_trees = sorted(components(img("tilesets_biome/TilesetNature.png").crop((128, 0, 192, 82)), 1, 80),
                        key=lambda c: (c[1], c[0]))
    snow_trees = [(c[0] + 128, c[1], c[2] + 128, c[3]) for c in snow_trees]
    palms = 0
    for _ in range(70):
        x, y = rng.randint(40, PX_W - 40), rng.randint(120, 900)
        if keep_clear(x, y):
            region = rng.choice(snow_trees)
            static_prop(f"PohonSalju{palms}", (x, y), "res://assets/tilesets_biome/TilesetNature.png",
                        (region[2] - region[0], region[3] - region[1]), region=region, collision=(10, 6))
            palms += 1

    # ------------------------------------------------------------ stasiun & penanda
    for i, k in enumerate(("bonfire1", "bonfire2", "bonfire3")):
        inst(f"Bonfire{i + 1}", bonfire_scene, pts[k])
    inst("Checkpoint1", checkpoint_scene, pts["cp1"])
    inst("Checkpoint2", checkpoint_scene, pts["cp2"])
    inst("StasiunPortal", station_scene, pts["station"], puzzle_scene=f"ExtResource(\"{puzzle_scene}\")", chapter="4",
         station_label="\"Batu Portal\"")
    inst("Gerbang", gate_scene, pts["gate"], chapter="4", required_stage="2", gate_height="170.0")
    inst("PulangBarat", exit_scene, pts["exit_west"], to_chapter="3", sign_text="\"Kembali ke Pelabuhan Antre\"")
    inst("PulangTimur", exit_scene, pts["exit_east"], to_chapter="5", sign_text="\"Jembatan Es ke Pohon Dunia\"")
    inst("Megas", npc_scene, pts["megas"], npc_id="\"megas\"")

    # ------------------------------------------------------------ musuh (id, x, dy dari jalan): lebih berat dari Ch1
    enemies = [
        ("skeleton", 640, -90), ("skeleton_rogue", 760, 100), ("orc", 900, -50), ("orc_rogue", 1050, 90),
        ("skeleton_warrior", 1200, -110), ("orc_warrior", 1350, 80), ("skeleton_rogue", 1500, -60), ("skeleton_mage", 1650, 110),
        ("orc_warrior", 1780, -30), ("skeleton_warrior", 2050, -100), ("orc_warrior", 2180, 110), ("orc_shaman", 2300, -70),
        ("skeleton_mage", 2420, 120), ("skeleton_warrior", 2550, -20), ("orc_shaman", 2900, 100), ("skeleton_mage", 3000, -110),
        ("orc_warrior", 3100, 60), ("skeleton_warrior", 3200, -60),
    ]
    for i, (eid, x, dy) in enumerate(enemies):
        x, y = on_road(x, dy)
        inst(f"Musuh{i + 1}", enemy_scene, (x, max(150, min(880, y))), enemy_id=f"\"{eid}\"")

    # ------------------------------------------------------------ peti, bijih & collectible
    for i, (x, dy) in enumerate([(1100, 170), (2200, -190), (3050, 190)]):
        inst(f"Peti{i + 1}", chest_scene, on_road(x, dy), roll_count="2")
    for i, (x, dy) in enumerate([(520, 140), (820, -150), (1300, 130), (1650, -120), (1960, 150), (2450, 130),
                                 (2750, -140), (3150, -110), (4000, 150), (4350, -140)]):
        inst(f"Bijih{i + 1}", collect["Ore"], on_road(x, dy))
    for i, (x, dy) in enumerate([(430, -110), (1180, 100), (1800, -140), (2260, 160), (2900, -140), (3980, 120)]):
        inst(f"Herb{i + 1}", collect["Herb"], on_road(x, dy))
    for i, (x, dy) in enumerate([(600, 40), (1100, -50), (1500, 50), (2200, -30), (2600, 60)]):
        inst(f"Koin{i + 1}", collect["GoldCoin"], on_road(x, dy))
    inst("Potion1", collect["Potion"], on_road(1800, 170))
    inst("Potion2", collect["Potion"], on_road(2780, -170))

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*pts["start"]))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*pts["boss"]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Megas", "Marker2D", "NPCSpawns", position=v2(*pts["megas"]), **{"metadata/npc_id": "\"megas\""})
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(*pts['start'])}\n")
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Ch4_GuaRantai.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    if os.environ.get("PREVIEW"):   # gambar pratinjau peta (tile saja) untuk pengecekan cepat tanpa editor
        from PIL import Image
        atlas = Image.open(os.path.join(ROOT, "assets/tilesets/snow_tiles.png")).convert("RGBA")
        pv = Image.new("RGBA", (PX_W, PX_H))
        for tx, ty, _, idx, _ in ground:
            pv.paste(atlas.crop((idx * 16, 0, idx * 16 + 16, 16)), (tx * 16, ty * 16))
        pv.convert("RGB").resize((PX_W // 4, PX_H // 4), Image.NEAREST).save(os.environ["PREVIEW"])
    outside = [p for p in recorded if not walk(*p)]
    organic.save_preview(os.path.join(ROOT, "tools/preview_ch4.png"), mask, recorded)
    print("Ch4_GuaRantai.tscn:", n, "batu,", palms, "palem,", len(enemies), "musuh,", len(blobs), "sel tebing sebaran,", len(outside), "objek di luar")
    return outside


if __name__ == "__main__":
    extra = []
    for _ in range(4):   # ulangi sampai semua objek berada di dalam celah gunung
        out = build_ch4(extra)
        if not out:
            break
        extra += out
