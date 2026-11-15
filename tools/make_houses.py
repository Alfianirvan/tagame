"""Perakit rumah varian dari kit bangunan Pixel Crawler (Walls.png, Roofs.png, Props.png) -> PNG BARU.

Aset asli tidak diubah. Hasil: assets/props/buildings/variants/<Nama>.png + pratinjau docs/layout/rumah_varian.png.
Sebuah rumah = deretan MODUL berdampingan (rata di kaki), tiap modul = dinding (1-2 lantai) + atap:
  "A"  atap pelana lebar 128 px (Roofs (0,6)-(128,95)),
  "B"  atap runcing 96 px (Roofs (16,80)-(112,176), tanpa atap datar di bawahnya),
  "C"  atap datar (Roofs (32,160)-(96,208)) yang bisa dilebarkan (papan vertikal diulang),
  "P"  teras: atap datar C + 2 tiang kayu, tanpa dinding.
Warna atap: coklat (kayu), hijau (asli), merah / biru (hijau diwarnai ulang).
Jalankan:  python tools/make_houses.py   (lalu python tools/make_prefabs.py untuk prefab Rumah_*)
"""
import colorsys
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "assets", "props", "buildings")
OUT = os.path.join(B, "variants")

WALLS = Image.open(os.path.join(B, "Walls.png")).convert("RGBA")
ROOFS = Image.open(os.path.join(B, "Roofs.png")).convert("RGBA")
PROPS = Image.open(os.path.join(B, "Props.png")).convert("RGBA")

# dinding: x awal blok bahan (panel 32,16,32,16 px) pada pita y 185-240
MATERIAL = {"gelondong": 0, "papan": 96, "papan_gelap": 192, "rangka": 288, "krem": 384, "bata": 480}
WALL_Y0, WALL_Y1 = 185, 240
FLOOR_H = WALL_Y1 - WALL_Y0            # 55 px per lantai
PANELS = [(0, 32), (32, 16), (48, 32), (80, 16)]
ROOF_OVERLAP = 6


def bbox_crop(sheet, box):
    """Potong kotak kasar lalu rapatkan ke piksel tak transparan."""
    c = sheet.crop(box)
    bb = c.getbbox()
    return c.crop(bb) if bb else c


# potongan props (kotak kasar, dirapatkan otomatis)
DOOR = {"kayu": (100, 28, 124, 65), "lengkung_besi": (132, 24, 156, 65), "lengkung_abu": (164, 24, 188, 65),
        "hijau": (196, 63, 220, 97)}
FRAME = {"kayu": (0, 22, 32, 65), "lengkung_kayu": (32, 19, 64, 65), "batu": (64, 19, 96, 65)}
WINDOW = {"biru": (131, 98, 157, 125), "kecil": (32, 80, 48, 96), "kecil2": (48, 80, 64, 96), "lengkung": (100, 65, 124, 97),
          "daun_hijau": (128, 65, 160, 97), "daun_hijau2": (160, 65, 192, 97), "kisi": (100, 99, 124, 123),
          "bingkai": (35, 97, 61, 126), "tutup": (67, 97, 93, 126)}
CHIMNEY = (3, 72, 29, 145)
PLANTER = (48, 148, 80, 172)
SHUTTER = (79, 131, 145, 157)
BENCH = (82, 159, 142, 193)
POST = (16, 188, 32, 240)          # di Roofs.png


def component_mask(sheet, seed):
    """Topeng piksel (y, x) yang tersambung (8 arah, alpha > 0) dengan titik seed (x, y)."""
    a = np.array(sheet)[:, :, 3] > 0
    h, w = a.shape
    mask = np.zeros_like(a)
    stack = [(seed[1], seed[0])]
    while stack:
        y, x = stack.pop()
        if not (0 <= y < h and 0 <= x < w) or mask[y, x] or not a[y, x]:
            continue
        mask[y, x] = True
        stack.extend((y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return mask


def recolor_hue(im, hue, sat_mul=1.0, val_mul=1.0):
    """Atap hijau -> warna lain (hue 0..1), hanya piksel berwarna (bukan garis hitam)."""
    a = np.array(im).astype(float) / 255.0
    out = a.copy()
    h, w = a.shape[:2]
    for y in range(h):
        for x in range(w):
            r, g, b, al = a[y, x]
            if al == 0:
                continue
            hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
            if ss > 0.2:
                rr, gg, bb = colorsys.hsv_to_rgb(hue, min(1, ss * sat_mul), min(1, vv * val_mul))
                out[y, x, :3] = (rr, gg, bb)
    return Image.fromarray((out * 255).astype(np.uint8))


def roof_piece(kind, color):
    """Potongan atap A/B/C dalam warna tertentu."""
    green = color in ("hijau", "merah", "biru")
    dx = 128 if green else 0
    if kind == "A":
        im = ROOFS.crop((dx, 6, dx + 128, 95))
    elif kind == "B":
        # atap runcing bersisipan dengan tepi bawah atap A: ambil komponen pikselnya saja (flood fill dari lereng),
        # lalu buang tiang samping & atap datar C yang menempel di bawahnya
        mask = component_mask(ROOFS, (dx + 40, 140))
        mask[:, :dx + 16] = False
        mask[:, dx + 112:] = False
        mask[160:, dx + 32:dx + 96] = False
        mask[178:, :] = False
        a = np.array(ROOFS).copy()
        a[~mask, 3] = 0
        im = Image.fromarray(a).crop((dx + 16, 78, dx + 112, 178))
        im = im.crop(im.getbbox())
    else:  # C
        im = ROOFS.crop((dx + 32, 160, dx + 96, 207))
        im = im.crop(im.getbbox())
    if color == "merah":
        im = recolor_hue(im, 0.01, 1.05, 0.95)
    elif color == "biru":
        im = recolor_hue(im, 0.6, 0.95, 0.95)
    return im


def stretch_flat(roof, width):
    """Lebarkan atap datar C: kolom tengah (papan vertikal) diulang sampai lebar `width`."""
    if width <= roof.width:
        return _shrink(roof, width)
    edge = 8
    mid = roof.crop((edge, 0, roof.width - edge, roof.height))
    out = Image.new("RGBA", (width, roof.height))
    out.alpha_composite(roof.crop((0, 0, edge, roof.height)), (0, 0))
    x = edge
    while x < width - edge:
        out.alpha_composite(mid, (x, 0))
        x += mid.width
    out.alpha_composite(roof.crop((roof.width - edge, 0, roof.width, roof.height)), (width - edge, 0))
    return out


def _shrink(roof, width):
    half = width // 2
    out = Image.new("RGBA", (width, roof.height))
    out.alpha_composite(roof.crop((0, 0, half, roof.height)), (0, 0))
    out.alpha_composite(roof.crop((roof.width - (width - half), 0, roof.width, roof.height)), (half, 0))
    return out


def wall_strip(material, width, floors):
    base = MATERIAL[material]
    out = Image.new("RGBA", (width, FLOOR_H * floors - (floors - 1) * 3))
    for f in range(floors):
        row = Image.new("RGBA", (width, FLOOR_H))
        x, i = 0, 0
        while x < width:
            ox, w = PANELS[i % 4]
            w = min(w, width - x)
            row.alpha_composite(WALLS.crop((base + ox, WALL_Y0, base + ox + w, WALL_Y1)), (x, 0))
            x += w
            i += 1
        out.alpha_composite(row, (0, f * (FLOOR_H - 3)))
    return out


def wall_color(wall):
    a = np.array(wall)
    solid = a[a[:, :, 3] == 255][:, :3]
    return tuple(int(v) for v in solid[len(solid) // 3: 2 * len(solid) // 3].mean(axis=0)) + (255,)


def fill_under_roof(roof, color):
    """Isi celah di bawah atap (segitiga pelana) dengan warna dinding: tiap baris antara piksel atap terluar."""
    ra = np.array(roof)
    fill = Image.new("RGBA", roof.size)
    px = fill.load()
    for y in range(roof.height):
        xs = np.where(ra[y, :, 3] > 0)[0]
        if len(xs):
            for x in range(xs.min(), xs.max() + 1):
                px[x, y] = color
    return fill


def module(spec):
    """Satu modul -> (gambar, lebar). spec: dict(kind, wall, floors, roof, width, door, windows, chimney, planter)."""
    kind = spec["kind"]
    color = spec.get("roof", "coklat")
    if kind == "P":   # teras: atap datar + tiang
        width = spec.get("width", 48)
        roof = stretch_flat(roof_piece("C", color), width)
        post = bbox_crop(ROOFS, POST)      # tiang kayu (lembar Roofs)
        post_h = FLOOR_H - 2
        im = Image.new("RGBA", (width, roof.height - ROOF_OVERLAP + post_h))
        for px_ in (3, width - post.width - 3):
            p = post.resize((post.width, post_h), Image.NEAREST)
            im.alpha_composite(p, (px_, im.height - post_h))
        im.alpha_composite(roof, (0, 0))
        return im
    floors = spec.get("floors", 1)
    roof = roof_piece(kind, color)
    if kind == "C":
        roof = stretch_flat(roof, spec.get("width", 64))
    width = roof.width
    wall = wall_strip(spec["wall"], width, floors)
    wc = wall_color(wall)
    # pintu, jendela di dinding
    if spec.get("door"):
        frame_k, door_k = spec["door"]
        door = bbox_crop(PROPS, DOOR[door_k])
        dx = spec.get("door_x", (width - door.width) // 2)
        if frame_k:
            fr = bbox_crop(PROPS, FRAME[frame_k])
            wall.alpha_composite(fr, (dx + door.width // 2 - fr.width // 2, wall.height - fr.height))
        wall.alpha_composite(door, (dx, wall.height - door.height - 1))
    for (wk, wx, floor_i) in spec.get("windows", []):
        win = bbox_crop(PROPS, WINDOW[wk])
        wy = wall.height - (floor_i + 1) * (FLOOR_H - 3) + 13
        wall.alpha_composite(win, (wx if wx >= 0 else width + wx - win.width, wy))
        if spec.get("planter") and floor_i == 0 and wk.startswith("daun"):
            pl = bbox_crop(PROPS, PLANTER)
            wall.alpha_composite(pl, ((wx if wx >= 0 else width + wx - win.width) + win.width // 2 - pl.width // 2, wy + win.height - 6))
    if spec.get("shutter"):
        sh = bbox_crop(PROPS, SHUTTER)
        wall.alpha_composite(sh, (spec["shutter"], wall.height - sh.height - 8))
    top = roof.height - ROOF_OVERLAP
    chim = bbox_crop(PROPS, CHIMNEY) if spec.get("chimney") is not None else None
    extra = max(0, chim.height - top - 10) if chim else 0
    im = Image.new("RGBA", (width, extra + top + wall.height))
    im.alpha_composite(wall, (0, extra + top))
    im.alpha_composite(fill_under_roof(roof, wc), (0, extra))
    if chim is not None:   # cerobong di belakang lereng atap
        im.alpha_composite(chim, (spec["chimney"], 0))
    im.alpha_composite(roof, (0, extra))
    if spec.get("door"):
        im.info["door_cx"] = dx + door.width / 2     # pusat pintu (px dari kiri modul)
    return im


def house(name, mods, overlap=0):
    """Gabung modul berdampingan (rata bawah). Modul dengan "front": True digambar paling akhir (di depan)."""
    ims = [module(m) for m in mods]
    width = sum(i.width for i in ims) - overlap * (len(ims) - 1)
    height = max(i.height for i in ims)
    out = Image.new("RGBA", (width, height))
    xs, x = [], 0
    for i in ims:
        xs.append(x)
        x += i.width - overlap
    order = sorted(range(len(ims)), key=lambda k: (mods[k].get("front", False), ims[k].height))
    for k in order:
        out.alpha_composite(ims[k], (xs[k], height - ims[k].height))
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name + ".png"))
    for k, i in enumerate(ims):   # geser pintu dari pusat gambar (px, + = kanan): dipakai pagar & pintu interior
        if "door_cx" in i.info:
            DOOR_DX[name] = round(xs[k] + i.info["door_cx"] - width / 2)
            break
    return out


DOOR_DX = {}


# ------------------------------------------------------------------ daftar varian
DESIGNS = {
    # bermenara + teras (seperti contoh): menara 2 lantai, badan atap runcing, teras bertiang
    "Rumah_Menara_Hijau": [
        dict(kind="C", wall="bata", floors=2, roof="hijau", width=56, windows=[("daun_hijau", 12, 1)], planter=True),
        dict(kind="B", wall="krem", floors=1, roof="hijau", door=("batu", "lengkung_besi"), windows=[("biru", 8, 0)]),
        dict(kind="P", roof="hijau", width=44)],
    "Rumah_Menara_Kayu": [
        dict(kind="C", wall="gelondong", floors=2, roof="coklat", width=56, windows=[("tutup", 15, 1)]),
        dict(kind="B", wall="papan", floors=1, roof="coklat", door=("lengkung_kayu", "kayu"), windows=[("bingkai", 6, 0)]),
        dict(kind="P", roof="coklat", width=44)],
    "Rumah_Menara_Merah": [
        dict(kind="P", roof="merah", width=44),
        dict(kind="B", wall="rangka", floors=1, roof="merah", door=("kayu", "lengkung_abu"), windows=[("biru", -8, 0)]),
        dict(kind="C", wall="krem", floors=2, roof="merah", width=56, windows=[("lengkung", 16, 1), ("daun_hijau2", 12, 0)], planter=True)],
    # dua lantai beratap pelana lebar, cerobong
    "Rumah_Loteng_Hijau": [dict(kind="A", wall="papan", floors=2, roof="hijau", door=("kayu", "kayu"), chimney=86,
                                windows=[("biru", 12, 0), ("biru", -12, 0), ("kecil", 30, 1), ("kecil2", -30, 1)])],
    "Rumah_Loteng_Merah": [dict(kind="A", wall="krem", floors=2, roof="merah", door=("batu", "lengkung_besi"), chimney=20,
                                windows=[("daun_hijau", 10, 0), ("daun_hijau2", -10, 0), ("lengkung", 22, 1), ("lengkung", -22, 1)], planter=True)],
    "Rumah_Loteng_Biru": [dict(kind="A", wall="bata", floors=2, roof="biru", door=("batu", "lengkung_abu"), chimney=88,
                               windows=[("biru", 12, 0), ("biru", -12, 0), ("bingkai", 24, 1), ("bingkai", -24, 1)])],
    "Rumah_Loteng_Coklat": [dict(kind="A", wall="papan_gelap", floors=2, roof="coklat", door=("kayu", "kayu"), chimney=20,
                                 windows=[("tutup", 12, 0), ("tutup", -12, 0), ("kisi", 26, 1), ("kisi", -26, 1)])],
    # atap runcing satu lantai (rumah warga kecil)
    "Rumah_Runcing_Coklat": [dict(kind="B", wall="papan_gelap", floors=1, roof="coklat", door=(None, "kayu"),
                                  windows=[("kisi", 8, 0), ("kisi", -8, 0)])],
    "Rumah_Runcing_Biru": [dict(kind="B", wall="bata", floors=1, roof="biru", door=("batu", "lengkung_abu"),
                                windows=[("daun_hijau", 4, 0)], planter=True)],
    "Rumah_Runcing_Merah": [dict(kind="B", wall="krem", floors=1, roof="merah", door=("kayu", "kayu"), windows=[("biru", 8, 0), ("biru", -8, 0)])],
    # rumah pelana + teras samping
    "Rumah_Teras_Coklat": [dict(kind="A", wall="gelondong", floors=1, roof="coklat", door=("kayu", "kayu"), chimney=90,
                                windows=[("tutup", 12, 0), ("tutup", -12, 0)]),
                           dict(kind="P", roof="coklat", width=48)],
    "Rumah_Teras_Biru": [dict(kind="P", roof="biru", width=48),
                         dict(kind="A", wall="rangka", floors=1, roof="biru", door=("batu", "lengkung_besi"),
                              windows=[("biru", 12, 0), ("biru", -12, 0)])],
    # gudang panjang: dua pelana + sayap atap datar
    "Gudang_Panjang": [dict(kind="A", wall="papan_gelap", floors=1, roof="coklat", door=(None, "hijau"), windows=[("kisi", 14, 0)]),
                       dict(kind="C", wall="papan_gelap", floors=1, roof="coklat", width=72, windows=[("kisi", 26, 0)])],
    # pondok kecil atap datar
    "Pondok_Kecil": [dict(kind="C", wall="gelondong", floors=1, roof="coklat", width=64, door=(None, "kayu"))],
    "Pondok_Hijau": [dict(kind="C", wall="papan", floors=1, roof="hijau", width=72, door=(None, "kayu"), door_x=8,
                          windows=[("kecil", -10, 0)])],
    # toko: jendela berdaun (etalase) + bangku di depan
    "Toko_Merah": [dict(kind="A", wall="krem", floors=1, roof="merah", door=("kayu", "kayu"), door_x=88, shutter=10)],
    "Toko_Hijau": [dict(kind="A", wall="papan", floors=1, roof="hijau", door=("kayu", "kayu"), door_x=14, shutter=50)],
}


def preview(images):
    font = ImageFont.load_default()
    cols = 4
    cell_w = max(i.width for i in images.values()) + 24
    cell_h = max(i.height for i in images.values()) + 26
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (86, 140, 60, 255))
    d = ImageDraw.Draw(sheet)
    for k, (name, im) in enumerate(images.items()):
        cx, cy = (k % cols) * cell_w, (k // cols) * cell_h
        sheet.alpha_composite(im, (cx + (cell_w - im.width) // 2, cy + cell_h - 16 - im.height))
        d.text((cx + 4, cy + cell_h - 13), name, fill=(255, 255, 255, 255), font=font)
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(os.path.join(ROOT, "docs", "layout", "rumah_varian.png"))


def main():
    images = {name: house(name, mods) for name, mods in DESIGNS.items()}
    for n, im in images.items():
        print(f"{n}: {im.size}")
    preview(images)
    with open(os.path.join(OUT, "_pintu.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(DOOR_DX, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
