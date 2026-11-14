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
D2 = (160, 85)                                       # pusat Desa 2 (timur, tercemar)
D3 = (43, 87)                                        # pusat Desa 3 (barat, porak-poranda)
D4 = (136, 22)                                       # pusat Desa 4 (utara, kubah segel) = titik_tile desa4
D4_RX, D4_RY = 150, 112                              # jari-jari kubah segel (px)
ARENA_CURSE = (640, 500)                             # ukuran tekstur tanah terkutuk arena (tools/make_cursed_ground.py)
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


def thin_cells(mask_cells, dist, seed=5):
    """Pilih titik (px, di tengah sel) dari sel True dengan jarak minimum `dist` (untuk menata sprite awan)."""
    r = random.Random(seed)
    cells = [(int(x), int(y)) for x, y in zip(*np.nonzero(mask_cells))]
    r.shuffle(cells)
    grid, out = {}, []
    for x, y in cells:
        px_, py_ = x * TILE + 8, y * TILE + 8
        gk = (int(px_ // dist), int(py_ // dist))
        if any(math.hypot(px_ - ox, py_ - oy) < dist for gx_ in (-1, 0, 1) for gy_ in (-1, 0, 1)
               for ox, oy in grid.get((gk[0] + gx_, gk[1] + gy_), ())):
            continue
        grid.setdefault(gk, []).append((px_, py_))
        out.append((px_, py_))
    return sorted(out)


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
    # ------------------------------------------------------------ SELURUH daratan bisa dijelajahi (tanpa dinding pohon)
    # batas hanya: (a) laut & sungai selatan (tile air + tepi pantai), (b) awan tebal ber-collision di perbatasan wilayah lain
    gate_v_y = 69 * TILE + 8                                  # pita awan 'gerbang desa' (baris 68-70), di atas Desa 2/3
    ga = route[route_i((P["bonfire_preboss"][0], ga_row * TILE + 8))]
    ga_col = int(ga[0] // TILE)
    gate_a = (int(ga_col * TILE + 8), ga_row * TILE + 8)
    # laut hanya di tempat yang BIRU pada docs/layout/*_layout.png; abu-abu = wilayah lain (daratan, tak bisa dimasuki)
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch1_HutanIndeks_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 36 and ty >= 8   # 8 baris atas tertutup judul gambar
    land = mask_d.copy()
    gray = ~sea_img & ~mask
    south = np.arange(H)[None, :] >= 95
    # jalan darat ke selatan (menuju Desa Algoria / wilayah sebelumnya) dari tepi selatan jembatan sampai tepi peta
    ey0, ex0 = int(P["entry"][1] // TILE), int(P["entry"][0] // TILE)
    rb = route[int(np.argmin(np.abs(route[:, 1] - (ey0 - 4) * TILE)))]
    cx0 = (ex0 + int(rb[0] // TILE)) // 2
    causeway = np.zeros_like(mask)
    causeway[cx0 - 3:cx0 + 4, ey0 - 2:H - 2] = True
    exit_south = (cx0 * TILE + 8, (H - 5) * TILE)
    land |= dilate(mask, 9) & gray & south                       # sungai selatan 9 tile (lebar, pembatas alami)
    land |= causeway
    ring = land & ~mask & gray                                   # 2 tile di luar mask yang berbatasan dengan wilayah lain
    ring_s = land & ~mask & gray & south & (dist_to(gx, gy, route) > 64) & ~causeway                                        # tepi selatan = SUNGAI (air + tepi pantai), bukan awan
    ring &= ~south
    exit_t = (int(P["exit"][0] // TILE), int(P["exit"][1] // TILE))
    plug = np.hypot(gx / TILE - exit_t[0], gy / TILE - exit_t[1]) <= 6.5
    plug &= land
    cloud_b = ring | plug                                        # awan perbatasan chapter berikutnya
    band_rows = {"desa": [gate_v_y // TILE + d for d in (-1, 0, 1)], "arena": [ga_row + d for d in (-1, 0, 1)]}
    bands = {}
    for key, rows in band_rows.items():
        b_ = np.zeros_like(mask)
        for r_ in rows:
            b_[:, r_] = land[:, r_] & ~cloud_b[:, r_]
        bands[key] = b_
    # gerbang arena = cincin awan tebal mengelilingi arena Golem (bukan pita lurus)
    bc = (P["boss_arena"][0] / TILE, P["boss_arena"][1] / TILE)
    dd = np.hypot(gx / TILE - bc[0], gy / TILE - bc[1])
    bands["arena"] = (dd >= 7.5) & (dd <= 9.2) & land & ~cloud_b
    # ---- Desa 2 (timur, tercemar) & Desa 3 (barat, porak-poranda): cincin kabut sampai Quest Awal selesai
    def ell(c, rx, ry):
        return np.hypot((gx - (c[0] * TILE + 8)) / (rx * TILE), (gy - (c[1] * TILE + 8)) / (ry * TILE))
    e2, e3 = ell(D2, 24, 20), ell(D3, 24, 20)
    ring2 = (e2 >= 0.93) & (e2 <= 1.07) & land & ~cloud_b
    ring3 = (e3 >= 0.93) & (e3 <= 1.07) & land & ~cloud_b
    # cincin menutup rapat sampai garis pantai (tidak ada celah di antara elips dan tepi pulau)
    ring3 |= land & (gx < D3[0] * TILE + 8 - 23.0 * TILE) & (np.abs(gy - (D3[1] * TILE + 8)) < 21.5 * TILE)
    ring2 |= land & (gx > D2[0] * TILE + 8 + 23.0 * TILE) & (np.abs(gy - (D2[1] * TILE + 8)) < 21.5 * TILE)
    no_trees = (e2 < 1.1) | (e3 < 1.1)
    # tanah terkutuk arena & kubah Desa 4: tanpa kelompok pohon
    ac = P["boss_arena"]
    no_trees |= np.hypot((gx - ac[0]) / (ARENA_CURSE[0] / 2 + 16), (gy - ac[1]) / (ARENA_CURSE[1] / 2 + 16)) < 1.0
    e4 = np.hypot((gx - (D4[0] * TILE + 8)) / (D4_RX + 70), (gy - (D4[1] * TILE + 8)) / (D4_RY + 60))
    no_trees |= e4 < 1.0
    pond = np.hypot((gx - (D2[0] * TILE + 8 + 13.5 * TILE)) / (4.4 * TILE), (gy - (D2[1] * TILE + 8 + 3.5 * TILE)) / (3.2 * TILE)) < 1.0
    nz = organic.smooth_noise(gx, gy, 6)
    tainted = (e2 + 0.10 * nz) < 0.88                               # tanah tercemar Desa 2
    scorched = (e3 + 0.10 * nz) < 0.80                              # tanah hangus Desa 3
    plaza_d = (np.hypot(gx - (D2[0] * TILE + 8), gy - (D2[1] * TILE + 8)) < 5.5 * TILE) |               (np.hypot(gx - (D3[0] * TILE + 8), gy - (D3[1] * TILE + 8)) < 5.5 * TILE)

    def winding(a, b, amp, seed, n=7):
        r_ = random.Random(seed)
        dxv, dyv = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dxv, dyv)
        nx_, ny_ = -dyv / ln, dxv / ln
        ph = r_.uniform(0, 6.28)
        pts_ = [a]
        for k in range(1, n):
            t_ = k / n
            off = amp * math.sin(t_ * math.pi * 1.7 + ph) * math.sin(math.pi * t_)
            pts_.append((a[0] + dxv * t_ + nx_ * off, a[1] + dyv * t_ + ny_ * off))
        pts_.append(b)
        return organic.polyline_samples(pts_, 12.0)

    road_e = winding(tp(27, 0), (D2[0] * TILE + 8, D2[1] * TILE + 8), 90, 41)
    road_w = winding(tp(-17, 0), (D3[0] * TILE + 8, D3[1] * TILE + 8), 80, 43)
    # jalan setapak Desa 4: dari jalur utama (sesudah arena) naik ke kaki kubah segel
    j4 = route[route_i((127 * TILE + 8, 38 * TILE + 8))]
    road_4 = winding((float(j4[0]), float(j4[1])), (D4[0] * TILE + 8, D4[1] * TILE + 8 + D4_RY + 20), 40, 47, n=5)
    roads_all = np.vstack([road_e, road_w, road_4])

    # ------------------------------------------------------------ sungai + jembatan di START (selatan), sejajar sumbu
    rivers = []
    key = "entry"
    ty0, ty1 = int(P[key][1] // TILE) - 5, int(P[key][1] // TILE) - 3
    mid = (ty0 + ty1) / 2 * TILE + 8
    ri = int(np.argmin(np.abs(route[:, 1] - mid)))
    bx = float(route[ri][0])
    txc = int(bx // TILE)
    lo = txc
    while lo > 0 and land[lo - 1, ty0:ty1 + 1].all():
        lo -= 1
    hi = txc
    while hi < W - 1 and land[hi + 1, ty0:ty1 + 1].all():
        hi += 1
    rivers.append({"rows": (ty0, ty1), "cols": (lo, hi), "bx": bx, "key": key})
    river = np.zeros_like(mask)
    bridge = np.zeros_like(mask)
    for r in rivers:
        river[r["cols"][0]:r["cols"][1] + 1, r["rows"][0]:r["rows"][1] + 1] = True
        for tx in range(r["cols"][0], r["cols"][1] + 1):
            if abs(tx * TILE + 8 - r["bx"]) <= 32:
                bridge[tx, r["rows"][0]:r["rows"][1] + 1] = True
    forest_cells = ~sea_img & ~land
    sea = sea_img & ~land
    river |= ring_s
    water = sea | river | pond
    # dataran yang boleh dihuni dekorasi/musuh/item: tidak termasuk awan perbatasan & pita gerbang quest
    corridor = land & ~cloud_b & ~bands["desa"] & ~bands["arena"] & ~ring2 & ~ring3

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
    is_dirt = (d_route <= 30 + 5 * organic.smooth_noise(gx, gy, 5)) | causeway
    is_dirt |= (dist_to(gx, gy, roads_all) <= 22 + 4 * organic.smooth_noise(gx, gy, 4)) | plaza_d
    for pt, rr in ((P["puzzle"], 52), (P["bonfire_preboss"], 40), (P["boss_arena"], 150), (P["exit"], 40), (P["entry"], 40)):
        is_dirt |= np.hypot(gx - pt[0], gy - pt[1]) <= rr
    ground, pathc, watc, rivc, brc, forest, pondc = [], [], [], [], [], [], []
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
                if pond[tx, ty]:
                    pondc.append(cell)
                elif sea[tx, ty]:
                    watc.append(cell)
                elif bridge[tx, ty]:
                    brc.append(cell)
                else:
                    rivc.append(cell)
            if forest_cells[tx, ty]:
                forest.append((tx, ty, 1, tx % 25, ty % 25))

    taintc, scorchc = [], []
    for tx in range(W):
        for ty in range(H):
            if (tainted[tx, ty] or scorched[tx, ty]) and land[tx, ty] and not water[tx, ty] and not ring2[tx, ty] and not ring3[tx, ty]:
                dd_ = grass[(tx * 3 + ty * 7) % 3] if tainted[tx, ty] else dirt[(tx * 3 + ty * 7) % 3]
                (taintc if tainted[tx, ty] else scorchc).append((tx, ty, 0, dd_[0], dd_[1]))

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
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    animal_script = sc.ext_res("Script", "res://scripts/world/Animal.gd")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")
    watcher_script = sc.ext_res("Script", "res://scripts/world/EventWatcher.gd")
    torch_script = sc.ext_res("Script", "res://scripts/puzzles/TorchSeal.gd")
    dome_script = sc.ext_res("Script", "res://scripts/world/SealDome.gd")
    altar_script = sc.ext_res("Script", "res://scripts/world/Altar.gd")
    tint_script = sc.ext_res("Script", "res://scripts/world/FlagTint.gd")

    sc.node("Ch1_HutanIndeks", "Node2D", script=f'ExtResource("{script}")', chapter="1", music_name='"ch1_hutan_indeks"',
            boss_music_name='"boss"', opening_story="true",
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")", map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Tercemar", "TileMapLayer", ".", tile_map_data=b64cells(taintc), tile_set=f'ExtResource("{ts_world}")',
            modulate="Color(0.74, 0.54, 0.9, 1)")
    sc.node("Hangus", "TileMapLayer", ".", tile_map_data=b64cells(scorchc), tile_set=f'ExtResource("{ts_world}")',
            modulate="Color(0.42, 0.38, 0.36, 1)")
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(pathc), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Forest", "TileMapLayer", ".", tile_map_data=b64cells(forest), tile_set=f'ExtResource("{ts_forest}")')
    sc.node("Water", "TileMapLayer", ".", tile_map_data=b64cells(watc), tile_set=f'ExtResource("{ts_water}")')
    sc.node("River", "TileMapLayer", ".", tile_map_data=b64cells(rivc), tile_set=f'ExtResource("{ts_water}")')
    sc.node("AirUngu", "TileMapLayer", ".", tile_map_data=b64cells(pondc), tile_set=f'ExtResource("{ts_water}")',
            modulate="Color(1.25, 0.45, 1.0, 1)")
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
    # Bonfire pra-boss di luar cincin awan arena: titik rute ~16 tile sebelum pusat arena
    _k = i_boss
    while _k > 0 and math.hypot(route[_k][0] - P["boss_arena"][0], route[_k][1] - P["boss_arena"][1]) < 16 * TILE:
        _k -= 1
    bf_pre = (int(route[_k][0]) + 40, int(route[_k][1]) + 8)
    bf3 = at(i_boss, i_exit, 0.62, 1, 56)
    cp1 = at(i_puz_r, i_pre, 0.55, 1, 48)
    cp2 = at(i_boss, i_exit, 0.30, -1, 52)
    # START: di tepi selatan jembatan (darat), bukan di atas jembatan/air
    start = (int(round(rivers[0]["bx"])), (rivers[0]["rows"][1] + 1) * TILE + 34)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf3)
    inst("Checkpoint1", checkpoint_scene, cp1)
    inst("Checkpoint2", checkpoint_scene, cp2)
    def cloud_barrier(name, cells_mask, mode, dist, text="", **props):
        """Awan ber-collision: node CloudBarrier + anak Block (TileMapLayer tak terlihat)."""
        pts = thin_cells(cells_mask, dist)
        arr = ", ".join(f"{x}, {y}" for x, y in pts)
        extra = {"locked_text": '"%s"' % text} if text else {}
        sc.node(name, "Node2D", ".", script=f'ExtResource("{cloud_script}")', mode=f'"{mode}"', chapter="1",
                cloud_points=f"PackedVector2Array({arr})", seed_value=str(rng.randint(1, 999)), **extra, **props)
        cells = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(cells_mask))]
        sc.node("Block", "TileMapLayer", name, tile_map_data=b64cells(cells), tile_set=f'ExtResource("{block_ts}")')
        return len(pts)

    n_cb = cloud_barrier("AwanPerbatasan", cloud_b, "chapter", 46)
    n_c2 = cloud_barrier("AwanDesa2", ring2, "stage", 40, "Kabut ungu pekat menghalangi.\nBantu Arman dulu.", required_stage="1",
                         tint="Color(0.82, 0.72, 0.95, 1)", scale_min="1.3", scale_max="1.9")
    n_c3 = cloud_barrier("AwanDesa3", ring3, "flag", 40, "Asap hitam menghalangi.\nLapor dulu kepada Arman.", required_stage="2",
                         required_flag='"ch1_lapor_desa2"',
                         tint="Color(0.62, 0.6, 0.62, 1)", scale_min="1.3", scale_max="1.9")
    n_cd = cloud_barrier("AwanGerbangDesa", bands["desa"], "flag", 40, "Kabut tebal menghalangi.\nArman belum menyusun petunjuk.",
                         required_stage="2", required_flag='"ch1_petunjuk_disusun"')
    n_ca = cloud_barrier("AwanGerbangArena", bands["arena"], "stage", 24, "Segel kabut arena.\nNyalakan obor segel dulu.", required_stage="2",
                         scale_min="1.3", scale_max="1.7")
    inst("PulangBarat", exit_scene, exit_south, to_chapter="0", sign_text='"Kembali ke Desa Algoria"')
    inst("PulangTimur", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="2", sign_text='"Ke Tambang Tumpuk"')
    # perkemahan kecil di Bonfire pra-boss & pasca-boss (prefab)
    for (bx, by), kit in ((bf_pre, (("Dapur_PanciGantung", (-58, 14)), ("Peti_Kayu_A", (52, 10)), ("Barel_Air", (64, 24)))),
                          (bf3, (("Dapur_Panggangan_Kecil", (-62, 14)), ("Barel_Besar", (56, 8)), ("Peti_Kayu_B", (70, 22))))):
        for nm, (ox, oy) in kit:
            prefab(f"Kemah_{nm}_{bx}", nm, (bx + ox, by + oy))

    # ------------------------------------------------------------ NPC
    door_x, door_y = tp(-11.5, -3.5)
    npc_positions = [("Arman", (door_x + 38, door_y + 18)), ("Penjaga", tp(17.0, 6.0)), ("Penebang", tp(22.0, -1.6)),
                     ("Sari", tp(-8.8, -13.2)), ("Pedagang", tp(8.8, 6.4)), ("PedagangAkhir", (bf3[0] + 52, bf3[1] + 18))]
    inst("Arman", npc_scene, (door_x + 38, door_y + 18), npc_id='"arman"')
    inst("Penjaga", npc_scene, tp(17.0, 6.0), npc_id='"penjaga"', dialog_id='"ch1_penjaga"', villager_chapter="1")
    inst("Penebang", npc_scene, tp(22.0, -1.6), npc_id='"penebang"', dialog_id='"ch1_penebang"', villager_chapter="1")
    inst("Sari", npc_scene, tp(-8.8, -13.2), npc_id='"sari"', dialog_id='"ch1_sari"', villager_chapter="1")
    inst("Pedagang", npc_scene, tp(8.8, 6.4), npc_id='"pedagang"', opens_shop="true")
    inst("PedagangAkhir", npc_scene, (bf3[0] + 52, bf3[1] + 18), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuArman", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_RumahArman.tscn"', hint_text='"E: Masuk rumah Arman"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuArman", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    # ------------------------------------------------------------ DESA 2 (tercemar) & DESA 3 (porak-poranda)
    def d2(dx, dy):
        return (round(D2[0] * TILE + 8 + dx * TILE), round(D2[1] * TILE + 8 + dy * TILE))

    def d3(dx, dy):
        return (round(D3[0] * TILE + 8 + dx * TILE), round(D3[1] * TILE + 8 + dy * TILE))

    PURPLE = "Color(0.8, 0.6, 1, 1)"
    prefab("D2Sumur", "Sumur", d2(0, 0), modulate=PURPLE)
    for nm, pref, (dx, dy) in (("D2Rumah1", "Rumah_Papan", (-9.5, -4.5)), ("D2Rumah2", "Rumah_Kayu", (8.5, -4.5)),
                               ("D2Rumah3", "Rumah_Krem", (-9.5, 10.0)), ("D2Lumbung", "Lumbung", (7.5, 10.2))):
        prefab(nm, pref, d2(dx, dy), modulate="Color(0.85, 0.8, 0.9, 1)")
    prefab("D2Barel", "Barel_Air", d2(-4.0, -6.0), modulate=PURPLE)
    prefab("D2Peti", "Peti_Kayu_A", d2(4.2, -5.5))
    prefab("D2Guci", "Guci", d2(-3.8, 6.0), modulate=PURPLE)
    prefab("D2PapanMasuk", "Papan_Kanan", d2(-15.8, 2.2), solid=False)
    mill_tex = sc.ext_res("Texture2D", "res://assets/ninja/animated/WaterMill/Watermill_A_34x36.png")
    sc.node("D2Kincir", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{mill_tex}")',
            position=v2(*d2(13.5, -0.9)), frame_w="34", frame_h="36", fps="4.0", random_phase="false", modulate="Color(0.85, 0.75, 0.95, 1)")
    buildings.append((d2(13.5, -0.9)[0], d2(13.5, -0.9)[1], 34, 36))
    inst("BonfireDesa2", bonfire_scene, d2(-2.5, 7.8))
    inst("BenderaDesa2", checkpoint_scene, d2(-14.5, 5.2))
    inst("PetiDesa2", chest_scene, d2(1.5, 13.0), roll_count="2")
    # puzzle rak lumbung (Quest Tengah langkah 1): memurnikan sumur Desa 2
    inst("StasiunRak", station_scene, d2(7.5, 12.8), puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="1",
         station_label='"Rak Lumbung"', complete_flag='"ch1_sumur_murni"', required_step='"ch1_tengah:desa2"')
    npc_positions.append(("Rak", d2(7.5, 12.8)))
    tint_targets = ", ".join(f'"{n}"' for n in ("Tercemar", "AirUngu", "D2Sumur", "D2Barel", "D2Guci", "D2Kincir",
                                                  "D2Rumah1", "D2Rumah2", "D2Rumah3", "D2Lumbung"))
    sc.node("Desa2Pulih", "Node", ".", script=f'ExtResource("{tint_script}")', flag='"ch1_sumur_murni"',
            target_names=f"PackedStringArray({tint_targets})")

    prefab("D3Ruina1", "Ruina_1", d3(-9.5, -5.5))
    prefab("D3Ruina2", "Ruina_3", d3(9.5, -6.5))
    prefab("D3Ruina3", "Ruina_4", d3(-11.5, 7.0))
    prefab("D3Ruina4", "Ruina_5", d3(12.0, 7.5))
    prefab("D3Tenda1", "Tenda_1", d3(-5.0, 11.2))
    prefab("D3Tenda2", "Tenda_3", d3(5.2, 11.6))
    prefab("D3Tenda3", "Tenda_2", d3(0.4, 14.0))
    for nm, pref, (dx, dy) in (("D3PuingA", "Puing_Batu", (-1.5, -9.0)), ("D3PuingB", "Puing_Pilar", (3.5, -8.4)),
                               ("D3PuingC", "Puing_Kayu", (-14.0, 0.5)), ("D3Tronk", "Tronk_Kayu", (14.5, -1.8)),
                               ("D3Kotak", "Kotak_Rusak", (6.8, 3.2)), ("D3Peti", "Peti_Kayu_B", (-7.0, 13.0))):
        prefab(nm, pref, d3(dx, dy), solid=False)
    flam_tex = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    smoke_tex = sc.ext_res("Texture2D", "res://assets/ninja/fx/Smoke/Smoke/SpriteSheet.png")
    for i, (dx, dy) in enumerate(((-7.0, -3.2), (7.4, -3.4), (-12.5, 3.2), (14.2, 3.4), (0.5, -7.4))):
        fp = d3(dx, dy)
        sc.node(f"D3Api{i}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_tex}")',
                position=v2(*fp), frame_w="20", frame_h="30", fps="9.0")
        sc.node(f"D3Asap{i}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{smoke_tex}")',
                position=v2(fp[0], fp[1] - 22), frame_w="32", frame_h="32", fps="5.0", z_index="6", modulate="Color(0.7, 0.7, 0.7, 0.8)")
    inst("BonfireDesa3", bonfire_scene, d3(0.2, 9.0))
    inst("BenderaDesa3", checkpoint_scene, d3(14.5, 6.0))
    inst("PetiDesa3", chest_scene, d3(-15.0, -7.5), roll_count="2")
    prefab("D3PapanMasuk", "Papan_Kiri", d3(16.4, 0.4), solid=False)
    surv = [("Rani", d3(-3.0, 8.4)), ("Darso", d3(3.4, 8.8)), ("Tami", d3(-5.5, -1.6))]
    for nm, pos in surv:
        inst(nm, npc_scene, pos, npc_id=f'"{nm.lower()}"', dialog_id=f'"ch1_{nm.lower()}"', villager_chapter="101")
        npc_positions.append((nm, pos))
    npc_positions += [("Bf2", d2(-2.5, 7.8)), ("Bf3", d3(0.2, 9.0)), ("Fl2", d2(-14.5, 5.2)), ("Fl3", d3(14.5, 6.0))]

    # ------------------------------------------------------------ ARENA GOLEM: tanah terkutuk, obor segel, bendera, Skeleton
    def land_ok_px(x_, y_):
        tx2_, ty2_ = int(x_ // TILE), int(y_ // TILE)
        return 0 <= tx2_ < W and 0 <= ty2_ < H and corridor[tx2_, ty2_] and not water[tx2_, ty2_]

    def before_arena(tiles, side=0, off=0):
        """Titik rute `tiles` tile sebelum pusat arena (diukur lurus), digeser ke samping `side*off` px."""
        k = i_boss
        while k > 0 and math.hypot(route[k][0] - P["boss_arena"][0], route[k][1] - P["boss_arena"][1]) < tiles * TILE:
            k -= 1
        return at(k, k, 0, side, off)

    ax, ay = int(P["boss_arena"][0]), int(P["boss_arena"][1])
    curse_tex = sc.ext_res("Texture2D", "res://assets/props/generated/cursed_arena.png")
    sc.node("TanahKutukArena", "Sprite2D", "Decor", texture=f'ExtResource("{curse_tex}")', position=v2(ax, ay))
    torch_c = before_arena(14.2, -1, 130)   # di sisi jalan, terpisah dari perkemahan Bonfire pra-boss
    sc.node("OborSegel", "Node2D", "Objects", script=f'ExtResource("{torch_script}")', position=v2(*torch_c))
    for k_ in range(5):
        buildings.append((torch_c[0] - 72 + 36 * k_, torch_c[1], 12, 20))
    cp_curse = before_arena(18.0, -1, 48)    # di luar pita kabut jalan utara (baris 68-70)
    cp_arena = before_arena(13.5, -1, 70)
    inst("BenderaKutuk", checkpoint_scene, cp_curse)
    inst("BenderaArena", checkpoint_scene, cp_arena)
    npc_positions += [("Obor", torch_c), ("FlKutuk", cp_curse), ("FlArena", cp_arena)]
    # dekorasi kutukan di sekitar arena (tidak memudar; arena tetap bekas pertempuran)
    curse_deco = ["Kutuk_TanamanMata_1", "Kutuk_TanamanMata_2", "Kutuk_BanyakMata", "Kutuk_BatuMata", "Kutuk_Batu_1",
                  "Kutuk_Batu_2", "Kutuk_Tentakel", "Kutuk_Tulang_1", "Kutuk_Tulang_2", "Kutuk_Tulang_3"]
    arena_deco = []
    for k_ in range(26):
        ang = rng.random() * math.tau
        rr = rng.uniform(10.5, 18.0)
        x_ = round(ax + math.cos(ang) * rr * TILE * 1.0)
        y_ = round(ay + math.sin(ang) * rr * TILE * 0.75)
        tx_, ty_ = int(x_ // TILE), int(y_ // TILE)
        pref = curse_deco[k_ % len(curse_deco)]
        pw_, ph_ = PREFAB_SIZE.get(pref, (16, 16))
        if not all(land_ok_px(x_ + ox_, y_ + oy_) for ox_, oy_ in ((0, 0), (-pw_ / 2, 0), (pw_ / 2, 0), (-pw_ / 2, -ph_ * 0.6), (pw_ / 2, -ph_ * 0.6))):
            continue
        if float(d_route[tx_, ty_]) < 40 or any(math.hypot(x_ - qx, y_ - qy) < 46 for qx, qy in arena_deco):
            continue
        if any(math.hypot(x_ - vx, y_ - vy) < 70 for vx, vy in (torch_c, cp_curse, cp_arena, bf_pre)):
            continue
        prefab(f"KutukArena{k_}", pref, (x_, y_), solid=not pref.startswith("Kutuk_Tulang"))
        arena_deco.append((x_, y_))

    # ------------------------------------------------------------ DESA 4 (utara): kubah segel, reruntuhan, altar, tetua
    def d4(dx, dy):
        return (round(D4[0] * TILE + 8 + dx * TILE), round(D4[1] * TILE + 8 + dy * TILE))

    d4tex = sc.ext_res("Texture2D", "res://assets/props/generated/cursed_desa4.png")
    sc.node("D4KutukTanah", "Sprite2D", "Decor", texture=f'ExtResource("{d4tex}")', position=v2(*d4(0, 0)))
    prefab("D4Altar", "Altar_Segel", d4(0, 0.5))
    sc.node("AltarSegel", "Area2D", "Objects", script=f'ExtResource("{altar_script}")', position=v2(*d4(0, 0.5)))
    for nm, pref, (dx, dy) in (("D4Ruina1", "Ruina_2", (-6.0, -3.2)), ("D4Ruina2", "Ruina_1", (5.6, -3.6)),
                               ("D4Ruina3", "Ruina_3", (-6.4, 4.2)), ("D4Pilar1", "Pilar_Lumut", (-2.4, -2.0)),
                               ("D4Pilar2", "Pilar_Lumut", (2.4, -2.0)), ("D4Pilar3", "Pilar_Lumut", (6.0, 3.6))):
        prefab(nm, pref, d4(dx, dy))
    for k_, (pref, (dx, dy)) in enumerate((("Kutuk_Reruntuhan_1", (3.6, 4.6)), ("Kutuk_Reruntuhan_2", (-3.4, 5.0)),
                                           ("Kutuk_TanamanMata_1", (-7.6, 0.6)), ("Kutuk_BanyakMata", (7.4, 0.2)),
                                           ("Kutuk_Tulang_1", (-1.8, 3.0)), ("Kutuk_Tulang_3", (2.0, 2.8)),
                                           ("Kutuk_BatuMata", (0.4, -4.6)), ("Kutuk_Tentakel", (-4.6, -0.6)))):
        prefab(f"D4Kutuk{k_}", pref, d4(dx, dy), solid=False)
    inst("Tetua", npc_scene, d4(2.6, 1.6), npc_id='"tetua"', hidden_until_flag='"ch1_segel_pudar"')
    sc.node("KubahSegel", "Node2D", ".", script=f'ExtResource("{dome_script}")', position=v2(*d4(0, 0)),
            radius_x=str(float(D4_RX)), radius_y=str(float(D4_RY)))
    prefab("PapanDesa4", "Papan_Kanan", (round(j4[0]) + 30, round(j4[1]) - 18), solid=False)
    npc_positions += [("Tetua", d4(2.6, 1.6)), ("Altar", d4(0, 0.5))]
    extra_keypts = [torch_c, cp_curse, cp_arena, d4(0, 0)]

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

    keypts = list(P.values()) + [cp1, cp2, bf3, gate_a, (CX, gate_v_y), start, bf1] + extra_keypts
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

    # kelompok pohon DEKORASI: celah lebar antar-kelompok, collision hanya di batang (10x6 px) -> tidak pernah jadi dinding
    clusters = []
    for _try in range(6000):
        if len(clusters) >= 85:
            break
        x, y = rng.randint(60, PX_W - 60), rng.randint(80, PX_H - 60)
        tx, ty = int(x // TILE), int(y // TILE)
        if not corridor[tx, ty] or water[tx, ty] or village_rect[tx, ty] or no_trees[tx, ty] or road_dist(x, y) < 70 or near_building(x, y, 5 * TILE):
            continue
        if any(math.hypot(x - cx, y - cy) < 170 for cx, cy in clusters):
            continue
        clusters.append((x, y))
        for _k in range(rng.randint(3, 6)):
            ang, rad = rng.random() * math.tau, rng.random() * 52
            px_, py_ = round(x + math.cos(ang) * rad), round(y + math.sin(ang) * rad * 0.7)
            tx2, ty2 = int(px_ // TILE), int(py_ // TILE)
            if 0 <= tx2 < W and 0 <= ty2 < H and corridor[tx2, ty2] and not water[tx2, ty2] and not village_rect[tx2, ty2] and not no_trees[tx2, ty2]                     and road_dist(px_, py_) > 50 and tree_ok(px_, py_, 34):
                placed_t.append((px_, py_))
                tree_at(px_, py_, True)
    near_forest = dilate(corridor, 4) & forest_cells
    for ty in range(H):
        for tx in range(W):
            if near_forest[tx, ty] and (tx * 5 + ty * 3) % 4 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if tree_ok(x, y, 20):
                    placed_t.append((x, y))
                    tree_at(x, y, False)
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

    # ------------------------------------------------------------ Dusun Larik: lapak pasar, spanduk, papan penunjuk, hewan, bunga, bendera, Goblin
    prefab("LapakSayur", "Lapak_Sayur", tp(-8.8, 4.2))
    prefab("LapakKain", "Lapak_Kain", tp(8.8, 4.2))
    for i, (dx, dy, k) in enumerate(((-5.6, -6.6, 1), (5.6, -6.6, 2), (-5.6, 5.4, 3), (5.6, 5.4, 1))):
        prefab(f"Spanduk{i}", f"Spanduk_{k}", tp(dx, dy), solid=False)
    prefab("PapanBarat", "Papan_Kiri", tp(-17.4, -2.7), solid=False)
    prefab("PapanTimur", "Papan_Kanan", tp(27.4, -2.7), solid=False)
    prefab("PapanUtara", "Papan_Tiang", tp(2.8, -16.4), solid=False)
    sp = at(i_puz_r, i_pre, 0.12, 1, 36)
    prefab("PapanRute1", "Papan_Kanan", sp, solid=False)

    def land_ok(pt):
        tx_, ty_ = int(pt[0] // TILE), int(pt[1] // TILE)
        return 0 <= tx_ < W and 0 <= ty_ < H and corridor[tx_, ty_] and not water[tx_, ty_]

    animals = [("Chicken/SpriteSheetWhite", tp(-9.6, 15.8)), ("Chicken/SpriteSheetBrown", tp(-14.0, 15.6)),
               ("Chicken/SpriteSheetWhite", tp(-3.5, -9.8)), ("Chicken/SpriteSheetBrown", tp(14.0, -0.2)),
               ("Cow/SpriteSheetWhite", tp(17.5, 16.2)), ("Cow/SpriteSheetWhite", tp(26.0, 16.4)),
               ("Pig/SpriteSheetPink", tp(13.5, 17.0)), ("Pig/SpriteSheetBlack", tp(-16.0, 5.0)),
               ("Dog/SpriteSheet", tp(3.8, -9.6)), ("Cat/SpriteSheet", tp(-14.8, -1.6))]
    na = 0
    for sheet_, pos in animals:
        if land_ok(pos):
            tex = sc.ext_res("Texture2D", f"res://assets/ninja/animals/{sheet_}.png")
            bscale = 1.0 if sheet_.startswith(("Chicken", "Cat")) else (1.2 if sheet_.startswith("Dog") else 1.5)
            sc.node(f"Hewan{na}", "Node2D", "Objects", script=f'ExtResource("{animal_script}")', sheet=f'ExtResource("{tex}")',
                    position=v2(*pos), body_scale=str(bscale), wander_radius="55.0")
            na += 1
    plant_tex = sc.ext_res("Texture2D", "res://assets/ninja/animated/Plant/SpriteSheet16x16.png")
    nb = 0
    for _try in range(900):
        if nb >= 110:
            break
        x, y = rng.randint(40, PX_W - 40), rng.randint(60, PX_H - 60)
        tx, ty = int(x // TILE), int(y // TILE)
        in_vil = bool(village_rect[tx, ty]) and not in_village_stone[tx, ty]
        if not land_ok((x, y)) or covers_point(x, y) or near_building(x, y, 34):
            continue
        if not (in_vil or 46 < road_dist(x, y) < 130) or any(abs(x - px_) < 22 and abs(y - py_) < 14 for px_, py_ in placed_t):
            continue
        sc.node(f"Bunga{nb}", "Node2D", "Decor", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{plant_tex}")',
                position=v2(x, y), fps="3.0")
        nb += 1
    for nm, (dx, dy) in (("BenderaMasuk", (3.8, 15.4)), ("BenderaBarat", (-19.6, 2.8)), ("BenderaTimur", (28.6, 2.8))):
        inst(nm, checkpoint_scene, tp(dx, dy))
    for i, (dx, dy) in enumerate(((-5, 17.6), (5.2, 18.4), (-2.5, 19.6), (3.0, 16.8))):
        inst(f"GoblinEvent{i + 1}", enemy_scene, tp(dx, dy), enemy_id='"orc"', damage_scale="0.6")
    sc.node("SeranganGoblin", "Node2D", ".", script=f'ExtResource("{watcher_script}")', position=v2(*tp(0, 17.5)))
    for k_, (ck, (dx, dy)) in enumerate((("barang", (19.6, 15.4)), ("catatan", (-14.2, -11.0)), ("jejak", (31.6, -4.6))), start=1):
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*tp(dx, dy)),
                flag=f'"ch1_petunjuk_{k_}"', dialog_id=f'"ch1_petunjuk_{k_}"', required_step='"ch1_awal:petunjuk"', clue_kind=f'"{ck}"')
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")')

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
        return not near_building(x, y, 30) and not village_rect[tx, ty]

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

    # ---- musuh jalur & dalam Desa 2 / Desa 3 (naik bertahap: Goblin/Slime lemah -> Orc Warrior/Shaman sedang-kuat)
    def spot_near(x, y, avoid_village1=True):
        pt = find_clear(x, y)
        if pt is None:
            return None
        if avoid_village1 and village_rect[int(pt[0] // TILE), int(pt[1] // TILE)]:
            return None
        return pt

    def along(road, t, side, dist):
        i_ = min(len(road) - 2, max(1, int(len(road) * t)))
        a_, b_ = road[i_ - 1], road[i_ + 1]
        th = math.atan2(b_[1] - a_[1], b_[0] - a_[0]) + math.pi / 2
        return (road[i_][0] + math.cos(th) * side * dist, road[i_][1] + math.sin(th) * side * dist)

    def mob(name, eid, pt, **props):
        q = spot_near(pt[0], pt[1])
        if q:
            inst(name, enemy_scene, q, enemy_id=f'"{eid}"', **props)

    n_ = 0
    for t, side, eid in ((0.18, 1, "slime"), (0.30, -1, "mushroom"), (0.42, 1, "slime"), (0.52, -1, "slime"), (0.62, 1, "mushroom")):
        n_ += 1
        mob(f"JalurT{n_}", eid, along(road_e, t, side, rng.randint(36, 70)))
    n_ = 0
    for t, side, eid in ((0.15, 1, "orc"), (0.28, -1, "orc"), (0.40, 1, "orc_rogue"), (0.52, -1, "orc"), (0.64, 1, "orc_rogue")):
        n_ += 1
        mob(f"JalurB{n_}", eid, along(road_w, t, side, rng.randint(36, 70)))
    for k, (dx, dy, eid) in enumerate(((-7, -1, "slime2"), (6, 2, "slime2"), (-1, -8, "slime2"), (3, 9, "slime2"),
                                       (-8, 5, "mushroom2"), (11, -7, "mushroom2"), (-4, 12, "mushroom2"))):
        mob(f"D2Musuh{k + 1}", eid, d2(dx, dy))
    for k, (dx, dy, eid) in enumerate(((-6, -1, "orc_warrior"), (5, 0, "orc_warrior"), (2, -9, "orc_warrior"),
                                       (-10, 2, "orc_shaman"), (9, 3, "orc_shaman"))):
        mob(f"D3Musuh{k + 1}", eid, d3(dx, dy))
    # tanah terkutuk sekitar arena: Skeleton (kuat), di luar cincin awan arena dan jauh dari obor/bendera
    for k, (ang, rr, eid) in enumerate(((200, 13, "skeleton"), (240, 15, "skeleton_warrior"), (300, 12.5, "skeleton_rogue"),
                                        (20, 14, "skeleton"), (60, 13.5, "skeleton_mage"), (120, 15, "skeleton_warrior"),
                                        (160, 12, "skeleton_rogue"))):
        x_ = ax + math.cos(math.radians(ang)) * rr * TILE
        y_ = ay + math.sin(math.radians(ang)) * rr * TILE * 0.75
        if all(math.hypot(x_ - vx, y_ - vy) > 90 for vx, vy in (torch_c, cp_curse, cp_arena, bf_pre)):
            mob(f"Kerangka{k + 1}", eid, (x_, y_))

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
    walk = (land & ~water) | bridge

    def reach(blocked_rows, extra=None):
        from collections import deque
        sx, sy = int(start[0] // TILE), int(start[1] // TILE)
        seen = np.zeros_like(walk)
        seen[sx, sy] = True
        dq = deque([(sx, sy)])
        while dq:
            x, y = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and walk[nx, ny] and not seen[nx, ny] and ny not in blocked_rows and (extra is None or not extra[nx, ny]):
                    seen[nx, ny] = True
                    dq.append((nx, ny))
        return seen

    ex, ey = int(P["exit"][0] // TILE), int(P["exit"][1] // TILE)
    pz = (int(P["puzzle"][0] // TILE), int(P["puzzle"][1] // TILE))
    bossp = (int(P["boss_arena"][0] // TILE), int(P["boss_arena"][1] // TILE))
    open_all = reach(set())
    closed_v = reach({gate_v_y // TILE})
    closed_a = reach(set(), bands["arena"])
    d2t = (D2[0], D2[1])
    d3t = (D3[0], D3[1])
    r_closed = reach(set(), ring2 | ring3 | cloud_b)
    print("Desa 2/3: terjangkau saat terbuka =", bool(open_all[d2t]), bool(open_all[d3t]), "| terkunci selama kabut =", not r_closed[d2t], not r_closed[d3t])
    closed_c = reach(set(), cloud_b)
    print("awan perbatasan: exit terkunci selama awan ada =", not closed_c[ex, ey], "| exit terjangkau setelah awan hilang =", bool(open_all[ex, ey]))
    print("keterhubungan: exit terjangkau (gerbang terbuka) =", bool(open_all[ex, ey]),
          "| arena boss terkunci oleh gerbang desa =", not closed_v[bossp],
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
