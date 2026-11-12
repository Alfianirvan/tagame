"""Generator Ch1_HutanIndeks.tscn v3: bentuk wilayah dari docs/layout/region_layout.json + DUSUN LARIK berbasis BLUEPRINT GRID.

Jalankan dari folder proyek (setelah make_prefabs.py, make_water_edge.py, make_villagers.py, gen_interior.py):
    python tools/gen_ch1_v3.py
Blueprint desa (tile, pusat C; sumbu X ke timur, Y ke selatan):
    alun-alun 12x12 tile (lantai batu) + sumur di tengah
    4 jalan batu selebar 3 tile ke utara/selatan/timur/barat
    4 rumah di 4 kuadran (>= 2 tile dari jalan, >= 3 tile antar-rumah), pagar pekarangan depan
    bengkel kayu (Sawmill + Meja Kerja + Landasan + Tungku) di tepi TIMUR, dapur umum di barat laut, lumbung di tenggara
Tidak ada rotasi/skala pada prop; semua objek = instance prefab (scenes/prefabs/) di node Objects (y-sort), origin di kaki.
Gerbang desa & gerbang arena = palang MENDATAR (RegionGate.horizontal) pada "leher" jalan.
Air = autotile tepi buatan sendiri (tools/make_water_edge.py).
"""
import base64
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
import gen_ch1_v2 as v2mod  # noqa: E402  (memakai LAYOUT, bantuan numpy, dan fungsi pembantu)
from gen_village import A, ROOT, TILE, Scene, components, img, v2  # noqa: E402
import organic  # noqa: E402

LAYOUT, W, H, PX_W, PX_H, BACKUP = v2mod.LAYOUT, v2mod.W, v2mod.H, v2mod.PX_W, v2mod.PX_H, v2mod.BACKUP
dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx

C = (104, 102)                                       # pusat dusun (tile)
CX, CY = C[0] * TILE + 8, C[1] * TILE + 8            # pusat dusun (px)
DIRS8 = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PREFAB_SIZE = {}                                     # nama prefab -> (lebar, tinggi) sprite (dari _prefabs.json)


def tp(dx, dy):
    """Titik (px) pada offset tile (dx, dy) dari pusat dusun."""
    return (round(CX + dx * TILE), round(CY + dy * TILE))


def water_idx(is_water, x, y):
    """Bitmask darat 8 tetangga untuk sel air (x, y) -> koordinat atlas water_edge.png."""
    i = 0
    for bit, (dx, dy) in enumerate(DIRS8):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and not is_water[nx, ny]:
            i |= 1 << bit
    return i


def build():
    import json
    for e in json.load(open(os.path.join(ROOT, "scenes/prefabs/_prefabs.json"), encoding="utf-8")):
        PREFAB_SIZE[e["name"]] = (e["w"], e["h"])
    rng = random.Random(3003)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    orig = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute: entry -> jalan selatan -> alun-alun -> jalan utara -> puzzle -> ... -> exit
    s_end = tp(0, 16)
    n_end = tp(0, -26)
    i_s = idx_near(orig, s_end)
    i_puz = idx_near(orig, P["puzzle"])
    seg_south = organic.polyline_samples([tuple(p) for p in orig[: i_s + 1]] + [s_end, tp(0, 0)], 12.0)
    seg_north = organic.polyline_samples([tp(0, 0), n_end, tuple(orig[i_puz])], 12.0)
    rest = orig[i_puz:]
    route = np.vstack([seg_south, seg_north, rest])

    def route_i(pt):
        return idx_near(route, pt)

    i_puz_r = route_i(P["puzzle"])
    i_pre, i_boss, i_exit = route_i(P["bonfire_preboss"]), route_i(P["boss_arena"]), route_i(P["exit"])

    def tang(arr, i):
        a, b = arr[max(0, i - 3)], arr[min(len(arr) - 1, i + 3)]
        return math.atan2(b[1] - a[1], b[0] - a[0])

    def at(i_a, i_b, t, side=0.0, dist=0.0):
        i = int(i_a + (i_b - i_a) * t)
        th = tang(route, i)
        x, y = route[i]
        return (round(x + math.cos(th + math.pi / 2) * side * dist), round(y + math.sin(th + math.pi / 2) * side * dist))

    # ------------------------------------------------------------ area yang bisa dijelajahi
    mask_d = dilate(mask, 2)
    # lahan desa: gumpalan ORGANIK (bukan persegi): titik-titik tiap 4 tile, tepi berombak oleh noise; baris di atas C-17 milik leher gerbang
    jr = random.Random(5)
    vpts = [(tx * TILE + 8 + jr.randint(-26, 26), ty * TILE + 8 + jr.randint(-26, 26), jr.randint(-34, 22))
            for tx in range(C[0] - 23, C[0] + 35, 4) for ty in range(C[1] - 13, C[1] + 16, 4)]
    village_rect = organic.organic_mask(gx, gy, vpts, r_base=int(5.8 * TILE), r_amp=52, seed=77)
    top_wave = C[1] - 15 + np.round(3.0 * organic.smooth_noise(gx, gy, 9)).astype(int)     # tepi atas berombak, bukan garis lurus
    village_rect &= np.arange(H)[None, :] >= top_wave
    village_rect[:, :C[1] - 17] = False
    connector = dist_to(gx, gy, seg_south) <= 5 * TILE + 8
    skeleton = [(x, y, 0) for x, y in rest]
    pads = {"puzzle": 55, "bonfire_preboss": 40, "boss_arena": 85, "exit": 40}
    skeleton += [(P[k][0], P[k][1], r) for k, r in pads.items()]
    branches = []
    ga_row = int(((P["bonfire_preboss"][1] + P["boss_arena"][1]) / 2) // TILE)
    sealed_rows = set(range(C[1] - 25, C[1] - 16)) | set(range(ga_row - 4, ga_row + 5))      # baris leher gerbang (disegel)
    er8 = erode(mask, 8)

    def make_branch(a_i, b_i, t, side):
        base = route[int(a_i + (b_i - a_i) * t)]
        th = tang(route, int(a_i + (b_i - a_i) * t)) + side * math.pi / 2
        pts = [tuple(base)]
        for step in range(1, 40):
            x, y = base[0] + math.cos(th) * step * TILE, base[1] + math.sin(th) * step * TILE
            tx, ty = int(x // TILE), int(y // TILE)
            if not (0 <= tx < W and 0 <= ty < H) or not er8[tx, ty] or step > 26 or ty in sealed_rows:
                break
            pts.append((x, y))
        return pts

    for a_i, b_i, t, side in ((i_puz_r, i_pre, 0.4, 1), (i_pre, i_boss, 0.3, -1), (i_boss, i_exit, 0.55, 1)):
        pts = make_branch(a_i, b_i, t, side)
        if len(pts) < 8:
            pts = make_branch(a_i, b_i, t, -side)
        branches.append(pts)
        skeleton += [(x, y, -125) for x, y in pts] + [(pts[-1][0], pts[-1][1], 20)]
    corridor = organic.organic_mask(gx, gy, skeleton, r_base=205, r_amp=42, seed=31) & mask_d
    corridor |= village_rect & mask_d
    corridor |= connector & mask_d
    corridor |= dist_to(gx, gy, route) <= 34
    # gerbang desa: leher sempit lurus (sejajar sumbu) di atas desa, lebar 9 tile, menyegel seluruh peta di baris itu
    ty_a, ty_b = C[1] - 24, C[1] - 18
    cols = np.arange(W)
    keep = np.abs(cols - C[0]) <= 4
    for ty in range(ty_a, ty_b + 1):
        corridor[:, ty] &= keep
        corridor[np.abs(cols - C[0]) <= 4, ty] |= mask_d[np.abs(cols - C[0]) <= 4, ty]
    gate_v_y = (C[1] - 21) * TILE + 8
    # gerbang arena: leher lebar 11 tile di antara Bonfire pra-boss dan arena
    ga = route[route_i((P["bonfire_preboss"][0], ga_row * TILE + 8))]
    ga_col = int(ga[0] // TILE)
    keep2 = np.abs(cols - ga_col) <= 5
    for ty in range(ga_row - 3, ga_row + 4):
        corridor[:, ty] &= keep2
        corridor[keep2, ty] |= mask_d[keep2, ty]
    gate_a = (int(ga_col * TILE + 8), ga_row * TILE + 8)

    # ------------------------------------------------------------ sungai + jembatan (entry & exit), sejajar sumbu
    rivers = []
    for key, rows in (("entry", (-5, -3)), ("exit", (3, 5))):
        ty0, ty1 = int(P[key][1] // TILE) + rows[0], int(P[key][1] // TILE) + rows[1]
        mid = (ty0 + ty1) / 2 * TILE + 8
        ri = int(np.argmin(np.abs(route[:, 1] - mid)))
        bx = float(route[ri][0])
        txc = int(bx // TILE)
        lo = txc
        while lo > 0 and corridor[lo - 1, ty0:ty1 + 1].all():
            lo -= 1
        hi = txc
        while hi < W - 1 and corridor[hi + 1, ty0:ty1 + 1].all():
            hi += 1
        rivers.append({"rows": (ty0, ty1), "cols": (lo, hi), "bx": bx, "key": key})
    river = np.zeros_like(mask)
    bridge = np.zeros_like(mask)
    for r in rivers:
        river[r["cols"][0]:r["cols"][1] + 1, r["rows"][0]:r["rows"][1] + 1] = True
        for tx in range(r["cols"][0], r["cols"][1] + 1):
            if abs(tx * TILE + 8 - r["bx"]) <= 32:
                bridge[tx, r["rows"][0]:r["rows"][1] + 1] = True
    # laut hanya di tempat yang BIRU pada docs/layout/*_layout.png; abu-abu = wilayah lain (daratan, tak bisa dimasuki) -> kanopi hutan
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch1_HutanIndeks_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 36 and ty >= 8   # 8 baris atas tertutup judul gambar
    forest_cells = (mask | ~sea_img) & ~corridor
    sea = sea_img & ~mask & ~corridor
    water = sea | river

    # ------------------------------------------------------------ peta tile
    grass = [(1, 10), (2, 10), (3, 10)]          # hanya baris 10: baris 11 lebih gelap -> pola kotak-kotak
    stone = [(6, 10), (7, 10), (8, 10)]
    dirt = [(11, 10), (12, 10), (13, 10)]
    d_route = dist_to(gx, gy, route)
    in_village_stone = np.zeros_like(mask)
    in_village_stone[C[0] - 6:C[0] + 6, C[1] - 6:C[1] + 6] = True                 # alun-alun 12x12
    in_village_stone[C[0] - 1:C[0] + 2, C[1] - 17:C[1] + 17] = True               # jalan utara-selatan, 3 tile
    in_village_stone[C[0] - 18:C[0] + 28, C[1] - 1:C[1] + 2] = True               # jalan barat-timur, 3 tile
    in_village_stone &= mask_d
    is_dirt = d_route <= 30 + 5 * organic.smooth_noise(gx, gy, 5)
    for pt, rr in ((P["puzzle"], 52), (P["bonfire_preboss"], 40), (P["boss_arena"], 150), (P["exit"], 40), (P["entry"], 40)):
        is_dirt |= np.hypot(gx - pt[0], gy - pt[1]) <= rr
    ground, pathc, watc, rivc, brc, forest = [], [], [], [], [], []
    for tx in range(W):
        for ty in range(H):
            g = grass[(tx * 7 + ty * 13) % 3]
            ground.append((tx, ty, 0, g[0], g[1]))
            if corridor[tx, ty] and not water[tx, ty]:
                if in_village_stone[tx, ty]:
                    s_ = stone[(tx * 7 + ty * 3) % 3]
                    pathc.append((tx, ty, 0, s_[0], s_[1]))
                elif is_dirt[tx, ty]:
                    d_ = dirt[(tx * 5 + ty * 11) % 3]
                    pathc.append((tx, ty, 0, d_[0], d_[1]))
            if water[tx, ty]:
                i = water_idx(water, tx, ty)
                cell = (tx, ty, 0, i % 16, i // 16)
                if sea[tx, ty]:
                    watc.append(cell)
                elif bridge[tx, ty]:
                    brc.append(cell)
                else:
                    rivc.append(cell)
            if forest_cells[tx, ty]:
                forest.append((tx, ty, 1, tx % 25, ty % 25))

    # ------------------------------------------------------------ scene
    sc = Scene()
    ts_world = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    ts_water = sc.ext_res("TileSet", "res://assets/tilesets/water_edge_tileset.tres")
    ts_nocol = sc.ext_res("TileSet", "res://assets/tilesets/water_edge_nocol_tileset.tres")
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
    anvil_script = sc.ext_res("Script", "res://scripts/entities/Anvil.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}

    sc.node("Ch1_HutanIndeks", "Node2D", script=f'ExtResource("{script}")', chapter="1", music_name='"ch1_hutan_indeks"',
            boss_music_name='"boss"', map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(pathc), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Forest", "TileMapLayer", ".", tile_map_data=b64cells(forest), tile_set=f'ExtResource("{ts_forest}")')
    sc.node("Water", "TileMapLayer", ".", tile_map_data=b64cells(watc), tile_set=f'ExtResource("{ts_water}")')
    sc.node("River", "TileMapLayer", ".", tile_map_data=b64cells(rivc), tile_set=f'ExtResource("{ts_water}")')
    sc.node("RiverBridge", "TileMapLayer", ".", tile_map_data=b64cells(brc), tile_set=f'ExtResource("{ts_nocol}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    recorded = []
    buildings = []        # (x, y_kaki, w, h) untuk membersihkan pohon

    def prefab(node, pref, pos, solid=True, **props):
        pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
        sc.node(node, None, "Objects", instance=pid, position=v2(*pos), **props)
        recorded.append(pos)
        if solid:
            w, h = PREFAB_SIZE.get(pref, (16, 16))
            buildings.append((pos[0], pos[1], w, h))

    def inst(name, scene_id, pos, **props):
        tx_, ty_ = int(pos[0] // TILE), int(pos[1] // TILE)
        if name.startswith(("Herb", "Koin", "Ore", "Potion")) and not (0 <= tx_ < W and 0 <= ty_ < H and corridor[tx_, ty_] and not water[tx_, ty_]):
            return                                   # collectible yang jatuh di hutan/air/leher gerbang dibuang
        recorded.append(pos)
        sc.node(name, None, "Objects", instance=scene_id, position=v2(*pos), **props)

    # ------------------------------------------------------------ DUSUN LARIK (blueprint)
    prefab("Sumur", "Sumur", tp(0, 1))
    houses = {"RumahArman": ("Rumah_Krem", (-11.5, -3.5)), "RumahPenebang": ("Rumah_Kayu", (11.5, -3.5)),
              "RumahWarga": ("Rumah_Hijau", (-11.5, 12.5)), "RumahPenjaga": ("Rumah_Papan", (11.5, 12.5))}
    for name, (pref, (dx, dy)) in houses.items():
        prefab(name, pref, tp(dx, dy))
    prefab("Lumbung", "Lumbung", tp(22.5, 12.5))
    # bengkel kayu di tepi timur (di luar jalan): Sawmill, Meja Kerja, Tunggul, Landasan tempa, Tungku
    prefab("Penggergajian", "Sawmill_Besar", tp(26, -9.4))
    prefab("MejaKerja", "MejaKerja_Kayu_2", tp(19.6, -3.1))
    prefab("LandasanTempa", "Landasan_1", tp(24.2, -3.1), script=f'ExtResource("{anvil_script}")')
    prefab("TungkuDesa", "Tungku_Bata_2", tp(28.6, -3.1))
    prefab("TunggulKapak", "Tunggul_Kapak", tp(30.6, -8.0))
    # dapur umum di barat laut
    prefab("DapurGrill", "Dapur_Panggangan_Besar", tp(-11, -14.5))
    prefab("DapurKompor", "Dapur_Kompor", tp(-16.5, -14.3))
    prefab("DapurBarel", "Barel_Air", tp(-6.5, -14.2))
    # alun-alun: lampu di keempat sudut + perabot
    for i, (dx, dy) in enumerate(((-7.2, -6.8), (7.2, -6.8), (-7.2, 7.2), (7.2, 7.2), (2.6, -12), (-2.6, 12))):
        prefab(f"Lampu{i}", "Lampu_Tiang", tp(dx, dy))
    prefab("AlunPeti1", "Peti_Kayu_A", tp(-4.5, -4.2))
    prefab("AlunPeti2", "Peti_Kayu_B", tp(4.4, -4.2))
    prefab("AlunBarel", "Barel_Besar", tp(-4.4, 5.2))
    prefab("AlunGuci", "Guci", tp(4.5, 5.2))
    prefab("OrangOrang", "OrangOrangSawah", tp(30, 14.5))
    # pagar pekarangan depan tiap rumah (celah 3 tile di pintu)
    fence_w = PREFAB_SIZE["Pagar_Kayu"][0]
    for name, (pref, (dx, dy)) in houses.items():
        fy = dy + (1.2 if dy < 0 else 1.7)
        left, right = dx - 4.2, dx + 4.2
        gap = 1.7
        n = 0
        for x0, x1 in ((left, dx - gap), (dx + gap, right)):
            x = x0 * TILE
            while x + fence_w / 2 <= x1 * TILE + 8:
                prefab(f"Pagar_{name}_{n}", "Pagar_Kayu", tp(0, 0)[0:0] or (round(CX + x + fence_w / 2), round(CY + fy * TILE)), solid=False)
                x += fence_w
                n += 1
        prefab(f"Tiang_{name}_L", "Tiang_Pagar", (round(CX + left * TILE), round(CY + fy * TILE)), solid=False)
        prefab(f"Tiang_{name}_R", "Tiang_Pagar", (round(CX + right * TILE), round(CY + fy * TILE)), solid=False)

    # ------------------------------------------------------------ penanda perjalanan
    bf1 = tp(-5, 8.5)
    bf_pre = P["bonfire_preboss"]
    bf3 = at(i_boss, i_exit, 0.62, 1, 56)
    cp1 = at(i_puz_r, i_pre, 0.55, 1, 48)
    cp2 = at(i_boss, i_exit, 0.30, -1, 52)
    start = tuple(int(v) for v in route[min(len(route) - 1, 3)])
    inst("Bonfire1", bonfire_scene, bf1)
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf3)
    inst("Checkpoint1", checkpoint_scene, cp1)
    inst("Checkpoint2", checkpoint_scene, cp2)
    inst("StasiunRak", station_scene, P["puzzle"], puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="1", station_label='"Rak Benih"')
    inst("GerbangDesa", gate_scene, (CX, gate_v_y), chapter="1", required_stage="1", gate_height=str(9 * TILE + 32),
         horizontal="true", locked_text='"Gerbang desa terkunci.\\nBantu Arman dulu."')
    inst("Gerbang", gate_scene, gate_a, chapter="1", required_stage="2", gate_height=str(11 * TILE + 32), horizontal="true")
    inst("PulangBarat", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="0", sign_text='"Kembali ke Desa Algoria"')
    inst("PulangTimur", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="2", sign_text='"Ke Tambang Tumpuk"')
    # perkemahan kecil di Bonfire pra-boss & pasca-boss (prefab)
    for (bx, by), kit in ((bf_pre, (("Dapur_PanciGantung", (-58, 14)), ("Peti_Kayu_A", (52, 10)), ("Barel_Air", (64, 24)))),
                          (bf3, (("Dapur_Panggangan_Kecil", (-62, 14)), ("Barel_Besar", (56, 8)), ("Peti_Kayu_B", (70, 22))))):
        for nm, (ox, oy) in kit:
            prefab(f"Kemah_{nm}_{bx}", nm, (bx + ox, by + oy))

    # ------------------------------------------------------------ NPC
    door_x, door_y = tp(-11.5, -3.5)
    npc_positions = [("Arman", (door_x + 38, door_y + 18)), ("Penjaga", tp(17.0, 6.0)), ("Penebang", tp(22.0, -1.6)),
                     ("Sari", tp(-8.8, -13.2)), ("Pedagang", tp(4.2, 9.2)), ("PedagangAkhir", (bf3[0] + 52, bf3[1] + 18))]
    inst("Arman", npc_scene, (door_x + 38, door_y + 18), npc_id='"arman"')
    inst("Penjaga", npc_scene, tp(17.0, 6.0), npc_id='"penjaga"', dialog_id='"ch1_penjaga"', villager_chapter="1")
    inst("Penebang", npc_scene, tp(22.0, -1.6), npc_id='"penebang"', dialog_id='"ch1_penebang"', villager_chapter="1")
    inst("Sari", npc_scene, tp(-8.8, -13.2), npc_id='"sari"', dialog_id='"ch1_sari"', villager_chapter="1")
    inst("Pedagang", npc_scene, tp(4.2, 9.2), npc_id='"pedagang"', opens_shop="true")
    inst("PedagangAkhir", npc_scene, (bf3[0] + 52, bf3[1] + 18), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuArman", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_RumahArman.tscn"', hint_text='"E: Masuk rumah Arman"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuArman", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    # ------------------------------------------------------------ pohon (bersih 4 tile dari bangunan)
    cells = {"m1a": ("Trees/Model_01/Size_03.png", (0, 0, 48, 96)), "m1b": ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
             "m2a": ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)), "m2b": ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))}
    trees = {}
    for k, (f, box) in cells.items():
        bb = img("props/" + f).crop(box).getbbox()
        trees[k] = (f, (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3]))
    veg = sorted([c for c in components(img("props/Vegetation.png").crop((0, 0, 190, 142)), 1) if c[2] - c[0] < 40],
                 key=lambda c: (c[1] // 8, c[0]))[:4]

    def near_building(x, y, clear=4 * TILE):
        for bx, by, w, h in buildings:
            dx = max(abs(x - bx) - w / 2, 0)
            dy = max(abs(y - (by - h / 2)) - h / 2, 0)
            if math.hypot(dx, dy) < clear:
                return True
        return False

    keypts = list(P.values()) + [cp1, cp2, bf3, gate_a, (CX, gate_v_y), start, bf1]
    inner = erode(corridor, 2)
    placed_t = []
    tnum = 0

    def sprite_node(parent, tex_path, region):
        tex = sc.ext_res("Texture2D", tex_path)
        w, h = region[2] - region[0], region[3] - region[1]
        sc.node("Sprite2D", "Sprite2D", parent, texture=f'ExtResource("{tex}")', offset=v2(0, -h / 2), region_enabled="true",
                region_rect=f"Rect2({region[0]}, {region[1]}, {w}, {h})")

    def tree_at(x, y, collide):
        nonlocal tnum
        f, region = trees[rng.choice(list(trees))]
        name = f"Pohon{tnum}"
        if collide:
            sc.node(name, "StaticBody2D", "Objects", position=v2(x, y), collision_layer=1, collision_mask=0)
            sprite_node(f"Objects/{name}", f"res://assets/props/{f}", region)
            sc.node("CollisionShape2D", "CollisionShape2D", f"Objects/{name}", position=v2(0, -3), shape=f'SubResource("{sc.rect_shape(10, 6)}")')
        else:
            sc.node(name, "Node2D", "Objects", position=v2(x, y))
            sprite_node(f"Objects/{name}", f"res://assets/props/{f}", region)
        tnum += 1

    # titik yang harus terlihat jelas: NPC, Bonfire, pedagang, gerbang. Tajuk pohon (tinggi ~96 px) tidak boleh menutupinya:
    # tolak pohon di jarak < 56 px, atau tepat di bawah titik itu (pohon dengan kaki lebih selatan menggambar di atasnya).
    visible_pts = [pos for nm, pos in npc_positions] + [bf1, bf_pre, bf3, cp1, cp2, start, (CX, gate_v_y), gate_a]

    def covers_point(x, y):
        for vx, vy in visible_pts:
            if math.hypot(x - vx, y - vy) < 56 or (abs(x - vx) < 34 and 0 <= y - vy <= 104):
                return True
        return False

    def tree_ok(x, y, gap=24):
        if covers_point(x, y):
            return False
        if any(abs(x - px) < gap and abs(y - py) < 12 for px, py in placed_t):
            return False
        if any(math.hypot(x - kx, y - ky) < 70 for kx, ky in keypts):
            return False
        return not near_building(x, y)

    road_d_cache = d_route
    def road_dist(x, y):
        return float(road_d_cache[int(x // TILE), int(y // TILE)]) if 0 <= x < PX_W and 0 <= y < PX_H else 0.0

    for ty in range(H):
        for tx in range(W):
            if corridor[tx, ty] and not inner[tx, ty] and (tx + 2 * ty) % 3 == 0 and not water[tx, ty]:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if road_dist(x, y) > 56 and tree_ok(x, y) and not in_village_stone[int(x // TILE), int(y // TILE)]:
                    placed_t.append((x, y))
                    tree_at(x, y, True)
    near_forest = dilate(corridor, 4) & forest_cells
    for ty in range(H):
        for tx in range(W):
            if near_forest[tx, ty] and (tx * 5 + ty * 3) % 4 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if tree_ok(x, y, 20):
                    placed_t.append((x, y))
                    tree_at(x, y, False)
    for _ in range(170):
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, PX_H - 60)
        tx, ty = int(x // TILE), int(y // TILE)
        if inner[tx, ty] and not village_rect[tx, ty] and road_dist(x, y) > 75 and tree_ok(x, y, 30):
            placed_t.append((x, y))
            tree_at(x, y, True)
    for n in range(150):
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, PX_H - 60)
        tx, ty = int(x // TILE), int(y // TILE)
        if corridor[tx, ty] and not water[tx, ty] and veg and road_dist(x, y) > 44 and not near_building(x, y, 40) and tree_ok(x, y, 10):
            region = rng.choice(veg)
            sc.node(f"Semak{n}", "Node2D", "Objects", position=v2(x, y))
            sprite_node(f"Objects/Semak{n}", "res://assets/props/Vegetation.png", region)

    # semak/rumpun di tepi lahan agar peralihan rumput -> hutan tidak berupa garis lurus
    edge_cells = corridor & ~erode(corridor, 1) & ~water & ~in_village_stone
    bn = 0
    for ty in range(H):
        for tx in range(W):
            if edge_cells[tx, ty] and veg and (tx * 3 + ty * 7) % 2 == 0:
                x, y = tx * TILE + 8 + rng.randint(-6, 6), ty * TILE + 12 + rng.randint(-4, 4)
                if road_dist(x, y) > 40 and not near_building(x, y, 36) and tree_ok(x, y, 14):
                    region = rng.choice(veg)
                    sc.node(f"SemakTepi{bn}", "Node2D", "Objects", position=v2(x, y))
                    sprite_node(f"Objects/SemakTepi{bn}", "res://assets/props/Vegetation.png", region)
                    bn += 1

    # ------------------------------------------------------------ musuh, peti, collectible
    old = open(BACKUP, encoding="utf-8").read()
    enemies = re.findall(r'\[node name="Musuh\d+"[^\]]*\]\nposition = [^\n]*\n(?:damage_scale = ([^\n]*)\n)?enemy_id = "([^"]*)"', old)
    segs = [(i_puz_r, i_pre), (i_pre, i_boss), (i_boss, i_exit)]
    solid_pts = placed_t

    def clear_spot(x, y):
        tx, ty = int(x // TILE), int(y // TILE)
        if not (0 <= tx < W and 0 <= ty < H) or not corridor[tx, ty] or water[tx, ty] or road_dist(x, y) < 22:
            return False
        if any(abs(x - px) < 32 and abs(y - py) < 24 for px, py in solid_pts):
            return False
        if any(abs(x - px) < 32 and 0 <= py - y <= 100 for px, py in solid_pts):      # tajuk pohon di selatan menutupi titik ini
            return False
        return not near_building(x, y, 30)

    def find_clear(x, y):
        """Titik bebas terdekat (spiral sampai 140 px) dari (x, y)."""
        if clear_spot(x, y):
            return (round(x), round(y))
        for r in range(12, 141, 12):
            for a in range(0, 360, 30):
                nx, ny = x + math.cos(math.radians(a)) * r, y + math.sin(math.radians(a)) * r
                if clear_spot(nx, ny):
                    return (round(nx), round(ny))
        return None

    for k, (ds, eid) in enumerate(enemies):
        seg = segs[0] if k < len(enemies) * 0.5 else segs[1]
        t = ((k % 5) + 0.6) / 5.4
        side = 1 if k % 2 == 0 else -1
        x, y = 0, 0
        for attempt in range(14):
            x, y = at(seg[0], seg[1], min(0.95, t + attempt * 0.012), side, rng.randint(40, 120))
            if clear_spot(x, y):
                break
        else:
            x, y = at(seg[0], seg[1], t)
        inst(f"Musuh{k + 1}", enemy_scene, (x, y), enemy_id=f'"{eid}"', **({"damage_scale": ds} if ds else {}))
    for i, e in enumerate([b[-1] for b in branches]):
        cpos = find_clear(e[0], e[1]) or (round(e[0]), round(e[1]))
        inst(f"Peti{i + 1}", chest_scene, cpos, roll_count="2")
        for nm, (ox, oy) in ((f"Herb{i * 3 + 1}", (26, 12)), (f"Herb{i * 3 + 2}", (-24, 16)), (f"Ore{i + 1}", (2, 30))):
            q = find_clear(cpos[0] + ox, cpos[1] + oy)
            if q:
                inst(nm, collect["Ore" if nm.startswith("Ore") else "Herb"], q)
    hn = 0
    for i in range(14):
        a_i, b_i = segs[i % 3]
        x, y = at(a_i, b_i, 0.1 + 0.8 * rng.random(), rng.choice((-1, 1)), rng.randint(60, 150))
        if clear_spot(x, y):
            if hn < 8:
                inst(f"Herb{10 + hn}", collect["Herb"], (x, y))
            elif hn < 12:
                inst(f"Koin{hn - 7}", collect["GoldCoin"], (x, y))
            hn += 1
    inst("Potion1", collect["Potion"], at(i_puz_r, i_pre, 0.8, -1, 70))

    # ------------------------------------------------------------ jembatan, marker, pemain, batas
    for r in rivers:
        y0, y1 = r["rows"][0] * TILE, (r["rows"][1] + 1) * TILE
        tex = sc.ext_res("Texture2D", "res://assets/props/bridge_wood.png")
        sc.node(f"Jembatan_{r['key']}", "Sprite2D", "Decor", position=v2(r["bx"], (y0 + y1) / 2), texture=f'ExtResource("{tex}")')
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    from_next = find_clear(P["exit"][0] + 44, P["exit"][1] + 4) or find_clear(P["exit"][0] - 44, P["exit"][1] + 4) or (int(P["exit"][0]), int(P["exit"][1]) + 40)
    sc.node("FromNext", "Marker2D", ".", position=v2(*from_next))   # titik muncul saat mundur dari chapter berikutnya
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Arman", "Marker2D", "NPCSpawns", position=v2(door_x + 38, door_y + 18), **{"metadata/npc_id": '"arman"'})
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
    # ---- uji keterhubungan: start -> exit harus tembus bila gerbang dibuka, dan terputus bila gerbang tertutup
    walk = (corridor & ~water) | bridge

    def reach(blocked_rows):
        from collections import deque
        sx, sy = int(start[0] // TILE), int(start[1] // TILE)
        seen = np.zeros_like(walk)
        seen[sx, sy] = True
        dq = deque([(sx, sy)])
        while dq:
            x, y = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and walk[nx, ny] and not seen[nx, ny] and ny not in blocked_rows:
                    seen[nx, ny] = True
                    dq.append((nx, ny))
        return seen

    ex, ey = int(P["exit"][0] // TILE), int(P["exit"][1] // TILE)
    pz = (int(P["puzzle"][0] // TILE), int(P["puzzle"][1] // TILE))
    bossp = (int(P["boss_arena"][0] // TILE), int(P["boss_arena"][1] // TILE))
    open_all = reach(set())
    closed_v = reach({gate_v_y // TILE})
    closed_a = reach({gate_a[1] // TILE})
    print("keterhubungan: exit terjangkau (gerbang terbuka) =", bool(open_all[ex, ey]),
          "| puzzle terkunci oleh gerbang desa =", not closed_v[pz],
          "| arena terkunci oleh gerbang arena =", not closed_a[bossp])
    out_b = [(n, (bx, by)) for bx, by, w, h in buildings for n in [0]
             if not all(corridor[int(px // TILE), int(py // TILE)] for px, py in ((bx - w / 2, by), (bx + w / 2, by), (bx - w / 2, by - h * 0.6), (bx + w / 2, by - h * 0.6)))]
    print("bangunan yang keluar dari lahan:", len(out_b), out_b[:4])
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and corridor[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Ch1_HutanIndeks.tscn:", tnum, "pohon,", len(enemies), "musuh, objek di luar koridor:", len(bad), bad[:5],
          "| koridor", int(corridor.sum()), "tile")
    return bad


if __name__ == "__main__":
    v2mod.make_bridge()
    build()
