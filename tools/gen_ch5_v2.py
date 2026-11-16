"""Generator Ch5_PohonDunia.tscn v2: bentuk wilayah dari docs/layout/region_layout.json + DESA AKAR (desa di antara akar raksasa).

Jalankan dari folder proyek (setelah make_prefabs.py, make_villagers.py, gen_akar_tileset.py, gen_interior.py):
    python tools/gen_ch5_v2.py
Tahap 1 (bagian ini): peta 152x117 tile, batas akar & laut ungu, Desa Akar + pinggiran + 3 petunjuk, gerbang kabut ajaib.
  - Lantai: rumput; jalan = tanah (autotile sudut / marching squares, tools/gen_akar_tileset.py).
  - Batas: laut UNGU di utara/barat/timur (biru pada *_layout.png), akar raksasa (relief kulit kayu) di luar mask.
  - AKAR RAKSASA Pohon Dunia (punggung kayu di DALAM wilayah) memancar dari BATANG di semenanjung utara: akar A ke pantai barat,
    akar B ke tebing selatan. Desa Akar ada di ceruk barat daya di antara keduanya; celah akar B = gerbang desa (kabut ajaib, quest_stage 1).
Blueprint Desa Akar (tema Tree): KOLAM AKAR ungu di tengah dikelilingi jalan tanah, pos Tedy (interior, rumah menara ungu) di kaki akar A,
  rumah Nyai Sekar, Wira, Dimas & warga di sekeliling kolam; pinggiran: kuil akar (barat laut), kebun sakura (barat), mata air ungu (timur).
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
W, H = LAYOUT["ukuran_tile"]            # 152 x 117
PX_W, PX_H = LAYOUT["ukuran_px"]        # 2432 x 1872
DOOR_DX = json.load(open(os.path.join(ROOT, "assets/props/buildings/variants/_pintu.json"), encoding="utf-8"))
TRUNK = (68, 24)                        # batang Pohon Dunia (semenanjung utara)
# akar raksasa (dataran kayu di DALAM wilayah, tile): (polyline, setengah lebar)
RIDGES = [([TRUNK, (TRUNK[0] + 0.01, TRUNK[1])], 7.0),                                          # batang Pohon Dunia
          ([(64, 30), (56, 40), (44, 49), (28, 53), (12, 55), (-3, 57)], 3.2),                  # akar A: dinding utara Desa Akar
          ([(66, 30), (64, 44), (61, 57), (59.5, 65)], 3.2),                                    # akar B atas
          ([(58.5, 76), (57.5, 85), (57, 96)], 3.2)]                                            # akar B bawah (celah = gerbang desa)
GATE_C = (59.2, 70.5)                   # pusat celah akar B (gerbang desa, kabut ajaib)
POND_C, POND_R = (36, 71), (4.6, 3.2)   # kolam akar di tengah Desa Akar
SPRING_C, SPRING_R = (51, 76.5), 2.4    # mata air ungu (pinggiran timur)
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
    rng = random.Random(5005)
    mask = np.array([[c == "#" for c in row] for row in LAYOUT["mask"]]).T
    P = {k: tpx(v) for k, v in LAYOUT["titik_tile"].items()}
    orig = organic.polyline_samples([tpx(p) for p in LAYOUT["jalan_tile"]], 12.0)
    gx, gy = organic.grid(W, H)

    def idx_near(arr, pt):
        return int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))

    # ------------------------------------------------------------ rute: entry -> kolam akar -> gerbang (celah akar B) -> jalan layout
    i_cont = idx_near(orig, tpx((65, 67)))
    seg_vil = organic.polyline_samples([P["entry"], tpx((33, 80)), tpx((36, 76.2)), tpx((44, 75)), tpx((50, 72.5)), tpx(GATE_C),
                                        tpx((65, 67))], 12.0)
    route = np.vstack([seg_vil, orig[i_cont:]])

    def route_i(pt):
        return idx_near(route, pt)

    i_boss = route_i(P["boss_arena"])

    # ------------------------------------------------------------ laut ungu (biru di *_layout.png), daratan, akar raksasa
    lay = np.array(Image.open(os.path.join(ROOT, "docs/layout/Ch5_PohonDunia_layout.png")).convert("RGB")).astype(int)
    sea_img = np.zeros_like(mask)
    for tx in range(W):
        for ty in range(H):
            py_, px_ = min(lay.shape[0] - 1, ty * 5 + 2), min(lay.shape[1] - 1, tx * 5 + 2)
            sea_img[tx, ty] = abs(lay[py_, px_] - np.array([40, 90, 160])).sum() < 60 and ty >= 6
    sea_img[:, :6] = sea_img[:, 6:7]
    land = dilate(mask, 2) & ~sea_img
    land |= np.hypot(gx - P["entry"][0], gy - P["entry"][1]) <= 3.5 * TILE
    nz_r = organic.smooth_noise(gx, gy, 31)
    ridge = np.zeros_like(mask)
    for pts, hw in RIDGES:
        ridge |= dist_to(gx, gy, organic.polyline_samples([tpx(p_) for p_ in pts], 12.0)) <= hw * TILE + 10 * nz_r
    land &= ~ridge
    land = dilate(erode(land, 1), 1) | (land & dilate(sea_img, 1))
    nz_l = organic.smooth_noise(gx, gy, 37)
    pond = (np.hypot((gx / TILE - 0.5 - POND_C[0]) / POND_R[0], (gy / TILE - 0.5 - POND_C[1]) / POND_R[1]) + 0.05 * nz_l < 1.0) & land
    pond |= (np.hypot(gx / TILE - 0.5 - SPRING_C[0], gy / TILE - 0.5 - SPRING_C[1]) + 0.1 * nz_l < SPRING_R) & land
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
    corridor = land & ~face_m & ~band

    # ------------------------------------------------------------ jalan tanah (rute + cabang pinggiran)
    SHRINE = tpx((12, 64))        # kuil akar (barat laut)
    GARDEN = tpx((8, 71))         # kebun sakura (barat)
    SPRING = tpx(SPRING_C)        # mata air ungu (timur)
    road_k = winding(tpx((30, 66)), SHRINE, 20, 81, n=4)
    road_g = winding(tpx((30, 75)), GARDEN, 18, 83, n=4)
    road_ring = np.vstack([organic.polyline_samples([tpx((36 + 7.6 * math.cos(t), 71.3 + 5.4 * math.sin(t))) for t in
                                                     np.linspace(0, math.tau, 40)], 12.0)])
    roads = np.vstack([route, road_k, road_g, road_ring])
    vx = (np.arange(W + 1) * TILE)[:, None] * np.ones((1, H + 1))
    vy = (np.arange(H + 1) * TILE)[None, :] * np.ones((W + 1, 1))
    vn = organic.smooth_noise(vx, vy, 4)
    dirt_v = dist_to(vx, vy, roads) <= 22 + 5 * vn
    pads = [(SHRINE, 60), (GARDEN, 50), (P["puzzle"], 60), (P["bonfire_preboss"], 46), (P["boss_arena"], 140), (P["entry"], 40)]
    for (px_, py_), rr in pads:
        dirt_v |= np.hypot(vx - px_, vy - py_) <= rr + 10 * vn

    # ------------------------------------------------------------ peta tile
    ground, cliffc, blockc = [], [], []
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
            key = (int(dirt_v[tx, ty]), int(dirt_v[tx + 1, ty]), int(dirt_v[tx, ty + 1]), int(dirt_v[tx + 1, ty + 1]))
            if key == (0, 0, 0, 0):
                a_ = GRASS[h_ % len(GRASS)]
            elif key == (1, 1, 1, 1):
                a_ = DIRT_DETAIL[h_ % 2] if h_ % 29 == 0 else DIRT[0]
            else:
                a_ = CORNER_TILES[key]
            ground.append((tx, ty, 0, a_[0], a_[1]))

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
    cloud_script = sc.ext_res("Script", "res://scripts/world/CloudBarrier.gd")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    clue_script = sc.ext_res("Script", "res://scripts/world/Clue.gd")

    sc.node("Ch5_PohonDunia", "Node2D", script=f'ExtResource("{script}")', chapter="5", music_name='"ch5_pohon_dunia"',
            boss_music_name='"boss_final_king_subiyan"',
            guide_route="PackedVector2Array(" + ", ".join(f"{int(x)}, {int(y)}" for x, y in route[::5]) + ")",
            map_size=f"Vector2i({PX_W}, {PX_H})", boss_scene=f'ExtResource("{boss_scene}")')
    sc.node("Ajaib", "CanvasModulate", ".", color="Color(1, 0.94, 1.04, 1)")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_akar}")')
    sc.node("Akar", "TileMapLayer", ".", tile_map_data=b64cells(cliffc), tile_set=f'ExtResource("{ts_akar}")')
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

    # ------------------------------------------------------------ DESA AKAR
    houses = {"PosTedy": ("Rumah_Menara_Ungu", (45, 65.6)),            # pos Tedy (interior) di kaki akar A
              "RumahSekar": ("Rumah_Loteng_Ungu", (25.5, 65.6)),       # tetua desa
              "RumahWira": ("Rumah_Runcing_Ungu", (21, 80.6)),         # penjaga akar
              "RumahDimas": ("Pondok_Ungu", (46, 81.6)),               # prajurit muda
              "RumahWarga": ("Rumah_Runcing_Ungu", (13, 75.6))}
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
        prefab(nm, pref, at(x, y))
    for i, (x, y) in enumerate(((29.0, 67.6), (43.0, 67.6), (29.4, 75.6), (42.6, 75.6), (33.0, 82.6), (53.6, 72.6))):
        prefab(f"Lentera{i}", "Lentera_Tiang", at(x, y), solid=False)
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
    wira_pos, sekar_pos, dimas_pos = at(24.4, 82.4), at(29.6, 67.8), at(49.6, 80.0)
    npc("Tedy", tedy_pos, npc_id='"tedy"')
    npc("Wira", wira_pos, npc_id='"wira"', dialog_id='"ch5_wira"', villager_chapter="5")
    npc("Sekar", sekar_pos, npc_id='"sekar"', dialog_id='"ch5_sekar"', villager_chapter="5")
    npc("Dimas", dimas_pos, npc_id='"dimas"', dialog_id='"ch5_dimas"', villager_chapter="5")
    npc("Pedagang", at(39.4, 78.0), npc_id='"pedagang"', opens_shop="true")
    sc.node("PintuTedy", "Area2D", "Objects", position=v2(door_x, door_y + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_PosTedy.tscn"', hint_text='"E: Masuk pos Tedy"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuTedy", shape=f'SubResource("{sc.rect_shape(46, 26)}")')

    start = tuple(int(v) for v in route[3])
    bf1 = at(32.4, 77.6)
    inst("Bonfire1", bonfire_scene, bf1)
    inst("BenderaMasuk", checkpoint_scene, at(35.6, 84.0))
    inst("BenderaGerbang", checkpoint_scene, at(54.2, 68.4))
    inst("BenderaKuil", checkpoint_scene, (kx_ + 60, ky_ + 30))
    inst("PetiKuil", chest_scene, (kx_ - 30, ky_ + 36), roll_count="2")
    inst("PetiKebun", chest_scene, (gx0 - 10, gy0 + 50), roll_count="2")
    clue_pts = [(kx_ + 4, ky_ + 18), (gx0 + 4, gy0 + 6), (sx_ - 36, sy_ - 30)]
    for k_, (ck, pos) in enumerate(zip(("jejak", "catatan", "barang"), clue_pts), start=1):
        sc.node(f"Petunjuk{k_}", "Area2D", "Objects", script=f'ExtResource("{clue_script}")', position=v2(*pos),
                flag=f'"ch5_petunjuk_{k_}"', dialog_id=f'"ch5_petunjuk_{k_}"', required_step='"ch5_awal:petunjuk"', clue_kind=f'"{ck}"')
        recorded.append(pos)
        npc_positions.append(pos)
    inst("PulangGua", exit_scene, tuple(int(v) for v in P["entry"]), to_chapter="4", sign_text='"Kembali ke Gua Rantai"')
    npc_positions += [bf1, start, SHRINE, GARDEN, SPRING, P["puzzle"], P["boss_arena"]]

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
    village_zone = (tcol >= 6) & (tcol <= 56) & (trow >= 58) & (trow <= 88)
    keypts = [P[k] for k in ("entry", "puzzle", "bonfire_preboss", "boss_arena")] + [bf1, start] + npc_positions
    no_deco = dilate(band, 3) | (np.hypot(gx - P["boss_arena"][0], gy - P["boss_arena"][1]) < 12 * TILE)

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
        q_ = at(x, y)
        tx_, ty_ = int(q_[0] // TILE), int(q_[1] // TILE)
        if corridor[tx_, ty_] and road_dist(*q_) > 30 and not near_building(q_[0], q_[1], 10):
            prefab(f"SakuraDesa{k}", "Sakura_1" if k % 2 else "Sakura_Besar", q_)
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', leaves="true", ray_alpha="0.12")

    nl = 0
    for nm, (bx_, by_) in (("Herb", (kx_ - 60, ky_ + 50)), ("Herb", (gx0 + 60, gy0 - 50)), ("GoldCoin", (sx_ + 50, sy_ + 30)),
                           ("Herb", (gx0 - 30, gy0 + 70)), ("Potion", at(47.0, 71.0))):
        tx_, ty_ = int(bx_ // TILE), int(by_ // TILE)
        if corridor[tx_, ty_] and not near_building(bx_, by_, 6):
            nl += 1
            inst(f"Pinggir{nm}{nl}", collect[nm], (bx_, by_))

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
    r_gate, r_open = reach(band), reach(np.zeros_like(walk))
    pts_ok = all(r_gate[int(px_ // TILE), int(py_ // TILE)] for px_, py_ in [tedy_pos, wira_pos, sekar_pos, dimas_pos] + clue_pts)
    print("start di daratan =", bool(walk[int(start[0] // TILE), int(start[1] // TILE)]),
          "| desa, 4 NPC & 3 petunjuk terjangkau saat gerbang tertutup =", pts_ok)
    print("gerbang mengunci puzzle =", not r_gate[t_["puzzle"]], "| puzzle terjangkau saat terbuka =", bool(r_open[t_["puzzle"]]),
          "| arena terjangkau saat terbuka =", bool(r_open[t_["boss_arena"]]))
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and walk[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Ch5_PohonDunia.tscn:", nm_, "pohon/batu, objek di luar daratan:", len(bad), bad[:6], "| koridor", int(corridor.sum()),
          "tile | collectible", nl)
    return bad


if __name__ == "__main__":
    build()
