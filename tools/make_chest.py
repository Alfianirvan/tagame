"""Membuat sprite peti pixel-art sederhana (assets/props/Chest_Closed.png & Chest_Open.png), 16x14."""
from PIL import Image, ImageDraw
OUT, WOOD, DARK, BAND, GOLD, INSIDE = (30, 18, 12), (166, 104, 56), (118, 70, 38), (80, 84, 96), (240, 200, 70), (40, 24, 18)

def base(open_):
    im = Image.new("RGBA", (16, 14), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((1, 6, 14, 13), fill=WOOD, outline=OUT)             # badan
    d.rectangle((2, 10, 13, 12), fill=DARK)
    d.rectangle((5, 6, 6, 13), fill=BAND); d.rectangle((9, 6, 10, 13), fill=BAND)
    if open_:
        d.rectangle((2, 1, 13, 5), fill=DARK, outline=OUT)           # tutup terbuka
        d.rectangle((3, 6, 12, 7), fill=INSIDE)                     # isi gelap
        d.point((7, 7), fill=GOLD); d.point((8, 7), fill=GOLD)
    else:
        d.rectangle((1, 2, 14, 6), fill=WOOD, outline=OUT)           # tutup
        d.rectangle((5, 2, 6, 6), fill=BAND); d.rectangle((9, 2, 10, 6), fill=BAND)
        d.rectangle((7, 5, 8, 8), fill=GOLD, outline=OUT)           # gembok
    return im

base(False).save("assets/props/Chest_Closed.png")
base(True).save("assets/props/Chest_Open.png")
