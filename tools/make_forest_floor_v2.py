"""Lantai hutan lebat v2: tajuk dari SPRITE POHON ASLI Pixel Crawler (sama dengan pohon dekorasi di map) ditumpuk rapat
di atas tanah gelap + bayangan, tersambung mulus (torus) -> assets/tilesets/forest_floor.png (400x400, 25x25 tile).
Tileset forest_tileset.tres tidak berubah. Jalankan:  python tools/make_forest_floor_v2.py
"""
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PROPS = os.path.join(ROOT, "assets", "props")
SIZE = 400


def tree_crops():
    cells = [("Trees/Model_01/Size_03.png", (0, 0, 48, 96)), ("Trees/Model_01/Size_03.png", (48, 0, 96, 96)),
             ("Trees/Model_02/Size_03.png", (0, 0, 48, 80)), ("Trees/Model_02/Size_03.png", (0, 80, 48, 160))]
    out = []
    for rel, box in cells:
        im = Image.open(os.path.join(PROPS, rel)).convert("RGBA")
        if box:
            im = im.crop(box)
        bb = im.getbbox()
        if bb:
            out.append(im.crop(bb))
    return out


def main():
    rng = random.Random(21)
    trees = tree_crops()
    print("sprite pohon:", [t.size for t in trees])
    base = Image.new("RGBA", (SIZE * 3, SIZE * 3), (18, 44, 26, 255))
    # variasi tanah gelap
    px = base.load()
    for _ in range(2200):
        x, y = rng.randrange(SIZE * 3), rng.randrange(SIZE * 3)
        c = rng.choice(((22, 52, 30, 255), (16, 40, 24, 255), (26, 58, 32, 255)))
        for dx in range(rng.randint(2, 6)):
            if x + dx < SIZE * 3:
                px[x + dx, y] = c
    pts = [(rng.uniform(0, SIZE), rng.uniform(0, SIZE), rng.randrange(len(trees))) for _ in range(150)]
    pts.sort(key=lambda p: p[1])
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for ox in (0, SIZE, 2 * SIZE):
        for oy in (0, SIZE, 2 * SIZE):
            for x, y, k in pts:
                w, h = trees[k].size
                sd.ellipse([x + ox - w * 0.45, y + oy - 6, x + ox + w * 0.45, y + oy + 8], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))
    base.alpha_composite(shadow)
    for ox in (0, SIZE, 2 * SIZE):
        for oy in (0, SIZE, 2 * SIZE):
            for x, y, k in pts:
                t = trees[k]
                base.alpha_composite(t, (int(x + ox - t.width / 2), int(y + oy - t.height)))
    # tonjolan gelap tipis supaya tampak rapat/teduh
    tile = base.crop((SIZE, SIZE, SIZE * 2, SIZE * 2))
    arr = np.array(tile).astype(float)
    arr[:, :, :3] *= 0.66
    tile = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    tile.save(os.path.join(ROOT, "assets", "tilesets", "forest_floor.png"))
    print("forest_floor.png ditulis")


if __name__ == "__main__":
    main()
