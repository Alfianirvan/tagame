"""Generator Tahap 10: scene Ch5_PohonDunia.tscn (hutan ajaib ungu/merah muda, pohon raksasa di tengah).

Jalankan dari folder proyek:  python tools/gen_magic_tileset.py && python tools/gen_ch5.py
Berbeda dari Ch1-Ch4 (koridor horizontal), tata letak Ch5 meniru struktur TREE:
  - Peta 3200 x 2400 px, Pohon Dunia raksasa di tengah.
  - Akar (root) di selatan: titik mulai + Tedy + Bonfire 1 + Checkpoint 1 di pangkal batang.
  - Jalan bercabang dua (kiri = barisan skeleton, kanan = barisan orc) yang melingkari pohon dan
    bertemu lagi di utara.
  - Tiap cabang punya ranting buntu (leaf) berisi peti/musuh kuat; ranting kanan atas berisi batu puzzle
    (TreeMaze, Quest Tengah), jadi pemain HARUS menjelajah sampai ke "daun".
  - Bonfire 2 di pertemuan cabang, lalu gerbang boss, lalu arena King Subiyan di puncak.
  - Wilayah terakhir: tidak ada jalan keluar ke depan (hanya kembali ke Gua Rantai).
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

MAP_W, MAP_H = 200, 150   # tile -> 3200 x 2400 px
PX_W, PX_H = MAP_W * TILE, MAP_H * TILE
ROAD_HALF = 24            # setengah lebar jalan
CX = PX_W // 2            # sumbu simetri (jalan kiri/kanan saling mencerminkan)


def mirror(pts):
    return [(PX_W - x, y) for x, y in pts]


def catmull(pts, step=8.0):
    """Titik-titik halus (Catmull-Rom) sepanjang polyline, jarak antar titik ~step px."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = [np.array(q, float) for q in p[i - 1:i + 3]]
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return np.array(out)


# ---- jalan (titik kontrol)
TRUNK = [(1600, 2330), (1600, 2150), (1600, 1800)]
LEFT_MAIN = [(1600, 1800), (1350, 1780), (1050, 1620), (830, 1350), (800, 1100), (900, 850), (1200, 690), (1600, 620)]
LEFT_LEAF1 = [(800, 1100), (600, 1070), (380, 1000)]          # ranting kiri tengah
LEFT_LEAF2 = [(1050, 1620), (880, 1830), (700, 2050)]         # ranting kiri bawah
FINAL = [(1600, 620), (1600, 420)]
PATHS = {"trunk": TRUNK, "left": LEFT_MAIN, "right": mirror(LEFT_MAIN), "leaf_l1": LEFT_LEAF1, "leaf_l2": LEFT_LEAF2,
         "leaf_r1": mirror(LEFT_LEAF1), "leaf_r2": mirror(LEFT_LEAF2), "final": FINAL}
SAMPLED = {k: catmull(v) for k, v in PATHS.items()}
ALL_ROAD = np.vstack(list(SAMPLED.values()))


def at(name, frac, off=0.0):
    """Titik pada jalan `name` di pecahan panjang `frac` (0..1), digeser `off` px tegak lurus."""
    pts = SAMPLED[name]
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    i = min(int(np.searchsorted(cum, frac * cum[-1])), len(pts) - 2)
    d = pts[i + 1] - pts[i]
    d = d / (np.linalg.norm(d) or 1)
    p = pts[i] + np.array([-d[1], d[0]]) * off
    return (round(float(p[0])), round(float(p[1])))


def build_ch5(extra=()):
    rng = random.Random(505)
    sc = Scene()
    recorded = []
    tileset = sc.ext_res("TileSet", "res://assets/tilesets/magic_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKing.tscn")
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    gate_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionGate.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/TreeMaze.tscn")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    pts = {
        "start": (1600, 2290), "exit_west": (1500, 2350), "tedy": (1690, 2250),
        "bonfire1": (1510, 2200), "cp1": (1600, 1800), "station": at("leaf_r1", 1.0),
        "bonfire2": (1470, 700), "gate": (1600, 560), "cp2": (1600, 470), "boss": (1600, 300),
    }
    gate_y = pts["gate"][1]
    arena = (1100, 60, 2100, gate_y)   # kotak arena puncak (x0, y0, x1, y1)
    giant = (1600, 1250)               # Pohon Dunia raksasa
    pools = [(1250, 1000, 60), (1950, 1500, 60), (1300, 2000, 55), (2000, 2050, 55), (1400, 1450, 45)]   # kolam ungu
    pads = [pts[k] for k in ("start", "bonfire1", "cp1", "bonfire2", "cp2", "tedy")] + [pts["station"], at("leaf_l1", 1.0),
                                                                                       at("leaf_l2", 1.0), at("leaf_r2", 1.0)]

    # ------------------------------------------------------------ tile (vektor numpy agar cepat)
    gx = (np.arange(MAP_W) * TILE + 8)[:, None] * np.ones((1, MAP_H))
    gy = (np.arange(MAP_H) * TILE + 8)[None, :] * np.ones((MAP_W, 1))
    d_road = np.full((MAP_W, MAP_H), 1e9)
    for p in ALL_ROAD:
        d_road = np.minimum(d_road, np.hypot(gx - p[0], gy - p[1]))
    d_pad = np.full((MAP_W, MAP_H), 1e9)
    for px, py in pads:
        d_pad = np.minimum(d_pad, np.hypot(gx - px, gy - py))
    d_boss = np.hypot(gx - pts["boss"][0], gy - pts["boss"][1])
    in_pool = np.zeros((MAP_W, MAP_H), bool)
    for px, py, r in pools:
        in_pool |= np.hypot(gx - px, gy - py) <= r
    in_pool &= d_road > 60
    # bentuk organik: hutan ajaib berkelok di sekitar akar-cabang-ranting, lapangan Pohon Dunia, dan arena puncak;
    # di luarnya "air ungu" (padat) seperti jurang di Peta Dunia
    skeleton = [(p[0], p[1], 0) for p in ALL_ROAD[::2]] + [(px, py, 80) for px, py in pads]
    skeleton += [(giant[0], giant[1], 260), (pts["boss"][0], pts["boss"][1], 270), (pts["gate"][0], pts["gate"][1], 60)]
    skeleton += [(x, y, 0) for x, y in organic.polyline_samples([(1600, 620), (1600, 300)], 20)]
    skeleton += [(x, y, 40) for x, y in extra]
    core = organic.organic_mask(gx, gy, skeleton, r_base=165, r_amp=60, seed=55)           # cabang pohon
    sil = organic.region_mask("ch5", MAP_W, MAP_H, seed=56)                                  # siluet Peta Dunia
    mask = (organic.dilate(core, 6) & sil) | organic.organic_mask(gx, gy, skeleton, r_base=80, r_amp=15, seed=57)
    walk = lambda x, y: organic.walkable_at(mask, x, y)   # noqa: E731
    inner = organic.erode(mask, 3)
    ground = []
    for tx in range(MAP_W):
        for ty in range(MAP_H):
            if in_pool[tx, ty] or not mask[tx, ty]:
                idx = 6
            elif d_boss[tx, ty] <= 210:
                idx = 5
            elif d_road[tx, ty] <= ROAD_HALF or d_pad[tx, ty] <= 44:
                idx = 3 if rng.random() < 0.75 else 4
            else:
                idx = 0 if rng.random() < 0.85 else rng.choice([1, 2])
            ground.append((tx, ty, 0, idx, 0))

    # ------------------------------------------------------------ node akar
    sc.node("Ch5_PohonDunia", "Node2D", script=f"ExtResource(\"{script}\")", chapter="5",
            music_name="\"ch5_pohon_dunia\"", boss_music_name="\"boss_final_king_subiyan\"",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f"ExtResource(\"{boss_scene}\")")
    sc.node("Suasana", "CanvasModulate", ".", color="Color(0.93, 0.82, 1.08, 1)")   # nuansa ungu tipis
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

    def static_prop(name, pos, tex_path, size, region=None, collision=None, scale=1):
        extra = {"scale": v2(scale, scale)} if scale != 1 else {}
        sc.node(name, "StaticBody2D", "Objects", position=v2(*pos), collision_layer=1, collision_mask=0, **extra)
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

    def keep_clear(x, y):
        tx, ty = cell(x, y)
        if d_road[tx, ty] < 52 or d_pad[tx, ty] < 78 or in_pool[tx, ty]:
            return False
        if arena[0] - 40 <= x <= arena[2] + 40 and y <= arena[3] + 40:
            return False
        if math.hypot(x - giant[0], y - giant[1]) < 250:
            return False
        if any(math.hypot(x - px, y - py) < r + 36 for px, py, r in pools):
            return False
        return True

    # ------------------------------------------------------------ pohon: sakura, musim gugur, dan Pohon Dunia raksasa
    nature = "tilesets_biome/TilesetNature.png"
    nat = img(nature)
    sak = components(nat.crop((192, 32, 256, 82)), 1, 80)[0]
    sak = (sak[0] + 192, sak[1] + 32, sak[2] + 192, sak[3] + 32)
    small = [(c[0], c[1] + 282, c[2], c[3] + 282) for c in sorted(components(nat.crop((0, 282, 192, 336)), 1, 80))
             if 20 < c[2] - c[0] < 50][:5]
    kinds = [sak] + small
    tex = "res://assets/tilesets_biome/TilesetNature.png"
    static_prop("PohonDunia", giant, tex, (sak[2] - sak[0], sak[3] - sak[1]), region=sak, collision=(44, 10), scale=6)

    spots = []
    for ty in range(MAP_H):                               # pita pohon mengikuti tepi organik
        for tx in range(MAP_W):
            if mask[tx, ty] and not inner[tx, ty] and (tx + 2 * ty) % 3 == 0:
                spots.append((tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)))
    for x in range(arena[0], arena[2] + 1, 26):           # dinding arena puncak: sisi selatan (celah di jalan)
        if abs(x - 1600) > 88:
            spots.append((x + rng.randint(-3, 3), gate_y))
    for y in range(arena[1], gate_y, 26):                 # dinding arena: sisi barat & timur
        spots += [(arena[0], y), (arena[2], y)]
    for _ in range(520):                                  # sebaran hutan ajaib
        x, y = rng.randint(40, PX_W - 40), rng.randint(130, PX_H - 60)
        if keep_clear(x, y):
            spots.append((x, y))
    placed = []
    n_trees = 0
    for x, y in spots:
        if any(abs(x - px) < 22 and abs(y - py) < 12 for px, py in placed):
            continue
        tx, ty = cell(x, y)
        if not mask[tx, ty]:
            continue
        if d_road[tx, ty] < 40 and not (abs(x - 1600) <= 100 and y > gate_y - 5 and y < gate_y + 5):
            continue
        if in_pool[tx, ty]:
            continue
        placed.append((x, y))
        r = rng.choice(kinds)
        static_prop(f"Pohon{n_trees}", (x, y), tex, (r[2] - r[0], r[3] - r[1]), region=r, collision=(10, 6))
        n_trees += 1

    # ------------------------------------------------------------ stasiun & penanda
    inst("Bonfire1", bonfire_scene, pts["bonfire1"])
    inst("Bonfire2", bonfire_scene, pts["bonfire2"])
    inst("Checkpoint1", checkpoint_scene, pts["cp1"])
    inst("Checkpoint2", checkpoint_scene, pts["cp2"])
    inst("StasiunLabirin", station_scene, pts["station"], puzzle_scene=f"ExtResource(\"{puzzle_scene}\")", chapter="5",
         station_label="\"Labirin Bercabang\"")
    inst("Gerbang", gate_scene, pts["gate"], chapter="5", required_stage="2", gate_height="180.0", rotation="1.5708")
    inst("PulangBarat", exit_scene, pts["exit_west"], to_chapter="4", sign_text="\"Kembali ke Gua Rantai\"")
    inst("Tedy", npc_scene, pts["tedy"], npc_id="\"tedy\"")

    # ------------------------------------------------------------ musuh (id, jalan, pecahan, geser tegak lurus)
    enemies = [
        ("skeleton", "trunk", 0.35, 60), ("orc", "trunk", 0.6, -60), ("skeleton_rogue", "trunk", 0.85, 50),
        ("skeleton_warrior", "left", 0.12, 50), ("skeleton_rogue", "left", 0.22, -60), ("skeleton_mage", "left", 0.32, 95),
        ("skeleton_warrior", "left", 0.45, -50), ("skeleton_mage", "left", 0.58, 90), ("skeleton_rogue", "left", 0.7, -70),
        ("skeleton_warrior", "left", 0.85, 60),
        ("orc_warrior", "right", 0.12, -50), ("orc_rogue", "right", 0.22, 60), ("orc_shaman", "right", 0.32, -95),
        ("orc_warrior", "right", 0.45, 50), ("orc_shaman", "right", 0.58, -90), ("orc_rogue", "right", 0.7, 70),
        ("orc_warrior", "right", 0.85, -60),
        ("skeleton_warrior", "leaf_l1", 0.55, 40), ("skeleton_mage", "leaf_l1", 0.85, -50),
        ("orc_warrior", "leaf_l2", 0.7, 40),
        ("orc_shaman", "leaf_r1", 0.5, 40), ("orc_warrior", "leaf_r1", 0.8, -50),
        ("skeleton_warrior", "leaf_r2", 0.7, -40),
    ]
    for i, (eid, path, frac, off) in enumerate(enemies):
        inst(f"Musuh{i + 1}", enemy_scene, at(path, frac, off), enemy_id=f"\"{eid}\"")

    # ------------------------------------------------------------ peti & collectible (hadiah di ujung ranting)
    chests = [at("leaf_l1", 1.0, 40), at("leaf_l2", 1.0, 40), at("leaf_r1", 1.0, -45), at("leaf_r2", 1.0, -40), at("left", 0.5, 120)]
    for i, p in enumerate(chests):
        inst(f"Peti{i + 1}", chest_scene, p, roll_count="3" if i < 4 else "2")
    for i, (path, frac, off) in enumerate([("trunk", 0.3, -80), ("left", 0.25, 110), ("left", 0.6, -100), ("right", 0.25, -110),
                                           ("right", 0.6, 100), ("leaf_l1", 0.5, -70), ("leaf_r2", 0.5, 70), ("final", 0.3, 90)]):
        inst(f"Herb{i + 1}", collect["Herb"], at(path, frac, off))
    for i, (path, frac, off) in enumerate([("trunk", 0.5, 30), ("left", 0.4, 40), ("right", 0.4, -40), ("left", 0.78, -30), ("right", 0.78, 30)]):
        inst(f"Koin{i + 1}", collect["GoldCoin"], at(path, frac, off))
    for i, (path, frac, off) in enumerate([("leaf_l2", 0.8, -60), ("leaf_r1", 0.7, 70), ("final", 0.8, -60)]):
        inst(f"Potion{i + 1}", collect["Potion"], at(path, frac, off))
    for i, (path, frac, off) in enumerate([("leaf_l1", 0.3, 60), ("leaf_r2", 0.85, 50), ("left", 0.15, 90), ("right", 0.15, -90)]):
        inst(f"Bijih{i + 1}", collect["Ore"], at(path, frac, off))

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*pts["start"]))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*pts["boss"]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Tedy", "Marker2D", "NPCSpawns", position=v2(*pts["tedy"]), **{"metadata/npc_id": "\"tedy\""})
    sc.nodes.append(f"[node name=\"Player\" parent=\"Objects\" instance=ExtResource(\"{player_scene}\")]\nposition = {v2(*pts['start'])}\n")
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f"SubResource(\"{sc.rect_shape(w, h)}\")")

    out = os.path.join(ROOT, "scenes/world/Ch5_PohonDunia.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())
    if os.environ.get("PREVIEW"):   # pratinjau tile + titik penting untuk pengecekan cepat tanpa editor
        atlas = Image.open(os.path.join(ROOT, "assets/tilesets/magic_tiles.png")).convert("RGBA")
        pv = Image.new("RGBA", (PX_W, PX_H))
        for tx, ty, _, idx, _ in ground:
            pv.paste(atlas.crop((idx * 16, 0, idx * 16 + 16, 16)), (tx * 16, ty * 16))
        pv = pv.convert("RGB")
        from PIL import ImageDraw
        dr = ImageDraw.Draw(pv)
        for x, y in placed:
            dr.rectangle((x - 6, y - 12, x + 6, y), fill=(60, 120, 60))
        dr.ellipse((giant[0] - 150, giant[1] - 100, giant[0] + 150, giant[1] + 20), fill=(220, 120, 160))
        for k, (x, y) in pts.items():
            dr.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(255, 0, 0), width=4)
        pv.resize((PX_W // 4, PX_H // 4), Image.NEAREST).save(os.environ["PREVIEW"])
    outside = [p for p in recorded if not walk(*p)]
    organic.save_preview(os.path.join(ROOT, "tools/preview_ch5.png"), mask, recorded, scale=3)
    print("Ch5_PohonDunia.tscn:", n_trees, "pohon,", len(enemies), "musuh,", len(chests), "peti,", len(outside), "objek di luar")
    return outside


if __name__ == "__main__":
    extra = []
    for _ in range(4):   # ulangi sampai semua objek berada di dalam area hutan
        out = build_ch5(extra)
        if not out:
            break
        extra += out
