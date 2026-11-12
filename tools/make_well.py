"""Gambar sumur batu 40x44 (cincin batu, air, dua tiang, atap kecil) -> assets/props/well_stone.png. Buatan sendiri, bergaya Pixel Crawler.
Jalankan:  python tools/make_well.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "props", "well_stone.png")

OL = (38, 26, 20, 255)
STONE, STONE_L, STONE_D = (150, 150, 158, 255), (190, 190, 198, 255), (104, 104, 114, 255)
WATER, WATER_L = (52, 110, 178, 255), (110, 170, 226, 255)
WOOD, WOOD_D, WOOD_L = (134, 88, 46, 255), (92, 58, 30, 255), (176, 122, 70, 255)
ROOF, ROOF_D = (150, 98, 52, 255), (104, 66, 34, 255)

im = Image.new("RGBA", (40, 44), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
# cincin batu (ellipse bawah = sisi depan, ellipse atas = bibir)
d.ellipse([3, 22, 36, 42], fill=OL)
d.ellipse([4, 23, 35, 41], fill=STONE_D)
d.rectangle([4, 30, 35, 36], fill=STONE_D)
d.ellipse([4, 21, 35, 37], fill=STONE)
# batu-batu bata pada dinding depan
for x in (8, 15, 22, 29):
    d.line([(x, 33), (x, 40)], fill=OL)
d.line([(6, 36), (33, 36)], fill=OL)
# bibir & air
d.ellipse([4, 20, 35, 36], fill=OL)
d.ellipse([5, 21, 34, 35], fill=STONE_L)
d.ellipse([8, 23, 31, 33], fill=OL)
d.ellipse([9, 24, 30, 32], fill=WATER)
d.ellipse([12, 25, 22, 28], fill=WATER_L)
# dua tiang kayu + palang
for x in (6, 30):
    d.rectangle([x - 1, 6, x + 3, 32], fill=OL)
    d.rectangle([x, 6, x + 2, 31], fill=WOOD)
    d.line([(x, 7), (x, 30)], fill=WOOD_L)
d.rectangle([5, 9, 36, 12], fill=OL)
d.rectangle([6, 10, 35, 11], fill=WOOD_L)
# atap kecil
d.polygon([(2, 8), (20, 0), (38, 8)], fill=OL)
d.polygon([(4, 8), (20, 2), (36, 8)], fill=ROOF)
d.polygon([(20, 2), (36, 8), (20, 8)], fill=ROOF_D)
# tali & timba
d.line([(20, 12), (20, 24)], fill=OL)
d.rectangle([17, 22, 23, 27], fill=OL)
d.rectangle([18, 23, 22, 26], fill=WOOD)
im.save(OUT)
print("well_stone.png", im.size)
