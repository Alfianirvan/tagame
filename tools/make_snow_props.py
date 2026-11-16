"""Properti Ch4 (Gua Rantai) buatan sendiri -> PNG BARU di assets/props/generated/ (aset asli tidak diubah).

  kristal_ungu_1.png / kristal_ungu_2.png : gugus kristal ungu dari ikon Ninja Adventure GemPurple (CC0), diperbesar 2x dan
                                            ditumpuk miring sehingga tampak seperti kristal yang tumbuh dari tanah salju.
Jalankan:  python tools/make_snow_props.py   (lalu python tools/make_prefabs.py)
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM = Image.open(os.path.join(ROOT, "assets/ninja/items/Resource/GemPurple.png")).convert("RGBA")
OUT = os.path.join(ROOT, "assets/props/generated")


def cluster(name, parts, size):
    """parts: (skala, x, y) kaki tiap kristal pada kanvas `size`."""
    im = Image.new("RGBA", size)
    for sc, x, y in parts:
        g = GEM.resize((GEM.width * sc, GEM.height * sc), Image.NEAREST)
        im.alpha_composite(g, (x - g.width // 2, y - g.height))
    im = im.crop(im.getbbox())
    im.save(os.path.join(OUT, name + ".png"))
    return im.size


def main():
    os.makedirs(OUT, exist_ok=True)
    print("kristal_ungu_1", cluster("kristal_ungu_1", [(2, 14, 40), (3, 28, 44), (2, 42, 42)], (60, 48)))
    print("kristal_ungu_2", cluster("kristal_ungu_2", [(2, 12, 34), (2, 26, 36)], (40, 40)))


if __name__ == "__main__":
    main()
