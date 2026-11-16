"""Generator Village.tscn v2: DESA ALGORIA BESAR (desa awal, tepi pantai) - permintaan Alfian: desa yang besar.

Jalankan dari folder proyek (setelah make_prefabs.py, make_houses.py, make_fields.py, make_villagers.py, gen_coast_tileset.py,
gen_interior.py):   python tools/gen_algoria.py
Prototipe lama (desa kecil 50x40) dicadangkan di ..\\_backup_scenes_organik\\Village_desa_kecil_lama.tscn.

Peta 128x96 tile (2048x1536 px), tileset pesisir (coast_tileset.tres: rumput + pasir + laut bertepi pasir + papan dermaga):
  - Batas: hutan lebat di utara & barat (pohon bertabrakan + Bounds), laut di selatan & timur (air ditutup penghalang tak terlihat).
  - JALAN UTAMA (batu) dari GERBANG HUTAN di utara (papan jalan ke Hutan Indeks) sampai PELABUHAN di selatan; JALAN PASAR barat-timur;
    jalan ladang (barat laut) & jalan timur.
  - ALUN-ALUN di persimpangan: sumur, 4 lapak, lampu, spanduk; BALAI DESA Joko (Rumah_Menara_Merah) & TOKO Pedagang di sisi utara.
  - PERMUKIMAN BARAT: rumah Raka (bisa dimasuki, Raka mulai di depannya) + bengkel tempa kecil (landasan = Tempa), rumah warga.
  - PERMUKIMAN TIMUR + TAMAN berkolam; LADANG & lumbung di barat laut; PELABUHAN kecil di pantai selatan (dermaga, kapal, lapak ikan).
"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ch1_v2 as v2mod  # noqa: E402
import organic  # noqa: E402
from gen_canyon_tileset import CORNER_TILES  # noqa: E402
from gen_coast_tileset import GRASS, PLANK, SAND, SAND_DETAIL, WATER_CORNER  # noqa: E402
from gen_village import ROOT, TILE, Scene, v2  # noqa: E402

dist_to, dilate, erode, b64cells, tpx = v2mod.dist_to, v2mod.dilate, v2mod.erode, v2mod.b64cells, v2mod.tpx
DOOR_DX = json.load(open(os.path.join(ROOT, "assets/props/buildings/variants/_pintu.json"), encoding="utf-8"))
W, H = 128, 96
PX_W, PX_H = W * TILE, H * TILE
GATE_T = (63, 2.5)                      # papan jalan ke Hutan Indeks (ujung utara jalan utama)
PLAZA = (52, 74, 38, 56)                # alun-alun (x0, x1, y0, y1) tile
POND_C, POND_R = (97, 63), (5.0, 3.4)   # kolam taman timur
DOCKS = [(62, 64, 80, 93), (84, 86, 83, 93)]   # dermaga (x0, x1, y0, y1) inklusif
PREFAB_SIZE = {}


def at(x, y):
    return (round(x * TILE + 8), round(y * TILE + 8))


def build():
    for e in json.load(open(os.path.join(ROOT, "scenes/prefabs/_prefabs.json"), encoding="utf-8")):
        PREFAB_SIZE[e["name"]] = (e["w"], e["h"])
    rng = random.Random(1001)
    gx, gy = organic.grid(W, H)
    tcol, trow = np.arange(W)[:, None], np.arange(H)[None, :]
    nz = organic.smooth_noise(gx, gy, 17)

    # ------------------------------------------------------------ laut (selatan & timur), daratan, kolam
    coast_y = 84 + 2.2 * np.sin(tcol * 0.17) + 1.2 * nz
    coast_x = 120 + 2.0 * np.sin(trow * 0.21) + 1.2 * nz
    sea = (trow >= coast_y) | ((tcol >= coast_x) & (trow >= 24))
    pond = (np.hypot((tcol - POND_C[0]) / POND_R[0], (trow - POND_C[1]) / POND_R[1]) + 0.06 * nz < 1.0)
    water = sea | pond
    land = ~water
    dock = np.zeros_like(land)
    for x0, x1, y0, y1 in DOCKS:
        dock[x0:x1 + 1, y0:y1 + 1] = True
    dock &= water | dilate(water, 3)
    # hutan batas: utara & barat (dan pojok timur laut), celah jalan utama di gerbang utara
    forest = ((trow <= 4 + 1.5 * nz) & ~((tcol >= 59) & (tcol <= 67))) | (tcol <= 4 + 1.5 * nz) \
        | ((tcol >= 116 + 2 * nz) & (trow < 26))
    forest &= land

    # ------------------------------------------------------------ jalan batu & pasir
    stone = np.zeros_like(land)
    stone[62:65, 3:81] = True                       # JALAN UTAMA (gerbang hutan -> pelabuhan)
    stone[12:114, 46:49] = True                     # JALAN PASAR (barat-timur)
    stone[12:62, 20:23] = True                      # jalan ladang (barat laut)
    stone[65:112, 28:31] = True                     # jalan timur
    stone[PLAZA[0]:PLAZA[1] + 1, PLAZA[2]:PLAZA[3] + 1] = True     # ALUN-ALUN
    stone[58:69, 77:81] = True                      # pangkal dermaga
    stone &= land & ~forest
    vx = (np.arange(W + 1) * TILE)[:, None] * np.ones((1, H + 1))
    vy = (np.arange(H + 1) * TILE)[None, :] * np.ones((W + 1, 1))
    vn = organic.smooth_noise(vx, vy, 4)
    pad_w = np.pad(water, 1, mode="edge")
    water_v = pad_w[:-1, :-1] & pad_w[1:, :-1] & pad_w[:-1, 1:] & pad_w[1:, 1:]
    dw = np.full(water.shape, 99.0)
    cur = water.copy()
    dw[cur] = 0
    for k in range(1, 7):
        nxt = dilate(cur, 1)
        dw[nxt & ~cur] = k
        cur = nxt
    pad_d = np.pad(dw, 1, mode="edge")
    dw_v = np.minimum(np.minimum(pad_d[:-1, :-1], pad_d[1:, :-1]), np.minimum(pad_d[:-1, 1:], pad_d[1:, 1:]))
    sand_v = (dw_v <= 3.0 + 2.0 * vn) | (dw_v <= 1)          # pantai & tepi kolam berpasir
    # jalan setapak pasir: dari jalan batu ke rumah-rumah & taman (garis lebar di sekitar jalan batu)
    stone_px = np.argwhere(stone)
    if len(stone_px):
        spts = np.column_stack([stone_px[:, 0] * TILE + 8, stone_px[:, 1] * TILE + 8]).astype(float)
        sand_v |= dist_to(vx, vy, spts[::3]) <= 24 + 5 * vn

    # ------------------------------------------------------------ peta tile
    ground, stonec, dockc, blockc = [], [], [], []
    for tx in range(W):
        for ty in range(H):
            h_ = (tx * 7 + ty * 13 + tx * ty) % 97
            if water[tx, ty]:
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
            if stone[tx, ty]:
                s_ = [(6, 10), (7, 10), (8, 10)][(tx * 7 + ty * 3) % 3]
                stonec.append((tx, ty, 0, s_[0], s_[1]))

    # ------------------------------------------------------------ scene
    sc = Scene()
    ts_coast = sc.ext_res("TileSet", "res://assets/tilesets/coast_tileset.tres")
    ts_world = sc.ext_res("TileSet", "res://assets/tilesets/world_tileset.tres")
    block_ts = sc.ext_res("TileSet", "res://assets/tilesets/block_tileset.tres")
    script = sc.ext_res("Script", "res://scripts/world/Village.gd")
    player_scene = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    npc_scene = sc.ext_res("PackedScene", "res://scenes/entities/NPC.tscn")
    bonfire_scene = sc.ext_res("PackedScene", "res://scenes/entities/Bonfire.tscn")
    checkpoint_scene = sc.ext_res("PackedScene", "res://scenes/entities/Checkpoint.tscn")
    exit_scene = sc.ext_res("PackedScene", "res://scenes/world/RegionExit.tscn")
    door_script = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    anvil_script = sc.ext_res("Script", "res://scripts/entities/Anvil.gd")
    animal_script = sc.ext_res("Script", "res://scripts/world/Animal.gd")
    atmos_script = sc.ext_res("Script", "res://scripts/world/Atmosphere.gd")
    collect = {n: sc.ext_res("PackedScene", f"res://scenes/entities/{n}.tscn") for n in ("Herb", "GoldCoin")}

    sc.node("Village", "Node2D", script=f'ExtResource("{script}")', map_size=f"Vector2i({PX_W}, {PX_H})")
    sc.node("Ground", "TileMapLayer", ".", tile_map_data=b64cells(ground), tile_set=f'ExtResource("{ts_coast}")')
    sc.node("Path", "TileMapLayer", ".", tile_map_data=b64cells(stonec), tile_set=f'ExtResource("{ts_world}")')
    sc.node("Dermaga", "TileMapLayer", ".", tile_map_data=b64cells(dockc), tile_set=f'ExtResource("{ts_coast}")')
    sc.node("AirPenghalang", "TileMapLayer", ".", tile_map_data=b64cells(blockc), tile_set=f'ExtResource("{block_ts}")')
    sc.node("Decor", "Node2D", ".")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")

    recorded, buildings = [], []

    def prefab(node, pref, pos, solid=True, **props):  # noqa: E301
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

    fence_w = PREFAB_SIZE["Pagar_Kayu"][0]

    def house(name, pref, x, y, fence=True):
        prefab(name, pref, at(x, y))
        if not fence:
            return
        hw = PREFAB_SIZE[pref][0] / (2 * TILE) + 0.2
        dd = x + DOOR_DX.get(pref, 0) / TILE
        n = 0
        for x0, x1 in ((x - hw, dd - 1.7), (dd + 1.7, x + hw)):
            xx = x0 * TILE
            while xx + fence_w / 2 <= x1 * TILE + 8:
                prefab(f"Pagar_{name}_{n}", "Pagar_Kayu", (round(xx + fence_w / 2 + 8), round((y + 1.2) * TILE + 8)), solid=False)
                xx += fence_w
                n += 1

    # ---- ALUN-ALUN: balai desa, toko, sumur, lapak, lampu, spanduk
    house("BalaiDesa", "Rumah_Menara_Merah", 54, 37.5, fence=False)
    house("TokoAlun", "Toko_Merah", 72, 37.5, fence=False)
    prefab("Sumur", "Sumur", at(63.5, 51.5))
    for nm, pref, (x, y) in (("LapakKue", "Lapak_Tenda_Merah", (56, 42)), ("LapakBuah", "Lapak_Tenda_Kuning", (70.5, 42)),
                             ("LapakSayur", "Lapak_Sayur", (56, 54)), ("LapakKain", "Lapak_Kain", (70.5, 54)),
                             ("KeranjangAlun", "Keranjang_Buah_1", (58.6, 54.4)), ("TongAlun", "Barel_Besar", (68.4, 41.4))):
        prefab(nm, pref, at(x, y))
    for i, (x, y) in enumerate(((51.4, 37.8), (74.6, 37.8), (51.4, 56.6), (74.6, 56.6), (61.2, 33.0), (65.8, 60.0))):
        prefab(f"LampuAlun{i}", "Lampu_Tiang", at(x, y))
    for i, (x, y, k) in enumerate(((60.4, 38.6, 1), (66.6, 38.6, 2), (60.4, 56.2, 3), (66.6, 56.2, 1))):
        prefab(f"Spanduk{i}", f"Spanduk_{k}", at(x, y), solid=False)
    # ---- selatan alun-alun: penginapan & rumah
    house("Penginapan", "Rumah_Loteng_Biru", 56, 68.5)
    house("RumahSelatan", "Rumah_Teras_Biru", 74, 68.5)
    # ---- PERMUKIMAN BARAT: rumah Raka (interior) + bengkel tempa kecil, rumah warga
    house("RumahRaka", "Rumah_Teras_Coklat", 31, 64.5)
    prefab("LandasanRaka", "Landasan_1", at(40.6, 63.6), script=f'ExtResource("{anvil_script}")')
    prefab("MejaKerjaRaka", "MejaKerja_Kayu_2", at(44.2, 63.8))
    prefab("TungkuRaka", "Tungku_Bata_2", at(40.4, 59.6))
    prefab("KayuRaka", "Tumpukan_Kayu", at(44.6, 59.8), solid=False)
    house("RumahBarat1", "Rumah_Runcing_Coklat", 17, 64.5)
    house("RumahBarat2", "Rumah_Loteng_Hijau", 21, 42.5)
    house("RumahBarat3", "Rumah_Runcing_Merah", 33, 42.5)
    house("RumahBarat4", "Pondok_Hijau", 43.5, 42.5)
    house("RumahBarat5", "Rumah_Loteng_Merah", 20, 77.5)
    house("RumahBarat6", "Toko_Hijau", 35, 77.5)
    # ---- PERMUKIMAN TIMUR
    house("RumahTimur1", "Rumah_Runcing_Biru", 82, 26.5)
    house("RumahTimur2", "Rumah_Loteng_Coklat", 94, 26.5)
    house("RumahTimur3", "Pondok_Kecil", 105, 26.5)
    house("RumahTimur4", "Rumah_Menara_Hijau", 88, 44.5)
    house("RumahTimur5", "Rumah_Teras_Coklat", 105, 44.5)
    # ---- LADANG & lumbung (barat laut)
    for fname, img_name, (fx0, fy0) in (("LadangA", "Ladang_A", (12, 8)), ("LadangB", "Ladang_B", (26, 9)), ("LadangC", "Ladang_C", (38, 10))):
        tex = sc.ext_res("Texture2D", f"res://assets/props/fields/{img_name}.png")
        from PIL import Image
        fw, fh = Image.open(os.path.join(ROOT, "assets/props/fields", img_name + ".png")).size
        px0, py0 = fx0 * TILE, fy0 * TILE
        sc.node(fname, "Sprite2D", "Decor", texture=f'ExtResource("{tex}")', position=v2(px0, py0), centered="false")
        buildings.append((px0 + fw / 2, py0 + fh, fw, fh))
        n = 0
        for yy in (py0 - 4, py0 + fh + 6):
            xx = px0
            while xx + fence_w <= px0 + fw + 2:
                if not (yy > py0 and abs(xx + fence_w / 2 - (px0 + fw / 2)) < fence_w):
                    prefab(f"Pagar_{fname}_{n}", "Pagar_Kayu", (round(xx + fence_w / 2), yy), solid=False)
                    n += 1
                xx += fence_w
    prefab("Lumbung", "Lumbung", at(52, 18.5))
    prefab("OrangOrang1", "OrangOrangSawah", at(18, 12))
    prefab("OrangOrang2", "OrangOrangSawah", at(32, 12.6))
    # ---- PELABUHAN (selatan): gudang, lapak ikan, kargo, kapal
    prefab("GudangPelabuhan", "Gudang_Panjang", at(46, 80.5))
    for nm, pref, (x, y) in (("LapakIkan", "Lapak_Tenda_Merah", (69, 79.5)), ("KeranjangIkan", "Keranjang_Buah_2", (71.6, 80.4)),
                             ("PetiDermaga", "Peti_Tumpuk_1", (58.4, 79.6)), ("TongDermaga", "Tong_Peti", (57.6, 78.2))):
        prefab(nm, pref, at(x, y))
    house("RumahNelayan", "Pondok_Hijau", 80, 79.5, fence=False)
    for nm, pref, (x, y) in (("KapalLayar", "Kapal_Layar", (68.5, 92.5)), ("PerahuNelayan", "Perahu_Kecil", (89, 90)),
                             ("PerahuPantai", "Perahu_Kecil", (100, 88))):
        prefab(nm, pref, (round(x * TILE + 8), round(y * TILE + 12)), solid=False)
        recorded.pop()                      # kapal & perahu memang di atas air
    # ---- TAMAN timur: kolam, bangku, bunga
    for nm, pref, (x, y) in (("BangkuTaman", "Tronk_Kayu", (90, 58.4)), ("BatuTaman", "Batu_Besar_2", (104, 60)),
                             ("BatuTaman2", "Batu_Sedang_1", (91, 68))):
        prefab(nm, pref, at(x, y))
    # ---- gerbang hutan (utara): papan jalan, tiang pagar, lentera
    for i, (x, y) in enumerate(((60.4, 6.0), (66.2, 6.0))):
        prefab(f"TiangGerbang{i}", "Tiang_Pagar", at(x, y), solid=False)
    for i, (x, y) in enumerate(((60.6, 12.0), (65.6, 22.0), (60.6, 30.0), (65.8, 70.0), (60.6, 76.0), (30.0, 49.8),
                                (46.0, 49.8), (82.0, 49.8), (100.0, 49.8))):
        prefab(f"Lentera{i}", "Lentera_Tiang", at(x, y), solid=False)
    prefab("PapanPasarBarat", "Papan_Kiri", at(48.4, 45.0), solid=False)
    prefab("PapanPasarTimur", "Papan_Kanan", at(78.4, 45.0), solid=False)
    prefab("PapanPelabuhan", "Papan_Tiang", at(66.0, 74.6), solid=False)

    # ------------------------------------------------------------ NPC, penanda
    bp, (bx_, by_) = "Rumah_Menara_Merah", (54, 37.5)
    joko_pos = at(bx_ + DOOR_DX.get(bp, 0) / TILE + 2.4, by_ + 1.6)
    rp, (rx_, ry_) = "Rumah_Teras_Coklat", (31, 64.5)
    rdoor = at(rx_ + DOOR_DX.get(rp, 0) / TILE, ry_)
    start = (rdoor[0], rdoor[1] + 34)
    npcs = {"Joko": (joko_pos, {"npc_id": '"joko"'}),
            "PedagangAlun": (at(69.4, 39.4), {"npc_id": '"pedagang"', "opens_shop": "true"}),
            "Ani": (at(57.8, 44.0), {"npc_id": '"ani"', "dialog_id": '"ch0_ani"'}),
            "Rudi": (at(63.6, 86.0), {"npc_id": '"rudi"', "dialog_id": '"ch0_rudi"'}),
            "Sumi": (at(25.0, 16.6), {"npc_id": '"sumi"', "dialog_id": '"ch0_sumi"'}),
            "Bagas": (at(66.8, 8.0), {"npc_id": '"bagas"', "dialog_id": '"ch0_bagas"'})}
    for nm, (pos, props) in npcs.items():
        inst(nm, npc_scene, pos, **props)
    sc.node("PintuRaka", "Area2D", "Objects", position=v2(rdoor[0], rdoor[1] + 14), script=f'ExtResource("{door_script}")',
            interior_scene='"res://scenes/world/Interior_RumahRaka.tscn"', hint_text='"E: Masuk rumah"')
    sc.node("CollisionShape2D", "CollisionShape2D", "Objects/PintuRaka", shape=f'SubResource("{sc.rect_shape(46, 26)}")')
    bonfire = at(66.6, 59.4)
    inst("Bonfire", bonfire_scene, bonfire)
    inst("BenderaAlun", checkpoint_scene, at(59.6, 58.0))
    gate = at(*GATE_T)
    inst("GerbangHutan", exit_scene, gate, to_chapter="1", sign_text='"Jalan ke Hutan Indeks"')
    keypts = [p for p, _ in npcs.values()] + [start, bonfire, gate]

    # hewan desa
    animals = [("Chicken/SpriteSheetWhite", at(24, 70)), ("Chicken/SpriteSheetBrown", at(14, 70)), ("Chicken/SpriteSheetWhite", at(46, 22.6)),
               ("Cow/SpriteSheetWhite", at(14, 18)), ("Cow/SpriteSheetWhite", at(44, 17)), ("Pig/SpriteSheetPink", at(56, 22.4)),
               ("Dog/SpriteSheet", at(36, 69)), ("Cat/SpriteSheet", at(62, 59)), ("Cat/SpriteSheet", at(90, 50.6))]
    for na, (sheet_, pos) in enumerate(animals):
        tex = sc.ext_res("Texture2D", f"res://assets/ninja/animals/{sheet_}.png")
        bscale = 1.0 if sheet_.startswith(("Chicken", "Cat")) else (1.2 if sheet_.startswith("Dog") else 1.5)
        sc.node(f"Hewan{na}", "Node2D", "Objects", script=f'ExtResource("{animal_script}")', sheet=f'ExtResource("{tex}")',
                position=v2(*pos), body_scale=str(bscale), wander_radius="55.0")

    # ------------------------------------------------------------ pohon: hutan batas + rumpun di halaman/taman
    tree_cells = {"m1a": ("Trees/Model_01/Size_03.png", (0, 0, 48, 96)), "m1b": ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
                  "m2a": ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)), "m2b": ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))}
    from PIL import Image
    trees = {}
    for k, (f, box) in tree_cells.items():
        bb = Image.open(os.path.join(ROOT, "assets/props", f)).convert("RGBA").crop(box).getbbox()
        trees[k] = (f, (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3]))
    tnum = [0]

    def tree_at(x, y, collide=True):
        f, region = trees[rng.choice(list(trees))]
        tex = sc.ext_res("Texture2D", f"res://assets/props/{f}")
        w, h = region[2] - region[0], region[3] - region[1]
        name = f"Pohon{tnum[0]}"
        if collide:
            sc.node(name, "StaticBody2D", "Objects", position=v2(x, y), collision_layer=1, collision_mask=0)
        else:
            sc.node(name, "Node2D", "Objects", position=v2(x, y))
        sc.node("Sprite2D", "Sprite2D", f"Objects/{name}", texture=f'ExtResource("{tex}")', offset=v2(0, -h / 2), region_enabled="true",
                region_rect=f"Rect2({region[0]}, {region[1]}, {w}, {h})")
        if collide:
            sc.node("CollisionShape2D", "CollisionShape2D", f"Objects/{name}", position=v2(0, -3), shape=f'SubResource("{sc.rect_shape(12, 8)}")')
        tnum[0] += 1
        buildings.append((x, y, 20, 12))

    stone_d = dist_to(gx, gy, np.argwhere(stone)[:, ::1].astype(float) * TILE + 8) if stone.any() else np.full(gx.shape, 999.0)
    # hutan batas: rapat
    for ty in range(H):
        for tx in range(W):
            if forest[tx, ty] and (tx * 5 + ty * 3) % 3 == 0:
                x, y = tx * TILE + 8 + rng.randint(-5, 5), ty * TILE + 14 + rng.randint(-3, 3)
                if all(math.hypot(x - kx, y - ky) > 70 for kx, ky in keypts):
                    tree_at(x, y, True)
    # dinding tak terlihat di hutan batas (pohon dekorasi tidak menutup celah sepenuhnya)
    blockc_f = [(int(x), int(y), 0, 0, 0) for x, y in zip(*np.nonzero(erode(forest, 1)))]
    sc.node("HutanPenghalang", "TileMapLayer", ".", tile_map_data=b64cells(blockc_f), tile_set=f'ExtResource("{block_ts}")')
    # rumpun pohon di halaman & taman (tanpa menutup jalan, rumah, NPC)
    open_land = land & ~forest & ~stone & ~dilate(dock, 2) & (dw >= 2)
    placed = []
    for _try in range(5000):
        if len(placed) >= 110:
            break
        x, y = rng.randint(80, PX_W - 80), rng.randint(110, PX_H - 60)
        tx_, ty_ = int(x // TILE), int(y // TILE)
        if not open_land[tx_, ty_] or float(stone_d[tx_, ty_]) < 40 or near_building(x, y, 26):
            continue
        if any(math.hypot(x - kx, y - ky) < 70 for kx, ky in keypts) or any(math.hypot(x - qx, y - qy) < 60 for qx, qy in placed):
            continue
        placed.append((x, y))
        tree_at(x, y, True)
    # semak & bunga kecil
    flowers = 0
    plant_tex = sc.ext_res("Texture2D", "res://assets/ninja/animated/Plant/SpriteSheet16x16.png")
    animprop_script = sc.ext_res("Script", "res://scripts/world/AnimProp.gd")
    for _try in range(1500):
        if flowers >= 90:
            break
        x, y = rng.randint(60, PX_W - 60), rng.randint(90, PX_H - 60)
        tx_, ty_ = int(x // TILE), int(y // TILE)
        if not open_land[tx_, ty_] or float(stone_d[tx_, ty_]) < 26 or near_building(x, y, 14):
            continue
        sc.node(f"Bunga{flowers}", "Node2D", "Decor", script=f'ExtResource("{animprop_script}")', strip=f'ExtResource("{plant_tex}")',
                position=v2(x, y), fps="3.0")
        flowers += 1
    for k, (nm, (x, y)) in enumerate((("Herb", (14, 30)), ("Herb", (108, 70)), ("GoldCoin", (46, 88)), ("Herb", (40, 26)))):
        q = at(x, y)
        if open_land[int(q[0] // TILE), int(q[1] // TILE)] and not near_building(q[0], q[1], 8):
            inst(f"Desa{nm}{k}", collect[nm], q)
    sc.node("Suasana", "Node2D", ".", script=f'ExtResource("{atmos_script}")', ray_alpha="0.10")

    # ------------------------------------------------------------ marker, pemain, batas
    sc.node("PlayerStart", "Marker2D", ".", position=v2(*start))
    sc.node("FromNext", "Marker2D", ".", position=v2(*at(63, 7.5)))
    sc.node("NPCSpawns", "Node2D", ".")
    sc.node("Joko", "Marker2D", "NPCSpawns", position=v2(*joko_pos), **{"metadata/npc_id": '"joko"'})
    sc.node("PedagangAlun", "Marker2D", "NPCSpawns", position=v2(*npcs["PedagangAlun"][0]), **{"metadata/npc_id": '"pedagang"'})
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player_scene}")]\nposition = {v2(*start)}\n')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    t = 32
    for nm, (x, y, w, h) in {"Atas": (PX_W / 2, -t / 2, PX_W + 2 * t, t), "Bawah": (PX_W / 2, PX_H + t / 2, PX_W + 2 * t, t),
                             "Kiri": (-t / 2, PX_H / 2, t, PX_H), "Kanan": (PX_W + t / 2, PX_H / 2, t, PX_H)}.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')
    with open(os.path.join(ROOT, "scenes/world/Village.tscn"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())

    # ------------------------------------------------------------ uji keterhubungan
    walk = (land & ~erode(forest, 1)) | dock
    from collections import deque
    sx, sy = int(start[0] // TILE), int(start[1] // TILE)
    seen = np.zeros_like(walk)
    seen[sx, sy] = True
    dq = deque([(sx, sy)])
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and walk[nx, ny] and not seen[nx, ny]:
                seen[nx, ny] = True
                dq.append((nx, ny))
    ok = {nm: bool(seen[int(p[0] // TILE), int(p[1] // TILE)]) for nm, (p, _) in npcs.items()}
    ok.update(gerbang=bool(seen[int(gate[0] // TILE), int(gate[1] // TILE)]), bonfire=bool(seen[int(bonfire[0] // TILE), int(bonfire[1] // TILE)]),
              dermaga_ujung=bool(seen[63, 92]))
    print("terjangkau dari depan rumah Raka:", ok)
    bad = [p for p in recorded if not (0 <= p[0] < PX_W and 0 <= p[1] < PX_H and walk[int(p[0] // TILE), int(p[1] // TILE)])]
    print("Village.tscn: %dx%d tile, %d pohon, %d bunga, objek di luar daratan: %d %s" % (W, H, tnum[0], flowers, len(bad), bad[:6]))


if __name__ == "__main__":
    build()
