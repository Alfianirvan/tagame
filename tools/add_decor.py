"""Menambah DEKORASI ke scene dunia yang sudah ada (Village + Ch1-Ch5) tanpa membuat ulang scene.

Scene digenerate oleh gen_*.py lalu dirapikan manual di editor, jadi skrip ini hanya MENYISIPKAN node baru bernama
"Dekor_*" di bawah node Objects (beserta ext_resource/sub_resource ber-id "decor_*"). Menjalankan ulang aman: blok
Dekor_* lama dibuang dulu lalu dibuat lagi. Node lain tidak disentuh.

Sprite dari aset Pixel Crawler yang sudah ada di proyek (assets/props): stasiun pandai besi, dapur/api unggun, tungku,
meja kerja, plus barel/peti/periuk dari Furniture.png. Posisi dipilih di sekitar titik yang pasti bisa dijalani:
Bonfire (perkemahan), Checkpoint, Peti, dan collectible (Herb/Koin/Potion). Tidak menimpa objek lain (jarak minimal).

Jalankan dari folder proyek:  python tools/add_decor.py
"""
import math
import os
import random
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PROPS = os.path.join(ROOT, "assets", "props")

# nama -> (file relatif assets/props, kotak potong x0,y0,x1,y1)
SPRITES = {
    "anvil_s": ("stations/Anvil/Anvil.png", (1, 37, 63, 76)),
    "anvil_m": ("stations/Anvil/Anvil.png", (80, 36, 159, 92)),
    "anvil_l": ("stations/Anvil/Anvil.png", (176, 14, 272, 97)),
    "spit": ("stations/Cooking Station/Cooking Station.png", (1, 20, 62, 61)),
    "pot_roast": ("stations/Cooking Station/Cooking Station.png", (77, 20, 124, 63)),
    "grill_s": ("stations/Cooking Station/Cooking Station.png", (144, 20, 201, 64)),
    "grill_l": ("stations/Cooking Station/Cooking Station.png", (211, 17, 282, 64)),
    "tripod": ("stations/Cooking Station/Cooking Station.png", (11, 67, 53, 121)),
    "kettle": ("stations/Cooking Station/Cooking Station.png", (78, 82, 114, 127)),
    "cooker": ("stations/Cooking Station/Cooking Station.png", (144, 101, 192, 128)),
    "butcher": ("stations/Cooking Station/Cooking Station.png", (144, 160, 192, 208)),
    "furnace_stone": ("stations/Furnace/Furnace.png", (52, 15, 89, 64)),
    "furnace_brick": ("stations/Furnace/Furnace.png", (54, 71, 90, 128)),
    "furnace_iron": ("stations/Furnace/Furnace.png", (53, 133, 91, 192)),
    "workbench": ("stations/Workbench/Workbench.png", (48, 14, 96, 48)),
    "workbench_b": ("stations/Workbench/Workbench.png", (48, 190, 96, 224)),
    "barrel_w": ("Furniture.png", (769, 13, 783, 32)),
    "barrel_e": ("Furniture.png", (785, 13, 799, 32)),
    "crate_a": ("Furniture.png", (720, 73, 744, 96)),
    "crate_b": ("Furniture.png", (744, 73, 768, 96)),
    "pot": ("Furniture.png", (769, 80, 783, 96)),
    "bucket": ("Furniture.png", (738, 17, 750, 32)),
}
SMALL = ["barrel_w", "barrel_e", "crate_a", "crate_b", "pot", "bucket"]

# Tema per scene: perkemahan besar di Bonfire (dipilih berurutan), set kecil untuk Checkpoint/Peti/collectible.
THEMES = {
    "Village": {"camp": [["anvil_l", "workbench", "barrel_w", "crate_a"], ["grill_l", "cooker", "barrel_e", "crate_b"]],
                "small": SMALL},
    "Ch1_HutanIndeks": {"camp": [["anvil_m", "tripod", "barrel_w", "crate_a"], ["pot_roast", "kettle", "crate_b", "bucket"],
                                 ["grill_s", "tripod", "barrel_e", "crate_a"]],
                        "small": ["barrel_w", "crate_a", "pot", "bucket", "crate_b"]},
    "Ch2_TambangTumpuk": {"camp": [["anvil_m", "furnace_stone", "barrel_e", "crate_a"],
                                   ["workbench", "furnace_brick", "crate_b", "barrel_w"],
                                   ["anvil_l", "furnace_iron", "barrel_e", "crate_a"]],
                          "small": ["barrel_e", "crate_a", "crate_b", "bucket", "pot"]},
    "Ch3_PelabuhanAntre": {"camp": [["anvil_m", "grill_s", "barrel_w", "crate_a"], ["pot_roast", "cooker", "crate_b", "barrel_e"],
                                    ["grill_s", "kettle", "crate_a", "crate_b"]],
                           "small": ["crate_a", "crate_b", "barrel_w", "barrel_e", "bucket"]},
    "Ch4_GuaRantai": {"camp": [["anvil_m", "tripod", "barrel_e", "crate_a"], ["furnace_iron", "workbench_b", "crate_b", "barrel_w"],
                               ["pot_roast", "tripod", "crate_a", "barrel_e"]],
                      "small": ["crate_a", "barrel_e", "pot", "crate_b"]},
    "Ch5_PohonDunia": {"camp": [["anvil_m", "kettle", "pot", "barrel_w"], ["cooker", "workbench_b", "barrel_e", "crate_a"]],
                       "small": ["pot", "barrel_w", "bucket", "crate_a"]},
}
SCENES = ["Village", "Ch1_HutanIndeks", "Ch2_TambangTumpuk", "Ch3_PelabuhanAntre", "Ch4_GuaRantai", "Ch5_PohonDunia"]

_trim_cache = {}


def trimmed_box(name):
    """Kotak potong yang sudah dipangkas ke piksel terisi (relatif pada sheet)."""
    if name in _trim_cache:
        return _trim_cache[name]
    f, box = SPRITES[name]
    im = Image.open(os.path.join(PROPS, f)).convert("RGBA").crop(box)
    bb = im.getbbox()
    res = (f, (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3]))
    _trim_cache[name] = res
    return res


def split_sections(text):
    """Pecah tscn menjadi seksi (header '[...]' + isinya). Elemen pertama bisa kosong."""
    parts = re.split(r"(?m)^(?=\[)", text)
    return [p for p in parts if p != ""]


def strip_old_decor(sections):
    keep = []
    for s in sections:
        if re.match(r'\[node name="Dekor', s):
            continue
        if re.match(r'\[node name="[^"]+" type="[A-Za-z0-9]+" parent="Objects/Dekor', s):
            continue
        if re.match(r'\[(ext_resource|sub_resource)[^\]]* id="decor_', s):
            continue
        keep.append(s)
    return keep


def read_objects(sections):
    """Posisi semua node langsung di bawah Objects: {nama: (x, y)}."""
    out = {}
    for s in sections:
        m = re.match(r'\[node name="([^"]+)"[^\]]* parent="Objects"', s)
        if not m:
            continue
        p = re.search(r"(?m)^position = Vector2\(([-0-9.]+), ([-0-9.]+)\)", s)
        if p:
            out[m.group(1)] = (float(p.group(1)), float(p.group(2)))
    return out


def map_size(sections):
    for s in sections:
        m = re.search(r"map_size = Vector2i\((\d+), (\d+)\)", s)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def decorate(scene_name):
    path = os.path.join(ROOT, "scenes", "world", scene_name + ".tscn")
    raw = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    sections = strip_old_decor(split_sections(text))
    objs = read_objects(sections)
    size = map_size(sections)
    theme = THEMES[scene_name]
    rng = random.Random(sum(map(ord, scene_name)))

    occupied = list(objs.values())
    placed = []   # (nama sprite, x, y)

    def free(x, y, r):
        if size and not (40 < x < size[0] - 40 and 60 < y < size[1] - 30):
            return False
        return all(math.hypot(x - ox, y - oy) >= r for ox, oy in occupied)

    def put(name, ax, ay, radii, angles, min_gap):
        """Taruh sprite di sekitar anchor pada sudut/radius pertama yang kosong."""
        for r in radii:
            for a in angles:
                x = round(ax + math.cos(math.radians(a)) * r)
                y = round(ay + math.sin(math.radians(a)) * r * 0.7)
                if free(x, y, min_gap):
                    placed.append((name, x, y))
                    occupied.append((x, y))
                    return True
        return False

    def anchors(prefix):
        return sorted((v for k, v in objs.items() if re.match(prefix + r"\d*$", k)), key=lambda p: (p[0], p[1]))

    # perkemahan di tiap Bonfire: satu stasiun besar + tiga barang kecil melingkar
    camps = theme["camp"]
    for i, (bx, by) in enumerate(anchors("Bonfire")):
        kit = camps[i % len(camps)]
        base = rng.choice([200, 20, 160, 340])
        put(kit[0], bx, by, (78, 92, 108), [base + d for d in (0, 25, -25, 50, -50)], 34)
        for j, name in enumerate(kit[1:]):
            put(name, bx, by, (60, 72, 86), [base + 90 + j * 75 + d for d in (0, 20, -20, 40)], 22)

    # Checkpoint: barel + peti kecil; Peti: satu barang di sampingnya
    for cx, cy in anchors("Checkpoint"):
        for j in range(2):
            put(rng.choice(theme["small"]), cx, cy, (34, 44), [150 + j * 200 + d for d in (0, 30, -30)], 20)
    for cx, cy in anchors("Peti"):
        put(rng.choice(theme["small"]), cx, cy, (26, 34), [rng.choice([0, 180]) + d for d in (0, 40, -40)], 18)
    # taburan kecil di dekat collectible (titik yang pasti bisa dijalani); tiap 2 titik satu barang
    spots = [v for k, v in objs.items() if re.match(r"(Herb|Koin|Potion|Ore)\d*$", k)]
    rng.shuffle(spots)
    for hx, hy in spots[: max(4, len(spots) // 2)]:
        put(rng.choice(theme["small"]), hx, hy, (24, 32), [rng.randint(0, 359) + d for d in (0, 60, 120, 180)], 22)

    # ------------------------------------------------------------ tulis node baru
    ext_lines, sub_lines, node_lines = [], [], []
    ext_ids = {}
    sub_ids = {}
    for name, x, y in placed:
        f, box = trimmed_box(name)
        if f not in ext_ids:
            ext_ids[f] = "decor_" + re.sub(r"[^A-Za-z0-9]", "_", f)
            ext_lines.append(f'[ext_resource type="Texture2D" path="res://assets/props/{f}" id="{ext_ids[f]}"]\n')
    n = 0
    if any(nm.startswith("anvil") for nm, _, _ in placed):
        ext_lines.append('[ext_resource type="Script" path="res://scripts/entities/Anvil.gd" id="decor_script_anvil"]' + chr(10))
    for name, x, y in placed:
        f, box = trimmed_box(name)
        w, h = box[2] - box[0], box[3] - box[1]
        cw, ch = max(6, w - 8), max(6, min(12, h // 3))
        sid = f"decor_rect_{cw}_{ch}"
        if sid not in sub_ids:
            sub_ids[sid] = True
            sub_lines.append(f'[sub_resource type="RectangleShape2D" id="{sid}"]\nsize = Vector2({cw}, {ch})\n\n')
        nm = f"Dekor_{name}_{n}"
        n += 1
        node_lines.append(
            f'[node name="{nm}" type="StaticBody2D" parent="Objects"]' + chr(10)
            + ('script = ExtResource("decor_script_anvil")' + chr(10) if name.startswith("anvil") else "")
            + f'position = Vector2({x}, {y})' + chr(10)
            + f"collision_layer = 1\ncollision_mask = 0\n\n"
            + f'[node name="Sprite2D" type="Sprite2D" parent="Objects/{nm}"]\ntexture = ExtResource("{ext_ids[f]}")\n'
            + f"offset = Vector2(0, {-h / 2})\nregion_enabled = true\n"
            + f"region_rect = Rect2({box[0]}, {box[1]}, {w}, {h})\n\n"
            f'[node name="CollisionShape2D" type="CollisionShape2D" parent="Objects/{nm}"]\n'
            f"position = Vector2(0, {-ch / 2})\nshape = SubResource(\"{sid}\")\n\n")

    # sisipkan ext_resource setelah ext_resource terakhir, sub_resource sebelum node pertama, node di akhir
    last_ext = max((i for i, s in enumerate(sections) if s.startswith("[ext_resource")), default=0)
    first_node = next(i for i, s in enumerate(sections) if s.startswith("[node"))
    out = sections[: last_ext + 1]
    ext_block = "".join(ext_lines)
    if out and not out[-1].endswith("\n\n"):
        out[-1] = out[-1].rstrip("\n") + "\n"
    out.append(ext_block)
    out += sections[last_ext + 1: first_node]
    out.append("".join(sub_lines))
    out += sections[first_node:]
    if out[-1] and not out[-1].endswith("\n"):
        out[-1] += "\n"
    out.append("".join(node_lines).rstrip("\n") + "\n")
    result = "".join(out)
    steps = len(re.findall(r"(?m)^\[(ext_resource|sub_resource)", result)) + 1
    result = re.sub(r"load_steps=\d+", f"load_steps={steps}", result, count=1)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(result.replace("\n", nl))
    return placed


def main():
    names = sys.argv[1:] or SCENES
    for sc in names:
        placed = decorate(sc)
        kinds = {}
        for name, _, _ in placed:
            kinds[name] = kinds.get(name, 0) + 1
        print(f"{sc}: {len(placed)} dekorasi", dict(sorted(kinds.items())))


if __name__ == "__main__":
    main()
