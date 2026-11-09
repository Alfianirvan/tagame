"""Membuat sheet serang (Attack-Sheet.png, 6 frame 64x64) untuk Orc dan Skeleton: jarak dekat (senjata) dan penyihir (tongkat sihir).

Paket Pixel Crawler hanya punya Idle, Run, dan Death untuk musuh biasa, jadi frame serang dibuat dari frame Idle:
badan membungkuk (shear/squash), senjata (gada / belati / pedang tulang) digambar dan diayunkan, plus busur tebasan.
Frame 0-2 = bersiap (dipakai saat WINDUP), frame 3-5 = menebas (dipakai saat menerjang).
File asli tidak diubah; hasil ditulis ke assets/enemies/<jenis>/<Nama>/Attack/Attack-Sheet.png.

Jalankan:  python tools/make_enemy_attack.py
"""
import math
import os
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "enemies")
CANVAS = 64
FEET_Y = 46          # kaki pada kanvas 64 (idle 32x32 ditempel di (16,16) -> titik tengah sama dengan Run)
HAND = (36, 35)      # tangan kanan pada kanvas

# jenis -> (folder, senjata)
ENEMIES = {
    "orc/Orc": "gada",
    "orc/Orc - Rogue": "belati",
    "orc/Orc - Warrior": "kapak",
    "skeleton/Skeleton - Base": "pedang_tulang",
    "skeleton/Skeleton - Rogue": "belati_tulang",
    "skeleton/Skeleton - Warrior": "pedang_tulang_besar",
}

# (shear, squash_y, dx, dy, sudut_senjata, busur)  sudut: 0 = lurus ke kanan, -90 = ke atas, +90 = ke bawah
FRAMES = [
    (-0.05, 0.95, -1, 0, 70, None),
    (-0.15, 0.96, -2, 0, -55, None),
    (-0.22, 1.00, -3, -1, -115, None),
    (0.20, 0.98, 4, 0, -5, (-75, 25, 230)),
    (0.28, 0.94, 6, 1, 40, (-20, 75, 130)),
    (0.08, 0.98, 2, 0, 60, None),
]

# Penyihir (jarak jauh): jenis -> (warna tongkat, warna bola sihir; sama dengan projectile_color di enemies.json)
CASTERS = {
    "orc/Orc - Shaman": ((120, 85, 50, 255), (123, 214, 90)),
    "skeleton/Skeleton - Mage": ((200, 190, 170, 255), (176, 107, 255)),
}
# (shear, squash_y, dx, dy, sudut_tongkat, radius_bola, ledakan)  frame 0-2 mengumpulkan sihir, 3-5 melepas
CAST_FRAMES = [
    (-0.04, 0.96, -1, 0, -62, 2, 0),
    (-0.10, 0.98, -2, -1, -78, 3, 0),
    (-0.14, 1.00, -2, -1, -90, 4, 0),
    (0.12, 0.98, 3, 0, -25, 5, 1),
    (0.16, 0.97, 4, 0, -12, 3, 2),
    (0.05, 1.00, 1, 0, -45, 1, 0),
]

OUT = (28, 18, 12, 255)

WEAPONS = {
    # nama: (panjang, tebal, warna, bentuk)
    "gada": (14, 3, (150, 100, 55, 255), "gada"),
    "kapak": (15, 3, (130, 90, 55, 255), "kapak"),
    "belati": (9, 2, (205, 210, 220, 255), "bilah"),
    "pedang_tulang": (15, 2, (235, 228, 205, 255), "bilah"),
    "pedang_tulang_besar": (18, 3, (235, 228, 205, 255), "bilah"),
    "belati_tulang": (9, 2, (235, 228, 205, 255), "bilah"),
}


def body_frame(idle, shear, sy, dx, dy):
    """Menempel frame idle ke kanvas 64 lalu membungkuk (shear) dan menekan (squash) dengan titik putar di kaki."""
    base = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    base.paste(idle, (16, 16))
    y0 = FEET_Y
    data = (1, shear, -shear * y0 - dx, 0, 1.0 / sy, y0 - y0 / sy - dy)
    return base.transform((CANVAS, CANVAS), Image.AFFINE, data, resample=Image.NEAREST)


def draw_weapon(img, kind, angle, hand):
    length, width, color, shape = WEAPONS[kind]
    d = ImageDraw.Draw(img)
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    hx, hy = hand
    tx, ty = hx + ux * length, hy + uy * length
    d.line([(hx - ux * 2, hy - uy * 2), (tx, ty)], fill=OUT, width=width + 2)
    d.line([(hx - ux * 2, hy - uy * 2), (tx, ty)], fill=color, width=width)
    if shape == "gada":
        d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=OUT)
        d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=color)
    elif shape == "kapak":
        px, py = -uy, ux
        pts = [(tx - ux * 5 + px * 5, ty - uy * 5 + py * 5), (tx + ux * 1 + px * 6, ty + uy * 1 + py * 6),
               (tx + ux * 1 - px * 1, ty + uy * 1 - py * 1), (tx - ux * 5, ty - uy * 5)]
        d.polygon(pts, fill=(185, 190, 200, 255), outline=OUT)
    else:  # bilah: ujung runcing
        d.polygon([(tx + ux * 3, ty + uy * 3), (tx - uy * 1.5, ty + ux * 1.5), (tx + uy * 1.5, ty - ux * 1.5)], fill=color)
    # genggaman
    d.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(110, 140, 60, 255) if "tulang" not in kind else (225, 215, 190, 255), outline=OUT)


def draw_arc(img, hand, spec, tint):
    start, end, alpha = spec
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = hand
    r = 20
    d.arc([cx - r, cy - r, cx + r, cy + r], start, end, fill=tint + (alpha,), width=3)
    d.arc([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], start + 8, end - 8, fill=(255, 255, 255, alpha // 2), width=1)
    img.alpha_composite(layer)


def draw_staff(img, angle, hand, staff_color, orb_color, orb_r, burst):
    """Tongkat panjang dengan bola sihir bercahaya di ujung; burst = cincin cahaya saat sihir dilepas."""
    d = ImageDraw.Draw(img)
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    hx, hy = hand
    length = 20
    tx, ty = hx + ux * length, hy + uy * length
    d.line([(hx - ux * 3, hy - uy * 3), (tx, ty)], fill=OUT, width=4)
    d.line([(hx - ux * 3, hy - uy * 3), (tx, ty)], fill=staff_color, width=2)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    if orb_r > 0:
        g.ellipse([tx - orb_r - 2, ty - orb_r - 2, tx + orb_r + 2, ty + orb_r + 2], fill=orb_color + (90,))
        g.ellipse([tx - orb_r, ty - orb_r, tx + orb_r, ty + orb_r], fill=orb_color + (255,), outline=OUT)
        g.ellipse([tx - 1, ty - 1, tx + 1, ty + 1], fill=(255, 255, 255, 255))
    if burst:
        r = 7 if burst == 1 else 12
        g.ellipse([tx - r, ty - r, tx + r, ty + r], outline=orb_color + (200 if burst == 1 else 110,), width=2)
    img.alpha_composite(glow)
    d2 = ImageDraw.Draw(img)
    d2.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(110, 140, 60, 255) if orb_color[1] > 200 else (225, 215, 190, 255), outline=OUT)


def make_caster(folder):
    staff_color, orb_color = CASTERS[folder]
    idle = Image.open(os.path.join(ROOT, folder, "Idle", "Idle-Sheet.png")).convert("RGBA").crop((0, 0, 32, 32))
    out = Image.new("RGBA", (CANVAS * len(CAST_FRAMES), CANVAS), (0, 0, 0, 0))
    for i, (shear, sy, dx, dy, ang, orb_r, burst) in enumerate(CAST_FRAMES):
        f = body_frame(idle, shear, sy, dx, dy)
        hand = (HAND[0] + dx + shear * (FEET_Y - HAND[1]), HAND[1] + dy)
        draw_staff(f, ang, hand, staff_color, orb_color, orb_r, burst)
        out.paste(f, (i * CANVAS, 0))
    target = os.path.join(ROOT, folder, "Attack")
    os.makedirs(target, exist_ok=True)
    out.save(os.path.join(target, "Attack-Sheet.png"))
    return out


def make(folder, weapon):
    idle_path = os.path.join(ROOT, folder, "Idle", "Idle-Sheet.png")
    sheet = Image.open(idle_path).convert("RGBA")
    idle = sheet.crop((0, 0, 32, 32))   # frame idle pertama
    tint = (225, 255, 200) if folder.startswith("orc") else (255, 250, 235)
    out = Image.new("RGBA", (CANVAS * len(FRAMES), CANVAS), (0, 0, 0, 0))
    for i, (shear, sy, dx, dy, ang, arc) in enumerate(FRAMES):
        f = body_frame(idle, shear, sy, dx, dy)
        hand = (HAND[0] + dx + shear * (FEET_Y - HAND[1]), HAND[1] + dy)
        # senjata di depan badan saat menebas; di belakang badan hanya saat diangkat ke atas-belakang
        behind = ang < -130
        if behind:
            layer = Image.new("RGBA", f.size, (0, 0, 0, 0))
            draw_weapon(layer, weapon, ang, hand)
            layer.alpha_composite(f)
            f = layer
        else:
            draw_weapon(f, weapon, ang, hand)
        if arc:
            draw_arc(f, hand, arc, tint)
        out.paste(f, (i * CANVAS, 0))
    target = os.path.join(ROOT, folder, "Attack")
    os.makedirs(target, exist_ok=True)
    out.save(os.path.join(target, "Attack-Sheet.png"))
    return out


if __name__ == "__main__":
    for folder, weapon in ENEMIES.items():
        make(folder, weapon)
        print("dibuat:", folder, "->", weapon)
    for folder in CASTERS:
        make_caster(folder)
        print("dibuat:", folder, "-> tongkat sihir")
