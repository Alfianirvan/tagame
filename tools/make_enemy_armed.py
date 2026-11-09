"""Membuat sheet musuh BERSENJATA (Idle, Run, Attack) memakai sprite senjata asli Pixel Crawler (Weapons/Wood & Bone).

Hasil ditulis sebagai file baru (file asli tidak diubah):
    assets/enemies/<jenis>/<Nama>/Idle/Idle-Armed-Sheet.png    4 frame 64x64
    assets/enemies/<jenis>/<Nama>/Run/Run-Armed-Sheet.png      6 frame 64x64
    assets/enemies/<jenis>/<Nama>/Attack/Attack-Sheet.png      6 frame 64x64 (bersiap 0-2, menebas 3-5)
Semua kanvas 64x64 dengan titik kaki di (32, 46): sama dengan Attack-Sheet lama, sehingga posisi badan di game konsisten
(sprite.offset Enemy = (0, -14)). Sheet Run asli menaruh kaki di y=63 (17 px terlalu rendah), di sini digeser naik.
EnemySprites.gd otomatis memakai file "-Armed-Sheet" bila ada.

Jalankan:  python tools/make_enemy_armed.py [pratinjau.png]
"""
import math
import os
import sys

from PIL import Image

import make_enemy_attack as base

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "assets", "enemies")
WEAPON_DIR = os.path.join(HERE, "..", "assets", "weapons")
CANVAS = 64
FEET_Y = 46
RUN_SHIFT = -17     # geser Run asli (kaki di y=63) ke y=46

# Kotak potong senjata pada sheet (x0, y0, x1, y1), lalu dipangkas ke piksel terisi.
# grip = titik genggam (pecahan lebar, tinggi gambar yang sudah dipangkas); pre_rot = putar dulu (derajat, searah jarum jam)
# agar ujung senjata menghadap ke atas.
ITEMS = {
    "wood_dagger": ("Wood", (35, 17, 45, 45), (0.5, 0.82), 0),
    "wood_sword": ("Wood", (3, 6, 13, 47), (0.5, 0.86), 0),
    "wood_bow": ("Wood", (52, 48, 62, 80), (0.5, 0.5), 0),
    "wood_shield_big": ("Wood", (119, 19, 136, 43), (0.5, 0.5), 0),
    "wood_wand": ("Wood", (81, 3, 110, 13), (0.5, 0.5), -90),     # gambar horizontal, permata di kanan -> putar ke atas
    "bone_dagger": ("Bone", (37, 17, 43, 44), (0.5, 0.85), 0),
    "bone_scimitar": ("Bone", (0, 0, 16, 48), (0.5, 0.88), 0),
    "bone_staff": ("Bone", (99, 22, 109, 61), (0.5, 0.72), 0),
    "bone_shield_small": ("Bone", (145, 0, 159, 16), (0.5, 0.5), 0),
}

# jenis -> (senjata utama, tangan kedua, tangan utama (x, y) pada kanvas Idle, penyihir?)
GEAR = {
    "orc/Orc": ("bone_dagger", None),
    "orc/Orc - Rogue": ("wood_dagger", None),
    "orc/Orc - Warrior": ("bone_scimitar", "wood_shield_big"),
    "orc/Orc - Shaman": ("bone_staff", "bone_shield_small"),
    "skeleton/Skeleton - Base": ("wood_dagger", None),
    "skeleton/Skeleton - Rogue": ("wood_dagger", None),
    "skeleton/Skeleton - Warrior": ("wood_sword", "wood_shield_big"),
    "skeleton/Skeleton - Mage": ("wood_wand", None),
}
CASTER_ORB = {"orc/Orc - Shaman": (123, 214, 90), "skeleton/Skeleton - Mage": (176, 107, 255)}

# Posisi tangan utama pada kanvas Idle 64x64 (idle ditempel di (16,16)); bisa disetel per jenis.
HANDS = {
    "default": (38, 34),
}

# sudut senjata tiap frame serang melee: bersiap (0-2) mengangkat ke belakang, menebas (3-5) ke depan-bawah
SWING = [-98, -115, -128, -35, 20, 55]

_item_cache = {}


def item_image(key):
    """Gambar senjata (tegak, ujung ke atas) dan titik genggamnya dalam piksel."""
    if key in _item_cache:
        return _item_cache[key]
    sheet, box, grip, pre = ITEMS[key]
    im = Image.open(os.path.join(WEAPON_DIR, sheet + ".png")).convert("RGBA").crop(box)
    im = im.crop(im.getbbox())
    if pre:
        im = im.rotate(-pre, expand=True, resample=Image.NEAREST)
        im = im.crop(im.getbbox())
    pos = (grip[0] * im.width, grip[1] * im.height)
    _item_cache[key] = (im, pos)
    return _item_cache[key]


def paste_item(canvas, key, hand, angle, behind=None):
    """Tempel senjata dengan genggaman di `hand`; angle: 0 = ke kanan, -90 = ke atas. Mengembalikan posisi ujung."""
    im, (gx, gy) = item_image(key)
    rot = -(angle + 90.0)    # PIL memutar berlawanan arah jarum jam
    big = Image.new("RGBA", (im.width * 3, im.height * 3), (0, 0, 0, 0))
    big.paste(im, (im.width, im.height))
    pivot = (im.width + gx, im.height + gy)
    r = big.rotate(rot, center=pivot, resample=Image.NEAREST)
    x0 = int(round(hand[0] - pivot[0]))
    y0 = int(round(hand[1] - pivot[1]))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    _safe_paste(layer, r, x0, y0)
    if behind is not None:
        layer.alpha_composite(behind)
        return layer, None
    canvas.alpha_composite(layer)
    # ujung senjata (titik puncak gambar, di atas genggaman)
    a = math.radians(angle)
    length = gy
    return canvas, (hand[0] + math.cos(a) * length, hand[1] + math.sin(a) * length)


def _safe_paste(layer, img, x0, y0):
    tmp = Image.new("RGBA", (layer.width + 2 * img.width, layer.height + 2 * img.height), (0, 0, 0, 0))
    tmp.alpha_composite(img, (img.width + x0, img.height + y0))
    layer.alpha_composite(tmp.crop((img.width, img.height, img.width + layer.width, img.height + layer.height)))


def offhand(canvas, key, hand):
    """Perisai / busur di tangan belakang. Perisai digambar DI BELAKANG badan (separuh terlihat di sisi belakang),
    busur di depan badan. Mengembalikan kanvas hasil (perisai membuat lapisan baru di bawah badan)."""
    im, _ = item_image(key)
    if "shield" in key:
        im = im.resize((max(1, round(im.width * 0.8)), max(1, round(im.height * 0.8))), Image.NEAREST)
        cx, cy = hand[0] - 14, hand[1] + 4
    else:
        cx, cy = hand[0] - 10, hand[1]
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))
    if "shield" in key:
        layer.alpha_composite(canvas)
        return layer
    canvas.alpha_composite(layer)
    return canvas


def load_sheet(folder, action):
    return Image.open(os.path.join(ROOT, folder, action, action + "-Sheet.png")).convert("RGBA")


def frame_at(sheet, i, size):
    return sheet.crop((i * size, 0, i * size + size, size))


def top_y(img):
    return img.getbbox()[1]


def make_idle(folder, main, off):
    sheet = load_sheet(folder, "Idle")
    out = Image.new("RGBA", (CANVAS * 4, CANVAS), (0, 0, 0, 0))
    hx, hy = HANDS.get(folder, HANDS["default"])
    tops = []
    for i in range(4):
        f = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        f.paste(frame_at(sheet, i, 32), (16, 16))
        tops.append(top_y(f))
        dy = tops[-1] - tops[0]
        hand = (hx, hy + dy)
        if off:
            f = offhand(f, off, hand)
        paste_item(f, main, hand, -78 if "staff" not in main and "wand" not in main else -88)
        out.paste(f, (i * CANVAS, 0))
    return out


def make_run(folder, main, off):
    sheet = load_sheet(folder, "Run")
    out = Image.new("RGBA", (CANVAS * 6, CANVAS), (0, 0, 0, 0))
    hx, hy = HANDS.get(folder, HANDS["default"])
    first = None
    for i in range(6):
        src = frame_at(sheet, i, 64)
        f = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        f.paste(src.crop((0, -RUN_SHIFT, 64, 64)), (0, 0))
        t = top_y(f)
        first = t if first is None else first
        hand = (hx + 1, hy + (t - first) - 1)
        if off:
            f = offhand(f, off, hand)
        ang = -62 + (6 if i % 3 == 0 else -4 if i % 3 == 1 else 2)
        if "staff" in main or "wand" in main:
            ang = -84
        paste_item(f, main, hand, ang)
        out.paste(f, (i * CANVAS, 0))
    return out


def make_attack(folder, main, off):
    """Frame serang: badan dari Idle (membungkuk) + senjata asli yang diayun. Frame 0-2 bersiap, 3-5 menebas."""
    sheet = load_sheet(folder, "Idle")
    idle = sheet.crop((0, 0, 32, 32))
    caster = folder in CASTER_ORB
    frames = base.CAST_FRAMES if caster else [
        (sh, sq, dx_, dy_, a, arc_) for (sh, sq, dx_, dy_, _old, arc_), a in zip(base.FRAMES, SWING)]
    out = Image.new("RGBA", (CANVAS * len(frames), CANVAS), (0, 0, 0, 0))
    tint = (225, 255, 200) if folder.startswith("orc") else (255, 250, 235)
    for i, spec in enumerate(frames):
        if caster:
            shear, sy, dx, dy, ang, orb_r, burst = spec
            arc = None
        else:
            shear, sy, dx, dy, ang, arc = spec
        f = base.body_frame(idle, shear, sy, dx, dy)
        hx, hy = HANDS.get(folder, HANDS["default"])
        hand = (hx + dx + shear * (base.FEET_Y - hy), hy + dy)
        if off:
            f = offhand(f, off, hand)
        behind = False   # senjata selalu di depan badan
        if behind:
            layer = Image.new("RGBA", f.size, (0, 0, 0, 0))
            paste_item(layer, main, hand, ang)
            layer.alpha_composite(f)
            f = layer
            tip = None
        else:
            _, tip = paste_item(f, main, hand, ang)
        if arc:
            base.draw_arc(f, hand, arc, tint)
        if caster and tip is not None:
            orb = CASTER_ORB[folder]
            # cahaya sihir di ujung tongkat: membesar saat dilepas
            glow = Image.new("RGBA", f.size, (0, 0, 0, 0))
            from PIL import ImageDraw
            g = ImageDraw.Draw(glow)
            tx, ty = tip
            r = max(1, orb_r)
            if orb_r > 3 or burst:
                g.ellipse([tx - r - 2, ty - r - 2, tx + r + 2, ty + r + 2], fill=orb + (90,))
                g.ellipse([tx - r + 1, ty - r + 1, tx + r - 1, ty + r - 1], fill=orb + (255,))
            if burst:
                rr = 7 if burst == 1 else 12
                g.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], outline=orb + (200 if burst == 1 else 110,), width=2)
            f.alpha_composite(glow)
        out.paste(f, (i * CANVAS, 0))
    return out


def save(img, folder, action, name):
    d = os.path.join(ROOT, folder, action)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, name))


def main():
    preview = []
    for folder, (main_w, off) in GEAR.items():
        idle = make_idle(folder, main_w, off)
        run = make_run(folder, main_w, off)
        att = make_attack(folder, main_w, off)
        save(idle, folder, "Idle", "Idle-Armed-Sheet.png")
        save(run, folder, "Run", "Run-Armed-Sheet.png")
        save(att, folder, "Attack", "Attack-Sheet.png")
        print("dibuat:", folder, "->", main_w, off or "")
        row = Image.new("RGBA", (CANVAS * 9, CANVAS), (70, 70, 80, 255))
        row.alpha_composite(idle.crop((0, 0, CANVAS, CANVAS)), (0, 0))
        row.alpha_composite(run.crop((0, 0, CANVAS * 3, CANVAS)), (CANVAS, 0))
        row.alpha_composite(att.crop((0, 0, CANVAS * 5, CANVAS)), (CANVAS * 4, 0))
        preview.append(row)
    if len(sys.argv) > 1:
        sheet = Image.new("RGBA", (CANVAS * 9, CANVAS * len(preview)), (70, 70, 80, 255))
        for i, r in enumerate(preview):
            sheet.alpha_composite(r, (0, i * CANVAS))
        sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(sys.argv[1])


if __name__ == "__main__":
    main()
