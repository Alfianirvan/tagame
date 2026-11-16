"""Generator Ch4_GuaRantai.tscn v2: bentuk wilayah dari docs/layout/region_layout.json + DESA SIMPUL (danau beku berpulau).

Jalankan dari folder proyek (setelah make_prefabs.py, make_villagers.py, gen_glacier_tileset.py, gen_interior.py):
    python tools/gen_ch4_v2.py
Tahap 1 (bagian ini): peta 165x128 tile, batas gletser, Desa Simpul + pinggiran + 3 petunjuk, gerbang badai salju.
  - Lantai: salju; jalan = salju padat bertepi (autotile sudut / marching squares, tools/gen_glacier_tileset.py).
  - Batas: laut beku di barat (biru pada *_layout.png), dataran tinggi bertebing salju di luar mask (abu-abu = wilayah lain),
    awan perbatasan hanya di titik keluar ke Pohon Dunia (hilang setelah Chapter 4 selesai).
  - KANTONG DESA di tenggara dipagari PUNGGUNG ES (R1 utara, R2 barat); celah di barat laut = gerbang badai salju (quest_stage 1).
Blueprint Desa Simpul (tema Linked List): DANAU BEKU di tengah kantong dengan 3 PULAU yang dirantai JEMBATAN papan:
  tepi masuk -> Pulau 1 (Gilang) -> Pulau 2 (rumah Megas = interior, alun-alun, Bonfire, Pedagang) -> Pulau 3 -> tepi utara -> gerbang.
  Tepi danau: rumah warga, pondok pencari kristal (timur laut), gua kristal (barat daya), tepi danau tenggara.
Tahap 2 (rute zig-zag melintasi gletser, punggung es N1/N2/N3 di dalam wilayah): gerbang desa -> LERENG SELATAN ke barat ->
  CELAH BARAT (dekat laut beku) -> LEMBAH TENGAH ke timur -> CELAH TIMUR -> DATARAN UTARA (stasiun batu portal = Quest Tengah) ->
  DINDING RANTAI ES di celah N3 (StageBlocker, hilang di quest_stage 2) -> Bonfire pra-boss -> ARENA LANTAI ES Ksatria Rantai -> jembatan es
  (exit). Jalan pintas arena -> desa = 2 RUNTUHAN ES di celah N2 & N1 (StageBlocker mode crystal).
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ch1_v2 as v2mod  # noqa: E402  (bantuan numpy)
import organic  # noqa: E402
from gen_canyon_tileset import CORNER_TILES  # noqa: E402
from gen_glacier_tileset import PATH, PATH_DETAIL, PLANK, SNOW, WATER_CORNER  # noqa: E402
from gen_village import ROOT, TILE, Scene, v2  # noqa: E402

dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx
LAYOUT = json.load(open(os.path.join(ROOT, "docs/layout/region_layout.json"), encoding="utf-8"))["Ch4_GuaRantai"]
W, H = LAYOUT["ukuran_tile"]            # 165 x 128
PX_W, PX_H = LAYOUT["ukuran_px"]        # 2640 x 2048
DOOR_DX = json.load(open(os.path.join(ROOT, "assets/props/buildings/variants/_pintu.json"), encoding="utf-8"))
# punggung es (dataran tinggi di DALAM wilayah, tile): (polyline, setengah lebar). Celah di antara R1 & R2 = gerbang desa.
RIDGES = [([(147, 66), (128, 67), (110, 68)], 3.2),                              # R1: dinding utara kantong desa
          ([(101, 73), (97, 82), (96, 96), (97, 110), (99, 125)], 3.2),          # R2: dinding barat kantong desa
          ([(148, 59), (124, 60), (106, 60.5)], 3.2),                            # N1 timur | celah runtuhan es (jalan pintas)
          ([(94, 60.5), (70, 60.5), (40, 60)], 3.2),                             # N1 barat (CELAH BARAT di antara ujungnya & laut)
          ([(16, 44), (40, 45), (75, 46)], 3.2),                                 # N2 barat | celah runtuhan es (jalan pintas)
          ([(86, 46), (110, 46), (128, 46)], 3.2),                               # N2 timur (CELAH TIMUR di ujung timurnya)
          ([(101, 44), (100.5, 40.5)], 3.0),                                     # N3 bawah | celah = DINDING RANTAI ES
          ([(98.5, 28.5), (97, 16), (96, 1)], 3.0)]                              # N3 atas
GATE_C = (105.8, 70.4)                   # pusat celah gerbang (badai salju)
PUZZLE_T = (116, 34)                     # stasiun batu portal (puzzle layout (89,52) dipindah ke dataran utara)
PREBOSS_T = (86, 36)
EXIT_T = (38, 4)                         # celah gunung barat laut = jembatan es ke Pohon Dunia (exit layout (67,19) dipindah)
ARENA_ICE = (10.5, 7.5)                  # jari-jari lantai es arena (tile)
GAPS = {"n1": (98, 102, 56, 65), "n2": (79, 82, 41, 51), "n3": (92, 105, 32, 37)}   # celah yang selalu terbuka (lalu ditutup penghalang)
LAKE_C, LAKE_R = (121, 93), (18, 15)     # danau beku Desa Simpul (pusat, jari-jari tile)
ISLANDS = {"Pulau1": ((130, 100), 5.0), "Pulau2": ((125, 87), 7.0), "Pulau3": ((110, 90), 5.0)}
SHORE_N = (110, 79.5)                    # ujung jembatan Pulau 3 di tepi utara danau
SHORE_E = (138.5, 100)                   # ujung jembatan Pulau 1 di tepi timur (dekat pintu masuk)
DIRS8 = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PREFAB_SIZE = {}


def at(x, y):
    """Titik (px) pada tile absolut (x, y), pecahan boleh."""
    return (round(x * TILE + 8), round(y * TILE + 8))


def thin_cells(mask_cells, dist, seed=5):
    r = random.Random(seed)
    cells = [(int(x), int(y)) for x, y in zip(*np.nonzero(mask_cells))]
    r.shuffle(cells)
    out = []
    for x, y in cells:
        px_, py_ = x * TILE + 8, y * TILE + 8
        if all(math.hypot(px_ - ox, py_ - oy) >= dist for ox, oy in out):
            out.append((px_, py_))
    return sorted(out)


def winding(a, b, amp, seed, n=7):
    r_ = random.Random(seed)
    dxv, dyv = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dxv, dyv) or 1.0
    nx_, ny_ = -dyv / ln, dxv / ln
    ph = r_.uniform(0, 6.28)
    pts_ = [a]
    for k in range(1, n):
        t_ = k / n
        off = amp * math.sin(t_ * math.pi * 1.7 + ph) * math.sin(math.pi * t_)
        pts_.append((a[0] + dxv * t_ + nx_ * off, a[1] + dyv * t_ + ny_ * off))
    pts_.append(b)
    return organic.polyline_samples(pts_, 12.0)


def build():
    for e in json.load(open(os.path.join(ROOT, "scenes/prefabs/_prefabs.json"), encoding="utf-8")):
        PREFAB_SIZE[e["name"]] = (e["w"], e["h"])
    rng = random.Random(4004)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    P.update(puzzle=tpx(PUZZLE_T), bonfire_preboss=tpx(PREBOSS_T), exit=tpx(EXIT_T))
    orig = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)
    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]
    I1, I2, I3 = (ISLANDS[k][0] for k in ("Pulau1", "Pulau2", "Pulau3"))

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute: entry -> jembatan -> Pulau 1 -> Pulau 2 (alun-alun) ->
    # Pulau 3 -> tepi utara -> gerbang badai salju -> jalan layout (puzzle, Bonfire pra-boss, arena) -> exit
    seg_vil = organic.polyline_samples([P["entry"], tpx(SHORE_E), tpx(I1), tpx((125, 91.5)), tpx(I3), tpx((110, 83)), tpx(SHORE_N),
                                        tpx((108, 75)), tpx(GATE_C), tpx((101, 65))], 12.0)
    seg_s = np.vstack([winding(tpx((101, 65)), tpx((72, 69)), 22, 71, n=4), winding(tpx((72, 69)), tpx((44, 67)), 20, 72, n=4),
                       organic.polyline_samples([tpx((44, 67)), tpx((32, 60)), tpx((33, 53))], 12.0)])
    seg_m = np.vstack([winding(tpx((33, 53)), tpx((80, 54)), 18, 73, n=5), winding(tpx((80, 54)), tpx((126, 52.5)), 18, 74, n=5),
                       organic.polyline_samples([tpx((126, 52.5)), tpx((142, 49)), tpx((141, 40))], 12.0)])
    seg_n = np.vstack([winding(tpx((141, 40)), tpx((118, 36.5)), 14, 75, n=3),
                       organic.polyline_samples([tpx((118, 36.5)), tpx((104, 34.5)), tpx((96, 34.5)), P["bonfire_preboss"],
                                                 P["boss_arena"], tpx((58, 21)), tpx((46, 13)), tpx((40, 8)), P["exit"]], 12.0)])
    route = np.vstack([seg_vil, seg_s, seg_m, seg_n])

    def route_i(pt):
        return idx_near(route, pt)

    i_boss, i_exit = route_i(P["boss_arena"]), route_i(P["exit"])
    i_gate = route_i(tpx(GATE_C))

    # ------------------------------------------------------------ laut beku (biru di *_layout.png), daratan, punggung es
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch4_GuaRantai_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 60 and ty >= 6
    sea_img[:, :6] = sea_img[:, 6:7]                       # 6 baris atas gambar tertutup judul: lanjutkan baris ke-6
    land = dilate(mask, 2) & ~sea_img
    land |= np.hypot(gx - P["entry"][0], gy - P["entry"][1]) <= 4.0 * TILE
    nz_r = organic.smooth_noise(gx, gy, 23)
    ridge = np.zeros_like(mask)
    for pts, hw in RIDGES:
        ridge |= dist_to(gx, gy, organic.polyline_samples([tpx(p_) for p_ in pts], 12.0)) <= hw * TILE + 10 * nz_r
    for x0, x1, y0, y1 in GAPS.values():            # celah punggung es selalu bisa dilalui (lalu ditutup penghalang)
        ridge[x0:x1 + 1, y0:y1 + 1] = False
    land &= ~ridge
    land = dilate(erode(land, 1), 1) | (land & dilate(sea_img, 1))
    # DANAU BEKU Desa Simpul (tepi berombak) + 3 pulau
    nz_l = organic.smooth_noise(gx, gy, 29)
    lake = (np.hypot((gx / TILE - 0.5 - LAKE_C[0]) / LAKE_R[0], (gy / TILE - 0.5 - LAKE_C[1]) / LAKE_R[1]) + 0.04 * nz_l < 1.0) & land
    isl = np.zeros_like(mask)
    for (cx_, cy_), r_ in ISLANDS.values():
        isl |= np.hypot(gx / TILE - 0.5 - cx_, gy / TILE - 0.5 - cy_) + 0.08 * nz_l <= r_
    lake &= ~isl
    sea = (sea_img & ~land) | lake
    land &= ~lake
    plateau = ~land & ~sea
    # jembatan papan: segmen antar-pulau (3 tile lebar) di atas air danau, bisa dilalui
    bridges = [(SHORE_E, I1), (I1, I2), (I2, I3), (I3, SHORE_N)]
    dock = np.zeros_like(mask)
    for a_, b_ in bridges:
        dock |= dist_to(gx, gy, organic.polyline_samples([tpx(a_), tpx(b_)], 6.0)) <= 1.3 * TILE
    dock &= lake
    # wajah tebing: 2 tile di bawah tepi selatan dataran tinggi
    face = {}
    keep_free = [P["entry"]]
    for tx in range(W):
        for ty in range(H - 1):
            if plateau[tx, ty] and not plateau[tx, ty + 1]:
                for k, cy_ in ((1, 5), (2, 7)):
                    y2 = ty + k
                    if y2 < H and land[tx, y2] and not any(math.hypot(tx * TILE + 8 - kx, y2 * TILE + 8 - ky) < 3.5 * TILE for kx, ky in keep_free):
                        face[(tx, y2)] = cy_
    face_m = np.zeros_like(mask)
    for (tx, ty) in face:
        face_m[tx, ty] = True

    # ------------------------------------------------------------ titik sudut air
    pad_sea = np.pad(sea, 1, mode="edge")
    water_v = pad_sea[:-1, :-1] & pad_sea[1:, :-1] & pad_sea[:-1, 1:] & pad_sea[1:, 1:]     # 4 sel di sekitar titik = air
    near_water_v = np.pad(dilate(sea, 1), 1, mode="edge")
    near_water_v = near_water_v[:-1, :-1] | near_water_v[1:, :-1] | near_water_v[:-1, 1:] | near_water_v[1:, 1:]

    # ------------------------------------------------------------ gerbang & kabut
    band = land & ~face_m & (np.hypot(gx / TILE - 0.5 - GATE_C[0], gy / TILE - 0.5 - GATE_C[1]) <= 4.2)
    exit_t = (P["exit"][0] / TILE, P["exit"][1] / TILE)
    plug = (np.hypot(gx / TILE - exit_t[0], gy / TILE - exit_t[1]) <= 4.5) & land & ~face_m
    gapm = {}
    for nm_g, (x0, x1, y0, y1) in GAPS.items():
        m_ = np.zeros_like(mask)
        m_[x0:x1 + 1, y0:y1 + 1] = True
        gapm[nm_g] = m_ & land & ~face_m
    open_l = land & ~face_m
    # penghalang memotong lorong celah selebar-lebarnya (celah N3 = lorong barat-timur -> kolom; celah N1/N2 = utara-selatan -> baris)
    bar_block = open_l & (tcol >= 96) & (tcol <= 99) & (trow >= 29) & (trow <= 40)      # dinding rantai es (Quest Tengah)
    sc1_block = open_l & (trow >= 60) & (trow <= 61) & (tcol >= 92) & (tcol <= 108)    # runtuhan es N1 (jalan pintas, Kristal)
    sc2_block = open_l & (trow >= 45) & (trow <= 46) & (tcol >= 71) & (tcol <= 90)     # runtuhan es N2 (jalan pintas, Kristal)
    corridor = land & ~face_m & ~band & ~plug & ~bar_block & ~sc1_block & ~sc2_block   # dataran yang boleh dihuni objek

    # ------------------------------------------------------------ jalan salju padat (rute + cabang pinggiran)
    CRYSTAL = tpx((105, 113))     # gua kristal (barat daya kantong)
    HUT = tpx((135, 77))          # pondok pencari kristal (timur laut)
    ICE_SE = tpx((130, 109.5))    # tepi danau tenggara
    road_k = winding(tpx((126, 110)), CRYSTAL, 26, 61, n=4)
    road_h = winding(tpx((114, 77)), HUT, 18, 63, n=4)
    road_s = winding(tpx(SHORE_E), ICE_SE, 14, 65, n=3)
    road_ring = winding(tpx((128, 109)), tpx((139, 103)), 10, 67, n=3)
    roads = np.vstack([route, road_k, road_h, road_s, road_ring])
    vx = (np.arange(W + 1) * TILE)[:, None] * np.ones((1, H + 1))
    vy = (np.arange(H + 1) * TILE)[None, :] * np.ones((W + 1, 1))
    vn = organic.smooth_noise(vx, vy, 4)
    path_v = dist_to(vx, vy, roads) <= 22 + 5 * vn
    pads = [(tpx((125, 89.5)), 70), (CRYSTAL, 60), (HUT, 54), (ICE_SE, 44), (P["puzzle"], 60), (P["bonfire_preboss"], 46),
            (P["boss_arena"], 140), (P["exit"], 44), (P["entry"], 40), (tpx((122, 111)), 56)]
    for (px_, py_), rr in pads:
        path_v |= np.hypot(vx - px_, vy - py_) <= rr + 10 * vn
    path_v &= ~near_water_v          # tepi air = salju (tile air bertepi salju)
    ac_ = (P["boss_arena"][0] / TILE - 0.5, P["boss_arena"][1] / TILE - 0.5)
    ice_v = np.hypot((vx / TILE - 0.5 - ac_[0]) / ARENA_ICE[0], (vy / TILE - 0.5 - ac_[1]) / ARENA_ICE[1]) + 0.06 * vn < 1.0

    # ------------------------------------------------------------ peta tile
    ground, cliffc, dockc, blockc = [], [], [], []
    for tx in range(W):
        for ty in range(H):
            if plateau[tx, ty]:
                n_ = ty == 0 or plateau[tx, ty - 1]
                w_ = tx == 0 or plateau[tx - 1, ty]
                e_ = tx == W - 1 or plateau[tx + 1, ty]
                cliffc.append((tx, ty, 1, 1 if not w_ else (3 if not e_ else 2), 6 if n_ else 5))
                continue
            if (tx, ty) in face:
                lft = tx > 0 and (tx - 1, ty) in face
                rgt = tx < W - 1 and (tx + 1, ty) in face
                cliffc.append((tx, ty, 1, 5 if (lft and rgt) else (4 if not lft else 6), face[(tx, ty)]))
                continue
            h_ = (tx * 7 + ty * 13 + tx * ty) % 97
            if sea[tx, ty]:
                wk = (int(water_v[tx, ty]), int(water_v[tx + 1, ty]), int(water_v[tx, ty + 1]), int(water_v[tx + 1, ty + 1]))
                if wk == (0, 0, 0, 0):
                    ground.append((tx, ty, 0, SNOW[0][0], SNOW[0][1]))
                else:
                    a_ = WATER_CORNER[wk]
                    ground.append((tx, ty, 2, a_[0], a_[1]))
                    if sum(wk) >= 2 and not dock[tx, ty]:
                        blockc.append((tx, ty, 0, 0, 0))
                if dock[tx, ty]:
                    p_ = PLANK[(tx * 3 + ty) % 3]
                    dockc.append((tx, ty, 2, p_[0], p_[1]))
                continue
            ik = (int(ice_v[tx, ty]), int(ice_v[tx + 1, ty]), int(ice_v[tx, ty + 1]), int(ice_v[tx + 1, ty + 1]))
            if ik != (0, 0, 0, 0):      # lantai es arena (sumber 3, bit = titik sudut es)
                a_ = (1, 1) if ik == (1, 1, 1, 1) else CORNER_TILES[ik]
                ground.append((tx, ty, 3, a_[0], a_[1]))
                continue
            key = (int(path_v[tx, ty]), int(path_v[tx + 1, ty]), int(path_v[tx, ty + 1]), int(path_v[tx + 1, ty + 1]))
            if key == (0, 0, 0, 0):
                a_ = SNOW[h_ % len(SNOW)]
            elif key == (1, 1, 1, 1):
                a_ = PATH_DETAIL[h_ % 2] if h_ % 29 == 0 else PATH[0]
            else:
                a_ = CORNER_TILES[key]
            ground.append((tx, ty, 0, a_[0], a_[1]))

    # jalur pintas (panah setelah Kristal): arena -> runtuhan es N2 -> lembah tengah -> runtuhan es N1 -> gerbang -> Pulau 2 (Megas)
    short_route = organic.polyline_samples([P["boss_arena"], tpx((80, 38)), tpx((80.5, 46)), tpx((92, 53)), tpx((100, 56)),
                                            tpx((100, 61)), tpx((101, 65)), tpx(GATE_C), tpx((108, 75)), tpx(SHORE_N), tpx(I3),
                                            tpx((125, 91.5))], 12.0)

    # ------------------------------------------------------------ scene
    sc = Scene()
    ts_glacier = sc.ext_res("TileSet", "res://assets/tilesets/glacier_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKsatria.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/LinkedPortals.tscn")
    blocker_script = sc.ext_res("Script", "res://scripts/world/StageBlocker.gd")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")
    flam_tex = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")

    sc.node("Ch4_GuaRantai", "Node2D", script=f'ExtResource("{script}")', chapter="4", music_name='"ch4_gua_rantai"',
            boss_music_name='"boss"',
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")",
            shortcut_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in short_route[::4]) + ")",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Dingin", "CanvasModulate", ".", color="Color(0.9, 0.95, 1.06, 1)")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_glacier}")')
    sc.node("Jembatan", "TileMapLayer", ".", tile_map_data=b64cells(dockc), tile_set=f'ExtResource("{ts_glacier}")')
    sc.node("Tebing", "TileMapLayer", ".", tile_map_data=b64cells(cliffc), tile_set=f'ExtResource("{ts_glacier}")')
    sc.node("AirPenghalang", "TileMapLayer", ".", tile_map_data=b64cells(blockc), tile_set=f'ExtResource("{block_ts}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    recorded = []
    buildings = []        # (x, y_kaki, w, h): area bebas dekorasi

    def prefab(node, pref, pos, solid=True, record=True, **props):
        pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
        sc.node(node, None, "Objects", instance=pid, position=v2(*pos), **props)
        if record:
            recorded.append(pos)
        if solid:
            w, h = PREFAB_SIZE.get(pref, (16, 16))
            buildings.append((pos[0], pos[1], w, h))

    def inst(name, scene_id, pos, **props):
        recorded.append(pos)
        sc.node(name, None, "Objects", instance=scene_id, position=v2(*pos), **props)

    def near_building(x, y, clear=3 * TILE):
        for bx, by, w, h in buildings:
            dx = max(abs(x - bx) - w / 2, 0)
            dy = max(abs(y - (by - h / 2)) - h / 2, 0)
            if math.hypot(dx, dy) < clear:
                return True
        return False

    # ------------------------------------------------------------ DESA SIMPUL
    houses = {"RumahMegas": ("Rumah_Menara_Salju", (125, 87.6)),          # Pulau 2 (interior)
              "RumahGilang": ("Rumah_Runcing_Salju", (130, 101.6)),        # Pulau 1
              "RumahPulau3": ("Rumah_Loteng_Salju", (110, 91.2)),          # Pulau 3
              "RumahTepiUtara": ("Rumah_Teras_Salju", (124, 76.2)),        # tepi utara danau
              "RumahTepiSelatan": ("Rumah_Runcing_Salju", (118, 113.6)),   # tepi selatan danau
              "PondokKristal": ("Pondok_Salju", (135, 77.0))}              # pondok pencari kristal (timur laut)
    for name, (pref, (x, y)) in houses.items():
        prefab(name, pref, at(x, y))
    # alun-alun Pulau 2: sumur, lapak, tong, lampu
    for nm, pref, (x, y) in (("Sumur", "Sumur", (121.6, 90.8)), ("LapakJimat", "Lapak_Kain", (128.6, 90.6))):
        prefab(nm, pref, at(x, y))
    for i, (x, y) in enumerate(((119.6, 89.2), (130.4, 89.2), (126.4, 101.8), (133.6, 101.8), (107.0, 89.4), (113.4, 89.6),
                                (108.4, 77.4))):
        prefab(f"Lentera{i}", "Lentera_Tiang", at(x, y), solid=False)
    # pinggiran 1: GUA KRISTAL (barat daya) - kristal ungu di antara batu kelabu
    cx_, cy_ = CRYSTAL
    for k, (pref, (ox, oy)) in enumerate((("Batu_Kelabu", (-50, -40)), ("Kristal_Ungu_1", (-6, -44)), ("Kristal_Ungu_2", (40, -34)),
                                          ("Kristal_Ungu_1", (62, 18)), ("Kristal_Ungu_2", (-60, 20)), ("Batu_Kelabu", (12, 52)),
                                          ("Gundukan_Salju", (-30, 50)))):
        prefab(f"GuaKristal{k}", pref, (cx_ + ox, cy_ + oy))
    # pinggiran 2: PONDOK PENCARI KRISTAL (timur laut) - kayu, peti, kristal hasil tambang
    hx_, hy_ = HUT
    for k, (pref, (ox, oy)) in enumerate((("Tumpukan_Kayu", (-58, 22)), ("Peti_Kayu_B", (52, 18)), ("Kristal_Ungu_2", (60, -6)),
                                          ("Barel_Air", (-46, 4)))):
        prefab(f"Pondok{k}", pref, (hx_ + ox, hy_ + oy))
    # pinggiran 3: TEPI DANAU TENGGARA - lubang pancing beku, gundukan salju
    ix_, iy_ = ICE_SE
    for k, (pref, (ox, oy)) in enumerate((("Gundukan_Salju", (-40, 26)), ("Peti_Kayu_A", (34, 22)), ("Pinus_Salju_1", (60, -10)))):
        prefab(f"TepiDanau{k}", pref, (ix_ + ox, iy_ + oy))

    # ------------------------------------------------------------ NPC & penanda
    mp, (mx_, my_) = houses["RumahMegas"]
    door_x, door_y = at(mx_ + DOOR_DX.get(mp, 0) / TILE, my_)
    npc_positions = []

    def npc(name, pos, **props):
        inst(name, npc_scene, pos, **props)
        npc_positions.append(pos)

    megas_pos = (door_x + 40, door_y + 24)
    gilang_pos, laras_pos, bayu_pos = at(132.6, 102.8), at(112.8, 92.6), at(108.4, 108.6)
    npc("Megas", megas_pos, npc_id='"megas"')
    npc("Gilang", gilang_pos, npc_id='"gilang"', dialog_id='"ch4_gilang"', villager_chapter="4")
    npc("Laras", laras_pos, npc_id='"laras"', dialog_id='"ch4_laras"', villager_chapter="4")
    npc("Bayu", bayu_pos, npc_id='"bayu"', dialog_id='"ch4_bayu"', villager_chapter="4")
    npc("Pedagang", at(126.4, 92.0), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuMegas", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_RumahMegas.tscn"', hint_text='"E: Masuk rumah Megas"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuMegas", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    start = tuple(int(v) for v in route[3])
    bf1 = at(123.2, 92.4)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("BenderaMasuk", checkpoint_scene, at(139.6, 95.0))
    inst("BenderaGerbang", checkpoint_scene, at(111.6, 75.0))
    inst("BenderaKristal", checkpoint_scene, (cx_ + 80, cy_ - 50))
    inst("PetiKristal", chest_scene, (cx_ - 20, cy_ + 20), roll_count="2")
    inst("PetiPondok", chest_scene, (hx_ + 30, hy_ + 50), roll_count="2")
    clue_pts = [(ix_ + 4, iy_ - 10), (hx_ - 10, hy_ + 30), (cx_ + 20, cy_ - 4)]
    for k_, (ck, pos) in enumerate(zip(("catatan", "barang", "jejak"), clue_pts), start=1):
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*pos),
                flag=f'"ch4_petunjuk_{k_}"', dialog_id=f'"ch4_petunjuk_{k_}"', required_step='"ch4_awal:petunjuk"', clue_kind=f'"{ck}"')
        recorded.append(pos)
        npc_positions.append(pos)
    inst("PulangPelabuhan", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="3", sign_text='"Kembali ke Pelabuhan Antre"')
    inst("KePohonDunia", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="5", sign_text='"Jembatan es ke Pohon Dunia"')
    npc_positions += [bf1, start, CRYSTAL, HUT, ICE_SE, P["puzzle"], P["boss_arena"]]

    # ---- perjalanan: stasiun batu portal (Quest Tengah) di dataran utara, lingkaran batu portal, Bonfire, bendera
    px0, py0 = P["puzzle"]
    inst("StasiunPortal", station_scene, (int(px0), int(py0) + 36), puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="4",
         station_label='"Batu Portal"')
    for k in range(6):          # lingkaran batu portal (pilar berlumut & kristal) mengelilingi stasiun
        ang = math.pi * 0.1 + k * math.tau / 6
        pref = "Pilar_Lumut" if k % 2 == 0 else "Kristal_Ungu_2"
        prefab(f"BatuPortal{k}", pref, (round(px0 + math.cos(ang) * 74), round(py0 + 30 + math.sin(ang) * 46)))
    bf_pre = (int(P["bonfire_preboss"][0]) + 10, int(P["bonfire_preboss"][1]) + 26)
    bf_mid = at(62, 55.0)
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf_mid)
    flags = {"BenderaBarat": at(36, 63.5), "BenderaTengah": at(108, 55.5), "BenderaUtara": at(136, 37.5)}
    for nm_f, pos in flags.items():
        inst(nm_f, checkpoint_scene, pos)
    npc_positions += [(int(px0), int(py0) + 36), bf_pre, bf_mid] + list(flags.values())
    # arena lantai es: obor di tepi, bongkahan es & rantai kristal
    ax_, ay_ = (int(v) for v in P["boss_arena"])
    for k in range(6):
        ang = math.pi * 0.15 + k * math.tau / 6
        fx_, fy_ = round(ax_ + math.cos(ang) * 150), round(ay_ + math.sin(ang) * 100)
        prefab(f"TiangObor{k}", "Lentera_Tiang", (fx_, fy_ + 4), solid=False)
        sc.node(f"OborArena{k}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_tex}")',
                position=v2(fx_, fy_ - 26), frame_w="20", frame_h="30", fps="9.0")
    for k, (pref, (ox, oy)) in enumerate((("Kristal_Ungu_1", (-176, -60)), ("Batu_Kelabu", (186, -50)), ("Kristal_Ungu_2", (-180, 70)),
                                          ("Gundukan_Salju", (176, 76)))):
        prefab(f"TepiArena{k}", pref, (ax_ + ox, ay_ + oy))
    npc_positions += [(ax_, ay_)]

    # penghalang tumpukan objek (scripts/world/StageBlocker.gd)
    def blocker(name, cells, mode, stage, text, pieces, opened=""):
        xs, ys = np.nonzero(cells)
        c0 = (int(xs.mean()) * TILE + 8, int(ys.max() + 1) * TILE)
        sc.node(name, "Node2D", "Objects", script=f'ExtResource("{blocker_script}")', position=v2(*c0), y_sort_enabled="true",
                mode=f'"{mode}"', chapter="4", required_stage=str(stage), locked_text=f'"{text}"', opened_text=f'"{opened}"',
                hint_size=f"Vector2({(xs.max() - xs.min() + 9) * TILE}, {(ys.max() - ys.min() + 9) * TILE})")
        for k, (pref, (ox, oy)) in enumerate(pieces):
            pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
            sc.node(f"{name}{k}", None, f"Objects/{name}", instance=pid, position=v2(ox, oy))
        cells_l = [(int(x) - (c0[0] - 8) // TILE, int(y) - c0[1] // TILE, 0, 0, 0) for x, y in zip(xs, ys)]
        sc.node("Block", "TileMapLayer", f"Objects/{name}", position=v2(-8, 0), tile_map_data=b64cells(cells_l),
                tile_set=f'ExtResource("{block_ts}")')
        recorded.append(c0)
        return c0

    ICE_PIECES = [("Gundukan_Salju", (-26, -6)), ("Batu_Kelabu", (4, -2)), ("Gundukan_Salju", (34, -4))]
    bar_c = blocker("DindingRantaiEs", bar_block, "stage", 2, "Dinding rantai es menutup celah.\nSambung batu portal dulu.",
                    [("Kristal_Ungu_1", (-60, -14)), ("Batu_Kelabu", (-14, -6)), ("Kristal_Ungu_1", (30, -12)), ("Kristal_Ungu_2", (70, -4))],
                    "Batu portal tersambung! Rantai es pecah.\nJalan ke arena Ksatria Rantai terbuka.")
    sc1_c = blocker("RuntuhanEsSelatan", sc1_block, "crystal", 4, "Runtuhan es menutup celah.\nMungkin terbuka setelah Ksatria Rantai kalah.",
                    ICE_PIECES, "Gemuruh! Runtuhan es di dekat gerbang desa mencair.")
    sc2_c = blocker("RuntuhanEsUtara", sc2_block, "crystal", 4, "Runtuhan es menutup celah.\nMungkin terbuka setelah Ksatria Rantai kalah.",
                    ICE_PIECES, "Gemuruh! Runtuhan es mencair.\nJalan pintas ke Desa Simpul terbuka.")
    npc_positions += [bar_c, sc1_c, sc2_c]

    def cloud_barrier(name, cells_mask, mode, dist, text="", **props):
        pts = thin_cells(cells_mask, dist)
        arr = ", ".join(f"{x}, {y}" for x, y in pts)
        extra = {"locked_text": '"%s"' % text} if text else {}
        sc.node(name, "Node2D", ".", script=f'ExtResource("{cloud_script}")', mode=f'"{mode}"', chapter="4",
                cloud_points=f"PackedVector2Array({arr})", seed_value=str(rng.randint(1, 999)), **extra, **props)
        cells = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(cells_mask))]
        sc.node("Block", "TileMapLayer", name, tile_map_data=b64cells(cells), tile_set=f'ExtResource("{block_ts}")')

    SNOWSTORM = "Color(0.92, 0.96, 1, 1)"
    cloud_barrier("AwanPerbatasan", plug, "chapter", 26, tint=SNOWSTORM, scale_min="1.2", scale_max="1.6")
    cloud_barrier("AwanGerbangDesa", band, "stage", 30, "Badai salju menutup celah gunung.\\nBantu Megas dulu.",
                  required_stage="1", tint=SNOWSTORM, scale_min="1.3", scale_max="1.9")

    # ------------------------------------------------------------ dekorasi: pinus bersalju, gundukan, batu kelabu
    d_route = dist_to(gx, gy, roads)

    def road_dist(x, y):
        tx_, ty_ = int(x // TILE), int(y // TILE)
        return float(d_route[tx_, ty_]) if 0 <= tx_ < W and 0 <= ty_ < H else 0.0

    pocket = (tcol >= 100) & (trow >= 72)
    village_zone = (np.hypot((gx / TILE - LAKE_C[0]) / (LAKE_R[0] + 2), (gy / TILE - LAKE_C[1]) / (LAKE_R[1] + 2)) < 1.0) & pocket
    keypts = [P[k] for k in ("entry", "puzzle", "bonfire_preboss", "boss_arena", "exit")] + [bf1, start] + npc_positions
    no_deco = dilate(dock | band | plug | gapm["n1"] | gapm["n2"] | gapm["n3"], 3) \
        | (np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 13 * TILE)

    def fits(pref, x, y, margin=8):
        w, h = PREFAB_SIZE[pref]
        for ox, oy in ((-w / 2 - margin, 0), (w / 2 + margin, 0), (-w / 2 - margin, -h), (w / 2 + margin, -h), (0, margin), (0, -h / 2)):
            tx_, ty_ = int((x + ox) // TILE), int((y + oy) // TILE)
            if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or village_zone[tx_, ty_] or no_deco[tx_, ty_]:
                return False
        if road_dist(x, y) < w / 2 + 30 or road_dist(x, y - h / 2) < w / 2 + 30:
            return False
        if any(math.hypot(x - kx, y - ky) < 80 for kx, ky in keypts):
            return False
        return not near_building(x, y, 14)

    big = ["Pinus_Salju_Rumpun", "Pinus_Salju_1", "Pohon_Salju_Besar", "Pinus_Salju_Rumpun", "Pohon_Salju_Bulat"]
    small = ["Pinus_Salju_1", "Pinus_Salju_2", "Gundukan_Salju", "Pohon_Salju_Bulat", "Batu_Sedang_1"]
    clusters, nm_ = [], 0
    for _try in range(12000):
        if len(clusters) >= 120:
            break
        x, y = rng.randint(60, PX_W - 60), rng.randint(90, PX_H - 50)
        if any(math.hypot(x - cx2, y - cy2) < 130 for cx2, cy2 in clusters):
            continue
        pref = rng.choice(big)
        if not fits(pref, x, y):
            continue
        clusters.append((x, y))
        prefab(f"Pinus{nm_}", pref, (x, y))
        nm_ += 1
        for _k in range(rng.randint(2, 4)):
            p3 = rng.choice(small)
            ang = rng.random() * math.tau
            x3, y3 = round(x + math.cos(ang) * rng.randint(30, 80)), round(y + math.sin(ang) * rng.randint(20, 50))
            if fits(p3, x3, y3, 2):
                prefab(f"Pinus{nm_}", p3, (x3, y3))
                nm_ += 1
    for k in range(14):        # batu kelabu besar di luar kantong desa
        x, y = rng.randint(80, PX_W - 80), rng.randint(120, PX_H - 60)
        if fits("Batu_Kelabu", x, y, 4):
            prefab(f"BatuKelabu{k}", "Batu_Kelabu", (x, y))
            nm_ += 1
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', leaves="false", ray_alpha="0.08")

    # ------------------------------------------------------------ collectible pinggiran desa (aman, tanpa musuh di Tahap 1)
    nl = 0
    for nm, (bx_, by_) in (("Ore", (cx_ - 40, cy_ - 70)), ("Ore", (cx_ + 70, cy_ - 60)), ("Herb", (hx_ - 70, hy_ + 50)),
                           ("GoldCoin", (ix_ - 60, iy_ + 10)), ("Herb", (ix_ + 20, iy_ + 40)), ("Potion", at(115.0, 76.0))):
        tx_, ty_ = int(bx_ // TILE), int(by_ // TILE)
        if corridor[tx_, ty_] and not near_building(bx_, by_, 6):
            nl += 1
            inst(f"Pinggir{nm}{nl}", collect[nm], (bx_, by_))

    # ------------------------------------------------------------ musuh, peti, collectible (perjalanan)
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    taken = []
    ice_t = np.hypot((gx / TILE - 0.5 - ac_[0]) / (ARENA_ICE[0] + 1), (gy / TILE - 0.5 - ac_[1]) / (ARENA_ICE[1] + 1)) < 1.0

    def spot(pt, r_min=20):
        """Titik bebas terdekat (spiral sampai 140 px) dari pt (px)."""
        for r in [0] + list(range(12, 141, 12)):
            for a_ in range(0, 360, 30):
                x, y = round(pt[0] + math.cos(math.radians(a_)) * r), round(pt[1] + math.sin(math.radians(a_)) * r)
                tx_, ty_ = int(x // TILE), int(y // TILE)
                if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or ice_t[tx_, ty_] or village_zone[tx_, ty_] \
                        or road_dist(x, y) < r_min:
                    continue
                if near_building(x, y, 14) or any(math.hypot(x - qx2, y - qy2) < 26 for qx2, qy2 in taken):
                    continue
                taken.append((x, y))
                return (round(x), round(y))
        return None

    # kerangka penjaga gua (Skeleton) & slime es. Zona aman: kelompok pertama >= 44 tile dari gerbang desa.
    groups = {"Selatan1": ((62, 71), ["slime", "slime2", "slime"]),
              "Selatan2": ((44, 75), ["skeleton", "skeleton_rogue"]),
              "Barat1": ((29, 54), ["skeleton", "skeleton_warrior", "skeleton_rogue"]),
              "Tengah1": ((70, 52), ["slime3", "skeleton", "skeleton_mage"]),
              "Tengah2": ((112, 52), ["skeleton_warrior", "skeleton_rogue", "skeleton"]),
              "Timur1": ((148, 44), ["skeleton_mage", "skeleton", "slime3"]),
              "Utara1": ((128, 28), ["skeleton_warrior", "skeleton_mage", "skeleton_rogue"]),
              "Utara2": ((108, 20), ["skeleton", "slime3"]),
              "Gua1": ((56, 38), ["skeleton_mage", "skeleton_warrior"])}
    n_mob = 0
    for gname, ((gx_t, gy_t), ids) in groups.items():
        for k, eid in enumerate(ids):
            ang = k * math.tau / len(ids) + 0.5
            q = spot((gx_t * TILE + 8 + math.cos(ang) * 34, gy_t * TILE + 8 + math.sin(ang) * 26))
            if q:
                inst(f"Musuh{gname}_{k + 1}", enemy_scene, q, enemy_id=f'"{eid}"')
                n_mob += 1
    chests = {"PetiSelatan": (40, 82), "PetiBarat": (26, 48), "PetiTengah": (92, 56), "PetiTimur": (152, 52), "PetiUtara": (120, 16)}
    for nm, (cx2, cy2) in chests.items():
        q = spot(tpx((cx2, cy2)))
        if not q:
            print("PERINGATAN: peti", nm, "tidak dapat tempat")
            continue
        inst(nm, chest_scene, q, roll_count="2")
        for kind, (ox, oy) in (("Herb", (30, 14)), ("GoldCoin", (-28, 16)), ("Ore", (2, 34))):
            q2 = spot((q[0] + ox, q[1] + oy), 0)
            if q2:
                nl += 1
                inst(f"{kind}{nl}", collect[kind], q2)
    for k in range(28):
        i_ = rng.randint(i_gate + 10, i_boss)
        th = rng.random() * math.tau
        pt = (route[i_][0] + math.cos(th) * rng.randint(50, 130), route[i_][1] + math.sin(th) * rng.randint(40, 100))
        q = spot(pt, 30)
        if q:
            kind = ("Herb", "GoldCoin", "Ore", "Herb")[k % 4]
            nl += 1
            inst(f"{kind}{nl}", collect[kind], q)
    for k, pt in enumerate((at(50, 66), at(132, 40))):
        q = spot(pt, 24)
        if q:
            inst(f"Potion{k + 1}", collect["Potion"], q)

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    fn = route[max(0, i_exit - 8)]
    sc.node("FromNext", "Marker2D", ".", position=v2(int(fn[0]), int(fn[1])))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Megas", "Marker2D", "NPCSpawns", position=v2(*megas_pos), **{"metadata/npc_id": '"megas"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')

    out = os.path.join(ROOT, "scenes/world/Ch4_GuaRantai.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ uji keterhubungan (grid tile, objek padat diabaikan)
    walk = (land & ~face_m) | dock

    def reach(block):
        from collections import deque
        sx, sy = int(start[0] // TILE), int(start[1] // TILE)
        seen = np.zeros_like(walk)
        seen[sx, sy] = True
        dq = deque([(sx, sy)])
        while dq:
            x, y = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and walk[nx, ny] and not seen[nx, ny] and not block[nx, ny]:
                    seen[nx, ny] = True
                    dq.append((nx, ny))
        return seen

    t_ = {k: (int(v[0] // TILE), int(v[1] // TILE)) for k, v in P.items()}
    sc_both = sc1_block | sc2_block
    r_gate, r_open = reach(band | plug | bar_block | sc_both), reach(plug | bar_block | sc_both)
    r_all, r_short = reach(plug | sc_both), reach(plug | bar_block)
    pts_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in [megas_pos, gilang_pos, laras_pos, bayu_pos] + clue_pts)
    isl_ok = all(r_gate[int(c[0]), int(c[1])] for c, _ in ISLANDS.values())
    print("start di daratan =", bool(walk[int(start[0] // TILE), int(start[1] // TILE)]),
          "| desa, 4 NPC, 3 petunjuk & 3 pulau terjangkau saat gerbang tertutup =", pts_ok and isl_ok)
    print("gerbang mengunci puzzle =", not r_gate[t_["puzzle"]], "| puzzle terjangkau saat terbuka =", bool(r_open[t_["puzzle"]]))
    print("rantai es mengunci arena =", not r_open[t_["boss_arena"]], "| arena terjangkau setelah rantai pecah =", bool(r_all[t_["boss_arena"]]),
          "| jalan pintas (runtuhan es dibuka) menembus ke arena =", bool(r_short[t_["boss_arena"]]))
    print("awan perbatasan mengunci exit =", not reach(sc_both | plug)[t_["exit"]], "| exit terjangkau tanpa awan =",
          bool(reach(np.zeros_like(walk))[t_["exit"]]))
    length = float(np.sum(np.hypot(*np.diff(route[i_gate:i_boss], axis=0).T))) / TILE
    print("musuh:", n_mob, "| jalan gerbang->arena %.0f tile" % length)
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and walk[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Ch4_GuaRantai.tscn:", nm_, "pinus/batu, objek di luar daratan:", len(bad), bad[:6], "| koridor", int(corridor.sum()),
          "tile | jembatan", int(dock.sum()), "tile | collectible", nl)
    return bad


if __name__ == "__main__":
    build()
