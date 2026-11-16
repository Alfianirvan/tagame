"""Generator Ch5_PohonDunia.tscn v2: bentuk wilayah dari docs/layout/region_layout.json + DESA AKAR (desa di antara akar raksasa).

Jalankan dari folder proyek (setelah make_prefabs.py, make_villagers.py, gen_akar_tileset.py, gen_interior.py):
    python tools/gen_ch5_v2.py
Tahap 1 (bagian ini): peta 205x158 tile (layout 152x117 diperbesar 1,35x), batas akar & laut ungu, Desa Akar + pinggiran + 3 petunjuk, gerbang kabut ajaib.
  - Lantai: rumput; jalan = tanah (autotile sudut / marching squares, tools/gen_akar_tileset.py).
  - Batas: laut UNGU di utara/barat/timur (biru pada *_layout.png), akar raksasa (relief kulit kayu) di luar mask.
  - AKAR RAKSASA Pohon Dunia (punggung kayu di DALAM wilayah) memancar dari BATANG di semenanjung utara: akar A ke pantai barat,
    akar B ke tebing selatan. Desa Akar ada di ceruk barat daya di antara keduanya; celah akar B = gerbang desa (kabut ajaib, quest_stage 1).
Blueprint Desa Akar (tema Tree): KOLAM AKAR ungu di tengah dikelilingi jalan tanah, pos Tedy (interior, rumah menara ungu) di kaki akar A,
  rumah Nyai Sekar, Wira, Dimas & warga di sekeliling kolam; pinggiran: kuil akar (barat laut), kebun sakura (barat), mata air ungu (timur).
Tahap 2 (koordinat tile peta terskala): akar E membelah dataran timur -> rute memutar: gerbang desa -> DATARAN SELATAN ke timur ->
  celah timur -> DATARAN UTARA ke barat -> PERSIMPANGAN CABANG (stasiun labirin BST = Quest Tengah) -> SEGEL CABANG di kaki
  TANGGA AKAR (StageBlocker, hilang di quest_stage 2) -> tangga papan menembus batang Pohon Dunia -> ARENA TAJUK POHON (King Subiyan)
  di ujung utara semenanjung. Akar C & D dari batang ke laut: tajuk hanya bisa dicapai lewat tangga. Jalan pintas arena -> desa =
  AKAR TUMBANG di celah akar E (StageBlocker mode crystal).
DUSUN RANTING (dataran tenggara, cabang jalan dari rute): 4 rumah di sekitar kolam ungu & altar akar, Bonfire, lapak + Pedagang,
  warga Banyu, Lastri, Tole (dialog bertema Tree); kemah pasukan King Subiyan di timurnya (dusun terkepung).
  MISI (langkah Quest Tengah): temui Pak Banyu -> nyalakan LENTERA RANTING (puzzle TreeTraversal, penelusuran pre-order)
  -> baru stasiun labirin bercabang terbuka.
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
from gen_akar_tileset import DIRT, DIRT_DETAIL, GRASS, PLANK, WATER_CORNER  # noqa: E402
from gen_canyon_tileset import CORNER_TILES  # noqa: E402
from gen_village import ROOT, TILE, Scene, v2  # noqa: E402

dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx
LAYOUT = json.load(open(os.path.join(ROOT, "docs/layout/region_layout.json"), encoding="utf-8"))["Ch5_PohonDunia"]
# peta DIPERBESAR 1,35x dari region_layout (152x117 -> 205x158): bentuk, akar, gerbang & pinggiran terskala; Desa Akar digeser utuh
S = 1.35
W0, H0 = LAYOUT["ukuran_tile"]          # 152 x 117 (layout asli)
W, H = round(W0 * S), round(H0 * S)     # 205 x 158
PX_W, PX_H = W * 16, H * 16
VOFF = (36 * (S - 1), 72 * (S - 1))     # geser Desa Akar (pusat kolam layout (36,72)) ke pusat ceruk yang terskala


def sp(p):
    """Titik tile layout -> tile peta terskala."""
    return (p[0] * S, p[1] * S)


def vp(p):
    """Titik tile Desa Akar (rancangan pada skala layout) -> tile peta (digeser utuh, tidak terskala)."""
    return (p[0] + VOFF[0], p[1] + VOFF[1])
DOOR_DX = json.load(open(os.path.join(ROOT, "assets/props/buildings/variants/_pintu.json"), encoding="utf-8"))
TRUNK = sp((68, 24))                    # batang Pohon Dunia (semenanjung utara)
# akar raksasa (dataran kayu di DALAM wilayah, tile): (polyline, setengah lebar)
RIDGES = [([TRUNK, (TRUNK[0] + 0.01, TRUNK[1])], 7.0 * S),                                              # batang Pohon Dunia
          ([sp(q) for q in ((64, 30), (56, 40), (44, 49), (28, 53), (12, 55), (-3, 57))], 3.2),         # akar A: dinding utara Desa Akar
          ([sp(q) for q in ((66, 30), (64, 44), (61, 57), (59.8, 66.2))], 3.2),                         # akar B atas
          ([sp(q) for q in ((58.4, 75.2), (57.5, 85), (57, 96))], 3.2),                                 # akar B bawah (celah = gerbang)
          # Tahap 2 (tile peta terskala): akar C/D (batang -> laut timur/barat), akar E (membelah dataran timur, celah jalan pintas)
          ([(100, 33), (118, 34), (142, 36)], 3.2),
          ([(84, 30), (74, 29), (60, 28)], 3.2),
          ([(84, 68), (89.5, 68.5)], 3.2),
          ([(101, 69), (130, 70), (154, 71.5)], 3.2)]
STAIR_X = (90, 93)                      # tangga akar menembus batang Pohon Dunia (kolom tile)
STAIR_Y = (21, 45)
ARENA_T = (95, 12.5)                    # arena tajuk pohon (ujung utara semenanjung)
PUZZLE_T = (130, 55)                    # persimpangan cabang = stasiun labirin BST
PREBOSS_T = (99, 50)
RANTING_C = (157, 128)                  # DUSUN RANTING di dataran tenggara (permintaan Alfian): rumah di sekitar kolam ungu & altar akar
RANTING_BOX = (143, 174, 113, 143)      # kotak dusun (x0, x1, y0, y1): bebas musuh & dekorasi acak
SE_PONDS = [((152, 137), (3.6, 2.6)), ((186, 122), (2.8, 2.2))]   # kolam ungu kecil (pusat, jari-jari tile) di dataran tenggara
GAPS = {"tangga": (STAIR_X[0], STAIR_X[1], STAIR_Y[0], STAIR_Y[1]), "pintas": (93, 97, 63, 75)}
GATE_C = sp((59.2, 70.6))               # pusat celah akar B (gerbang desa, kabut ajaib)
POND_C, POND_R = vp((36, 71)), (4.6, 3.2)   # kolam akar di tengah Desa Akar
SPRING_C, SPRING_R = sp((51, 76.5)), 2.4    # mata air ungu (pinggiran timur)
PREFAB_SIZE = {}


def at(x, y):
    """Titik (px) pada tile absolut (x, y), pecahan boleh."""
    return (round(x * TILE + 8), round(y * TILE + 8))


def vat(x, y):
    """Titik (px) rancangan Desa Akar (skala layout) setelah digeser utuh ke pusat ceruk yang terskala."""
    return at(x + VOFF[0], y + VOFF[1])


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
    rng = random.Random(5005)
    mask0 = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    ix_, iy_ = np.minimum((np.arange(W) / S).astype(int), W0 - 1), np.minimum((np.arange(H) / S).astype(int), H0 - 1)
    mask = mask0[ix_][:, iy_]                                   # mask layout diperbesar (tetangga terdekat)
    P = {k: tpx(sp(v)) for k, v in LAYOUT["titik_tile"].items()}
    P.update(puzzle=tpx(PUZZLE_T), bonfire_preboss=tpx(PREBOSS_T), boss_arena=tpx(ARENA_T))
    orig = organic.polyline_samples([tpx(sp(q)) for q in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute: entry -> kolam akar -> gerbang (celah akar B) -> jalan layout
    seg_vil = organic.polyline_samples([P["entry"], tpx(vp((33, 82))), tpx(vp((36, 76.2))), tpx(vp((44, 75))), tpx(vp((50, 72.5))),
                                        tpx(sp((54, 71.5))), tpx(GATE_C), tpx((92, 98))], 12.0)
    seg_s = np.vstack([winding(tpx((92, 98)), tpx((125, 110)), 24, 91, n=4), winding(tpx((125, 110)), tpx((156, 100)), 22, 92, n=4),
                       winding(tpx((156, 100)), tpx((166, 80)), 16, 93, n=3), organic.polyline_samples([tpx((166, 80)), tpx((163, 64))], 12.0)])
    seg_n = np.vstack([winding(tpx((163, 64)), tpx((150, 57)), 12, 94, n=3), winding(tpx((150, 57)), tpx((PUZZLE_T[0], PUZZLE_T[1] + 2)), 10, 95, n=3),
                       winding(tpx((PUZZLE_T[0], PUZZLE_T[1] + 2)), tpx((106, 50)), 14, 96, n=3),
                       organic.polyline_samples([tpx((106, 50)), tpx((91.5, 48)), tpx((91.5, 22)), P["boss_arena"]], 12.0)])
    route = np.vstack([seg_vil, seg_s, seg_n])

    def route_i(pt):
        return idx_near(route, pt)

    i_boss = route_i(P["boss_arena"])
    i_gate = route_i(tpx(GATE_C))

    # ------------------------------------------------------------ laut ungu (biru di *_layout.png), daratan, akar raksasa
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch5_PohonDunia_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, int(ty / S) * 5 + 2), min(lay.shape[1] - 1, int(tx / S) * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 60 and ty >= 6
    sea_img[:, :8] = sea_img[:, 8:9]
    land = dilate(mask, 2) & ~sea_img
    land |= np.hypot(gx - P["entry"][0], gy - P["entry"][1]) <= 3.5 * TILE
    nz_r = organic.smooth_noise(gx, gy, 31)
    ridge = np.zeros_like(mask)
    for pts, hw in RIDGES:
        ridge |= dist_to(gx, gy, organic.polyline_samples([tpx(p_) for p_ in pts], 12.0)) <= hw * TILE + 10 * nz_r
    for x0, x1, y0, y1 in GAPS.values():            # tangga & celah jalan pintas selalu bisa dilalui (lalu ditutup penghalang)
        ridge[x0:x1 + 1, y0:y1 + 1] = False
    land &= ~ridge
    land = dilate(erode(land, 1), 1) | (land & dilate(sea_img, 1))
    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]
    stair = (tcol >= STAIR_X[0]) & (tcol <= STAIR_X[1]) & (trow >= STAIR_Y[0]) & (trow <= STAIR_Y[1])
    land |= stair & ~sea_img
    nz_l = organic.smooth_noise(gx, gy, 37)
    pond = (np.hypot((gx / TILE - 0.5 - POND_C[0]) / POND_R[0], (gy / TILE - 0.5 - POND_C[1]) / POND_R[1]) + 0.05 * nz_l < 1.0) & land
    pond |= (np.hypot(gx / TILE - 0.5 - SPRING_C[0], gy / TILE - 0.5 - SPRING_C[1]) + 0.1 * nz_l < SPRING_R) & land
    for (pcx, pcy), pr in SE_PONDS:                 # kolam ungu kecil di dataran tenggara
        pond |= (np.hypot((gx / TILE - 0.5 - pcx) / pr[0], (gy / TILE - 0.5 - pcy) / pr[1]) + 0.08 * nz_l < 1.0) & land
    sea = (sea_img & ~land) | pond
    land &= ~pond
    plateau = ~land & ~sea
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

    pad_sea = np.pad(sea, 1, mode="edge")
    water_v = pad_sea[:-1, :-1] & pad_sea[1:, :-1] & pad_sea[:-1, 1:] & pad_sea[1:, 1:]

    # ------------------------------------------------------------ gerbang (kabut ajaib di celah akar B)
    band = land & ~face_m & (np.hypot(gx / TILE - 0.5 - GATE_C[0], gy / TILE - 0.5 - GATE_C[1]) <= 4.0)
    open_l = land & ~face_m
    bar_block = open_l & (tcol >= STAIR_X[0] - 1) & (tcol <= STAIR_X[1] + 1) & (trow >= 43) & (trow <= 44)   # segel cabang (Quest Tengah)
    sc_block = open_l & (trow >= 68) & (trow <= 70) & (tcol >= 86) & (tcol <= 104)                          # akar tumbang (Kristal)
    corridor = land & ~face_m & ~band & ~bar_block & ~sc_block & ~stair

    # ------------------------------------------------------------ jalan tanah (rute + cabang pinggiran)
    SHRINE = tpx(sp((12, 64)))    # kuil akar (barat laut)
    GARDEN = tpx(sp((8, 71)))     # kebun sakura (barat)
    SPRING = tpx(SPRING_C)        # mata air ungu (timur)
    road_k = winding(tpx(vp((30, 66))), SHRINE, 20, 81, n=4)
    road_g = winding(tpx(vp((30, 75))), GARDEN, 18, 83, n=4)
    road_ring = np.vstack([organic.polyline_samples([tpx(vp((36 + 7.6 * math.cos(t), 71.3 + 5.4 * math.sin(t)))) for t in
                                                     np.linspace(0, math.tau, 40)], 12.0)])
    road_d = winding(tpx((150, 104)), tpx((157, 125)), 12, 97, n=3)           # cabang jalan ke Dusun Ranting
    roads = np.vstack([route, road_k, road_g, road_ring, road_d])
    vx = (np.arange(W + 1) * TILE)[:, None] * np.ones((1, H + 1))
    vy = (np.arange(H + 1) * TILE)[None, :] * np.ones((W + 1, 1))
    vn = organic.smooth_noise(vx, vy, 4)
    dirt_v = dist_to(vx, vy, roads) <= 22 + 5 * vn
    pads = [(SHRINE, 60), (GARDEN, 50), (tpx((157, 129)), 92), (P["puzzle"], 70), (P["bonfire_preboss"], 46), (P["boss_arena"], 130), (P["entry"], 40)]
    for (px_, py_), rr in pads:
        dirt_v |= np.hypot(vx - px_, vy - py_) <= rr + 10 * vn

    # ------------------------------------------------------------ peta tile
    ground, cliffc, blockc, stairc = [], [], [], []
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
                    ground.append((tx, ty, 0, GRASS[0][0], GRASS[0][1]))
                else:
                    a_ = WATER_CORNER[wk]
                    ground.append((tx, ty, 2, a_[0], a_[1]))
                    if sum(wk) >= 2:
                        blockc.append((tx, ty, 0, 0, 0))
                continue
            if stair[tx, ty]:          # tangga papan di dalam batang Pohon Dunia
                p_ = PLANK[(tx * 3 + ty) % 3]
                stairc.append((tx, ty, 2, p_[0], p_[1]))
            key = (int(dirt_v[tx, ty]), int(dirt_v[tx + 1, ty]), int(dirt_v[tx, ty + 1]), int(dirt_v[tx + 1, ty + 1]))
            if key == (0, 0, 0, 0):
                a_ = GRASS[h_ % len(GRASS)]
            elif key == (1, 1, 1, 1):
                a_ = DIRT_DETAIL[h_ % 2] if h_ % 29 == 0 else DIRT[0]
            else:
                a_ = CORNER_TILES[key]
            ground.append((tx, ty, 0, a_[0], a_[1]))

    # jalur pintas (panah setelah Kristal): arena -> tangga -> celah akar tumbang -> gerbang desa -> pos Tedy
    short_route = organic.polyline_samples([P["boss_arena"], tpx((91.5, 22)), tpx((91.5, 48)), tpx((95, 58)), tpx((95, 69)),
                                            tpx((90, 82)), tpx((84, 93)), tpx(GATE_C), tpx(vp((50, 72.5))), tpx(vp((46, 68.2)))], 12.0)

    # ------------------------------------------------------------ scene
    sc = Scene()
    ts_akar = sc.ext_res("TileSet", "res://assets/tilesets/akar_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Region.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    boss_scene = sc.ext_res("PackedScene", "res://scenes/entities/BossKing.tscn")
    chest_scene = sc.ext_res("PackedScene", "res://scenes/entities/Chest.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin", "Potion", "Ore")}
    station_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    puzzle_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/TreeMaze.tscn")
    blocker_script = sc.ext_res("Script", "res://scripts/world/StageBlocker.gd")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")
    flam_tex = sc.ext_res("Texture2D", "res://assets/ninja/fx/Flam/Flam.png")
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")

    sc.node("Ch5_PohonDunia", "Node2D", script=f'ExtResource("{script}")', chapter="5", music_name='"ch5_pohon_dunia"',
            boss_music_name='"boss_final_king_subiyan"',
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")",
            shortcut_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in short_route[::4]) + ")",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ajaib", "CanvasModulate", ".", color="Color(1, 0.94, 1.04, 1)")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_akar}")')
    sc.node("Akar", "TileMapLayer", ".", tile_map_data=b64cells(cliffc), tile_set=f'ExtResource("{ts_akar}")')
    sc.node("TanggaAkar", "TileMapLayer", ".", tile_map_data=b64cells(stairc), tile_set=f'ExtResource("{ts_akar}")')
    sc.node("AirPenghalang", "TileMapLayer", ".", tile_map_data=b64cells(blockc), tile_set=f'ExtResource("{block_ts}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    recorded = []
    buildings = []

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
            wk = land & ~face_m
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

    # ------------------------------------------------------------ DESA AKAR
    houses = {"PosTedy": ("Rumah_Menara_Ungu", (45, 65.6)),            # pos Tedy (interior) di kaki akar A
              "RumahSekar": ("Rumah_Loteng_Ungu", (25.5, 65.6)),       # tetua desa
              "RumahWira": ("Rumah_Runcing_Ungu", (21, 80.6)),         # penjaga akar
              "RumahDimas": ("Pondok_Ungu", (46, 81.6)),               # prajurit muda
              "RumahWarga": ("Rumah_Runcing_Ungu", (13, 75.6))}
    houses = {k: (pref, vp(xy)) for k, (pref, xy) in houses.items()}
    for name, (pref, (x, y)) in houses.items():
        prefab(name, pref, at(x, y))
    fence_w = PREFAB_SIZE["Pagar_Kayu"][0]
    for name, (pref, (x, y)) in houses.items():          # pagar pekarangan (celah di pintu)
        if name in ("PosTedy", "RumahDimas"):
            continue
        hw = PREFAB_SIZE[pref][0] / (2 * TILE) + 0.2
        dd = x + DOOR_DX.get(pref, 0) / TILE
        n = 0
        for x0, x1 in ((x - hw, dd - 1.7), (dd + 1.7, x + hw)):
            xx = x0 * TILE
            while xx + fence_w / 2 <= x1 * TILE + 8:
                prefab(f"Pagar_{name}_{n}", "Pagar_Kayu", (round(xx + fence_w / 2 + 8), round((y + 1.2) * TILE + 8)), solid=False)
                xx += fence_w
                n += 1
    for nm, pref, (x, y) in (("LapakAkar", "Lapak_Sayur", (41.4, 77.8)), ("TongAkar", "Barel_Besar", (28.4, 77.6)),
                             ("PetiAkar", "Peti_Kayu_A", (43.6, 68.4))):
        prefab(nm, pref, vat(x, y))
    for i, (x, y) in enumerate(((29.0, 67.6), (43.0, 67.6), (29.4, 75.6), (42.6, 75.6), (33.0, 82.6), (53.6, 72.6))):
        prefab(f"Lentera{i}", "Lentera_Tiang", vat(x, y), solid=False)
    # pinggiran 1: KUIL AKAR (barat laut) - altar & pilar berlumut di bawah sakura besar
    kx_, ky_ = SHRINE
    for k, (pref, (ox, oy)) in enumerate((("Altar_Segel", (0, -6)), ("Pilar_Lumut", (-40, -10)), ("Pilar_Lumut", (40, -10)),
                                          ("Sakura_Besar", (-70, -30)), ("Sakura_1", (68, -28)))):
        prefab(f"KuilAkar{k}", pref, (kx_ + ox, ky_ + oy))
    # pinggiran 2: KEBUN SAKURA (barat)
    gx0, gy0 = GARDEN
    for k, (pref, (ox, oy)) in enumerate((("Sakura_Rumpun", (-30, -40)), ("Sakura_1", (40, -30)), ("Sakura_Besar", (50, 40)),
                                          ("Sakura_1", (-46, 36)), ("Keranjang_Buah_2", (16, 22)))):
        prefab(f"KebunSakura{k}", pref, (gx0 + ox, gy0 + oy))
    # pinggiran 3: MATA AIR UNGU (timur, dekat gerbang)
    sx_, sy_ = SPRING
    for k, (pref, (ox, oy)) in enumerate((("Batu_Sedang_1", (-44, 10)), ("Batu_Besar_2", (46, -14)), ("Sakura_1", (30, 50)))):
        prefab(f"MataAir{k}", pref, (sx_ + ox, sy_ + oy))

    # ------------------------------------------------------------ NPC & penanda
    tp_, (tx0_, ty0_) = houses["PosTedy"]
    door_x, door_y = at(tx0_ + DOOR_DX.get(tp_, 0) / TILE, ty0_)
    npc_positions = []

    def npc(name, pos, **props):
        inst(name, npc_scene, pos, **props)
        npc_positions.append(pos)

    tedy_pos = (door_x + 40, door_y + 24)
    wira_pos, sekar_pos, dimas_pos = vat(24.4, 82.4), vat(29.6, 67.8), vat(49.6, 80.0)
    npc("Tedy", tedy_pos, npc_id='"tedy"')
    npc("Wira", wira_pos, npc_id='"wira"', dialog_id='"ch5_wira"', villager_chapter="5")
    npc("Sekar", sekar_pos, npc_id='"sekar"', dialog_id='"ch5_sekar"', villager_chapter="5")
    npc("Dimas", dimas_pos, npc_id='"dimas"', dialog_id='"ch5_dimas"', villager_chapter="5")
    npc("Pedagang", vat(39.4, 78.0), npc_id='"pedagang"', opens_shop="true")
    # ---- DUSUN RANTING (dataran tenggara): rumah di sekitar kolam ungu, lapak, warga (dialog bertema Tree)
    for name, (pref, (x, y)) in {"RantingRumah1": ("Rumah_Loteng_Ungu", (146, 124)), "RantingRumah2": ("Rumah_Runcing_Ungu", (155, 119.5)),
                                 "RantingRumah3": ("Pondok_Ungu", (171, 127.5)), "RantingRumah4": ("Rumah_Teras_Coklat", (163, 140.5))}.items():
        prefab(name, pref, at(x, y))
    for nm, pref, (x, y) in (("RantingLapak", "Lapak_Sayur", (150.6, 130.8)), ("RantingTong", "Barel_Air", (167.4, 131.6)),
                             ("RantingPeti", "Peti_Kayu_A", (141.8, 126.4))):
        prefab(nm, pref, at(x, y))
    for i, (x, y) in enumerate(((151.6, 126.4), (163.6, 126.6), (158.0, 134.6), (147.0, 132.4))):
        prefab(f"LenteraRanting{i}", "Lentera_Tiang", at(x, y), solid=False)
    npc("Banyu", at(149.4, 127.2), npc_id='"banyu"')      # dialog dari langkah quest (misi lentera ranting)
    lantern_scene = sc.ext_res("PackedScene", "res://scenes/puzzles/TreeTraversal.tscn")
    station_scene0 = sc.ext_res("PackedScene", "res://scenes/puzzles/PuzzleStation.tscn")
    inst("StasiunLentera", station_scene0, at(157.6, 124.4), puzzle_scene=f'ExtResource("{lantern_scene}")', chapter="5",
         station_label='"Lentera Ranting"', complete_flag='"ch5_lentera_ranting"', required_step='"ch5_tengah:lentera"')
    npc_positions.append(at(157.6, 124.4))
    npc("Lastri", at(153.8, 132.0), npc_id='"lastri"', dialog_id='"ch5_lastri"')
    npc("Tole", at(166.0, 133.4), npc_id='"tole"', dialog_id='"ch5_tole"')
    npc("PedagangRanting", at(160.6, 131.4), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuTedy", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_PosTedy.tscn"', hint_text='"E: Masuk pos Tedy"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuTedy", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    start = tuple(int(v) for v in route[3])
    bf1 = vat(32.4, 77.6)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("BenderaMasuk", checkpoint_scene, vat(35.6, 84.0))
    inst("BenderaGerbang", checkpoint_scene, at(*sp((54.6, 68.2))))
    inst("BenderaKuil", checkpoint_scene, (kx_ + 60, ky_ + 30))
    inst("PetiKuil", chest_scene, open_spot((kx_ - 30, ky_ + 36)), roll_count="2")
    inst("PetiKebun", chest_scene, open_spot((gx0 - 10, gy0 + 50)), roll_count="2")
    clue_pts = [open_spot(p_) for p_ in ((kx_ + 4, ky_ + 18), (gx0 + 4, gy0 + 6), (sx_ - 36, sy_ - 30))]
    for k_, (ck, pos) in enumerate(zip(("jejak", "catatan", "barang"), clue_pts), start=1):
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*pos),
                flag=f'"ch5_petunjuk_{k_}"', dialog_id=f'"ch5_petunjuk_{k_}"', required_step='"ch5_awal:petunjuk"', clue_kind=f'"{ck}"')
        recorded.append(pos)
        npc_positions.append(pos)
    inst("PulangGua", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="4", sign_text='"Kembali ke Gua Rantai"')
    npc_positions += [bf1, start, SHRINE, GARDEN, SPRING, P["puzzle"], P["boss_arena"]]

    # ---- perjalanan: persimpangan cabang (stasiun labirin BST), Bonfire, bendera, arena tajuk pohon, penghalang
    px0, py0 = P["puzzle"]
    inst("StasiunLabirin", station_scene, (int(px0), int(py0) + 36), puzzle_scene=f'ExtResource("{puzzle_scene}")', chapter="5",
         station_label='"Labirin Bercabang"')
    for k, (pref, (ox, oy)) in enumerate((("Papan_Kiri", (-60, 30)), ("Papan_Kanan", (60, 30)), ("Pilar_Lumut", (-40, -10)),
                                          ("Pilar_Lumut", (40, -10)), ("Sakura_Besar", (-96, -6)), ("Pohon_Gugur_Besar", (96, -6)))):
        prefab(f"Persimpangan{k}", pref, (int(px0) + ox, int(py0) + oy), solid=not pref.startswith("Papan"))
    bf_pre = (int(P["bonfire_preboss"][0]), int(P["bonfire_preboss"][1]) + 20)
    bf_mid = at(157.6, 129.8)                      # Bonfire di Dusun Ranting
    inst("Bonfire2", bonfire_scene, bf_pre)
    inst("Bonfire3", bonfire_scene, bf_mid)
    flags = {"BenderaSelatan": at(120, 104), "BenderaRanting": at(144.6, 131.6), "BenderaTimur": at(170, 80), "BenderaUtara": at(140, 60)}
    for nm_f, pos in flags.items():
        inst(nm_f, checkpoint_scene, pos)
    npc_positions += [(int(px0), int(py0) + 36), bf_pre, bf_mid] + list(flags.values())
    ax_, ay_ = (int(v) for v in P["boss_arena"])
    for k in range(6):          # obor & pilar di tepi tajuk
        ang = math.pi * 0.15 + k * math.tau / 6
        fx_, fy_ = round(ax_ + math.cos(ang) * 150), round(ay_ + math.sin(ang) * 96)
        prefab(f"TiangObor{k}", "Lentera_Tiang", (fx_, fy_ + 4), solid=False)
        sc.node(f"OborArena{k}", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_tex}")',
                position=v2(fx_, fy_ - 26), frame_w="20", frame_h="30", fps="9.0")
    for k, (pref, (ox, oy)) in enumerate((("Sakura_Besar", (-190, -40)), ("Sakura_Besar", (190, -36)), ("Pilar_Lumut", (-176, 60)),
                                          ("Pilar_Lumut", (176, 62)))):
        prefab(f"TepiTajuk{k}", pref, (ax_ + ox, ay_ + oy))
    for k, y_ in enumerate((45.6,)):                  # lentera di kaki tangga akar
        prefab(f"LenteraTangga{k}", "Lentera_Tiang", at(STAIR_X[1] + 1.4, y_), solid=False)
    npc_positions += [(ax_, ay_)]

    def blocker(name, cells, mode, stage, text, pieces, opened=""):
        xs, ys = np.nonzero(cells)
        c0 = (int(xs.mean()) * TILE + 8, int(ys.max() + 1) * TILE)
        sc.node(name, "Node2D", "Objects", script=f'ExtResource("{blocker_script}")', position=v2(*c0), y_sort_enabled="true",
                mode=f'"{mode}"', chapter="5", required_stage=str(stage), locked_text=f'"{text}"', opened_text=f'"{opened}"',
                hint_size=f"Vector2({(xs.max() - xs.min() + 9) * TILE}, {(ys.max() - ys.min() + 9) * TILE})")
        for k, (pref, (ox, oy)) in enumerate(pieces):
            pid = sc.ext_res("PackedScene", f"res://scenes/prefabs/{pref}.tscn")
            sc.node(f"{name}{k}", None, f"Objects/{name}", instance=pid, position=v2(ox, oy))
        cells_l = [(int(x) - (c0[0] - 8) // TILE, int(y) - c0[1] // TILE, 0, 0, 0) for x, y in zip(xs, ys)]
        sc.node("Block", "TileMapLayer", f"Objects/{name}", position=v2(-8, 0), tile_map_data=b64cells(cells_l),
                tile_set=f'ExtResource("{block_ts}")')
        recorded.append(c0)
        return c0

    bar_c = blocker("SegelCabang", bar_block, "stage", 2, "Segel cabang menutup tangga akar.\nLewati labirin bercabang dulu.",
                    [("Kristal_Ungu_1", (-26, -10)), ("Kristal_Ungu_2", (10, -4)), ("Kristal_Ungu_2", (34, -12))],
                    "Labirin terpecahkan! Segel cabang memudar.\nTangga akar menuju tajuk Pohon Dunia terbuka.")
    sc_c = blocker("AkarTumbang", sc_block, "crystal", 5, "Akar tumbang menutup celah.\nMungkin terbuka setelah King Subiyan kalah.",
                   [("Tronk_Kayu", (-40, -6)), ("Tunggul_Besar", (-8, -2)), ("Tronk_Kayu", (24, -8)), ("Puing_Kayu", (54, -2))],
                   "Akar tumbang menyusut kembali ke tanah.\nJalan pintas ke Desa Akar terbuka.")
    npc_positions += [bar_c, sc_c]

    def cloud_barrier(name, cells_mask, mode, dist, text="", **props):
        pts = thin_cells(cells_mask, dist)
        arr = ", ".join(f"{x}, {y}" for x, y in pts)
        extra = {"locked_text": '"%s"' % text} if text else {}
        sc.node(name, "Node2D", ".", script=f'ExtResource("{cloud_script}")', mode=f'"{mode}"', chapter="5",
                cloud_points=f"PackedVector2Array({arr})", seed_value=str(rng.randint(1, 999)), **extra, **props)
        cells = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(cells_mask))]
        sc.node("Block", "TileMapLayer", name, tile_map_data=b64cells(cells), tile_set=f'ExtResource("{block_ts}")')

    cloud_barrier("AwanGerbangDesa", band, "stage", 30, "Kabut ajaib menutup celah akar.\\nBantu Tedy dulu.",
                  required_stage="1", tint="Color(0.98, 0.84, 1, 1)", scale_min="1.3", scale_max="1.9")

    # ------------------------------------------------------------ dekorasi: sakura, pohon gugur, batu, tunggul
    d_route = dist_to(gx, gy, roads)

    def road_dist(x, y):
        tx_, ty_ = int(x // TILE), int(y // TILE)
        return float(d_route[tx_, ty_]) if 0 <= tx_ < W and 0 <= ty_ < H else 0.0

    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]
    village_zone = (tcol >= 6 + VOFF[0]) & (tcol <= 58 + VOFF[0]) & (trow >= 58 + VOFF[1]) & (trow <= 88 + VOFF[1])
    village_zone |= (tcol >= RANTING_BOX[0]) & (tcol <= RANTING_BOX[1]) & (trow >= RANTING_BOX[2]) & (trow <= RANTING_BOX[3])
    keypts = [P[k] for k in ("entry", "puzzle", "bonfire_preboss", "boss_arena")] + [bf1, start] + npc_positions
    no_deco = dilate(band | bar_block | sc_block | stair, 3) | (np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 13 * TILE) \
        | (np.hypot(gx - P["puzzle"][0], gy - P["puzzle"][1]) < 8 * TILE)

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

    # ------------------------------------------------------------ DATARAN TENGGARA: landmark kecil (bukan hanya pohon acak)
    desa_akar = (tcol >= 6 + VOFF[0]) & (tcol <= 58 + VOFF[0]) & (trow >= 58 + VOFF[1]) & (trow <= 88 + VOFF[1])

    def fits_lm(pref, x, y, road_min):
        w, h = PREFAB_SIZE[pref]
        for ox, oy in ((-w / 2, 0), (w / 2, 0), (-w / 2, -h * 0.7), (w / 2, -h * 0.7), (0, 4), (0, -h / 2)):
            tx_, ty_ = int((x + ox) // TILE), int((y + oy) // TILE)
            if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or desa_akar[tx_, ty_] or no_deco[tx_, ty_]:
                return False
        return road_dist(x, y) >= road_min + w / 2 and not near_building(x, y, 4) \
            and all(math.hypot(x - kx, y - ky) >= 44 for kx, ky in keypts)

    def lm(name, pref, tile, solid=True, road_min=14):
        bx_, by_ = at(*tile)
        for r in [0] + list(range(8, 97, 8)):
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
        # kemah pasukan King Subiyan
        "KemahPasukan": [("Tenda_1", (181, 140)), ("Tenda_3", (189, 137)), ("Tenda_2", (184, 147)), ("Peti_Tumpuk_2", (177, 146)),
                         ("Tong_Peti", (191, 144)), ("Barel_Besar", (192, 140)), ("Peti_Tumpuk_3", (178, 135)), ("Spanduk_2", (184, 134))],
        # reruntuhan desa lama yang terhimpit akar
        "DesaLama": [("Ruina_1", (132, 127)), ("Ruina_3", (140, 125)), ("Ruina_4", (128, 135)), ("Puing_Pilar", (137, 132)),
                     ("Puing_Batu", (144, 130)), ("Puing_Kayu", (125, 129)), ("Tronk_Kayu", (134, 139))],
        # altar akar kecil
        "AltarAkar": [("Altar_Segel", (164, 121.5)), ("Pilar_Lumut", (161, 120.5)), ("Pilar_Lumut", (167.5, 120.5)),
                      ("Kristal_Ungu_2", (161.4, 124.2)), ("Kristal_Ungu_1", (167.6, 124.6))],
        # menara pengintai rusak di tepi pantai timur
        "MenaraPengintai": [("Ruina_5", (192, 110)), ("Tangga_Kayu", (189, 111)), ("Peti_Kayu_B", (195, 113)), ("Puing_Kayu", (188, 114))],
        # tepi kolam ungu & rumpun sakura liar
        "TepiKolam": [("Batu_Besar_1", (147, 134)), ("Batu_Sedang_1", (157, 140)), ("Sakura_Besar", (150, 132)), ("Batu_Besar_2", (183, 120)),
                      ("Sakura_1", (189, 125))],
        "SakuraLiar": [("Sakura_Rumpun", (118, 146)), ("Sakura_Besar", (124, 150)), ("Pohon_Gugur_Besar", (114, 140)), ("Sakura_1", (128, 146))],
    }
    for grp, items in landmarks.items():
        for k, (pref, tile) in enumerate(items):
            solid_ = not pref.startswith(("Puing_Batu", "Spanduk", "Tangga"))
            if lm(f"{grp}{k}", pref, tile, solid=solid_, road_min=0 if pref.startswith(("Spanduk", "Tangga")) else 14):
                n_lm += 1
    q_ = lm("TripodKemahPasukan", "Dapur_Tripod", (185, 142), road_min=8)
    if q_:
        sc.node("ApiKemahPasukan", "Node2D", "Objects", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{flam_tex}")',
                position=v2(q_[0], q_[1] - 2), frame_w="20", frame_h="30", fps="9.0", modulate="Color(1, 1, 1, 0.9)")
    # lentera tiap ~14 tile & papan penunjuk di sepanjang rute dataran timur
    east = [(x, y) for x, y in route[i_gate:i_boss] if x > 86 * TILE and y > 50 * TILE]
    for k in range(0, len(east), 19):
        x, y = east[k]
        for side in (1, -1):
            if lm(f"LenteraTimur{k}", "Lentera_Tiang", (x / TILE - 0.5 + side * 1.6, y / TILE - 0.5), solid=False, road_min=-6):
                break
    lm("PapanSelatan", "Papan_Kanan", (100, 101), solid=False, road_min=-4)
    lm("PapanCelah", "Papan_Tiang", (168, 76), solid=False, road_min=-4)
    print("dataran tenggara & jalan timur: landmark", n_lm)

    big = ["Sakura_Rumpun", "Sakura_Besar", "Pohon_Gugur_Besar", "Sakura_Rumpun", "Sakura_1"]
    small = ["Sakura_1", "Batu_Sedang_1", "Batu_Sedang_2", "Tunggul_Besar", "Sakura_1"]
    clusters, nm_ = [], 0
    for _try in range(12000):
        if len(clusters) >= 110:
            break
        x, y = rng.randint(60, PX_W - 60), rng.randint(90, PX_H - 50)
        if any(math.hypot(x - cx2, y - cy2) < 130 for cx2, cy2 in clusters):
            continue
        pref = rng.choice(big)
        if not fits(pref, x, y):
            continue
        clusters.append((x, y))
        prefab(f"Sakura{nm_}", pref, (x, y))
        nm_ += 1
        for _k in range(rng.randint(2, 4)):
            p3 = rng.choice(small)
            ang = rng.random() * math.tau
            x3, y3 = round(x + math.cos(ang) * rng.randint(30, 80)), round(y + math.sin(ang) * rng.randint(20, 50))
            if fits(p3, x3, y3, 2):
                prefab(f"Sakura{nm_}", p3, (x3, y3))
                nm_ += 1
    # sakura di tepi desa (di luar jalan & rumah)
    for k, (x, y) in enumerate(((8, 64), (16, 62), (52, 64), (10, 84), (40, 86), (54, 86), (18, 70), (50, 70))):
        q_ = vat(x, y)
        tx_, ty_ = int(q_[0] // TILE), int(q_[1] // TILE)
        if corridor[tx_, ty_] and road_dist(*q_) > 30 and not near_building(q_[0], q_[1], 10):
            prefab(f"SakuraDesa{k}", "Sakura_1" if k % 2 else "Sakura_Besar", q_)
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', leaves="true", ray_alpha="0.12")

    nl = 0
    for nm, (bx_, by_) in (("Herb", (kx_ - 60, ky_ + 50)), ("Herb", (gx0 + 60, gy0 - 50)), ("GoldCoin", (sx_ + 50, sy_ + 30)),
                           ("Herb", (gx0 - 30, gy0 + 70)), ("Potion", vat(47.0, 71.0))):
        tx_, ty_ = int(bx_ // TILE), int(by_ // TILE)
        if corridor[tx_, ty_] and not near_building(bx_, by_, 6):
            nl += 1
            inst(f"Pinggir{nm}{nl}", collect[nm], (bx_, by_))

    # ------------------------------------------------------------ musuh, peti, collectible (perjalanan)
    enemy_scene = sc.ext_res("PackedScene", "res://scenes/entities/Enemy.tscn")
    taken = []
    arena_t = np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 11 * TILE

    def spot(pt, r_min=20):
        """Titik bebas terdekat (spiral sampai 140 px) dari pt (px)."""
        for r in [0] + list(range(12, 141, 12)):
            for a_ in range(0, 360, 30):
                x, y = round(pt[0] + math.cos(math.radians(a_)) * r), round(pt[1] + math.sin(math.radians(a_)) * r)
                tx_, ty_ = int(x // TILE), int(y // TILE)
                if not (0 <= tx_ < W and 0 <= ty_ < H) or not corridor[tx_, ty_] or arena_t[tx_, ty_] or village_zone[tx_, ty_] \
                        or road_dist(x, y) < r_min:
                    continue
                if near_building(x, y, 14) or any(math.hypot(x - qx2, y - qy2) < 26 for qx2, qy2 in taken):
                    continue
                taken.append((x, y))
                return (round(x), round(y))
        return None

    # pasukan King Subiyan (Orc + Skeleton) & jamur/slime liar. Zona aman: kelompok pertama >= 44 tile dari gerbang desa.
    groups = {"Selatan1": ((122, 118), ["orc", "orc_rogue", "mushroom2"]),
              "Selatan2": ((122, 128), ["skeleton", "skeleton_rogue", "orc_warrior"]),
              "Selatan3": ((176, 104), ["mushroom2", "slime3", "orc_shaman"]),
              "Selatan4": ((132, 142), ["orc", "slime3"]),
              "Timur1": ((176, 86), ["skeleton_warrior", "orc_warrior", "skeleton_rogue"]),
              "Utara1": ((156, 56), ["skeleton_mage", "orc_shaman", "skeleton"]),
              "Utara2": ((118, 50), ["orc_warrior", "skeleton_warrior", "orc_rogue"]),
              "Utara3": ((142, 46), ["mushroom2", "slime3"]),
              "Semenanjung": ((112, 42), ["skeleton_mage", "skeleton_rogue", "orc_warrior"])}
    n_mob = 0
    for gname, ((gx_t, gy_t), ids) in groups.items():
        for k, eid in enumerate(ids):
            ang = k * math.tau / len(ids) + 0.5
            q = spot((gx_t * TILE + 8 + math.cos(ang) * 34, gy_t * TILE + 8 + math.sin(ang) * 26))
            if q:
                inst(f"Musuh{gname}_{k + 1}", enemy_scene, q, enemy_id=f'"{eid}"')
                n_mob += 1
    chests = {"PetiSelatan": (124, 134), "PetiTenggara": (150, 142), "PetiTimur": (190, 96), "PetiUtara": (146, 44), "PetiSemenanjung": (110, 40)}
    for nm, (cx2, cy2) in chests.items():
        q = open_spot(tpx((cx2, cy2)))
        if not q:
            print("PERINGATAN: peti", nm, "tidak dapat tempat")
            continue
        inst(nm, chest_scene, q, roll_count="2")
        for kind, (ox, oy) in (("Herb", (30, 14)), ("GoldCoin", (-28, 16)), ("Ore", (2, 34))):
            q2 = spot((q[0] + ox, q[1] + oy), 0)
            if q2:
                nl += 1
                inst(f"{kind}{nl}", collect[kind], q2)
    for k in range(30):
        i_ = rng.randint(i_gate + 10, i_boss - 20)
        th = rng.random() * math.tau
        pt = (route[i_][0] + math.cos(th) * rng.randint(50, 130), route[i_][1] + math.sin(th) * rng.randint(40, 100))
        q = spot(pt, 30)
        if q:
            kind = ("Herb", "GoldCoin", "Ore", "Herb")[k % 4]
            nl += 1
            inst(f"{kind}{nl}", collect[kind], q)
    for k, pt in enumerate((at(112, 112), at(150, 62), at(104, 52))):
        q = spot(pt, 24)
        if q:
            inst(f"Potion{k + 1}", collect["Potion"], q)

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    sc.node("BossSpawn", "Marker2D", ".", position=v2(*[int(v) for v in P["boss_arena"]]))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Tedy", "Marker2D", "NPCSpawns", position=v2(*tedy_pos), **{"metadata/npc_id": '"tedy"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')

    out = os.path.join(ROOT, "scenes/world/Ch5_PohonDunia.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ uji keterhubungan
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
    r_gate, r_open = reach(band | bar_block | sc_block), reach(bar_block | sc_block)
    east_gap = open_l & (tcol >= 150) & (trow >= 58) & (trow <= 78)       # celah timur akar E (rute utama)
    r_all, r_short = reach(sc_block), reach(east_gap)                      # jalan pintas: tanpa celah timur, lewat akar tumbang
    pts_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in [tedy_pos, wira_pos, sekar_pos, dimas_pos] + clue_pts)
    print("start di daratan =", bool(walk[int(start[0] // TILE), int(start[1] // TILE)]),
          "| desa, 4 NPC & 3 petunjuk terjangkau saat gerbang tertutup =", pts_ok)
    print("gerbang mengunci puzzle =", not r_gate[t_["puzzle"]], "| puzzle terjangkau saat terbuka =", bool(r_open[t_["puzzle"]]))
    print("segel cabang mengunci arena =", not r_open[t_["boss_arena"]], "| arena terjangkau lewat tangga =", bool(r_all[t_["boss_arena"]]),
          "| jalan pintas (akar tumbang dibuka, tanpa celah timur) menembus ke tajuk =", bool(r_short[t_["boss_arena"]]),
          "| tanpa akar tumbang & celah timur dataran utara terkunci =", not reach(east_gap | sc_block)[t_["puzzle"]])
    length = float(np.sum(np.hypot(*np.diff(route[i_gate:i_boss], axis=0).T))) / TILE
    print("musuh:", n_mob, "| jalan gerbang->arena %.0f tile" % length)
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and walk[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Ch5_PohonDunia.tscn:", nm_, "pohon/batu, objek di luar daratan:", len(bad), bad[:6], "| koridor", int(corridor.sum()),
          "tile | collectible", nl)
    return bad


if __name__ == "__main__":
    build()
