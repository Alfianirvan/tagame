"""Ambil siluet tiap wilayah dari worldmap/peta_dunia_preview.png -> tools/region_masks/<nama>.png (putih = wilayah).

Jalankan dari folder proyek:  python tools/extract_regions.py
Tiap piksel diklasifikasi (laut / hutan / gurun / gunung ungu / padang / ...) lewat warna acuan terdekat,
lalu wilayah ditentukan dari warna + pita tinggi (Desa y>1115, Ch5 y<275, dst.).
Label putih, lingkaran biru, dan awan diisi dari tetangga terdekat. Hasil dipakai generator scene agar
bentuk wilayah sama dengan Peta Dunia (tools/organic.py: load_region_mask).
"""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "..", "worldmap", "peta_dunia_preview.png")
OUT = os.path.join(ROOT, "tools", "region_masks")
S = 3  # skala turun

# (warna, kelas) kelas: w=air, f=hutan, b=gurun/coklat, p=gunung ungu, g=padang hijau/pasir (dibagi per pita tinggi)
SEEDS = [((28, 74, 146), "w"), ((40, 112, 184), "w"), ((70, 150, 210), "w"), ((190, 225, 235), "w"), ((120, 190, 225), "w"),
         ((28, 78, 44), "f"), ((40, 100, 50), "f"), ((20, 60, 35), "f"),
         ((183, 151, 106), "b"), ((191, 157, 111), "b"), ((140, 110, 80), "b"), ((110, 85, 60), "b"),
         ((80, 72, 126), "p"), ((72, 64, 113), "p"), ((150, 140, 190), "p"), ((200, 205, 225), "p"), ((50, 45, 90), "p"), ((120, 110, 160), "p"),
         ((198, 190, 138), "g"), ((227, 218, 159), "g"), ((110, 180, 89), "g"), ((130, 190, 100), "g"), ((46, 106, 56), "g"),
         ((72, 153, 101), "g"), ((96, 150, 80), "g"), ((160, 205, 120), "g"), ((90, 140, 70), "g"), ((60, 120, 70), "g")]


def main():
    im = Image.open(SRC).convert("RGB")
    sm = np.array(im.resize((im.width // S, im.height // S), Image.BOX)).astype(int)
    h, w, _ = sm.shape
    seeds = np.array([c for c, _ in SEEDS])
    kinds = np.array([k for _, k in SEEDS])
    d = ((sm[:, :, None, :] - seeds[None, None]) ** 2).sum(-1)
    kind = kinds[d.argmin(-1)]
    # label putih/awan & lingkaran biru penanda = tak diketahui
    white = (sm[..., 0] > 235) & (sm[..., 1] > 232) & (sm[..., 2] > 225)
    circ = (abs(sm[..., 0] - 41) < 25) & (abs(sm[..., 1] - 171) < 25) & (abs(sm[..., 2] - 230) < 25)
    orange = (sm[..., 0] > 200) & (sm[..., 1] > 100) & (sm[..., 1] < 160) & (sm[..., 2] < 90)
    unknown = white | circ | orange
    yy = (np.arange(h) * S + S // 2)[:, None] * np.ones((1, w))
    region = np.full((h, w), "", dtype=object)
    xx = (np.arange(w) * S + S // 2)[None, :] * np.ones((h, 1))
    region[kind == "b"] = "ch2"
    region[kind == "p"] = "ch4"
    gf = (kind == "g") | (kind == "f")
    region[gf] = "ch3"
    region[gf & (yy >= 815)] = "ch1"
    region[gf & (yy >= 1118 + (xx - 90) * 0.15)] = "village"
    region[gf & (yy < 275)] = "ch5"
    # coklat/ungu yang nyasar di luar wilayahnya -> ikut tetangga
    region[(kind == "b") & (yy < 500)] = "ch3"
    region[(kind == "p") & (yy > 600)] = "ch2"
    region[(kind == "w")] = ""
    region[unknown] = "?"
    # isi '?' dari piksel berlabel terdekat (hanya bila dekat daratan)
    known = np.argwhere((region != "") & (region != "?"))
    unk = np.argwhere(region == "?")
    for i in range(0, len(unk), 400):
        ch = unk[i:i + 400]
        dd = ((ch[:, None, :] - known[None]) ** 2).sum(-1)
        j = dd.argmin(1)
        near = np.sqrt(dd[np.arange(len(ch)), j]) < 14
        for (y, x), jj, ok in zip(ch, j, near):
            region[y, x] = region[tuple(known[jj])] if ok else ""
    region[(xx < 62) | (xx > 740)] = ""                      # awan di tepi gambar bukan daratan
    names = ["", "village", "ch1", "ch2", "ch3", "ch4", "ch5"]
    idx = np.zeros((h, w), np.uint8)
    for i, n in enumerate(names):
        idx[region == n] = i
    idx = np.array(Image.fromarray(idx).filter(ImageFilter.ModeFilter(13)))   # haluskan bintik antar-wilayah
    for i, n in enumerate(names):
        region[idx == i] = n
    os.makedirs(OUT, exist_ok=True)
    keep_all = np.zeros((h, w, 3), np.uint8)
    cols = {"village": (230, 80, 80), "ch1": (30, 120, 40), "ch2": (190, 140, 70), "ch3": (240, 220, 100), "ch4": (150, 90, 200), "ch5": (80, 220, 120)}
    for name in cols:
        m = (region == name)
        im2 = Image.fromarray((m * 255).astype(np.uint8))
        im2 = im2.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MedianFilter(5))
        m = np.array(im2) > 127
        m = largest_component(m)
        ys, xs = np.where(m)
        crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        Image.fromarray((crop * 255).astype(np.uint8)).save(os.path.join(OUT, name + ".png"))
        keep_all[m] = cols[name]
        print(name, "bbox(px asli)", xs.min() * S, ys.min() * S, xs.max() * S, ys.max() * S, "ukuran", crop.shape[::-1])
    Image.fromarray(keep_all).resize((w * 2, h * 2), Image.NEAREST).save(os.path.join(OUT, "_semua.png"))


def largest_component(m):
    seen = np.zeros(m.shape, bool)
    best = []
    for sy, sx in np.argwhere(m):
        if seen[sy, sx]:
            continue
        comp, stack = [], [(sy, sx)]
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros(m.shape, bool)
    for y, x in best:
        out[y, x] = True
    return out


if __name__ == "__main__":
    main()
