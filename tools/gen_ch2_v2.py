"""Generator Ch2_TambangTumpuk.tscn v2: bentuk wilayah dari docs/layout/region_layout.json + KAMPUNG TUMPUK (blueprint grid).

Jalankan dari folder proyek (setelah make_prefabs.py, make_villagers.py, gen_canyon_tileset.py, gen_interior.py):
    python tools/gen_ch2_v2.py
Tahap 1 (bagian ini): peta 161x161 tile, batas ngarai, Kampung Tumpuk + pinggiran + 3 petunjuk, gerbang kabut debu.
  - Lantai: pasir oranye; jalan = pasir terang bertepi (autotile sudut / marching squares, tools/gen_canyon_tileset.py).
  - Batas: laut di barat (biru pada *_layout.png), DATARAN TINGGI bertebing di luar mask (abu-abu = wilayah lain),
    awan perbatasan hanya di titik keluar ke Pelabuhan Antre (hilang setelah Chapter 2 selesai).
  - Dekorasi: kelompok MESA (prefab Mesa_*) + batu, tanpa rotasi/skala; semua objek prefab y-sort, origin di kaki.
Blueprint desa (tile, pusat C; X ke timur, Y ke selatan): alun-alun 12x12 batu + sumur, jalan batu 3 tile ke U/S/T/B,
  4 rumah di 4 kuadran, BENGKEL LILBAH di barat (landasan + tungku + meja kerja), GUDANG PETI di timur (lumbung + tumpukan peti),
  pinggiran: galian batu (barat), perkemahan penambang (selatan).
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
from gen_canyon_tileset import CORNER_TILES, LIGHT_DETAIL, MINE_CORNER, MINE_DETAIL, MINE_FLOOR, SAND  # noqa: E402
from gen_village import ROOT, TILE, Scene, v2  # noqa: E402

dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx
LAYOUT = json.load(open(os.path.join(ROOT, "docs/layout/region_layout.json"), encoding="utf-8"))["Ch2_TambangTumpuk"]
W, H = LAYOUT["ukuran_tile"]            # 161 x 161
PX_W, PX_H = LAYOUT["ukuran_px"]        # 2576 x 2576
C = tuple(LAYOUT["titik_tile"]["village_center"])   # (102, 96) pusat Kampung Tumpuk
CX, CY = C[0] * TILE + 8, C[1] * TILE + 8
GATE_ROW = C[1] - 17                    # baris tengah pita kabut debu gerbang desa (79)
MINE_MOUTH = (80, 48)                   # mulut tambang = stasiun puzzle tumpukan peti (titik_tile puzzle asli (84,67) dipindah)
TUNNEL_Y = 47.5                         # baris tengah lorong tambang (baris 45-50, 4 baris bisa dilalui di bawah wajah tebing)
TUNNEL_X = (86, 98)                     # lorong menembus punggung tebing C
SHORTCUT_X = (106, 111)                 # celah longsoran di punggung tebing A = jalan pintas aula -> desa (terbuka setelah Kristal)
# punggung tebing (dataran tinggi di DALAM wilayah, tile): (polyline, setengah lebar)
RIDGES = [([(93, 66), (110, 66), (130, 65), (156, 66)], 3.2),      # A: memisahkan aula tambang dari kantong utara desa
          ([(92, -2), (92, 30), (92, 44), (92, 66)], 3.0),         # C: dinding barat aula tambang (ditembus lorong)
          ([(66, 61), (80, 62), (92, 62)], 2.6)]                   # D: memaksa jalan memutar lewat ngarai barat
DIRS8 = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
PREFAB_SIZE = {}


def tp(dx, dy):
    """Titik (px) pada offset tile (dx, dy) dari pusat kampung."""
    return (round(CX + dx * TILE), round(CY + dy * TILE))


def water_idx(is_water, x, y):
    i = 0
    for bit, (dx, dy) in enumerate(DIRS8):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and not is_water[nx, ny]:
            i |= 1 << bit
    return i


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
    rng = random.Random(2002)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    orig = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute (Tahap 2): entry -> alun-alun -> gerbang utara -> kantong barat ->
    # NGARAI BARAT (memutar ke utara) -> mulut tambang (stasiun tumpukan peti) -> LORONG TAMBANG menembus punggung tebing ->
    # aula tambang (Bonfire pra-boss, arena Penyihir Menara) -> exit. Panjang desa->arena >= 120 tile (PANDUAN 2b).
    P["puzzle"] = tpx(MINE_MOUTH)
    seg_in = winding(P["entry"], tp(24, 0), 24, 11, n=4)
    seg_vil = organic.polyline_samples([tp(24, 0), tp(0, 0), tp(0, -16)], 12.0)
    seg_w = winding(tp(0, -16), tpx((78, 73)), 26, 13, n=5)
    seg_c = np.vstack([winding(tpx((78, 73)), tpx((60, 67)), 18, 14, n=4), winding(tpx((60, 67)), tpx((58, 52)), 22, 15, n=4),
                       winding(tpx((58, 52)), tpx(MINE_MOUTH), 20, 16, n=5)])
    seg_t = organic.polyline_samples([tpx(MINE_MOUTH), tpx((88, TUNNEL_Y)), tpx((99, TUNNEL_Y)), P["bonfire_preboss"],
                                      P["boss_arena"], tpx((121, 43)), P["exit"]], 12.0)
    route = np.vstack([seg_in, seg_vil, seg_w, seg_c, seg_t])

    def route_i(pt):
        return idx_near(route, pt)

    i_puz, i_pre, i_boss, i_exit = (route_i(P[k]) for k in ("puzzle", "bonfire_preboss", "boss_arena", "exit"))

    # ------------------------------------------------------------ laut (biru di *_layout.png), daratan, dataran tinggi
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch2_TambangTumpuk_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 60 and ty >= 8
    sea_img[:, :8] = sea_img[:, 8:9]                       # 8 baris atas gambar tertutup judul: lanjutkan baris ke-8
    land = dilate(mask, 2) & ~sea_img
    # lorong masuk (dari Hutan Indeks) & keluar (ke Pelabuhan Antre) menembus tebing
    for key, pts in (("entry", seg_in[:8]), ("exit", orig[-6:])):
        land |= dist_to(gx, gy, pts) <= 3.2 * TILE
        land |= np.hypot(gx - P[key][0], gy - P[key][1]) <= 3.5 * TILE
    nz_r = organic.smooth_noise(gx, gy, 9)
    ridge = np.zeros_like(mask)
    for pts, hw in RIDGES:
        ridge |= dist_to(gx, gy, organic.polyline_samples([tpx(p_) for p_ in pts], 12.0)) <= hw * TILE + 10 * nz_r
    land &= ~ridge
    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]
    tunnel = (tcol >= TUNNEL_X[0]) & (tcol <= TUNNEL_X[1]) & (trow >= int(TUNNEL_Y) - 2) & (trow <= int(TUNNEL_Y) + 3)
    shortcut = (tcol >= SHORTCUT_X[0]) & (tcol <= SHORTCUT_X[1]) & (trow >= 61) & (trow <= 71)
    land |= tunnel | (shortcut & dilate(mask, 1))
    land = dilate(erode(land, 1), 1) | (land & dilate(sea_img, 1))   # haluskan tonjolan selebar 1 tile
    mine = land & (((tcol >= 95) & (trow <= 62)) | (tunnel & ridge))   # lantai tambang abu: lorong (di dalam tebing) + aula tambang
    sea = sea_img & ~land
    plateau = ~land & ~sea
    # wajah tebing: 2 tile di bawah tepi selatan dataran tinggi (menjorok ke daratan, bertabrakan)
    face = {}
    keep_free = [P["entry"], P["exit"]]
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

    # ------------------------------------------------------------ gerbang & kabut
    band = np.zeros_like(mask)
    for r_ in (GATE_ROW - 1, GATE_ROW, GATE_ROW + 1):
        band[:, r_] = land[:, r_] & ~face_m[:, r_]
    exit_t = (P["exit"][0] / TILE, P["exit"][1] / TILE)
    plug = (np.hypot(gx / TILE - exit_t[0], gy / TILE - exit_t[1]) <= 4.5) & land & ~face_m
    bc = (P["boss_arena"][0] / TILE, P["boss_arena"][1] / TILE)
    dd = np.hypot(gx / TILE - bc[0], gy / TILE - bc[1])
    arena_ring = np.zeros_like(mask)        # (Tahap 2) arena dikunci oleh peti di lorong tambang, bukan cincin awan
    # penghalang: kolom peti di lorong tambang (Quest Tengah) & longsoran batu di celah jalan pintas (Kristal)
    crate_block = tunnel & (tcol >= 91) & (tcol <= 92) & ~face_m
    rock_block = shortcut & land & (trow >= 65) & (trow <= 66) & ~face_m
    corridor = land & ~face_m & ~band & ~plug & ~arena_ring & ~crate_block & ~rock_block   # dataran yang boleh dihuni objek

    # ------------------------------------------------------------ jalan cabang (tanah terang) di dalam kampung & pinggiran
    QUARRY = tp(-33, 5)       # galian batu (barat)
    CAMP = tp(-3, 24)         # perkemahan penambang (selatan)
    STORE = tp(26, -7)        # gudang peti (timur laut)
    road_q = winding(tp(-18, 0), QUARRY, 30, 21, n=5)
    road_c = winding(tp(0, 14), CAMP, 24, 23, n=4)
    road_s = winding(tp(18, 0), (STORE[0] - 10, STORE[1] + 46), 12, 25, n=3)
    roads = np.vstack([route, road_q, road_c, road_s])
    # titik sudut (vertex) jalan terang: jarak dari titik sudut tile ke jalan, dengan tepi berombak
    vx = (np.arange(W + 1) * TILE)[:, None] * np.ones((1, H + 1))
    vy = (np.arange(H + 1) * TILE)[None, :] * np.ones((W + 1, 1))
    vn = organic.smooth_noise(vx, vy, 4)
    vd = dist_to(vx, vy, roads)
    light_v = vd <= 26 + 6 * vn
    pads = [(tp(0, 0), 150), (QUARRY, 70), (CAMP, 70), (STORE, 60), (P["puzzle"], 60), (P["bonfire_preboss"], 46),
            (P["boss_arena"], 140), (P["exit"], 44), (P["entry"], 44)]
    for (px_, py_), rr in pads:
        light_v |= np.hypot(vx - px_, vy - py_) <= rr + 10 * vn

    # ------------------------------------------------------------ peta tile
    stone = [(6, 10), (7, 10), (8, 10)]
    in_stone = np.zeros_like(mask)
    in_stone[C[0] - 6:C[0] + 6, C[1] - 6:C[1] + 6] = True                  # alun-alun 12x12
    in_stone[C[0] - 1:C[0] + 2, C[1] - 15:C[1] + 14] = True                # jalan utara-selatan
    in_stone[C[0] - 18:C[0] + 25, C[1] - 1:C[1] + 2] = True                # jalan barat-timur
    ground, stonec, cliffc, watc = [], [], [], []
    for tx in range(W):
        for ty in range(H):
            if plateau[tx, ty]:
                n_ = ty == 0 or plateau[tx, ty - 1]
                w_ = tx == 0 or plateau[tx - 1, ty]
                e_ = tx == W - 1 or plateau[tx + 1, ty]
                if not n_:
                    cx_ = 1 if not w_ else (3 if not e_ else 2)
                    cliffc.append((tx, ty, 1, cx_, 5))
                else:
                    cliffc.append((tx, ty, 1, 1 if not w_ else (3 if not e_ else 2), 6))
                continue
            if (tx, ty) in face:
                lft = tx > 0 and (tx - 1, ty) in face
                rgt = tx < W - 1 and (tx + 1, ty) in face
                cliffc.append((tx, ty, 1, 5 if (lft and rgt) else (4 if not lft else 6), face[(tx, ty)]))
                continue
            if sea[tx, ty]:
                i = water_idx(sea, tx, ty)
                watc.append((tx, ty, 0, i % 16, i // 16))
                continue
            key = (int(light_v[tx, ty]), int(light_v[tx + 1, ty]), int(light_v[tx, ty + 1]), int(light_v[tx + 1, ty + 1]))
            h_ = (tx * 7 + ty * 13 + tx * ty) % 97
            in_mine = mine[tx, ty]
            if key == (0, 0, 0, 0):
                a_ = (MINE_FLOOR if in_mine else SAND)[h_ % len(MINE_FLOOR if in_mine else SAND)]
            elif key == (1, 1, 1, 1) and h_ % 23 == 0:
                a_ = (MINE_DETAIL if in_mine else LIGHT_DETAIL)[h_ % 2]
            else:
                a_ = (MINE_CORNER if in_mine else CORNER_TILES)[key]
            ground.append((tx, ty, 0, a_[0], a_[1]))
            if in_stone[tx, ty] and corridor[tx, ty]:
                s_ = stone[(tx * 7 + ty * 3) % 3]
                stonec.append((tx, ty, 0, s_[0], s_[1]))

    # ------------------------------------------------------------ scene
    # jalur pintas (panah setelah Kristal): arena -> celah longsoran -> kantong utara -> gerbang desa -> alun-alun -> Lilbah
    sxm = (SHORTCUT_X[0] + SHORTCUT_X[1]) / 2
    short_route = organic.polyline_samples([P["boss_arena"], tpx((sxm, 57)), tpx((sxm, 72)), tp(0, -16), tp(0, 0), tp(-21, 1.6)], 12.0)
    sc = Scene()
    ts_canyon = sc.ext_res("TileSet", "res://assets/tilesets/canyon_tileset.tres")
    ts_world = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    ts_water = sc.ext_res("TileSet", "res://assets/tilesets/water_edge_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossPenyihir.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/StackCrates.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    anvil_script = sc.ext_res("Script", "res://scripts/entities/Anvil.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    animal_script = sc.ext_res("Script", "res://scripts/world/Animal.gd")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")

    sc.node("Ch2_TambangTumpuk", "Node2D", script=f'ExtResource("{script}")', chapter="2", music_name='"ch2_tambang_tumpuk"',
            boss_music_name='"boss"',
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")",
            shortcut_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in short_route[::4]) + ")",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_canyon}")')
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(stonec), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Water", "TileMapLayer", ".", tile_map_data=b64cells(watc), tile_set=f'ExtResource("{ts_water}")')
    sc.node("Tebing", "TileMapLayer", ".", tile_map_data=b64cells(cliffc), tile_set=f'ExtResource("{ts_canyon}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    recorded = []
    buildings = []        # (x, y_kaki, w, h): area bebas dekorasi

    def prefab(node, pref, pos, solid=True, **props):
        pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
        sc.node(node, None, "Objects", instance=pid, position=v2(*pos), **props)
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

    # ------------------------------------------------------------ KAMPUNG TUMPUK (blueprint)
    prefab("Sumur", "Sumur", tp(0, 1))
    houses = {"RumahMandor": ("Rumah_Krem", (-11.5, -3.5)), "RumahMirah": ("Rumah_Kayu", (11.5, -3.5)),
              "RumahWarga": ("Rumah_Papan", (-11.5, 12.5)), "RumahUdin": ("Rumah_Hijau", (11.5, 12.5))}
    for name, (pref, (dx, dy)) in houses.items():
        prefab(name, pref, tp(dx, dy))
    # bengkel Lilbah (barat, di luar jalan): landasan besar = Tempa, tungku, meja kerja, peti bahan
    prefab("LandasanLilbah", "Landasan_3", tp(-22.5, -3.2), script=f'ExtResource("{anvil_script}")')
    prefab("TungkuBesi", "Tungku_Besi_2", tp(-27.6, -3.4))
    prefab("TungkuBatu", "Tungku_Batu_2", tp(-17.6, -3.6))
    prefab("MejaKerjaLilbah", "MejaKerja_Besi_2", tp(-25.0, 4.6))
    prefab("PetiBahan", "Peti_Kayu_A", tp(-20.6, 4.4))
    prefab("BijihBengkel", "Bijih_Tumpuk_1", tp(-29.2, 3.8), solid=False)
    prefab("KayuBengkel", "Tumpukan_Kayu", tp(-18.8, -7.6))
    # gudang peti (timur laut): lumbung + tumpukan peti yang ditumpuk salah
    prefab("Gudang", "Lumbung", STORE)
    for k, (pref, (ox, oy)) in enumerate((("Peti_Tumpuk_2", (-58, 30)), ("Peti_Tumpuk_1", (-30, 38)), ("Peti_Tumpuk_3", (58, 30)),
                                          ("Peti_Tong", (84, 40)), ("Tong_Peti", (-86, 34)), ("Peti_Kayu_B", (36, 46)))):
        prefab(f"GudangPeti{k}", pref, (STORE[0] + ox, STORE[1] + oy))
    # alun-alun: lampu di keempat sudut + perabot
    for i, (dx, dy) in enumerate(((-7.2, -6.8), (7.2, -6.8), (-7.2, 7.2), (7.2, 7.2), (2.6, -13), (-2.6, 12.5))):
        prefab(f"Lampu{i}", "Lampu_Tiang", tp(dx, dy))
    prefab("AlunPeti1", "Peti_Kayu_A", tp(-4.5, -4.2))
    prefab("AlunPeti2", "Peti_Kayu_B", tp(4.4, -4.2))
    prefab("AlunTong", "Barel_Besar", tp(-4.4, 5.2))
    prefab("AlunGuci", "Guci_Tambang", tp(4.5, 5.2))
    prefab("LapakBijih", "Lapak_Kain", tp(-8.8, 4.2))
    prefab("LapakSayur", "Lapak_Sayur", tp(8.8, 4.2))
    for i, (dx, dy, k) in enumerate(((-5.6, -6.6, 1), (5.6, -6.6, 2), (-5.6, 5.4, 3), (5.6, 5.4, 1))):
        prefab(f"Spanduk{i}", f"Spanduk_{k}", tp(dx, dy), solid=False)
    # pagar pekarangan depan tiap rumah (celah di pintu)
    fence_w = PREFAB_SIZE["Pagar_Kayu"][0]
    for name, (pref, (dx, dy)) in houses.items():
        fy = dy + (1.2 if dy < 0 else 1.7)
        left, right, gap = dx - 4.2, dx + 4.2, 1.7
        n = 0
        for x0, x1 in ((left, dx - gap), (dx + gap, right)):
            x = x0 * TILE
            while x + fence_w / 2 <= x1 * TILE + 8:
                prefab(f"Pagar_{name}_{n}", "Pagar_Kayu", (round(CX + x + fence_w / 2), round(CY + fy * TILE)), solid=False)
                x += fence_w
                n += 1
        prefab(f"Tiang_{name}_L", "Tiang_Pagar", (round(CX + left * TILE), round(CY + fy * TILE)), solid=False)
        prefab(f"Tiang_{name}_R", "Tiang_Pagar", (round(CX + right * TILE), round(CY + fy * TILE)), solid=False)
    # lentera di sepanjang jalan masuk & jalan utara
    for i, (dx, dy) in enumerate(((16.0, -2.4), (21.5, 2.6), (-2.4, -10.0), (-15.0, 2.6))):
        prefab(f"Lentera{i}", "Lentera_Tiang", tp(dx, dy), solid=False)
    prefab("PapanBarat", "Papan_Kiri", tp(-17.6, -2.8), solid=False)
    prefab("PapanTimur", "Papan_Kanan", tp(24.6, -2.8), solid=False)
    prefab("PapanUtara", "Papan_Tiang", tp(-2.8, -14.2), solid=False)
    prefab("PapanSelatan", "Papan_Tiang", tp(2.8, 14.6), solid=False)

    # ---- pinggiran 1: GALIAN BATU (barat) - mesa dipahat, tangga, tumpukan bijih, batu
    qx, qy = QUARRY
    prefab("GalianMesa1", "Mesa_Besar", (qx - 40, qy - 44))
    prefab("GalianMesa2", "Mesa_Sedang", (qx + 26, qy - 52))
    prefab("GalianMesa3", "Mesa_Kecil", (qx - 86, qy - 20))
    prefab("GalianTangga", "Tangga_Kayu", (qx - 6, qy - 42), solid=False)
    for k, (pref, (ox, oy)) in enumerate((("Bijih_Tumpuk_1", (-30, 8)), ("Bijih_Tumpuk_2", (18, 14)), ("Bijih_Kecil", (40, 0)),
                                          ("Batu_Besar_2", (62, -18)), ("Batu_Sedang_1", (-60, 22)), ("Tong_Peti", (54, 30)),
                                          ("Batu_Sedang_2", (-14, 36)))):
        prefab(f"Galian{k}", pref, (qx + ox, qy + oy), solid=not pref.startswith("Bijih"))
    # ---- pinggiran 2: PERKEMAHAN PENAMBANG (selatan) - tenda, api unggun kecil, kayu
    cx_, cy_ = CAMP
    for k, (pref, (ox, oy)) in enumerate((("Tenda_1", (-52, -10)), ("Tenda_3", (48, -14)), ("Tenda_2", (-6, -36)),
                                          ("Tumpukan_Kayu", (60, 24)), ("Tunggul_Besar", (-58, 26)), ("Dapur_Tripod", (6, 20)),
                                          ("Peti_Kayu_A", (-26, 34)), ("Barel_Air", (30, 36)))):
        prefab(f"Kemah{k}", pref, (cx_ + ox, cy_ + oy))

    # ------------------------------------------------------------ NPC & penanda
    door_x, door_y = tp(-11.5, -3.5)
    npc_positions = []

    def npc(name, pos, **props):
        inst(name, npc_scene, pos, **props)
        npc_positions.append(pos)

    npc("Lilbah", tp(-21.0, 1.6), npc_id='"lilbah"')
    npc("Mandor", (door_x + 38, door_y + 18), npc_id='"mandor"', dialog_id='"ch2_mandor"', villager_chapter="2")
    npc("Mirah", tp(15.2, 1.8), npc_id='"mirah"', dialog_id='"ch2_mirah"', villager_chapter="2")
    npc("Udin", (STORE[0] - 4, STORE[1] + 64), npc_id='"udin"', dialog_id='"ch2_udin"', villager_chapter="2")
    npc("Pedagang", tp(8.8, 7.0), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuMandor", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_RumahMandor.tscn"', hint_text='"E: Masuk rumah Mandor"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuMandor", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    start = tuple(int(v) for v in route[6])
    bf1 = tp(-5, 8.5)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("BenderaMasuk", checkpoint_scene, (int(route[14][0]) + 40, int(route[14][1])))
    inst("BenderaGerbang", checkpoint_scene, tp(4.2, -13.5))
    inst("BenderaGalian", checkpoint_scene, (qx + 70, qy + 44))
    inst("PetiKampung", chest_scene, (cx_ + 80, cy_ - 30), roll_count="2")
    inst("PetiGalian", chest_scene, (qx - 70, qy + 52), roll_count="2")
    for k_, (ck, pos) in enumerate((("barang", (STORE[0] + 4, STORE[1] + 44)), ("jejak", (qx + 4, qy - 14)),
                                    ("catatan", (cx_ + 26, cy_ - 2))), start=1):
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*pos),
                flag=f'"ch2_petunjuk_{k_}"', dialog_id=f'"ch2_petunjuk_{k_}"', required_step='"ch2_awal:petunjuk"', clue_kind=f'"{ck}"')
        recorded.append(pos)
        npc_positions.append(pos)

    # ---- perjalanan: mulut tambang (puzzle), lorong tambang (peti penghalang), aula tambang, Bonfire, bendera
    mx, my = P["puzzle"]
    inst("StasiunPeti", station_scene, (int(mx), int(my) + 36), puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="2",
         station_label='"Tumpukan Peti"')
    k_ = i_boss
    while k_ > 0 and math.hypot(route[k_][0] - P["boss_arena"][0], route[k_][1] - P["boss_arena"][1]) < 12 * TILE:
        k_ -= 1
    bf_pre = (int(route[k_][0]) - 6, int(route[k_][1]) + 44)
    bf_canyon = tpx((65, 55))
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf_canyon)
    flags = {"BenderaNgarai": tpx((70, 70)), "BenderaTambang": (int(mx) - 70, int(my) + 40), "BenderaAula": tpx((101, 54.5))}
    for nm, pos in flags.items():
        inst(nm, checkpoint_scene, pos)
    inst("PulangHutan", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="1", sign_text='"Kembali ke Hutan Indeks"')
    inst("KePelabuhan", exit_scene, tuple(int(v) for v in P["exit"]), to_chapter="3", sign_text='"Ke Pelabuhan Antre"')
    npc_positions += [bf1, bf_pre, bf_canyon, start, (int(mx), int(my) + 36)] + list(flags.values())

    # penghalang tumpukan objek: hilang saat syarat terpenuhi (scripts/world/StageBlocker.gd)
    blocker_script = sc.ext_res("Script", "res://scripts/world/StageBlocker.gd")

    def blocker(name, cells, mode, stage, text, pieces, opened=""):
        xs, ys = np.nonzero(cells)
        c0 = (int(xs.mean()) * TILE + 8, int(ys.max() + 1) * TILE)
        sc.node(name, "Node2D", "Objects", script=f'ExtResource("{blocker_script}")', position=v2(*c0), y_sort_enabled="true",
                mode=f'"{mode}"', chapter="2", required_stage=str(stage), locked_text=f'"{text}"', opened_text=f'"{opened}"',
                hint_size=f"Vector2({(xs.max() - xs.min() + 9) * TILE}, {(ys.max() - ys.min() + 9) * TILE})")
        for k, (pref, (ox, oy)) in enumerate(pieces):
            pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
            sc.node(f"{name}{k}", None, f"Objects/{name}", instance=pid, position=v2(ox, oy))
        # tile penghalang tak terlihat (koordinat sel relatif terhadap node; node tepat di batas sel + 8 px)
        cells_l = [(int(x) - (c0[0] - 8) // TILE, int(y) - c0[1] // TILE, 0, 0, 0) for x, y in zip(xs, ys)]
        sc.node("Block", "TileMapLayer", f"Objects/{name}", position=v2(-8, 0), tile_map_data=b64cells(cells_l),
                tile_set=f'ExtResource("{block_ts}")')
        recorded.append(c0)

    blocker("PetiTerowongan", crate_block, "stage", 2, "Tumpukan peti menutup terowongan.\nSelesaikan teka-teki peti dulu.",
            [("Peti_Tumpuk_2", (-8, -50)), ("Peti_Tumpuk_1", (10, -32)), ("Peti_Tumpuk_3", (-6, -14)), ("Peti_Tong", (12, 2))],
            "Peti penutup terowongan disingkirkan.\nJalan ke aula tambang terbuka.")
    blocker("LongsoranPintas", rock_block, "crystal", 3, "Longsoran batu menutup jalan.\nMungkin terbuka setelah tambang aman.",
            [("Batu_Besar_1", (-28, -2)), ("Batu_Besar_2", (4, -10)), ("Batu_Gelap_2", (30, 0)), ("Batu_Sedang_1", (-8, 6)),
             ("Batu_Abu_1", (46, -8))], "Gemuruh! Longsoran di selatan aula tersingkir.\nJalan pintas ke Kampung Tumpuk terbuka.")
    # dekorasi lorong & mulut tambang, obor di tepi arena
    tx0, tx1 = TUNNEL_X
    ty_t = TUNNEL_Y * TILE + 8
    for k, xx in enumerate((tx0 + 1, tx0 + 9, tx1 - 1)):
        prefab(f"LenteraLorong{k}", "Lentera_Tiang", (xx * TILE + 8, int(ty_t + 26)), solid=False)
    prefab("TanggaMulut", "Tangga_Kayu", (tx0 * TILE - 30, int(ty_t - 6)), solid=False)
    for k, (pref, (ox, oy)) in enumerate((("Bijih_Tumpuk_1", (-62, -20)), ("Tong_Peti", (-74, 30)), ("Peti_Tumpuk_3", (54, 70)),
                                          ("Bijih_Tumpuk_2", (40, -34)), ("Guci_Tambang", (-40, 70)))):
        prefab(f"MulutTambang{k}", pref, (int(mx) + ox, int(my) + oy), solid=not pref.startswith("Bijih"))
    ax_, ay_ = (int(v) for v in P["boss_arena"])
    flam_arena = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    for k in range(6):
        ang = math.pi * 0.15 + k * math.tau / 6
        fx, fy = round(ax_ + math.cos(ang) * 150), round(ay_ + math.sin(ang) * 110)
        prefab(f"TiangObor{k}", "Batu_Sedang_2", (fx, fy + 4), solid=False)
        sc.node(f"OborArena{k}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_arena}")',
                position=v2(fx, fy), frame_w="20", frame_h="30", fps="9.0")
    npc_positions += [(ax_, ay_)]

    def cloud_barrier(name, cells_mask, mode, dist, text="", **props):
        pts = thin_cells(cells_mask, dist)
        arr = ", ".join(f"{x}, {y}" for x, y in pts)
        extra = {"locked_text": '"%s"' % text} if text else {}
        sc.node(name, "Node2D", ".", script=f'ExtResource("{cloud_script}")', mode=f'"{mode}"', chapter="2",
                cloud_points=f"PackedVector2Array({arr})", seed_value=str(rng.randint(1, 999)), **extra, **props)
        cells = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(cells_mask))]
        sc.node("Block", "TileMapLayer", name, tile_map_data=b64cells(cells), tile_set=f'ExtResource("{block_ts}")')

    DUST = "Color(0.96, 0.84, 0.66, 1)"
    cloud_barrier("AwanPerbatasan", plug, "chapter", 26, tint=DUST, scale_min="1.2", scale_max="1.6")
    cloud_barrier("AwanGerbangDesa", band, "stage", 40, "Badai debu menutup jalan ke tambang.\nBantu Lilbah dulu.",
                  required_stage="1", tint=DUST, scale_min="1.3", scale_max="1.9")

    # ------------------------------------------------------------ MESA & batu (dekorasi ngarai)
    d_route = dist_to(gx, gy, roads)

    def road_dist(x, y):
        tx_, ty_ = int(x // TILE), int(y // TILE)
        return float(d_route[tx_, ty_]) if 0 <= tx_ < W and 0 <= ty_ < H else 0.0

    village_zone = np.hypot((gx - CX) / (32 * TILE), (gy - (CY + 2 * TILE)) / (20 * TILE)) < 1.0
    keypts = list(P.values()) + [bf1, bf_pre, start, QUARRY, CAMP, STORE] + npc_positions
    no_deco = dilate(tunnel | crate_block | rock_block | shortcut, 3) | (np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 12 * TILE)

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

    mesas = ["Mesa_Kecil", "Mesa_Sedang", "Mesa_Lebar", "Mesa_Besar", "Mesa_Tinggi"]
    rocks = ["Batu_Besar_1", "Batu_Besar_2", "Batu_Sedang_1", "Batu_Sedang_2", "Batu_Gelap_1", "Batu_Gelap_2", "Batu_Abu_1"]
    clusters, nm_ = [], 0
    for _try in range(9000):
        if len(clusters) >= 70:
            break
        x, y = rng.randint(80, PX_W - 80), rng.randint(120, PX_H - 60)
        if any(math.hypot(x - cx2, y - cy2) < 210 for cx2, cy2 in clusters):
            continue
        pref = rng.choice(mesas)
        if not fits(pref, x, y):
            continue
        clusters.append((x, y))
        prefab(f"Mesa{nm_}", pref, (x, y))
        nm_ += 1
        # 1-3 mesa tetangga menempel (formasi batu), lalu batu kecil di sekelilingnya
        for _k in range(rng.randint(1, 3)):
            p2 = rng.choice(mesas)
            w1 = PREFAB_SIZE[pref][0]
            x2 = x + rng.choice((-1, 1)) * rng.randint(int(w1 * 0.6), int(w1 * 1.1))
            y2 = y + rng.randint(-34, 40)
            if fits(p2, x2, y2, 4):
                prefab(f"Mesa{nm_}", p2, (x2, y2))
                nm_ += 1
        for _k in range(rng.randint(1, 3)):
            p3 = rng.choice(rocks)
            ang = rng.random() * math.tau
            x3, y3 = round(x + math.cos(ang) * rng.randint(60, 100)), round(y + math.sin(ang) * rng.randint(30, 60))
            if fits(p3, x3, y3, 2):
                prefab(f"Mesa{nm_}", p3, (x3, y3))
                nm_ += 1
    # batu & bijih kecil tersebar di dekat jalan (tanpa tabrakan berarti: hanya batu kecil)
    for k in range(120):
        x, y = rng.randint(60, PX_W - 60), rng.randint(80, PX_H - 60)
        tx_, ty_ = int(x // TILE), int(y // TILE)
        pref = rng.choice(["Batu_Sedang_1", "Batu_Sedang_2", "Bijih_Kecil"])
        if corridor[tx_, ty_] and not village_zone[tx_, ty_] and not no_deco[tx_, ty_] and 40 < road_dist(x, y) < 260 and not near_building(x, y, 20) \
                and all(math.hypot(x - kx, y - ky) > 60 for kx, ky in keypts):
            prefab(f"Kerikil{k}", pref, (x, y), solid=False)
            buildings.append((x, y, 16, 12))

    # hewan kampung (ayam, kuda di perkemahan, anjing, kucing)
    animals = [("Chicken/SpriteSheetWhite", tp(-8.0, 15.6)), ("Chicken/SpriteSheetBrown", tp(-14.0, 15.2)),
               ("Chicken/SpriteSheetWhite", tp(14.5, -9.8)), ("Chicken/SpriteSheetBrown", (cx_ - 90, cy_ + 4)),
               ("Dog/SpriteSheet", tp(3.8, -9.6)), ("Cat/SpriteSheet", tp(-14.8, -0.6))]
    na = 0
    for sheet_, pos in animals:
        tex_path = os.path.join(ROOT, "assets/ninja/animals", sheet_ + ".png")
        if not os.path.exists(tex_path):
            alt = [f for f in os.listdir(os.path.dirname(tex_path)) if f.endswith(".png")]
            if not alt:
                continue
            sheet_ = os.path.dirname(sheet_) + "/" + alt[0][:-4]
        tex = sc.ext_res("Texture2D", f"res://assets/ninja/animals/{sheet_}.png")
        bscale = 1.0 if sheet_.startswith(("Chicken", "Cat")) else (1.2 if sheet_.startswith("Dog") else 1.5)
        sc.node(f"Hewan{na}", "Node2D", "Objects", script=f'ExtResource("{animal_script}")', sheet=f'ExtResource("{tex}")',
                position=v2(*pos), body_scale=str(bscale), wander_radius="50.0")
        na += 1
    # api unggun perkemahan (Flam beranimasi kecil di atas tripod)
    flam_tex = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    sc.node("ApiKemah", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_tex}")',
            position=v2(cx_ + 6, cy_ + 22), frame_w="20", frame_h="30", fps="9.0", modulate="Color(1, 1, 1, 0.9)")
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', leaves="false", ray_alpha="0.12")

    # ------------------------------------------------------------ musuh, peti, collectible (perjalanan)
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    taken = []

    def spot(pt, r_min=20):
        """Titik bebas terdekat (spiral sampai 140 px) dari pt (px)."""
        for r in [0] + list(range(12, 141, 12)):
            for a_ in range(0, 360, 30):
                x, y = pt[0] + math.cos(math.radians(a_)) * r, pt[1] + math.sin(math.radians(a_)) * r
                tx_, ty_ = int(x // TILE), int(y // TILE)
                if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or road_dist(x, y) < r_min:
                    continue
                if near_building(x, y, 14) or any(math.hypot(x - qx2, y - qy2) < 26 for qx2, qy2 in taken):
                    continue
                taken.append((x, y))
                return (round(x), round(y))
        return None

    # kelompok musuh (tile): perampok tambang (Orc) di ngarai, kerangka penambang (Skeleton) di dalam tambang.
    # Zona aman: kelompok pertama >= 45 tile dari tepi kampung (PANDUAN 2b).
    groups = {"Ngarai1": ((59, 63), ["orc", "orc_rogue", "orc_rogue"]),
              "Ngarai2": ((53, 50), ["orc", "orc_shaman", "orc_warrior"]),
              "Ngarai3": ((70, 40), ["orc_warrior", "orc_shaman", "orc_rogue"]),
              "Ngarai4": ((36, 30), ["orc", "orc_rogue", "orc_shaman"]),
              "Ngarai5": ((40, 68), ["orc_rogue", "orc"]),
              "Tambang1": ((99, 30), ["skeleton", "skeleton_rogue", "skeleton"]),
              "Tambang2": ((105, 24), ["skeleton_mage", "skeleton_warrior", "skeleton"]),
              "Tambang3": ((125, 56), ["skeleton_warrior", "skeleton_mage", "skeleton_rogue"]),
              "Tambang4": ((132, 47), ["skeleton_rogue", "skeleton"])}
    n_mob = 0
    for gname, ((gx_t, gy_t), ids) in groups.items():
        for k, eid in enumerate(ids):
            ang = k * math.tau / len(ids) + 0.5
            q = spot((gx_t * TILE + 8 + math.cos(ang) * 34, gy_t * TILE + 8 + math.sin(ang) * 26))
            if q:
                inst(f"Musuh{gname}_{k + 1}", enemy_scene, q, enemy_id=f'"{eid}"')
                n_mob += 1
    # peti harta + herb/ore di ujung cabang
    chests = {"PetiNgarai": (30, 25), "PetiPantai": (24, 50), "PetiKantong": (140, 74), "PetiAulaUtara": (104, 19),
              "PetiAulaTimur": (139, 55)}
    nl = 0
    for nm, (cx2, cy2) in chests.items():
        q = spot(tpx((cx2, cy2)))
        if not q:
            continue
        inst(nm, chest_scene, q, roll_count="2")
        for kind, (ox, oy) in (("Ore", (30, 14)), ("Herb", (-28, 16)), ("Ore" if nm.startswith("PetiAula") else "Herb", (2, 34))):
            q2 = spot((q[0] + ox, q[1] + oy), 0)
            if q2:
                nl += 1
                inst(f"{kind}{nl}", collect[kind], q2)
    # di sepanjang jalan: herb, koin, ore (lebih banyak ore di tambang), 2 potion
    for k in range(26):
        i_ = rng.randint(route_i(tp(0, -18)), i_boss)
        th = rng.random() * math.tau
        pt = (route[i_][0] + math.cos(th) * rng.randint(50, 130), route[i_][1] + math.sin(th) * rng.randint(40, 100))
        q = spot(pt, 30)
        if q:
            in_m = mine[int(q[0] // TILE), int(q[1] // TILE)]
            kind = ("Ore" if k % 2 else "GoldCoin") if in_m else ("Herb", "Herb", "GoldCoin", "Ore")[k % 4]
            nl += 1
            inst(f"{kind}{nl}", collect[kind], q)
    for k, pt in enumerate((tpx((62, 60)), tpx((99, 52)))):
        q = spot(pt, 24)
        if q:
            inst(f"Potion{k + 1}", collect["Potion"], q)
    # pinggiran kampung (Tahap 1)
    for k, (nm, ox, oy) in enumerate((("Herb", -40, 70), ("Herb", 90, 60), ("Ore", -96, -6), ("Ore", 30, -70), ("GoldCoin", 110, -20))):
        base = QUARRY if k < 4 else CAMP
        pos = (base[0] + ox, base[1] + oy)
        tx_, ty_ = int(pos[0] // TILE), int(pos[1] // TILE)
        if corridor[tx_, ty_] and not near_building(pos[0], pos[1], 6):
            inst(f"Pinggir{nm}{k + 1}", collect[nm], pos)

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    fn = route[max(0, i_exit - 8)]
    sc.node("FromNext", "Marker2D", ".", position=v2(int(fn[0]), int(fn[1])))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Lilbah", "Marker2D", "NPCSpawns", position=v2(*tp(-21.0, 1.6)), **{"metadata/npc_id": '"lilbah"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')

    out = os.path.join(ROOT, "scenes/world/Ch2_TambangTumpuk.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ uji keterhubungan (grid tile, objek padat diabaikan)
    walk = land & ~face_m

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
    none = np.zeros_like(walk)
    r_open, r_gate, r_plug = reach(rock_block), reach(band | plug | rock_block), reach(plug | rock_block)
    r_arena = reach(crate_block | plug | rock_block)
    r_short = reach(crate_block | plug)
    clue_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in ((STORE[0] + 4, STORE[1] + 44), (qx + 4, qy - 14), (cx_ + 26, cy_ - 2)))
    print("start ada di daratan =", bool(walk[int(start[0] // TILE), int(start[1] // TILE)]),
          "| desa & 3 petunjuk terjangkau saat gerbang tertutup =", bool(r_gate[C]) and clue_ok)
    print("gerbang desa mengunci puzzle =", not r_gate[t_["puzzle"]], "| puzzle terjangkau saat terbuka =", bool(r_open[t_["puzzle"]]))
    print("peti lorong mengunci boss =", not r_arena[t_["boss_arena"]], "| boss terjangkau lewat lorong =", bool(r_open[t_["boss_arena"]]),
          "| jalan pintas (longsoran dibuka) menembus ke aula =", bool(r_short[t_["boss_arena"]]))
    print("awan perbatasan mengunci exit =", not r_plug[t_["exit"]], "| exit terjangkau saat terbuka =", bool(r_open[t_["exit"]]))
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and corridor[int(p[0] // TILE), int(p[1] // TILE)])]
    length = float(np.sum(np.hypot(*np.diff(route[route_i(tp(0, 0)):i_boss], axis=0).T))) / TILE
    print("musuh:", n_mob, "| collectible:", nl)
    print("Ch2_TambangTumpuk.tscn:", nm_, "mesa/batu, objek di luar koridor:", len(bad), bad[:6],
          "| jalan desa->arena %.0f tile" % length, "| koridor", int(corridor.sum()), "tile")
    return bad


if __name__ == "__main__":
    build()
