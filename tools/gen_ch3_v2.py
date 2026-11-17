"""Generator Ch3_PelabuhanAntre.tscn v2: bentuk wilayah dari docs/layout/region_layout.json + KOTA PELABUHAN ANTRE (blueprint grid).

Jalankan dari folder proyek (setelah make_prefabs.py, make_villagers.py, gen_coast_tileset.py, gen_interior.py):
    python tools/gen_ch3_v2.py
Tahap 1 (bagian ini): peta 136x184 tile, batas pesisir, Kota Pelabuhan Antre + pinggiran + 3 petunjuk, gerbang kabut laut.
  - Lantai: rumput; jalan & pantai = pasir bertepi rumput (autotile sudut / marching squares, tools/gen_coast_tileset.py).
    Laut = blok air Ninja bertepi pasir (autotile sudut yang sama, bit = titik sudut air), papan dermaga di atas air.
  - Batas: laut di timur, TEBING batu pasir berpuncak rumput di luar mask (abu-abu = wilayah lain). Awan perbatasan hanya di
    titik keluar ke Gua Rantai (hilang setelah Chapter 3 selesai).
  - PUNGGUNG TEBING utara kota (dataran tinggi di dalam wilayah) memisahkan kota dari jalan pesisir; satu celah = gerbang kota
    (kabut laut, terbuka setelah Quest Awal).
Blueprint kota (tile, pusat C; X ke timur, Y ke selatan): alun-alun 12x12 batu + sumur, jalan batu ke U/S/B dan ke DERMAGA di timur,
  KEDAI DADANG (barat laut, bisa dimasuki) + 3 rumah, pasar tenda di alun-alun, gudang pelabuhan + loket tiket + tali antrean
  di pangkal dermaga penumpang (kapal layar bersandar), dermaga ikan di tenggara.
  Pinggiran: mercusuar di tanjung selatan, kebun kelapa di barat, pantai timur.
Perjalanan (Tahap 2): gerbang kota -> barat di antara punggung tebing N & L -> TONJOLAN BARAT (memutar) -> jalan sempit utara
  punggung L -> KORIDOR BARAT ke utara (di antara tebing batas & punggung M) -> warung pinggir jalan (stasiun antrean = Quest Tengah)
  -> BARIKADE BAJAK LAUT di celah punggung W/M (StageBlocker, hilang di quest_stage 2) -> Bonfire pra-boss -> DERMAGA BAJAK LAUT
  (arena Kapten, lantai papan) -> dermaga keluar di teluk utara (Kapal Dadang ke Gua Rantai, awan perbatasan).
  Jalan pintas arena -> kota = PESISIR TIMUR (di timur punggung M), ditutup PERAHU KARAM di celah sempit (StageBlocker mode crystal).
  Musuh: awak bajak laut (Orc) + slime pantai; zona aman kota (tidak ada musuh di selatan punggung N).
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
from gen_coast_tileset import GRASS, PLANK, SAND, SAND_DETAIL, WATER_CORNER  # noqa: E402
from gen_village import ROOT, TILE, Scene, v2  # noqa: E402

dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx
LAYOUT = json.load(open(os.path.join(ROOT, "docs/layout/region_layout.json"), encoding="utf-8"))["Ch3_PelabuhanAntre"]
W, H = LAYOUT["ukuran_tile"]            # 136 x 184
PX_W, PX_H = LAYOUT["ukuran_px"]        # 2176 x 2944
# geser pintu varian rumah dari pusat gambar (px), hasil tools/make_houses.py
DOOR_DX = json.load(open(os.path.join(ROOT, "assets/props/buildings/variants/_pintu.json"), encoding="utf-8"))
C = (72, 122)                           # pusat Kota Pelabuhan Antre (village_center layout (34,106) digeser ke pesisir timur)
CX, CY = C[0] * TILE + 8, C[1] * TILE + 8
GATE_X = (58, 86)                       # rentang kolom tempat celah gerbang kota pada punggung tebing utara
GATE_ROWS = (100, 104)
# punggung tebing (dataran tinggi di DALAM wilayah, tile): (polyline, setengah lebar)
RIDGES = [([(-3, 101), (20, 101), (44, 101), (60, 102)], 4.0),   # N-barat: dinding utara kota, dari tebing barat sampai celah gerbang
          ([(84, 102), (94, 100), (106, 97)], 4.0),                # N-timur: dari celah gerbang sampai laut
          ([(72, 93), (70, 86), (72, 80), (69, 72), (66, 56), (63, 40), (60, 35)], 3.5),   # M: koridor barat | pesisir timur
          ([(70, 87), (52, 87), (36, 87), (26, 87)], 3.0),         # L: memaksa jalan memutar lewat tonjolan barat
          ([(51, 32), (44, 31), (36, 30)], 3.5)]                   # W: menutup koridor barat di utara (celah = barikade)
BARRICADE = (52, 59, 29, 36)            # kotak tile celah punggung W/M (barikade bajak laut, Quest Tengah)
WRECK = (73, 82, 77, 83)                # kotak tile celah sempit pesisir timur (perahu karam, jalan pintas setelah Kristal)
EXIT_T = (91, 12)                       # ujung dermaga keluar di teluk utara (exit layout (49,56) dipindah)
ARENA_T = (70, 22)                      # dermaga bajak laut = arena Kapten (boss_arena layout (53,67) dipindah)
PUZZLE_T = (53, 46)                     # warung pinggir jalan = stasiun antrean (puzzle layout (56,88) dipindah)
PREBOSS_T = (57, 26)
COAST_X = 106                           # garis pantai kota diluruskan: laut di timur x = 106 (baris 105-148), teluk kecil di selatannya
PIER_A = (102, 122, 115, 117)           # dermaga penumpang (x0, x1, y0, y1) tile, inklusif, menjorok dari jalan dermaga
PIER_B = (102, 118, 138, 140)           # dermaga ikan
DADANG_T = (93.1, 121.4)                # posisi Dadang di depan Kedai (ujung panah jalan pintas)
PIER_X = (82, 92, 11, 13)               # dermaga keluar (teluk utara)
DIRS8 = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PREFAB_SIZE = {}


# Titik petunjuk/peti yang dipindah karena tertutup pohon/rumah/NPC/awan (hasil tools/fix_clue_spots.tscn; px absolut).
SPOT_FIX = {'Petunjuk3': (840, 2282)}

def tp(dx, dy):
    """Titik (px) pada offset tile (dx, dy) dari pusat kota."""
    return (round(CX + dx * TILE), round(CY + dy * TILE))


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
    rng = random.Random(3003)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    P.update(exit=tpx(EXIT_T), boss_arena=tpx(ARENA_T), puzzle=tpx(PUZZLE_T), bonfire_preboss=tpx(PREBOSS_T))
    orig = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)
    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute: entry (barat) -> gerbang barat kota -> alun-alun ->
    # gerbang utara (celah punggung tebing) -> jalan pesisir layout -> puzzle -> Bonfire pra-boss -> arena -> exit
    gate_c = tp(0, -19)
    seg_in = winding(P["entry"], tp(-26, 0), 30, 31, n=5)
    seg_vil = organic.polyline_samples([tp(-26, 0), tp(0, 0), gate_c], 12.0)
    seg_w = np.vstack([organic.polyline_samples([gate_c, tpx((64, 95))], 12.0), winding(tpx((64, 95)), tpx((24, 93)), 18, 33, n=5),
                       winding(tpx((24, 93)), tpx((13, 82)), 12, 34, n=3)])
    seg_c = np.vstack([winding(tpx((13, 82)), tpx((46, 80)), 14, 35, n=4), winding(tpx((46, 80)), tpx((55, 62)), 22, 36, n=4),
                       winding(tpx((55, 62)), P["puzzle"], 18, 37, n=3)])
    seg_t = np.vstack([winding(P["puzzle"], tpx((55.5, 33)), 10, 38, n=3),
                       organic.polyline_samples([tpx((55.5, 33)), P["bonfire_preboss"], P["boss_arena"], tpx((PIER_X[0], 12)), P["exit"]], 12.0)])
    route = np.vstack([seg_in, seg_vil, seg_w, seg_c, seg_t])

    def route_i(pt):
        return idx_near(route, pt)

    i_boss, i_exit = route_i(P["boss_arena"]), route_i(P["exit"])

    # ------------------------------------------------------------ laut (biru di *_layout.png + semua sel di timur mask), daratan
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch3_PelabuhanAntre_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 60
    for ty in range(H):     # label teks di atas laut pada gambar layout (abu-abu) = tetap laut
        xs = np.nonzero(mask[:, ty])[0]
        edge = xs.max() if len(xs) else (84 if ty < 40 else 116)
        sea_img[edge + 1:, ty] = True
    # pesisir kota diluruskan (kota tepi laut): pantai lurus di x = COAST_X, lalu teluk kecil melandai ke tanjung mercusuar
    force_land = np.zeros_like(mask)
    for ty in range(105, 161):
        cx_ = COAST_X if ty <= 148 else min(133, COAST_X + (ty - 148) * 2.3)
        for tx in range(95, W):
            sea_img[tx, ty] = tx > cx_
            force_land[tx, ty] = tx <= cx_
    land = (dilate(mask, 2) | force_land) & ~sea_img
    land |= (dist_to(gx, gy, seg_in[:8]) <= 3.2 * TILE) & ~sea_img
    land |= (np.hypot(gx - P["entry"][0], gy - P["entry"][1]) <= 3.5 * TILE) & ~sea_img
    nz_r = organic.smooth_noise(gx, gy, 19)
    ridge = np.zeros_like(mask)
    for pts, hw in RIDGES:
        ridge |= dist_to(gx, gy, organic.polyline_samples([tpx(p_) for p_ in pts], 12.0)) <= hw * TILE + 10 * nz_r
    land &= ~ridge
    land = dilate(erode(land, 1), 1) | (land & dilate(sea_img, 1))
    for x0, x1, y0, y1 in (BARRICADE, WRECK):      # celah penghalang selalu bisa dilalui (lalu ditutup StageBlocker)
        land[x0:x1 + 1, y0:y1 + 1] |= ~sea_img[x0:x1 + 1, y0:y1 + 1] & ~ridge[x0:x1 + 1, y0:y1 + 1]
    sea = sea_img & ~land
    plateau = ~land & ~sea
    # dermaga: papan di atas laut / pantai (tetap laut untuk autotile air, tetapi bisa dilalui)
    dock = np.zeros_like(mask)
    for x0, x1, y0, y1 in (PIER_A, PIER_B, PIER_X):
        dock[x0:x1 + 1, y0:y1 + 1] = True
    dock &= sea | dilate(sea, 3)
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

    # ------------------------------------------------------------ titik sudut air & pasir
    vxs = np.arange(W + 1)[:, None] * np.ones((1, H + 1), int)
    vys = np.arange(H + 1)[None, :] * np.ones((W + 1, 1), int)
    pad_sea = np.pad(sea, 1, mode="edge")
    water_v = pad_sea[:-1, :-1] & pad_sea[1:, :-1] & pad_sea[:-1, 1:] & pad_sea[1:, 1:]     # 4 sel di sekitar titik = laut
    # jarak sel ke laut (tile, lapis demi lapis sampai 8)
    dsea = np.full(sea.shape, 99.0)
    cur = sea.copy()
    dsea[cur] = 0
    for k in range(1, 9):
        nxt = dilate(cur, 1)
        dsea[nxt & ~cur] = k
        cur = nxt
    pad_d = np.pad(dsea, 1, mode="edge")
    dsea_v = np.minimum(np.minimum(pad_d[:-1, :-1], pad_d[1:, :-1]), np.minimum(pad_d[:-1, 1:], pad_d[1:, 1:]))
    vx = vxs * TILE * 1.0
    vy = vys * TILE * 1.0
    vn = organic.smooth_noise(vx, vy, 4)
    beach_v = dsea_v <= 3.0 + 2.2 * vn

    # ------------------------------------------------------------ gerbang & kabut
    band = land & ~face_m & (tcol >= GATE_X[0]) & (tcol <= GATE_X[1]) & (trow >= GATE_ROWS[0]) & (trow <= GATE_ROWS[1])
    # awan perbatasan menutup pangkal dermaga keluar (papan + pantai di sekitarnya)
    plug = (tcol >= PIER_X[0] - 3) & (tcol <= PIER_X[0] + 6) & (trow >= PIER_X[2] - 3) & (trow <= PIER_X[3] + 3) & ((land & ~face_m) | dock)
    walk_all = (land & ~face_m) | dock
    blk = {}
    for nm_b, (x0, x1, y0, y1) in (("barricade", BARRICADE), ("wreck", WRECK)):
        m_ = np.zeros_like(mask)
        m_[x0:x1 + 1, y0:y1 + 1] = True
        blk[nm_b] = m_ & land & ~face_m
    # penghalang = baris-baris tengah celah saja (cukup memotong jalan)
    bar_block = blk["barricade"] & (trow >= 32) & (trow <= 33)
    wreck_block = blk["wreck"] & (trow >= 80) & (trow <= 81)
    arena_ring = np.zeros_like(mask)
    corridor = land & ~face_m & ~band & ~plug & ~bar_block & ~wreck_block     # dataran yang boleh dihuni objek

    # ------------------------------------------------------------ jalan cabang (pasir) di kota & pinggiran
    LIGHT = tpx((110, 174))   # mercusuar (tanjung selatan)
    GROVE = tpx((52, 141))    # kebun kelapa (barat)
    FISH = tpx((103.5, 141))  # pasar ikan di pangkal dermaga ikan (sisi laut jalan dermaga)
    HARBOR = tpx((103, 112))  # loket tiket di pangkal dermaga penumpang
    road_l = winding(tpx((100, 150)), LIGHT, 20, 41, n=5)
    road_g = winding(tpx((58, 122)), GROVE, 20, 43, n=4)
    road_f = organic.polyline_samples([tpx((100, 141)), FISH], 12.0)
    # jalan kota: Jalan Pasar (barat-timur), jalan gerbang (utara), JALAN DERMAGA di tepi pantai, jalan selatan
    streets = np.vstack([organic.polyline_samples([tpx(a), tpx(b)], 12.0) for a, b in
                         (((50, 122), (101, 122)), ((72, 104), (72, 122)), ((100, 106), (100, 150)), ((60, 147), (100, 147)))])
    # pesisir timur = jalan pintas (pasir), dari aula arena turun ke celah perahu karam lalu ke gerbang kota
    short_route = organic.polyline_samples([P["boss_arena"], tpx((74, 36)), tpx((76, 56)), tpx((77.5, 70)), tpx((77.5, 80)),
                                            tpx((77, 90)), tpx((72, 97)), gate_c, tp(0, 0), tpx(DADANG_T)], 12.0)
    roads = np.vstack([route, road_l, road_g, road_f, streets, short_route[:-3]])
    vd = dist_to(vx, vy, roads)
    sand_v = beach_v | (vd <= 26 + 6 * vn)
    pads = [(tpx((79.5, 129)), 120), (HARBOR, 70), (FISH, 50), (LIGHT, 80), (GROVE, 50), (P["puzzle"], 70), (P["bonfire_preboss"], 46),
            (P["boss_arena"], 150), (P["entry"], 44), (tpx((PIER_X[0] - 2, 12)), 50)]
    for (px_, py_), rr in pads:
        sand_v |= np.hypot(vx - px_, vy - py_) <= rr + 10 * vn
    # titik sudut di sekitar sel laut harus pasir (tile air hanya bertepi pasir, tidak menyentuh rumput)
    sand_v |= dsea_v <= 1

    # ------------------------------------------------------------ peta tile
    stone = [(6, 10), (7, 10), (8, 10)]
    in_stone = np.zeros_like(mask)
    in_stone[50:102, 121:124] = True       # Jalan Pasar (barat-timur, dari jalan masuk barat ke jalan dermaga)
    in_stone[71:74, 103:124] = True        # jalan gerbang (ke celah punggung tebing utara)
    in_stone[99:102, 106:151] = True       # JALAN DERMAGA di sepanjang pantai
    in_stone[60:102, 146:149] = True       # jalan selatan (deretan rumah nelayan)
    in_stone[74:86, 125:134] = True        # alun-alun pasar (sumur, lapak)
    in_stone[102:105, 114:119] = True      # pangkal dermaga penumpang
    in_stone[102:105, 137:142] = True      # pangkal dermaga ikan
    deck = (np.abs(tcol - ARENA_T[0]) <= 9) & (np.abs(trow - ARENA_T[1]) <= 6) & land & ~face_m
    ground, stonec, cliffc, dockc, blockc = [], [], [], [], []
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
                    ground.append((tx, ty, 0, SAND[0][0], SAND[0][1]))
                else:
                    a_ = WATER_CORNER[wk]
                    ground.append((tx, ty, 2, a_[0], a_[1]))
                    if sum(wk) >= 2 and not dock[tx, ty]:
                        blockc.append((tx, ty, 0, 0, 0))
                if dock[tx, ty]:
                    p_ = PLANK[(tx * 3 + ty) % 3]
                    dockc.append((tx, ty, 2, p_[0], p_[1]))
                continue
            key = (int(sand_v[tx, ty]), int(sand_v[tx + 1, ty]), int(sand_v[tx, ty + 1]), int(sand_v[tx + 1, ty + 1]))
            if key == (0, 0, 0, 0):
                a_ = GRASS[h_ % len(GRASS)]
            elif key == (1, 1, 1, 1):
                a_ = SAND_DETAIL[h_ % 2] if h_ % 29 == 0 else SAND[0]
            else:
                a_ = CORNER_TILES[key]
            ground.append((tx, ty, 0, a_[0], a_[1]))
            if dock[tx, ty]:
                p_ = PLANK[(tx * 3 + ty) % 3]
                dockc.append((tx, ty, 2, p_[0], p_[1]))
            if in_stone[tx, ty] and corridor[tx, ty]:
                s_ = stone[(tx * 7 + ty * 3) % 3]
                stonec.append((tx, ty, 0, s_[0], s_[1]))
            elif deck[tx, ty] and not dock[tx, ty]:      # geladak papan dermaga bajak laut (arena)
                p_ = PLANK[(tx * 3 + ty) % 3]
                dockc.append((tx, ty, 2, p_[0], p_[1]))

    # ------------------------------------------------------------ scene
    sc = Scene()
    ts_coast = sc.ext_res("TileSet", "res://assets/tilesets/coast_tileset.tres")
    ts_world = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKapten.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/QueueCustomers.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    animal_script = sc.ext_res("Script", "res://scripts/world/Animal.gd")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")

    sc.node("Ch3_PelabuhanAntre", "Node2D", script=f'ExtResource("{script}")', chapter="3", music_name='"ch3_pelabuhan_antre"',
            boss_music_name='"boss"',
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")",
            shortcut_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in short_route[::4]) + ")",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_coast}")')
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(stonec), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Dermaga", "TileMapLayer", ".", tile_map_data=b64cells(dockc), tile_set=f'ExtResource("{ts_coast}")')
    sc.node("Tebing", "TileMapLayer", ".", tile_map_data=b64cells(cliffc), tile_set=f'ExtResource("{ts_coast}")')
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

    _open_cache = {}

    def open_spot(pt, clear=2, rmax=176):
        """Titik LAPANG terdekat untuk peti/petunjuk: tile dengan `clear` tile daratan bebas di sekelilingnya (tidak terjepit di kaki
        tebing / tepi air) DAN terjangkau dari pintu masuk wilayah (bukan kantong terisolasi). Kembali ke pt bila tak ketemu."""
        if "m" not in _open_cache:
            from collections import deque
            wk = walk_all
            seen = np.zeros_like(wk)
            sx, sy = int(P["entry"][0] // TILE), int(P["entry"][1] // TILE)
            seen[sx, sy] = True
            dq = deque([(sx, sy)])
            while dq:
                x_, y_ = dq.popleft()
                for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx_, ny_ = x_ + dx_, y_ + dy_
                    if 0 <= nx_ < W and 0 <= ny_ < H and wk[nx_, ny_] and not seen[nx_, ny_]:
                        seen[nx_, ny_] = True
                        dq.append((nx_, ny_))
            _open_cache["m"] = erode(corridor, clear) & seen
        m_ = _open_cache["m"]
        for r in [0] + list(range(8, rmax + 1, 8)):
            for a_ in range(0, 360, 20):
                x, y = round(pt[0] + math.cos(math.radians(a_)) * r), round(pt[1] + math.sin(math.radians(a_)) * r)
                tx_, ty_ = int(x // TILE), int(y // TILE)
                if 0 <= tx_ < W and 0 <= ty_ < H and m_[tx_, ty_] and not near_building(x, y, 22):
                    return (x, y)
        return (round(pt[0]), round(pt[1]))

    # ------------------------------------------------------------ KOTA PELABUHAN ANTRE (kota tepi laut)
    # Jalan Pasar (y 121-123) dari gerbang barat ke JALAN DERMAGA (x 99-101) di tepi pantai; dermaga penumpang & dermaga ikan
    # menjorok ke laut dari jalan dermaga. Deretan rumah menghadap jalan (pintu di selatan), alun-alun pasar di selatan Jalan Pasar,
    # gudang pelabuhan di antara alun-alun & jalan dermaga, jalan selatan dengan rumah nelayan.
    def at(x, y):
        """Titik (px) pada tile absolut (x, y), pecahan boleh."""
        return (round(x * TILE + 8), round(y * TILE + 8))

    houses = {"RumahWarga": ("Rumah_Loteng_Biru", (-10, -2.5)), "TokoPelabuhan": ("Toko_Merah", (7.5, -2.5)),
              "KedaiDadang": ("Rumah_Menara_Merah", (19, -2.5)), "RumahWulan": ("Rumah_Runcing_Biru", (-8, 10)),
              "RumahBahar": ("Rumah_Teras_Biru", (18, 22.5)), "RumahNelayan": ("Rumah_Runcing_Merah", (4, 22.5)),
              "RumahPelaut": ("Toko_Hijau", (-9, 22.5))}
    for name, (pref, (dx, dy)) in houses.items():
        prefab(name, pref, tp(dx, dy))
    prefab("GudangPelabuhan", "Gudang_Panjang", tp(20.5, 11))
    # alun-alun pasar: sumur, lapak tenda, keranjang, lampu, spanduk
    prefab("Sumur", "Sumur", at(79.5, 129))
    for nm, pref, (x, y) in (("LapakTendaMerah", "Lapak_Tenda_Merah", (75.8, 126.8)), ("LapakTendaKuning", "Lapak_Tenda_Kuning", (83.2, 126.8)),
                             ("LapakIkan", "Lapak_Kain", (75.8, 131.8)), ("LapakSayur", "Lapak_Sayur", (83.2, 131.8)),
                             ("AlunKeranjang1", "Keranjang_Buah_1", (77.6, 133.0)), ("AlunKeranjang2", "Keranjang_Buah_2", (81.4, 133.0))):
        prefab(nm, pref, at(x, y))
    for i, (x, y) in enumerate(((73.4, 124.6), (85.6, 124.6), (73.4, 134.2), (85.0, 134.6), (69.6, 112.0),
                                (102.4, 110.0), (102.4, 124.0), (102.4, 132.0), (102.4, 146.0))):
        prefab(f"Lampu{i}", "Lampu_Tiang", at(x, y))
    for i, (x, y, k) in enumerate(((74.6, 124.8, 1), (84.6, 124.8, 2))):
        prefab(f"Spanduk{i}", f"Spanduk_{k}", at(x, y), solid=False)
    prefab("KedaiTong1", "Barel_Besar", at(98.0, 117.4))
    # pagar pekarangan rumah warga (kedai & toko terbuka)
    fence_w = PREFAB_SIZE["Pagar_Kayu"][0]
    for name, (pref, (dx, dy)) in houses.items():
        if name in ("KedaiDadang", "TokoPelabuhan"):
            continue
        fy = dy + 1.1
        hw = PREFAB_SIZE[pref][0] / (2 * TILE) + 0.2          # pagar selebar rumah
        ddx = dx + DOOR_DX.get(pref, 0) / TILE                 # celah pagar di depan pintu
        left, right, gap = dx - hw, dx + hw, 1.7
        n = 0
        for x0, x1 in ((left, ddx - gap), (ddx + gap, right)):
            x = x0 * TILE
            while x + fence_w / 2 <= x1 * TILE + 8:
                prefab(f"Pagar_{name}_{n}", "Pagar_Kayu", (round(CX + x + fence_w / 2), round(CY + fy * TILE)), solid=False)
                x += fence_w
                n += 1
        prefab(f"Tiang_{name}_L", "Tiang_Pagar", (round(CX + left * TILE), round(CY + fy * TILE)), solid=False)
        prefab(f"Tiang_{name}_R", "Tiang_Pagar", (round(CX + right * TILE), round(CY + fy * TILE)), solid=False)
    prefab("PapanBarat", "Papan_Kiri", at(47.4, 119.2), solid=False)
    prefab("PapanTimur", "Papan_Kanan", at(98.2, 120.4), solid=False)
    prefab("PapanUtara", "Papan_Tiang", at(69.2, 107.8), solid=False)
    prefab("PapanSelatan", "Papan_Tiang", at(70.4, 144.8), solid=False)
    for i, (x, y) in enumerate(((52.0, 124.6), (70.0, 124.6), (69.6, 118.0), (73.0, 135.4))):
        prefab(f"Lentera{i}", "Lentera_Tiang", at(x, y), solid=False)

    # ---- pelabuhan: loket tiket & tali antrean di pangkal dermaga penumpang, peti kargo, kapal layar & perahu
    hx, hy = HARBOR
    prefab("LoketTiket", "Lapak_Tenda_Kuning", at(103.6, 112.4))
    for k in range(4):   # tiang tali antrean (barisan penumpang menuju loket)
        prefab(f"TaliAntrean{k}", "Tiang_Pagar", at(105.3, 106.8 + k * 1.4), solid=False)
    for k, (pref, (x, y)) in enumerate((("Peti_Tumpuk_2", (102.6, 120.2)), ("Peti_Tumpuk_1", (105.0, 120.6)), ("Peti_Tong", (103.4, 122.6)),
                                        ("Peti_Kayu_A", (105.2, 123.4)), ("Tong_Peti", (102.8, 127.6)), ("Barel_Besar", (105.0, 128.4)))):
        prefab(f"Kargo{k}", pref, at(x, y))
    def on_water(pref, target):
        """Titik kaki terdekat dari target (tile) yang seluruh tapak sprite-nya di atas air terbuka (bukan dermaga)."""
        w, h = PREFAB_SIZE[pref]
        wt, ht = math.ceil(w / TILE / 2) + 1, min(3, math.ceil(h / TILE) + 1)    # lambung saja (layar boleh menutupi apa pun)
        best = None
        for ty in range(target[1] - 12, target[1] + 13):
            for tx in range(target[0] - 12, target[0] + 13):
                x0, x1, y0 = tx - wt, tx + wt, ty - ht
                if x0 < 0 or x1 >= W or y0 < 0 or ty + 1 >= H:
                    continue
                if (sea[x0:x1 + 1, y0:ty + 2] & ~dilate(dock, 1)[x0:x1 + 1, y0:ty + 2]).all():
                    d_ = math.hypot(tx - target[0], ty - target[1])
                    if best is None or d_ < best[0]:
                        best = (d_, tx, ty)
        return (best[1] * TILE + 8, best[2] * TILE + 12) if best else None

    ax0, ax1, ay0, ay1 = PIER_A
    bx0, bx1, by0, by1 = PIER_B
    for nm, pref, tgt in (("KapalLayar", "Kapal_Layar", (ax1 - 2, ay1 + 4)), ("KapalBajakLaut", "Kapal_Layar", (92, 24)),
                          ("KapalDadang", "Kapal_Layar", (PIER_X[1] - 3, PIER_X[2] - 4)), ("PerahuIkan1", "Perahu_Kecil", (bx0 + 7, by0 - 2)),
                          ("PerahuIkan2", "Perahu_Kecil", (bx0 + 9, by1 + 3)), ("PerahuPantai", "Perahu_Kecil", (112, 108))):
        q_ = on_water(pref, tgt)
        if q_:
            prefab(nm, pref, q_, record=False)
        else:
            print("PERINGATAN: tidak ada air untuk", nm)
    fxp, fyp = FISH
    for k, (pref, (x, y)) in enumerate((("Lapak_Tenda_Merah", (104.2, 136.4)), ("Barel_Air", (102.4, 135.8)),
                                        ("Keranjang_Buah_1", (104.8, 143.6)), ("Peti_Kayu_A", (102.6, 144.0)))):
        prefab(f"PasarIkan{k}", pref, at(x, y))

    # ---- pinggiran 1: MERCUSUAR (tanjung selatan)
    lx, ly = LIGHT
    prefab("Mercusuar", "Menara_Kubah", (lx + 4, ly - 6))
    for k, (pref, (ox, oy), sol) in enumerate((("Batu_Besar_1", (-58, -10), True), ("Batu_Sedang_1", (52, 14), True),
                                               ("Kerang_1", (-30, 40), False), ("Kerang_2", (40, 44), False),
                                               ("Batu_Sedang_2", (-70, 34), True), ("Palem_1", (64, -40), True))):
        prefab(f"Tanjung{k}", pref, (lx + ox, ly + oy), solid=sol)
    # ---- pinggiran 2: KEBUN KELAPA (barat) - rumpun palem, keranjang kelapa
    gx0, gy0 = GROVE
    for k, (pref, (ox, oy)) in enumerate((("Palem_Rumpun_1", (-80, -50)), ("Palem_Rumpun_2", (70, -60)), ("Palem_1", (-96, 30)),
                                          ("Palem_2", (90, 24)), ("Palem_Rumpun_1", (-20, -96)), ("Palem_2", (20, 70)),
                                          ("Keranjang_Buah_2", (-44, 20)), ("Palem_1", (-60, 86)))):
        prefab(f"Kebun{k}", pref, (gx0 + ox, gy0 + oy))

    # ------------------------------------------------------------ NPC & penanda
    _kp, (_kdx, _kdy) = houses["KedaiDadang"]
    door_x, door_y = tp(_kdx + DOOR_DX.get(_kp, 0) / TILE, _kdy)
    npc_positions = []

    def npc(name, pos, **props):
        inst(name, npc_scene, pos, **props)
        npc_positions.append(pos)

    dadang_pos = (door_x + 40, door_y + 22)
    npc("Dadang", dadang_pos, npc_id='"dadang"')
    wulan_pos, nina_pos, bahar_pos = at(103.6, 113.8), at(104.4, 108.6), at(104.0, 141.8)
    npc("Wulan", wulan_pos, npc_id='"wulan"', dialog_id='"ch3_wulan"', villager_chapter="3")
    npc("Nina", nina_pos, npc_id='"nina"', dialog_id='"ch3_nina"', villager_chapter="3")
    npc("Bahar", bahar_pos, npc_id='"bahar"', dialog_id='"ch3_bahar"', villager_chapter="3")
    npc("Pedagang", at(78.0, 120.3), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuKedai", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_KedaiDadang.tscn"', hint_text='"E: Masuk Kedai Dadang"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuKedai", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    start = tuple(int(v) for v in route[6])
    bf1 = at(71.0, 129.5)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("BenderaMasuk", checkpoint_scene, (int(route[14][0]), int(route[14][1]) + 36))
    inst("BenderaGerbang", checkpoint_scene, tp(4.2, -14.5))
    inst("BenderaDermaga", checkpoint_scene, at(102.6, 107.0))
    inst("PetiMercusuar", chest_scene, open_spot((lx - 80, ly - 50)), roll_count="2")
    inst("PetiKebun", chest_scene, open_spot((gx0 + 10, gy0 - 60)), roll_count="2")
    clue_pts = [open_spot((lx - 28, ly + 8)), ((bx1 - 1) * TILE + 8, (by0 + 1) * TILE + 8), open_spot((gx0, gy0 + 18))]
    for k_, (ck, pos) in enumerate(zip(("barang", "catatan", "jejak"), clue_pts), start=1):
        pos = SPOT_FIX.get(f"Petunjuk{k_}", pos)
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*pos),
                flag=f'"ch3_petunjuk_{k_}"', dialog_id=f'"ch3_petunjuk_{k_}"', required_step='"ch3_awal:petunjuk"', clue_kind=f'"{ck}"')
        recorded.append(pos)
        npc_positions.append(pos)

    # ---- perjalanan: warung pinggir jalan (stasiun antrean), Bonfire, bendera, dermaga bajak laut, dermaga keluar
    mx, my = P["puzzle"]
    inst("StasiunAntrean", station_scene, (int(mx), int(my) + 36), puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="3",
         station_label='"Antrean Pelanggan"')
    for k, (pref, (ox, oy), sol) in enumerate((("Lapak_Tenda_Merah", (-54, -14), True), ("Lapak_Tenda_Kuning", (50, -16), True),
                                               ("Barel_Besar", (-80, 8), True), ("Keranjang_Buah_1", (74, 10), True),
                                               ("Dapur_Panggangan_Kecil", (-10, -40), True), ("Peti_Kayu_A", (84, -30), True))):
        prefab(f"Warung{k}", pref, (int(mx) + ox, int(my) + oy), solid=sol)
    for k in range(5):   # tali antrean pelanggan warung
        prefab(f"TaliWarung{k}", "Tiang_Pagar", (int(mx) - 52 + k * 26, int(my) + 70), solid=False)
    bf_pre = (int(P["bonfire_preboss"][0]) - 30, int(P["bonfire_preboss"][1]) + 20)
    bf_mid = tpx((40, 80.5))
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf_mid)
    flags = {"BenderaLobus": tpx((18, 90)), "BenderaKoridor": tpx((50, 64)), "BenderaUtara": tpx((52, 24))}
    for nm_f, pos in flags.items():
        inst(nm_f, checkpoint_scene, pos)
    inst("PulangTambang", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="2", sign_text='"Kembali ke Tambang Tumpuk"')
    inst("KeGua", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="4", sign_text='"Kapal Dadang: ke Gua Rantai"')
    npc_positions += [bf1, bf_pre, bf_mid, start, (int(mx), int(my) + 36), P["boss_arena"], HARBOR, FISH] + list(flags.values())
    # dermaga bajak laut: tong & peti rampasan di tepi geladak, obor, kapal bajak laut bersandar
    ax_, ay_ = (int(v) for v in P["boss_arena"])
    for k, (pref, (ox, oy)) in enumerate((("Peti_Tumpuk_2", (-150, -70)), ("Tong_Peti", (-120, -84)), ("Peti_Tong", (150, -74)),
                                          ("Barel_Besar", (126, -86)), ("Peti_Tumpuk_1", (-156, 84)), ("Barel_Air", (154, 86)))):
        prefab(f"Rampasan{k}", pref, (ax_ + ox, ay_ + oy))
    flam_arena = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")
    for k in range(6):
        ang = math.pi * 0.15 + k * math.tau / 6
        fx_, fy_ = round(ax_ + math.cos(ang) * 130), round(ay_ + math.sin(ang) * 80)
        prefab(f"TiangObor{k}", "Lentera_Tiang", (fx_, fy_ + 4), solid=False)
        sc.node(f"OborArena{k}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_arena}")',
                position=v2(fx_, fy_ - 26), frame_w="20", frame_h="30", fps="9.0")

    # penghalang tumpukan objek (scripts/world/StageBlocker.gd)
    blocker_script = sc.ext_res("Script", "res://scripts/world/StageBlocker.gd")

    def blocker(name, cells, mode, stage, text, pieces, opened=""):
        xs, ys = np.nonzero(cells)
        c0 = (int(xs.mean()) * TILE + 8, int(ys.max() + 1) * TILE)
        sc.node(name, "Node2D", "Objects", script=f'ExtResource("{blocker_script}")', position=v2(*c0), y_sort_enabled="true",
                mode=f'"{mode}"', chapter="3", required_stage=str(stage), locked_text=f'"{text}"', opened_text=f'"{opened}"',
                hint_size=f"Vector2({(xs.max() - xs.min() + 9) * TILE}, {(ys.max() - ys.min() + 9) * TILE})")
        for k, (pref, (ox, oy)) in enumerate(pieces):
            pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
            sc.node(f"{name}{k}", None, f"Objects/{name}", instance=pid, position=v2(ox, oy))
        cells_l = [(int(x) - (c0[0] - 8) // TILE, int(y) - c0[1] // TILE, 0, 0, 0) for x, y in zip(xs, ys)]
        sc.node("Block", "TileMapLayer", f"Objects/{name}", position=v2(-8, 0), tile_map_data=b64cells(cells_l),
                tile_set=f'ExtResource("{block_ts}")')
        recorded.append(c0)
        return c0

    bar_c = blocker("BarikadeBajakLaut", bar_block, "stage", 2, "Barikade bajak laut menutup jalan ke dermaga.\nBantu warung antrean dulu.",
                    [("Peti_Tumpuk_2", (-30, -18)), ("Tong_Peti", (-6, -8)), ("Peti_Tumpuk_3", (18, -16)), ("Peti_Tong", (36, 0)),
                     ("Barel_Besar", (-44, 2))],
                    "Para pelanggan membantu menyingkirkan barikade.\nJalan ke dermaga bajak laut terbuka.")
    wreck_c = blocker("PerahuKaram", wreck_block, "crystal", 3, "Perahu karam & jaring menutup pesisir.\nMungkin terbuka setelah Kapten kalah.",
                      [("Perahu_Kecil", (-14, -6)), ("Peti_Tumpuk_1", (16, -2)), ("Tong_Peti", (-34, 4)), ("Batu_Sedang_1", (30, 6))],
                      "Ombak menyeret perahu karam.\nJalan pintas pesisir ke Kota Pelabuhan Antre terbuka.")
    npc_positions += [bar_c, wreck_c]

    def cloud_barrier(name, cells_mask, mode, dist, text="", **props):
        pts = thin_cells(cells_mask, dist)
        arr = ", ".join(f"{x}, {y}" for x, y in pts)
        extra = {"locked_text": '"%s"' % text} if text else {}
        sc.node(name, "Node2D", ".", script=f'ExtResource("{cloud_script}")', mode=f'"{mode}"', chapter="3",
                cloud_points=f"PackedVector2Array({arr})", seed_value=str(rng.randint(1, 999)), **extra, **props)
        cells = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(cells_mask))]
        sc.node("Block", "TileMapLayer", name, tile_map_data=b64cells(cells), tile_set=f'ExtResource("{block_ts}")')

    MIST = "Color(0.92, 0.96, 1, 1)"
    cloud_barrier("AwanPerbatasan", plug, "chapter", 26, tint=MIST, scale_min="1.2", scale_max="1.6")
    cloud_barrier("AwanGerbangKota", band, "stage", 40, "Kabut laut tebal menutup jalan pesisir.\nBantu Dadang dulu.",
                  required_stage="1", tint=MIST, scale_min="1.3", scale_max="1.9")

    # ------------------------------------------------------------ dekorasi: rumpun palem, semak, batu
    d_route = dist_to(gx, gy, roads)

    def road_dist(x, y):
        tx_, ty_ = int(x // TILE), int(y // TILE)
        return float(d_route[tx_, ty_]) if 0 <= tx_ < W and 0 <= ty_ < H else 0.0

    village_zone = (tcol >= 47) & (tcol <= COAST_X + 1) & (trow >= 104) & (trow <= 151)     # kota: bebas dekorasi acak
    keypts = [P[k] for k in ("entry", "puzzle", "bonfire_preboss", "boss_arena", "exit")] + [bf1, bf_pre, start, LIGHT, GROVE, FISH, HARBOR] \
        + npc_positions
    no_deco = dilate(dock | band | plug | blk["barricade"] | blk["wreck"] | deck, 3) \
        | (np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 12 * TILE) \
        | (np.hypot(gx - GROVE[0], gy - GROVE[1]) < 9 * TILE) | (np.hypot(gx - LIGHT[0], gy - LIGHT[1]) < 7 * TILE)

    def fits(pref, x, y, margin=10):
        w, h = PREFAB_SIZE[pref]
        for ox, oy in ((-w / 2 - margin, 0), (w / 2 + margin, 0), (-w / 2 - margin, -h), (w / 2 + margin, -h), (0, margin), (0, -h / 2)):
            tx_, ty_ = int((x + ox) // TILE), int((y + oy) // TILE)
            if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or village_zone[tx_, ty_] or no_deco[tx_, ty_]:
                return False
        if road_dist(x, y) < w / 2 + 40 or road_dist(x, y - h / 2) < w / 2 + 40:
            return False
        if any(math.hypot(x - kx, y - ky) < 90 for kx, ky in keypts):
            return False
        return not near_building(x, y, 18)

    # ------------------------------------------------------------ DAERAH BARAT (tonjolan barat, jalan sempit selatan, koridor barat):
    # landmark kecil supaya perjalanan tidak kosong + dekorasi rapat. Titik dicari dekat target (spiral 80 px), tapak di daratan bebas.
    def fits_lm(pref, x, y, road_min):
        w, h = PREFAB_SIZE[pref]
        for ox, oy in ((-w / 2, 0), (w / 2, 0), (-w / 2, -h * 0.7), (w / 2, -h * 0.7), (0, 4), (0, -h / 2)):
            tx_, ty_ = int((x + ox) // TILE), int((y + oy) // TILE)
            if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or village_zone[tx_, ty_] or no_deco[tx_, ty_]:
                return False
        return road_dist(x, y) >= road_min + w / 2 and not near_building(x, y, 4) \
            and all(math.hypot(x - kx, y - ky) >= 44 for kx, ky in keypts)

    def lm(name, pref, tile, solid=True, road_min=14):
        bx_, by_ = at(*tile)
        for r in [0] + list(range(8, 81, 8)):
            for a_ in range(0, 360, 30):
                x, y = round(bx_ + math.cos(math.radians(a_)) * r), round(by_ + math.sin(math.radians(a_)) * r)
                if fits_lm(pref, x, y, road_min):
                    prefab(name, pref, (x, y), solid=solid)
                    if not solid:
                        buildings.append((x, y, PREFAB_SIZE[pref][0], 10))
                    return (x, y)
        return None

    n_lm = 0
    landmarks = {
        # kemah bajak laut di tonjolan barat (kelompok Lobus1 berjaga di dekatnya)
        "KemahBajak": [("Tenda_1", (5.5, 86.5)), ("Tenda_3", (10.5, 85.6)), ("Peti_Tumpuk_2", (3.6, 90.4)), ("Tong_Peti", (11.8, 90.6)),
                       ("Barel_Besar", (4.0, 93.2)), ("Peti_Kayu_B", (8.8, 93.6)), ("Tumpukan_Kayu", (13.6, 88.2))],
        # reruntuhan pos jaga di ujung barat laut tonjolan
        "PosJaga": [("Ruina_3", (6.0, 79.5)), ("Puing_Pilar", (10.4, 78.6)), ("Puing_Batu", (2.8, 80.8)), ("Batu_Besar_1", (13.2, 80.2))],
        # reruntuhan rumah & sumur tua di bagian lebar koridor barat (sisi timur jalan)
        "RumahTua": [("Ruina_4", (60.5, 69.5)), ("Puing_Kayu", (57.6, 72.6)), ("Ruina_2", (61.0, 63.0)), ("Kotak_Rusak", (58.4, 66.2))],
        # kemah penebang di sisi barat koridor
        "KemahPenebang": [("Tunggul_Kapak", (44.2, 69.0)), ("Tronk_Kayu", (46.0, 72.6)), ("Tumpukan_Kayu", (42.6, 73.8)),
                          ("Tunggul_Besar", (43.6, 65.4)), ("Tenda_2", (47.0, 63.4))],
        # gerobak rusak & tumpukan barang di jalan sempit selatan (di tepi, tidak menutup jalan)
        "Gerobak": [("Kotak_Rusak", (31.0, 96.2)), ("Barel_Air", (33.2, 96.4)), ("Peti_Kayu_A", (35.0, 96.0)),
                    ("Tunggul_Besar", (52.0, 92.2)), ("Batu_Besar_2", (14.6, 95.6))],
    }
    for grp, items in landmarks.items():
        for k, (pref, tile) in enumerate(items):
            if lm(f"{grp}{k}", pref, tile, solid=not pref.startswith(("Puing_Batu", "Kotak_Rusak"))):
                n_lm += 1
    for nm_f, tile, w_ in (("ApiKemahBajak", (8.0, 89.4), 20), ("ApiKemahPenebang", (45.6, 68.0), 20)):
        q_ = lm(f"Tripod{nm_f}", "Dapur_Tripod", tile, road_min=10)
        if q_:
            sc.node(nm_f, "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_arena}")',
                    position=v2(q_[0], q_[1] - 2), frame_w="20", frame_h="30", fps="9.0", modulate="Color(1, 1, 1, 0.9)")
    # lentera & papan di tepi jalan daerah barat (tiap ~14 tile)
    west = [(x, y) for x, y in route if x < 70 * TILE and 36 * TILE < y < 99 * TILE]
    for k in range(0, len(west), 19):
        x, y = west[k]
        for side in (1, -1):
            if lm(f"LenteraBarat{k}", "Lentera_Tiang", (x / TILE - 0.5 + side * 1.6, y / TILE - 0.5), solid=False, road_min=-6):
                break
    lm("PapanLobus", "Papan_Kiri", (22.0, 80.0), solid=False, road_min=-4)
    lm("PapanKoridor", "Papan_Tiang", (47.5, 78.6), solid=False, road_min=-4)
    # vegetasi rapat daerah barat: rumpun palem + semak/batu kecil (jarak antar-rumpun lebih rapat dari dekorasi umum)
    west_big = ["Palem_Rumpun_1", "Palem_Rumpun_2", "Palem_1", "Palem_2", "Semak_Pantai"]
    west_small = ["Semak_Pantai", "Palem_Kecil", "Batu_Sedang_1", "Batu_Sedang_2", "Palem_Kecil", "Batu_Besar_2"]
    wcl = []
    for _try in range(6000):
        if len(wcl) >= 70:
            break
        x, y = rng.randint(24, 72 * TILE), rng.randint(28 * TILE, 99 * TILE)
        if any(math.hypot(x - cx2, y - cy2) < 96 for cx2, cy2 in wcl):
            continue
        pref = rng.choice(west_big)
        if not fits_lm(pref, x, y, 22):
            continue
        wcl.append((x, y))
        prefab(f"Barat{n_lm}", pref, (x, y))
        n_lm += 1
        for _k in range(rng.randint(1, 3)):
            p3 = rng.choice(west_small)
            ang = rng.random() * math.tau
            x3, y3 = round(x + math.cos(ang) * rng.randint(30, 64)), round(y + math.sin(ang) * rng.randint(18, 40))
            if fits_lm(p3, x3, y3, 12):
                prefab(f"Barat{n_lm}", p3, (x3, y3), solid=not p3.startswith(("Palem_Kecil", "Batu_Sedang")))
                n_lm += 1
    print("daerah barat: landmark + dekorasi", n_lm)

    big = ["Palem_Rumpun_1", "Palem_Rumpun_2", "Palem_Rumpun_1", "Palem_1", "Palem_2"]
    small = ["Palem_1", "Palem_2", "Semak_Pantai", "Batu_Sedang_1", "Batu_Besar_2", "Palem_Kecil"]
    clusters, nm_ = [], 0
    for _try in range(9000):
        if len(clusters) >= 85:
            break
        x, y = rng.randint(80, PX_W - 80), rng.randint(120, PX_H - 60)
        if any(math.hypot(x - cx2, y - cy2) < 170 for cx2, cy2 in clusters):
            continue
        pref = rng.choice(big)
        if not fits(pref, x, y):
            continue
        clusters.append((x, y))
        prefab(f"Palem{nm_}", pref, (x, y))
        nm_ += 1
        for _k in range(rng.randint(2, 4)):
            p3 = rng.choice(small)
            ang = rng.random() * math.tau
            x3, y3 = round(x + math.cos(ang) * rng.randint(40, 90)), round(y + math.sin(ang) * rng.randint(24, 56))
            if fits(p3, x3, y3, 2):
                prefab(f"Palem{nm_}", p3, (x3, y3))
                nm_ += 1
    # kerang & kerikil di pantai (tanpa tabrakan)
    for k in range(110):
        x, y = rng.randint(60, PX_W - 60), rng.randint(80, PX_H - 60)
        tx_, ty_ = int(x // TILE), int(y // TILE)
        if not (corridor[tx_, ty_] and dsea[tx_, ty_] <= 4) or no_deco[tx_, ty_] or near_building(x, y, 20) \
                or any(math.hypot(x - kx, y - ky) < 60 for kx, ky in keypts):
            continue
        prefab(f"Kerang{k}", rng.choice(["Kerang_1", "Kerang_2", "Batu_Sedang_2"]), (x, y), solid=False)
        buildings.append((x, y, 16, 12))

    # hewan kota (ayam, anjing, kucing)
    animals = [("Chicken/SpriteSheetWhite", at(70.5, 138.0)), ("Chicken/SpriteSheetBrown", at(68.0, 140.5)),
               ("Chicken/SpriteSheetWhite", at(56.0, 126.5)), ("Dog/SpriteSheet", at(70.0, 115.0)), ("Cat/SpriteSheet", at(56.5, 121.4)),
               ("Cat/SpriteSheet", at(99.2, 111.4))]
    na = 0
    for sheet_, pos in animals:
        tex_path = os.path.join(ROOT, "assets/ninja/animals", sheet_ + ".png")
        if not os.path.exists(tex_path):
            alt = [f for f in os.listdir(os.path.dirname(tex_path)) if f.endswith(".png")]
            if not alt:
                continue
            sheet_ = os.path.dirname(sheet_) + "/" + alt[0][:-4]
        tex = sc.ext_res("Texture2D", f"res://assets/ninja/animals/{sheet_}.png")
        bscale = 1.0 if sheet_.startswith(("Chicken", "Cat")) else 1.2
        sc.node(f"Hewan{na}", "Node2D", "Objects", script=f'ExtResource("{animal_script}")', sheet=f'ExtResource("{tex}")',
                position=v2(*pos), body_scale=str(bscale), wander_radius="50.0")
        na += 1
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', leaves="false", ray_alpha="0.10")

    # ------------------------------------------------------------ collectible pinggiran kota (aman, tanpa musuh di Tahap 1)
    nl = 0
    for nm, (bx_, by_) in (("Herb", (GROVE[0] - 40, GROVE[1] + 50)), ("Herb", (GROVE[0] + 56, GROVE[1] - 10)),
                           ("GoldCoin", (LIGHT[0] + 30, LIGHT[1] - 40)), ("GoldCoin", (FISH[0] - 30, FISH[1] + 60)),
                           ("Herb", (LIGHT[0] - 90, LIGHT[1] + 10)), ("Potion", at(98.0, 108.5))):
        tx_, ty_ = int(bx_ // TILE), int(by_ // TILE)
        if corridor[tx_, ty_] and not near_building(bx_, by_, 6):
            nl += 1
            inst(f"Pinggir{nm}{nl}", collect[nm], (bx_, by_))

    # ------------------------------------------------------------ musuh, peti, collectible (perjalanan)
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    taken = []

    def spot(pt, r_min=20):
        """Titik bebas terdekat (spiral sampai 140 px) dari pt (px)."""
        for r in [0] + list(range(12, 141, 12)):
            for a_ in range(0, 360, 30):
                x, y = round(pt[0] + math.cos(math.radians(a_)) * r), round(pt[1] + math.sin(math.radians(a_)) * r)
                tx_, ty_ = int(x // TILE), int(y // TILE)
                if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or deck[tx_, ty_] or road_dist(x, y) < r_min:
                    continue
                if near_building(x, y, 14) or any(math.hypot(x - qx2, y - qy2) < 26 for qx2, qy2 in taken):
                    continue
                taken.append((x, y))
                return (round(x), round(y))
        return None

    # awak bajak laut (Orc) & slime pantai. Zona aman: semua kelompok di utara punggung tebing kota.
    groups = {"Lobus1": ((13, 84), ["orc_rogue", "orc", "orc_rogue"]),
              "Lobus2": ((32, 80), ["orc", "orc_shaman", "slime2"]),
              "Koridor1": ((52, 71), ["orc_warrior", "orc_rogue", "orc"]),
              "Koridor2": ((57, 57), ["orc_rogue", "orc_shaman", "orc_warrior"]),
              "Koridor3": ((48, 52), ["slime3", "orc_rogue"]),
              "Utara1": ((56, 14), ["orc_warrior", "orc_shaman", "orc_rogue"]),
              "Utara2": ((96, 28), ["orc", "orc_rogue", "orc_warrior"]),
              "Pesisir1": ((78, 62), ["slime2", "slime3", "slime2"]),
              "Pesisir2": ((80, 44), ["orc_rogue", "orc"])}
    n_mob = 0
    for gname, ((gx_t, gy_t), ids) in groups.items():
        for k, eid in enumerate(ids):
            ang = k * math.tau / len(ids) + 0.5
            q = spot((gx_t * TILE + 8 + math.cos(ang) * 34, gy_t * TILE + 8 + math.sin(ang) * 26))
            if q:
                inst(f"Musuh{gname}_{k + 1}", enemy_scene, q, enemy_id=f'"{eid}"')
                n_mob += 1
    chests = {"PetiLobus": (6, 92), "PetiKoridor": (45, 62), "PetiPesisirSelatan": (82, 90), "PetiUtara": (52, 9), "PetiTanjungUtara": (108, 22)}
    for nm, (cx2, cy2) in chests.items():
        q = open_spot(tpx((cx2, cy2)))
        if not q:
            print("PERINGATAN: peti", nm, "tidak dapat tempat")
            continue
        inst(nm, chest_scene, q, roll_count="2")
        for kind, (ox, oy) in (("Herb", (30, 14)), ("GoldCoin", (-28, 16)), ("Herb" if cy2 > 40 else "Ore", (2, 34))):
            q2 = spot((q[0] + ox, q[1] + oy), 0)
            if q2:
                nl += 1
                inst(f"{kind}{nl}", collect[kind], q2)
    i_gate, i_boss2 = route_i(gate_c), route_i(P["boss_arena"])
    for k in range(26):
        i_ = rng.randint(i_gate + 10, i_boss2)
        th = rng.random() * math.tau
        pt = (route[i_][0] + math.cos(th) * rng.randint(50, 130), route[i_][1] + math.sin(th) * rng.randint(40, 100))
        q = spot(pt, 30)
        if q:
            kind = ("Herb", "GoldCoin", "Herb", "Ore")[k % 4]
            nl += 1
            inst(f"{kind}{nl}", collect[kind], q)
    for k, pt in enumerate((tpx((30, 82)), tpx((58, 30)))):
        q = spot(pt, 24)
        if q:
            inst(f"Potion{k + 1}", collect["Potion"], q)

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    fn = tpx((PIER_X[0] - 3, 12))
    sc.node("FromNext", "Marker2D", ".", position=v2(int(fn[0]), int(fn[1])))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Dadang", "Marker2D", "NPCSpawns", position=v2(*dadang_pos), **{"metadata/npc_id": '"dadang"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')

    out = os.path.join(ROOT, "scenes/world/Ch3_PelabuhanAntre.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ uji keterhubungan (grid tile, objek padat diabaikan)
    blocked = np.zeros_like(mask)
    for x, y, *_ in blockc:
        blocked[x, y] = True
    walk = walk_all & ~blocked

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
    r_gate = reach(band | plug | bar_block | wreck_block)
    r_open = reach(plug | bar_block | wreck_block)
    r_all = reach(plug | wreck_block)
    r_short = reach(bar_block | plug)
    clue_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in clue_pts)
    npc_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in (dadang_pos, wulan_pos, nina_pos, bahar_pos))
    print("start di daratan =", bool(walk[int(start[0] // TILE), int(start[1] // TILE)]),
          "| kota, 4 NPC & 3 petunjuk terjangkau saat gerbang tertutup =", bool(r_gate[C]) and clue_ok and npc_ok)
    print("gerbang kota mengunci puzzle =", not r_gate[t_["puzzle"]], "| puzzle terjangkau saat terbuka =", bool(r_open[t_["puzzle"]]))
    print("barikade mengunci boss =", not r_open[t_["boss_arena"]], "| boss terjangkau saat terbuka =", bool(r_all[t_["boss_arena"]]),
          "| jalan pintas pesisir (perahu karam dibuka) menembus ke arena =", bool(r_short[t_["boss_arena"]]))
    print("awan perbatasan mengunci exit =", not reach(wreck_block | plug)[t_["exit"]], "| exit terjangkau saat terbuka =",
          bool(reach(np.zeros_like(walk))[t_["exit"]]))
    length = float(np.sum(np.hypot(*np.diff(route[route_i(tp(0, 0)):route_i(P["boss_arena"])], axis=0).T))) / TILE
    print("musuh:", n_mob, "| jalan kota->arena %.0f tile" % length)
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and walk_all[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Ch3_PelabuhanAntre.tscn:", nm_, "palem/semak/batu, objek di luar daratan:", len(bad), bad[:6],
          "| koridor", int(corridor.sum()), "tile | dermaga", int(dock.sum()), "tile | collectible", nl)
    return bad


if __name__ == "__main__":
    build()
