"""Memotong ikon item dari sprite sheet asli menjadi PNG baru (file asli tidak diubah).
Jalankan dari folder proyek: python tools/make_item_icons.py"""
from PIL import Image

def crop(src, box, out, size=24, tint=None):
    im = Image.open(src).convert("RGBA").crop(box)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    if tint:
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (int(r * tint[0]), int(g * tint[1]), int(b * tint[2]), a)
    scale = max(1, min(size // max(im.width, 1), size // max(im.height, 1)))
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
    canvas.save(f"assets/items/icons/{out}.png")

R = "assets/items/Resources.png"
W = "assets/weapons/Wood.png"
crop(R, (99, 18, 110, 30), "gold")
crop(R, (47, 15, 66, 29), "ore")
crop(R, (36, 115, 46, 124), "herb")
crop(R, (80, 18, 94, 31), "data_fragment", tint=(0.6, 1.4, 1.6))
crop(R, (4, 50, 14, 63), "potion")
crop(R, (36, 50, 46, 63), "potion_besar")
crop(W, (2, 5, 14, 47), "pedang_kayu")
crop(W, (2, 5, 14, 47), "pedang_besi", tint=(0.75, 0.85, 1.25))
crop(W, (66, 2, 78, 50), "tombak_kayu")
crop(W, (47, 17, 65, 47), "palu_kayu")
crop(W, (50, 47, 64, 81), "busur_kayu")
crop(W, (98, 20, 111, 62), "tongkat_sihir")
crop(W, (98, 20, 111, 62), "tongkat_sihir_plus", tint=(0.8, 1.0, 1.5))
for n, tint in [("helm_besi", (0.75, 0.85, 1.25)), ("zirah_rantai", (0.8, 0.9, 1.2)),
                ("armor_besi", (0.75, 0.85, 1.25)), ("perisai_legendaris", (1.4, 1.2, 0.5)),
                ("armor_legendaris", (1.4, 1.2, 0.5))]:
    pass  # ikon armor memakai ikon slot dari assets/ui/icons (lihat data/icons.json)
