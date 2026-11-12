"""Membuat prefab objek UTUH (1 sprite = 1 scene) di scenes/prefabs/ dari sprite sheet Pixel Crawler yang sudah ada di proyek.

Aturan prefab: root StaticBody2D dengan ORIGIN DI TITIK KAKI (tengah-bawah sprite), tanpa rotasi/skala.
 - Sprite dipotong per objek utuh lalu serpihan debu/arang yang terpisah dibuang (assets/props/prefab_sprites/), supaya tidak 'mengambang'.
 - Bayangan lembut (Polygon2D) di bawah objek supaya menapak di tanah.
 - Bangunan: tabrakan hanya di dinding bawah. Stasiun/perabot: tabrakan menutupi seluruh badan gambar.
 - Objek beranimasi memakai frame pertama (statis).
Daftar ukuran ditulis ke scenes/prefabs/_prefabs.json untuk perender (tools/render_prefabs.gd).

Jalankan:  python tools/make_prefabs.py
"""
import json
import math
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PROPS = os.path.join(ROOT, "assets", "props")
OUT = os.path.join(ROOT, "scenes", "prefabs")
SPRITE_OUT = os.path.join(PROPS, "prefab_sprites")
NL = chr(10)

# nama: (file relatif assets/props, kotak kasar x0,y0,x1,y1, (lebar tabrakan, tinggi[, titik jangkar x]) | None = otomatis)
SHEET = {
    "Sawmill_Kecil": ("stations/Sawmill/Base.png", (48, 0, 126, 66), None),
    "Sawmill_Besar": ("stations/Sawmill/Base.png", (144, 0, 256, 82), None),
    "Tunggul_Kapak": ("stations/Sawmill/Base.png", (0, 16, 42, 52), (24, 8)),
    "Landasan_1": ("stations/Anvil/Anvil.png", (1, 37, 63, 76), None),
    "Landasan_2": ("stations/Anvil/Anvil.png", (80, 36, 159, 92), None),
    "Landasan_3": ("stations/Anvil/Anvil.png", (176, 14, 272, 97), None),
    "Tungku_Batu_1": ("stations/Furnace/Furnace.png", (0, 26, 32, 64), None),
    "Tungku_Batu_2": ("stations/Furnace/Furnace.png", (52, 15, 89, 64), None),
    "Tungku_Bata_1": ("stations/Furnace/Furnace.png", (1, 87, 31, 128), None),
    "Tungku_Bata_2": ("stations/Furnace/Furnace.png", (54, 71, 90, 128), None),
    "Tungku_Besi_1": ("stations/Furnace/Furnace.png", (0, 147, 32, 192), None),
    "Tungku_Besi_2": ("stations/Furnace/Furnace.png", (53, 133, 91, 192), None),
    "MejaKerja_Kayu_1": ("stations/Workbench/Workbench.png", (0, 82, 32, 112), None),
    "MejaKerja_Kayu_2": ("stations/Workbench/Workbench.png", (48, 72, 96, 112), None),
    "MejaKerja_Kayu_3": ("stations/Workbench/Workbench.png", (112, 64, 176, 112), None),
    "MejaKerja_Besi_2": ("stations/Workbench/Workbench.png", (48, 112, 96, 162), None),
    "Dapur_PanggangApi": ("stations/Cooking Station/Cooking Station.png", (1, 20, 62, 61), None),
    "Dapur_PanciGantung": ("stations/Cooking Station/Cooking Station.png", (77, 20, 124, 63), None),
    "Dapur_Panggangan_Kecil": ("stations/Cooking Station/Cooking Station.png", (144, 20, 201, 64), None),
    "Dapur_Panggangan_Besar": ("stations/Cooking Station/Cooking Station.png", (211, 17, 282, 64), None),
    "Dapur_Tripod": ("stations/Cooking Station/Cooking Station.png", (11, 67, 53, 121), None),
    "Dapur_Ketel": ("stations/Cooking Station/Cooking Station.png", (78, 82, 114, 127), None),
    "Dapur_Kompor": ("stations/Cooking Station/Cooking Station.png", (144, 101, 192, 128), None),
    "Dapur_Besar": ("stations/Cooking Station/Cooking Station.png", (208, 70, 288, 144), None),
    "Barel_Air": ("Furniture.png", (769, 13, 783, 32), None),
    "Barel_Kosong": ("Furniture.png", (785, 13, 799, 32), None),
    "Peti_Kayu_A": ("Furniture.png", (720, 73, 736, 96), None),
    "Peti_Kayu_B": ("Furniture.png", (736, 73, 752, 96), None),
    "Barel_Besar": ("Furniture.png", (752, 73, 768, 96), None),
    "Guci": ("Furniture.png", (769, 80, 783, 96), None),
    "Lampu_Tiang": ("Furniture.png", (147, 448, 174, 494), (8, 6, -9)),
    "Pagar_Kayu": ("Furniture.png", (179, 422, 237, 445), (58, 8)),
    "Tiang_Pagar": ("Furniture.png", (162, 422, 174, 445), (8, 6)),
    "OrangOrangSawah": ("Farm.png", (245, 34, 267, 80), (10, 6)),
}
BUILDINGS = {
    "Rumah_Krem": "buildings/house_brown.png", "Rumah_Hijau": "buildings/house_green.png", "Rumah_Kayu": "buildings/house_log.png",
    "Rumah_Papan": "buildings/house_plank.png", "Lumbung": "buildings/house_dark.png",
}
WHOLE = {"Sumur": ("well_stone.png", (26, 12))}

NO_SHADOW = ("Lampu_Tiang", "Pagar_Kayu", "Tiang_Pagar", "Spanduk_1", "Spanduk_2", "Spanduk_3")
SOLID_BODY = ("Sawmill", "Landasan", "MejaKerja", "Tungku", "Dapur", "Peti", "Barel", "Sumur", "Lapak")


def clean_crop(rel, box):
    """Potong objek, buang serpihan terpisah (debu/arang) yang membuatnya tampak mengambang, pangkas ke piksel terisi."""
    im = Image.open(os.path.join(PROPS, rel)).convert("RGBA").crop(box)
    a = np.array(im)[:, :, 3] > 0
    height, width = a.shape
    d = a.copy()
    for _ in range(2):                      # sambungkan bagian yang berdekatan (<= 2 px)
        s_ = d.copy()
        s_[1:, :] |= d[:-1, :]
        s_[:-1, :] |= d[1:, :]
        s_[:, 1:] |= d[:, :-1]
        s_[:, :-1] |= d[:, 1:]
        s_[1:, 1:] |= d[:-1, :-1]
        s_[:-1, :-1] |= d[1:, 1:]
        s_[1:, :-1] |= d[:-1, 1:]
        s_[:-1, 1:] |= d[1:, :-1]
        d = s_
    lab = np.zeros((height, width), int)
    n = 0
    for y in range(height):
        for x in range(width):
            if d[y, x] and lab[y, x] == 0:
                n += 1
                st = [(y, x)]
                lab[y, x] = n
                while st:
                    cy, cx = st.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < height and 0 <= nx < width and d[ny, nx] and lab[ny, nx] == 0:
                                lab[ny, nx] = n
                                st.append((ny, nx))
    counts = {i: int((a & (lab == i)).sum()) for i in range(1, n + 1)}
    top = max(counts.values())
    keep = [i for i, c in counts.items() if c >= max(24, 0.06 * top)]
    out = np.array(im)
    out[~np.isin(lab, keep)] = 0
    clean = Image.fromarray(out).convert("RGBA")
    return clean.crop(clean.getbbox())


def auto_collision(name, w, h):
    if name.startswith(SOLID_BODY):
        # seluruh badan gambar bertabrakan: Raka tidak bisa berdiri 'di dalam' sprite dari sisi mana pun
        return (max(8, round(w * 0.92)), max(8, round(h)))
    return (max(6, round(w * 0.8)), max(6, min(14, h // 3)))


def write_prefab(name, rel, size, col):
    w, h = size
    if col is None:
        col = auto_collision(name, w, h)
    cw, ch = col[0], col[1]
    cdx = col[2] if len(col) > 2 else 0
    shadow = ""
    if name not in NO_SHADOW:
        sw = w * 0.92 if name.startswith(("Rumah", "Lumbung")) else min(w * 0.95, max(14.0, cw * 1.25))
        sh = max(8.0, min(18.0, h * 0.2))
        pts = ", ".join(
            f"{(sw / 2) * math.cos(2 * math.pi * k / 22) - cdx:.1f}, {-sh / 2 + (sh / 2) * math.sin(2 * math.pi * k / 22):.1f}"
            for k in range(22))
        shadow = (f'[node name="Sombra" type="Polygon2D" parent="."]{NL}color = Color(0, 0, 0, 0.26){NL}'
                  f'polygon = PackedVector2Array({pts}){NL}{NL}')
    lines = [
        '[gd_scene load_steps=3 format=3]', '',
        f'[ext_resource type="Texture2D" path="res://assets/props/{rel}" id="1"]', '',
        f'[sub_resource type="RectangleShape2D" id="1"]{NL}size = Vector2({cw}, {ch})', '',
        f'[node name="{name}" type="StaticBody2D"]{NL}collision_layer = 1{NL}collision_mask = 0', '',
    ]
    text = NL.join(lines) + NL + shadow
    text += (f'[node name="Sprite2D" type="Sprite2D" parent="."]{NL}texture = ExtResource("1"){NL}'
             f'offset = Vector2({-cdx}, {-h / 2}){NL}{NL}'
             f'[node name="CollisionShape2D" type="CollisionShape2D" parent="."]{NL}position = Vector2(0, {-ch / 2}){NL}'
             f'shape = SubResource("1"){NL}')
    open(os.path.join(OUT, name + ".tscn"), "w", encoding="utf-8", newline=NL).write(text)
    return {"name": name, "w": w, "h": h, "cw": cw, "ch": ch, "cdx": 0}


NINJA = os.path.join(ROOT, "assets", "ninja")
FIELDS = os.path.join(ROOT, "assets", "craftpix", "fields", "objects")


def composite_sprites():
    """Prefab gabungan/lintas-paket: lapak pasar (kain + keranjang), spanduk, papan penunjuk arah."""
    house = Image.open(os.path.join(NINJA, "tilesets", "TilesetHouse.png")).convert("RGBA")
    out = {}
    for name, awn_x, bk_x in (("Lapak_Sayur", 256, 256), ("Lapak_Kain", 304, 256)):
        canvas = Image.new("RGBA", (48, 38), (0, 0, 0, 0))
        canvas.alpha_composite(house.crop((awn_x, 256, awn_x + 48, 290)), (0, 0))
        baskets = house.crop((bk_x, 208, bk_x + 48, 224))
        canvas.alpha_composite(baskets, (0, 22))
        out[name] = (canvas, None)
    for k, bx in enumerate((448, 352 + 16 * 1, 352 + 16 * 3), start=1):
        out[f"Spanduk_{k}"] = (house.crop((bx, 320, bx + 16, 352)), (6, 4))
    for name, f in (("Papan_Kiri", "1.png"), ("Papan_Kanan", "4.png"), ("Papan_Tiang", "3.png")):
        out[name] = (Image.open(os.path.join(FIELDS, "3 Pointer", f)).convert("RGBA"), (8, 6))
    ab = Image.open(os.path.join(NINJA, "tilesets", "TilesetVillageAbandoned.png")).convert("RGBA")
    for name, box in (("Ruina_1", (0, 0, 64, 48)), ("Ruina_2", (176, 0, 224, 48)), ("Ruina_3", (176, 48, 224, 96)),
                      ("Ruina_4", (192, 96, 256, 176)), ("Ruina_5", (256, 80, 320, 169))):
        im = ab.crop(box)
        bb = im.getbbox()
        out[name] = (im, (max(16, (bb[2] - bb[0]) - 10), 24))
    for name, box in (("Puing_Batu", (0, 48, 32, 80)), ("Puing_Pilar", (96, 48, 128, 80)), ("Puing_Kayu", (112, 112, 144, 144))):
        out[name] = (ab.crop(box), (14, 8))
    for k in range(1, 5):
        out[f"Tenda_{k}"] = (Image.open(os.path.join(FIELDS, "8 Camp", f"{k}.png")).convert("RGBA"), None)
    out["Tronk_Kayu"] = (Image.open(os.path.join(FIELDS, "7 Decor", "Log1.png")).convert("RGBA"), (24, 8))
    out["Kotak_Rusak"] = (Image.open(os.path.join(FIELDS, "7 Decor", "Box1.png")).convert("RGBA"), (12, 8))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SPRITE_OUT, exist_ok=True)
    info = []
    for name, (rel, box, col) in SHEET.items():
        clean = clean_crop(rel, box)
        clean.save(os.path.join(SPRITE_OUT, name + ".png"))
        info.append(write_prefab(name, f"prefab_sprites/{name}.png", clean.size, col))
    for name, rel in BUILDINGS.items():
        im = Image.open(os.path.join(PROPS, rel))
        info.append(write_prefab(name, rel, im.size, (im.width - 12, 46)))
    for name, (rel, col) in WHOLE.items():
        im = Image.open(os.path.join(PROPS, rel))
        info.append(write_prefab(name, rel, im.size, col))
    for name, (im, col) in composite_sprites().items():
        im = im.crop(im.getbbox())
        im.save(os.path.join(SPRITE_OUT, name + ".png"))
        info.append(write_prefab(name, f"prefab_sprites/{name}.png", im.size, col))
    json.dump(info, open(os.path.join(OUT, "_prefabs.json"), "w", encoding="utf-8"), indent=1)
    print(len(info), "prefab ditulis ke scenes/prefabs/")


if __name__ == "__main__":
    main()
