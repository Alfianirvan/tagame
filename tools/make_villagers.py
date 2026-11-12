"""Membuat sprite warga (Idle samping, 4 frame 64x64) dari NPC Pixel Crawler, diwarnai ulang, di assets/characters/npc/.

Warga Dusun Larik (Ch1):  Penjaga (Knight), Penebang (Rogue), Sari (Tavern_B).
Format sama dengan NPC lain (NpcSprites.gd): <Nama>_Idle_Side-Sheet.png, kaki di y~46 pada kanvas 64.
Jalankan:  python tools/make_villagers.py
"""
import colorsys
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\TA GAME\Pixel Crawler - Free Pack 2.11\Pixel Crawler - Free Pack\Entities\Npc's"
OUT = os.path.join(HERE, "..", "assets", "characters", "npc")

# nama -> (folder sumber, geser hue (0..1), kecerahan)
VILLAGERS = {
    "Penjaga": ("Knight/Idle/Idle-Sheet.png", 0.0, 0.92),
    "Penebang": ("Rogue/Idle/Idle-Sheet.png", 0.06, 1.0),
    "Sari": ("Citizen_F/Tavern_B/Idle/Idle_Side-Sheet.png", 0.0, 1.0),
}


def recolor(im, shift, bright):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s > 0.15:
                h = (h + shift) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * bright))
            px[x, y] = (int(r * 255), int(g * 255), int(b * 255), a)
    return im


def main():
    for name, (rel, shift, bright) in VILLAGERS.items():
        sheet = Image.open(os.path.join(SRC, rel)).convert("RGBA")
        fs = sheet.height
        n = sheet.width // fs
        out = Image.new("RGBA", (64 * n, 64), (0, 0, 0, 0))
        for i in range(n):
            f = sheet.crop((i * fs, 0, i * fs + fs, fs))
            f = recolor(f, shift, bright)
            out.paste(f, (i * 64 + (64 - fs) // 2, (64 - fs) // 2), f)
        out.save(os.path.join(OUT, f"{name}_Idle_Side-Sheet.png"))
        print(name, sheet.size, "->", out.size)


if __name__ == "__main__":
    main()
