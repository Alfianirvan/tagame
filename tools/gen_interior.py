"""Membuat interior rumah: Rumah Arman (Ch1) dan Rumah Mandor (Ch2, Kampung Tumpuk).
Tiap rumah: assets/props/buildings/Interior/room_<id>.png + scenes/world/Interior_<Nama>.tscn.

Ruangan 288x192 dari Interior_Walls_01 (lantai & dinding log) dan Interior_Props_01 (kasur, meja, jendela, kompor, tanaman).
Pintu keluar di tengah bawah (InteriorDoor is_exit) mengembalikan Raka ke depan pintu rumah di wilayah.
Jalankan:  python tools/gen_interior.py
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_village import ROOT, Scene, v2  # noqa: E402

RW, RH = 288, 192
INT = os.path.join(ROOT, "assets/props/buildings/Interior")
WALLS = Image.open(os.path.join(INT, "Interior_Walls_01.png")).convert("RGBA")
PROPS = Image.open(os.path.join(INT, "Interior_Props_01.png")).convert("RGBA")

# (kotak sheet, posisi kaki x, y, kotak tabrakan (w, h) atau None)
ITEMS = [
    ((0, 288, 31, 346), (14, 112), None),            # kasur
    ((0, 288, 31, 346), (56, 112), None),            # kasur ke-2
    ((80, 8, 113, 42), (216, 126), (30, 14)),        # meja bulat
    ((68, 176, 91, 198), (56, 38), None),            # jendela di dinding
    ((116, 0, 145, 62), (252, 70), (28, 18)),        # kompor
    ((0, 352, 80, 384), (30, 186), None),            # tanaman
]


def trim(box, sheet=PROPS):
    c = sheet.crop(box)
    bb = c.getbbox()
    return c.crop(bb), (box[0] + bb[0], box[1] + bb[1])


def build_room(room_id):
    room = Image.new("RGBA", (RW, RH), (0, 0, 0, 255))
    floor = WALLS.crop((8, 328, 40, 360))
    for y in range(48, RH, 32):
        for x in range(0, RW, 32):
            room.alpha_composite(floor, (x, y))
    wall = WALLS.crop((32, 96, 64, 128))
    for x in range(0, RW, 32):
        room.alpha_composite(wall, (x, 16))
        room.alpha_composite(WALLS.crop((32, 96, 64, 112)), (x, 0))
    colliders = []
    for box, (fx, fy), col in ITEMS:
        im, _ = trim(box)
        room.alpha_composite(im, (fx - im.width // 2 if box[1] != 288 else fx, fy - im.height))
        if col:
            colliders.append((fx, fy, col[0], col[1]))
    rug, _ = trim((336, 336, 384, 384))
    room.alpha_composite(rug, (RW // 2 - rug.width // 2, RH - rug.height - 6))
    room.save(os.path.join(INT, f"room_{room_id}.png"))
    return colliders


def build_scene(colliders, room_id, scene_name, chapter, music):
    sc = Scene()
    script = sc.ext_res("Script", "res://scripts/world/Interior.gd")
    door = sc.ext_res("Script", "res://scripts/world/InteriorDoor.gd")
    player = sc.ext_res("PackedScene", "res://scenes/entities/Player.tscn")
    room = sc.ext_res("Texture2D", f"res://assets/props/buildings/Interior/room_{room_id}.png")
    sc.node(scene_name, "Node2D", script=f'ExtResource("{script}")', chapter=str(chapter), music_name=f'"{music}"',
            room_size=f"Vector2i({RW}, {RH})")
    sc.node("Latar", "ColorRect", ".", offset_left="-500.0", offset_top="-400.0", offset_right="800.0", offset_bottom="600.0",
            color="Color(0, 0, 0, 1)", z_index="-10")
    sc.node("Ruangan", "Sprite2D", ".", texture=f'ExtResource("{room}")', centered="false")
    sc.node("Objects", "Node2D", ".", y_sort_enabled="true")
    sc.nodes.append(f'[node name="Player" parent="Objects" instance=ExtResource("{player}")]\nposition = {v2(RW // 2, 148)}\n')
    sc.node("PlayerStart", "Marker2D", ".", position=v2(RW // 2, 148))
    sc.node("PintuKeluar", "Area2D", ".", position=v2(RW // 2, RH - 8), script=f'ExtResource("{door}")', is_exit="true")
    sc.node("CollisionShape2D", "CollisionShape2D", "PintuKeluar", shape=f'SubResource("{sc.rect_shape(70, 28)}")')
    sc.node("Bounds", "StaticBody2D", ".", collision_layer=1, collision_mask=0)
    walls = {"Atas": (RW / 2, 22, RW, 44), "Bawah": (RW / 2, RH + 8, RW, 16), "Kiri": (-8, RH / 2, 16, RH), "Kanan": (RW + 8, RH / 2, 16, RH)}
    for i, (fx, fy, w, h) in enumerate(colliders):
        walls[f"Furnitur{i}"] = (fx, fy - h / 2, w, h)
    walls["Kasur"] = (14 + 34, 112 - 26, 78, 52)
    for nm, (x, y, w, h) in walls.items():
        sc.node(nm, "CollisionShape2D", "Bounds", position=v2(x, y), shape=f'SubResource("{sc.rect_shape(w, h)}")')
    out = os.path.join(ROOT, f"scenes/world/{scene_name}.tscn")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sc.render())


if __name__ == "__main__":
    for rid, name, ch, music in (("arman", "Interior_RumahArman", 1, "desa_algoria"),
                                 ("mandor", "Interior_RumahMandor", 2, "desa_algoria")):
        build_scene(build_room(rid), rid, name, ch, music)
        print(name + ".tscn dibuat")
