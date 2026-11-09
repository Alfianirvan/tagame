"""Generator Tahap 10: scene Ch2_TambangTumpuk.tscn (ngarai gurun batu merah-oranye, mulut tambang).

Jalankan dari folder proyek:  python tools/gen_desert_tileset.py && python tools/gen_ch2.py
Memakai TileSet gurun (assets/tilesets/desert_tileset.tres). Hasilnya boleh dirapikan manual di editor Godot.

Tata letak Ch2 (VERTIKAL, 2400 x 4000 px): tambang bertingkat seperti tumpukan (STACK).
Seluruh peta adalah tebing padat; yang berjalan "dipahat" (carve) sebagai lantai:
  Tingkat 1 (y 200-520)    Mulut tambang: PlayerStart, papan kembali ke Hutan, Lilbah, Bonfire 1
        ramp kanan  -> turun ke tingkat 2 (urutan masuk-keluar: terakhir masuk, pertama keluar)
  Tingkat 2 (y 760-1080)   Lorong musuh ringan; kantong buntu berisi peti
        ramp kiri   -> tingkat 3
  Tingkat 3 (y 1320-1640)  Stasiun puzzle StackCrates (Quest Tengah); kantong buntu
        ramp kanan  -> tingkat 4
  Tingkat 4 (y 1880-2200)  Musuh berat, Bonfire 2; kantong buntu
        ramp kiri   -> Gerbang boss (terkunci sampai Quest Tengah selesai)
  Dasar tambang (y 2480-3440) Arena Penyihir Menara (luas, dengan pilar batu) + Checkpoint 2
        ramp kanan  -> tingkat 6 (y 3620-3900): Bonfire 3 dan papan terowongan ke Pelabuhan Antre
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_village import ROOT, TILE, Scene, components, encode_cells, img, v2  # noqa: E402
import organic  # noqa: E402

MAP_W, MAP_H = 150, 250   # tile -> 2400 x 4000 px
PX_W, PX_H = MAP_W * TILE, MAP_H * TILE

# Lantai yang dipahat (x0, y0, x1, y1) dalam px
BANDS = [(120, 200, 2280, 520), (120, 760, 2280, 1080), (120, 1320, 2280, 1640), (120, 1880, 2280, 2200),
         (200, 2480, 2200, 3440), (120, 3620, 2280, 3900)]
RAMPS = [(2050, 500, 2170, 780), (230, 1060, 350, 1340), (2050, 1620, 2170, 1900), (230, 2180, 350, 2500),
         (2050, 3420, 2170, 3640)]
POCKETS = [(1100, 1060, 1400, 1250), (900, 1620, 1200, 1790), (1100, 2180, 1500, 2380)]   # kantong buntu
PILLARS = [(640, 2780, 800, 2900), (1600, 2780, 1760, 2900), (640, 3180, 800, 3300), (1600, 3180, 1760, 3300)]   # pilar batu di arena
# garis rute utama (titik jalan tanah)
ROUTE = [(200, 360), (2110, 360), (2110, 920), (290, 920), (290, 1480), (2110, 1480), (2110, 2040), (290, 2040),
         (290, 2560), (1200, 2560), (1200, 3000), (2110, 3000), (2110, 3760)]


def dist_route(gx, gy):
    d = np.full(gx.shape, 1e9)
    for (x0, y0), (x1, y1) in zip(ROUTE[:-1], ROUTE[1:]):
        lx, ly = x1 - x0, y1 - y0
        t = np.clip(((gx - x0) * lx + (gy - y0) * ly) / (lx * lx + ly * ly), 0, 1)
        d = np.minimum(d, np.hypot(gx - (x0 + t * lx), gy - (y0 + t * ly)))
    return d


def build_ch2(extra=()):
    rng = random.Random(202)
    sc = Scene()
    recorded = []
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/desert_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossPenyihir.tscn")
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    gate_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionGate.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/StackCrates.tscn")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    pts = {
        "start": (230, 380), "exit_west": (160, 360), "lilbah": (340, 420), "bonfire1": (500, 330),
        "station": (1200, 1420), "bonfire2": (520, 2110), "gate": (290, 2380), "cp2": (420, 2570),
        "boss": (1200, 3000), "bonfire3": (1500, 3760), "exit_east": (2200, 3760),
    }
    pads = [pts[k] for k in ("start", "bonfire1", "station", "bonfire2", "cp2", "bonfire3", "lilbah")]

    # ------------------------------------------------------------ peta lantai (carve) dan tile
    gx = (np.arange(MAP_W) * TILE + 8)[:, None] * np.ones((1, MAP_H))
    gy = (np.arange(MAP_H) * TILE + 8)[None, :] * np.ones((MAP_W, 1))
    # bentuk organik: lorong tambang berkelok di sekitar ROUTE (tetap bertingkat seperti tumpukan), kantong buntu & arena bulat
    # Rute dilenturkan: belokan siku dibulatkan (Chaikin), ditambah lekukan samping, rongga gua (gelembung) di sepanjang jalan
    srng = random.Random(77)
    wiggly = []
    for (x0, y0), (x1, y1) in zip(ROUTE[:-1], ROUTE[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) // 260))
        nx, ny = -(y1 - y0), (x1 - x0)
        nl = math.hypot(nx, ny) or 1.0
        for k in range(n):
            t = k / n
            off = srng.uniform(-110, 110) if k else 0.0
            wiggly.append((x0 + (x1 - x0) * t + nx / nl * off, y0 + (y1 - y0) * t + ny / nl * off))
    wiggly.append(ROUTE[-1])
    smooth = wiggly
    for _ in range(3):
        nxt = [smooth[0]]
        for (ax, ay), (bx, by) in zip(smooth[:-1], smooth[1:]):
            nxt += [(0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by), (0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by)]
        nxt.append(smooth[-1])
        smooth = nxt
    route_line = organic.polyline_samples(smooth, 20)
    skeleton = [(x, y, 0) for x, y in route_line]
    for i in range(0, len(route_line), 13):               # rongga gua bulat berukuran acak
        bx, by = route_line[i]
        skeleton.append((bx + srng.uniform(-70, 70), by + srng.uniform(-70, 70), srng.uniform(25, 75)))
    skeleton += [(px, py, 70) for px, py in pads]
    skeleton += [(1200, 3000, 300), (1700, 3000, 120), (700, 3000, 120)]          # arena Penyihir Menara
    tail = organic.polyline_samples([(2110, 3760), (1500, 3820), (900, 3730), (350, 3790)], 20)   # lorong terakhir ke Bonfire 3 / terowongan
    skeleton += [(x, y, 0) for x, y in tail]
    for x0, y0, x1, y1 in POCKETS:                                                   # kantong buntu + lorong penyambung
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        skeleton += [(cx, cy, 60)] + [(x, y, 0) for x, y in organic.polyline_samples([(cx, cy - 140), (cx, cy)], 20)]
    skeleton += [(x, y, 70) for x, y in extra]
    core = organic.organic_mask(gx, gy, skeleton, r_base=135, r_amp=60, seed=22)          # lorong bertingkat
    sil = organic.region_mask("ch2", MAP_W, MAP_H, seed=21)                                # siluet Peta Dunia
    floor = (core & organic.dilate(sil, 2)) | organic.organic_mask(gx, gy, skeleton, r_base=70, r_amp=15, seed=23)
    for x0, y0, x1, y1 in PILLARS:
        floor &= ~(np.hypot(gx - (x0 + x1) / 2, gy - (y0 + y1) / 2) < 70)   # pilar batu bulat
    d_route = dist_route(gx, gy)
    d_pad = np.full(gx.shape, 1e9)
    for px, py in pads:
        d_pad = np.minimum(d_pad, np.hypot(gx - px, gy - py))
    d_boss = np.hypot(gx - pts["boss"][0], gy - pts["boss"][1])

    ground = []
    for tx in range(MAP_W):
        for ty in range(MAP_H):
            if not floor[tx, ty]:
                below_floor = ty + 1 < MAP_H and floor[tx, ty + 1]
                above_floor = ty > 0 and floor[tx, ty - 1]
                idx = 7 if below_floor and rng.random() < 0.5 else (8 if above_floor and rng.random() < 0.3 else rng.choice([5, 6, 9]))
            elif d_route[tx, ty] <= 28 or d_pad[tx, ty] <= 44 or d_boss[tx, ty] <= 230:
                idx = 3 if rng.random() < 0.75 else 4
            else:
                idx = 0 if rng.random() < 0.82 else rng.choice([1, 2])
            ground.append((tx, ty, 0, idx, 0))

    # ------------------------------------------------------------ node akar
    sc.node("Ch2_TambangTumpuk", "Node2D", script=f"ExtResource(\"{script}\")", chapter="2",
            music_name="\"ch2_tambang_tumpuk\"", boss_music_name="\"boss\"", map_size=f"Vector2i({PX_W}, {PX_H})",
            boss_scene=f"ExtResource(\"{boss_scene}\")")
    sc.node("Suasana", "CanvasModulate", ".", color="Color(0.92, 0.84, 0.78, 1)")   # lebih gelap & jingga: dalam tambang
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

    def cell(x, y):
        return (min(max(int(x // TILE), 0), MAP_W - 1), min(max(int(y // TILE), 0), MAP_H - 1))

    def open_around(x, y, r=1):
        tx, ty = cell(x, y)
        return all(floor[min(max(tx + dx, 0), MAP_W - 1), min(max(ty + dy, 0), MAP_H - 1)]
                   for dx in range(-r, r + 1) for dy in range(-r - 1, r + 1))

    def keep_clear(x, y):
        tx, ty = cell(x, y)
        return open_around(x, y) and d_route[tx, ty] > 48 and d_pad[tx, ty] > 80 and d_boss[tx, ty] > 120

    # ------------------------------------------------------------ batu coklat (Pixel Crawler Rocks) di lantai
    rocks = sorted(components(img("props/Rocks.png").crop((0, 15, 100, 75)), 1, 30), key=lambda c: -(c[2] - c[0]) * (c[3] - c[1]))
    rocks = [(c[0], c[1] + 15, c[2], c[3] + 15) for c in rocks][:7]
    n = 0
    for _ in range(260):
        x, y = rng.randint(130, PX_W - 130), rng.randint(210, PX_H - 120)
        if keep_clear(x, y):
            region = rng.choice(rocks)
            size = (region[2] - region[0], region[3] - region[1])
            static_prop(f"Batu{n}", (x, y), "res://assets/props/Rocks.png", size, region=region,
                        collision=(max(6, size[0] - 8), 6))
            n += 1

    # ------------------------------------------------------------ stasiun & penanda
    inst("Bonfire1", bonfire_scene, pts["bonfire1"])
    inst("Bonfire2", bonfire_scene, pts["bonfire2"])
    inst("Bonfire3", bonfire_scene, pts["bonfire3"])
    inst("Checkpoint2", checkpoint_scene, pts["cp2"])
    inst("Checkpoint1", checkpoint_scene, (2110, 1480 + 70))   # pangkal tingkat 3 sisi kanan
    inst("StasiunPeti", station_scene, pts["station"], puzzle_scene=f"ExtResource(\"{puzzle_scene}\")", chapter="2",
         station_label="\"Tumpukan Peti\"")
    inst("Gerbang", gate_scene, pts["gate"], chapter="2", required_stage="2", gate_height="128.0", rotation="1.5708")
    inst("PulangBarat", exit_scene, pts["exit_west"], to_chapter="1", sign_text="\"Kembali ke Hutan Indeks\"")
    inst("PulangTimur", exit_scene, pts["exit_east"], to_chapter="3", sign_text="\"Ke Pelabuhan Antre\"")
    inst("Lilbah", npc_scene, pts["lilbah"], npc_id="\"lilbah\"")

    # ------------------------------------------------------------ musuh (id, x, y): makin dalam makin berat
    enemies = [
        ("skeleton", 900, 410), ("orc", 1500, 320),                                                     # tingkat 1
        ("skeleton", 700, 850), ("orc", 1000, 1000), ("skeleton_rogue", 1300, 860), ("orc_rogue", 1600, 1000),
        ("skeleton", 1900, 870),                                                                        # tingkat 2
        ("orc_warrior", 700, 1400), ("skeleton_rogue", 900, 1560), ("orc_rogue", 1500, 1400),
        ("skeleton_warrior", 1750, 1560), ("orc_shaman", 1950, 1420),                                   # tingkat 3
        ("skeleton_warrior", 1900, 1950), ("orc_warrior", 1600, 2130), ("orc_shaman", 1300, 1960),
        ("skeleton_mage", 1000, 2130), ("skeleton_warrior", 750, 1970), ("orc_warrior", 900, 2100),     # tingkat 4
        ("orc_warrior", 1250, 1150), ("skeleton_warrior", 1050, 1720), ("orc_shaman", 1300, 2290),      # kantong buntu
    ]
    for i, (eid, x, y) in enumerate(enemies):
        inst(f"Musuh{i + 1}", enemy_scene, (x, y), enemy_id=f"\"{eid}\"")

    # ------------------------------------------------------------ peti, bijih & collectible
    for i, p in enumerate([(1250, 1190), (1050, 1750), (1300, 2330), (1500, 960)]):
        inst(f"Peti{i + 1}", chest_scene, p, roll_count="2")
    for i, p in enumerate([(1200, 1140), (1150, 1700), (1250, 2250), (600, 1000), (1800, 1560), (1800, 2130), (2100, 3300),
                           (500, 3350), (1900, 3760), (400, 3800)]):
        inst(f"Bijih{i + 1}", collect["Ore"], p)
    for i, p in enumerate([(800, 400), (1700, 450), (1500, 1020), (400, 1560), (2000, 1400), (1200, 2150), (700, 2150)]):
        inst(f"Herb{i + 1}", collect["Herb"], p)
    for i, p in enumerate([(1100, 360), (1300, 920), (700, 1480), (1500, 2040), (800, 3100), (1700, 3100)]):
        inst(f"Koin{i + 1}", collect["GoldCoin"], p)
    inst("Potion1", collect["Potion"], (1800, 1420))
    inst("Potion2", collect["Potion"], (1000, 2060))
    inst("Potion3", collect["Potion"], (1700, 3770))

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*pts["start"]))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*pts["boss"]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Lilbah", "Marker2D", "NPCSpawns", position=v2(*pts["lilbah"]), **{"metadata/npc_id": "\"lilbah\""})
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(*pts['start'])}\n")
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Ch2_TambangTumpuk.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    if os.environ.get("PREVIEW"):   # pratinjau tile + titik penting untuk pengecekan cepat tanpa editor
        from PIL import ImageDraw
        atlas = Image.open(os.path.join(ROOT, "assets/tilesets/desert_tiles.png")).convert("RGBA")
        pv = Image.new("RGBA", (PX_W, PX_H))
        for tx, ty, _, idx, _ in ground:
            pv.paste(atlas.crop((idx * 16, 0, idx * 16 + 16, 16)), (tx * 16, ty * 16))
        pv = pv.convert("RGB")
        dr = ImageDraw.Draw(pv)
        for k, (x, y) in pts.items():
            dr.ellipse((x - 16, y - 16, x + 16, y + 16), outline=(0, 0, 255), width=5)
        for _, x, y in enemies:
            dr.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(255, 0, 0))
        pv.resize((PX_W // 5, PX_H // 5), Image.NEAREST).save(os.environ["PREVIEW"])
    outside = [p for p in recorded if not floor[min(int(p[0] // TILE), MAP_W - 1), min(int(p[1] // TILE), MAP_H - 1)]]
    organic.save_preview(os.path.join(ROOT, "tools/preview_ch2.png"), floor, recorded, scale=3)
    print("Ch2_TambangTumpuk.tscn:", n, "batu,", len(enemies), "musuh,", len(outside), "objek di luar")
    return outside


if __name__ == "__main__":
    extra = []
    for _ in range(4):   # ulangi sampai semua objek berada di dalam lorong
        out = build_ch2(extra)
        if not out:
            break
        extra += out
