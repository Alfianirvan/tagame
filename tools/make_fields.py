"""Ladang (petak tanah olah + baris tanaman) dari Pixel Crawler Farm.png -> PNG BARU di assets/props/fields/.

Aset asli tidak diubah. Tiap ladang = kotak tile tanah olah (Farm.png (352,112)) dengan satu jenis tanaman per baris.
Dipakai sebagai Sprite2D di lapisan Decor (di bawah objek, tanpa tabrakan; pagar dipasang terpisah).
Jalankan:  python tools/make_fields.py
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FARM = Image.open(os.path.join(ROOT, "assets", "props", "Farm.png")).convert("RGBA")
OUT = os.path.join(ROOT, "assets", "props", "fields")
SOIL = FARM.crop((352, 112, 368, 128))
# tanaman dewasa (kolom 80) per jenis: baris y di Farm.png
CROP_Y = {"wortel": 16, "bit": 48, "kubis": 80, "selada": 112, "kembangkol": 144, "brokoli": 176, "bawang": 208}
CROP_X = 80                                   # kolom 80 = dewasa sehat (96 = layu)

FIELDS = {   # nama -> (lebar tile, tinggi tile, urutan tanaman per baris)
    "Ladang_A": (10, 6, ["wortel", "kubis", "wortel", "bawang", "kubis", "wortel"]),
    "Ladang_B": (8, 5, ["selada", "bit", "selada", "bit", "selada"]),
    "Ladang_C": (6, 4, ["brokoli", "kembangkol", "brokoli", "kembangkol"]),
}


def crop_sprite(kind):
    y = CROP_Y[kind]
    c = FARM.crop((CROP_X, y, CROP_X + 16, y + 16))
    return c.crop(c.getbbox()) if c.getbbox() else c


def make(name, wt, ht, rows):
    im = Image.new("RGBA", (wt * 16, ht * 16))
    for ty in range(ht):
        for tx in range(wt):
            im.alpha_composite(SOIL, (tx * 16, ty * 16))
    for ty, kind in enumerate(rows[:ht]):
        sp = crop_sprite(kind)
        for tx in range(wt):
            im.alpha_composite(sp, (tx * 16 + (16 - sp.width) // 2, ty * 16 + 16 - sp.height - 1))
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name + ".png"))
    return im.size


def main():
    for name, (wt, ht, rows) in FIELDS.items():
        print(name, make(name, wt, ht, rows))


if __name__ == "__main__":
    main()
