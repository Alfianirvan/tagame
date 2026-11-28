"""
Skrip untuk merender poster promosi 16:9 (1920x1080) 'Struktura: Legenda Dunia Data'
Disimpan di C:\\TA GAME\\poster_Struktura.png
"""
import os
from collections import deque
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

OUTPUT_PATH = r"C:\TA GAME\poster_Struktura.png"
FONT_PATH = r"C:\TA GAME\struktura\assets\fonts\Square-Black.ttf"
RAKA_RAW_PATH = r"C:\TA GAME\raka.png"
MAP_PATH = r"C:\TA GAME\struktura\assets\worldmap\peta_dunia.png"
VILLAGE_PATH = r"C:\TA GAME\struktura\docs\layout\Ch3_kota_tepilaut.png"
ALGORIA_PATH = r"C:\TA GAME\struktura\docs\layout\Algoria_seluruh_desa.png"

WIDTH = 1920
HEIGHT = 1080

def get_raka_cutout():
    im = Image.open(RAKA_RAW_PATH).convert('RGB')
    w, h = im.size
    arr = np.array(im)
    bg_target = np.array([130, 161, 128], dtype=float)

    visited = np.zeros((h, w), dtype=bool)
    is_bg = np.zeros((h, w), dtype=bool)

    queue = deque()
    for x in range(w):
        queue.append((0, x))
        queue.append((h - 1, x))
    for y in range(h):
        queue.append((y, 0))
        queue.append((y, w - 1))

    while queue:
        y, x = queue.popleft()
        if visited[y, x]:
            continue
        visited[y, x] = True
        dist = np.linalg.norm(arr[y, x].astype(float) - bg_target)
        if dist < 25:
            is_bg[y, x] = True
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                    queue.append((ny, nx))

    rgba = np.dstack([arr, np.where(is_bg, 0, 255).astype(np.uint8)])
    cutout = Image.fromarray(rgba)
    bbox = cutout.getbbox()
    return cutout.crop(bbox)

def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color, outline_width=4):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def main():
    poster = Image.new('RGBA', (WIDTH, HEIGHT), (15, 20, 30, 255))

    # 1. Base Background: Scenic village with coastal and atmospheric lighting
    village = Image.open(VILLAGE_PATH).convert('RGBA')
    # Scale village to fill canvas nicely
    vw, vh = village.size
    scale_v = max(WIDTH / vw, HEIGHT / vh) * 1.15
    nvw, nvh = int(vw * scale_v), int(vh * scale_v)
    village_scaled = village.resize((nvw, nvh), Image.Resampling.NEAREST)
    # Paste centered slightly shifted
    vx = (WIDTH - nvw) // 2
    vy = (HEIGHT - nvh) // 2 - 40
    poster.paste(village_scaled, (vx, vy), village_scaled)

    # 2. Add an atmospheric tint / gradient overlay
    # Darker on left and bottom for text clarity, vignette around edges
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d_overlay = ImageDraw.Draw(overlay)

    # Horizontal gradient (dark on left, clearer on right)
    for x in range(WIDTH):
        alpha = int(220 * (1.0 - (x / WIDTH) ** 1.4))
        alpha = max(40, min(240, alpha))
        d_overlay.line([(x, 0), (x, HEIGHT)], fill=(12, 18, 28, alpha))

    # Vertical gradient from bottom
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        if ratio > 0.5:
            b_alpha = int(210 * ((ratio - 0.5) / 0.5) ** 1.3)
            d_overlay.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, b_alpha))
        elif ratio < 0.2:
            t_alpha = int(140 * ((0.2 - ratio) / 0.2))
            d_overlay.line([(0, y), (WIDTH, y)], fill=(8, 12, 20, t_alpha))

    poster = Image.alpha_composite(poster, overlay)

    # 3. World map frame in mid-ground
    world_map = Image.open(MAP_PATH).convert('RGBA')
    mw, mh = world_map.size
    # Resize map keeping aspect ratio
    map_h = 740
    map_w = int(mw * (map_h / mh))
    map_scaled = world_map.resize((map_w, map_h), Image.Resampling.NEAREST)

    # Map frame / border
    frame_w = map_w + 24
    frame_h = map_h + 24
    map_card = Image.new('RGBA', (frame_w, frame_h), (0, 0, 0, 0))
    mc_draw = ImageDraw.Draw(map_card)
    # Outer drop shadow & frame
    mc_draw.rounded_rectangle([0, 0, frame_w, frame_h], radius=16, fill=(35, 22, 12, 220), outline=(212, 168, 85, 255), width=4)
    mc_draw.rounded_rectangle([8, 8, frame_w - 8, frame_h - 8], radius=10, fill=(20, 15, 10, 240), outline=(140, 95, 45, 255), width=2)
    map_card.paste(map_scaled, (12, 12), map_scaled)

    # Position map card in middle-right
    map_x = 980
    map_y = 170
    poster.paste(map_card, (map_x, map_y), map_card)

    # Map label header
    font_badge = ImageFont.truetype(FONT_PATH, 20)
    map_label_im = Image.new('RGBA', (280, 40), (0, 0, 0, 0))
    ml_draw = ImageDraw.Draw(map_label_im)
    ml_draw.rounded_rectangle([0, 0, 280, 40], radius=8, fill=(45, 28, 15, 240), outline=(230, 190, 100, 255), width=2)
    ml_draw.text((25, 8), "PETA DUNIA ALGORIA", font=font_badge, fill=(255, 230, 160))
    poster.paste(map_label_im, (map_x + (frame_w - 280) // 2, map_y - 20), map_label_im)

    # 4. Foreground: Character Raka
    raka = get_raka_cutout()
    rw, rh = raka.size
    # Scale Raka to be prominent on the far right
    target_rh = 940
    target_rw = int(rw * (target_rh / rh))
    raka_scaled = raka.resize((target_rw, target_rh), Image.Resampling.NEAREST)

    # Raka position: bottom right
    rx = WIDTH - target_rw + 70
    ry = HEIGHT - target_rh + 20

    # Subtle drop shadow behind Raka
    shadow_mask = raka_scaled.split()[3]
    shadow_im = Image.new('RGBA', (target_rw, target_rh), (5, 8, 15, 180))
    poster.paste(shadow_im, (rx - 15, ry + 15), shadow_mask)
    poster.paste(raka_scaled, (rx, ry), raka_scaled)

    # 5. Typography and Branding
    draw = ImageDraw.Draw(poster)

    # Fonts
    font_super = ImageFont.truetype(FONT_PATH, 118)
    font_title = ImageFont.truetype(FONT_PATH, 42)
    font_sub = ImageFont.truetype(FONT_PATH, 28)
    font_body = ImageFont.truetype(FONT_PATH, 22)
    font_small = ImageFont.truetype(FONT_PATH, 18)

    # Top Category Badge (Workshop PPLG)
    badge_x = 90
    badge_y = 90
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 520, badge_y + 44], radius=10, fill=(30, 45, 65, 230), outline=(100, 160, 230, 255), width=2)
    draw.text((badge_x + 22, badge_y + 11), "GAMEPROG · WORKSHOP PPLG · KELOMPOK 10", font=font_small, fill=(210, 235, 255))

    # Main Title: STRUKTURA
    title_x = 85
    title_y = 160
    # Deep shadow
    draw_text_with_outline(draw, (title_x, title_y), "STRUKTURA", font_super,
                           fill_color=(255, 215, 90), outline_color=(40, 20, 10), outline_width=9)
    # Inner bright highlights
    draw.text((title_x, title_y), "STRUKTURA", font=font_super, fill=(255, 235, 140))

    # Subtitle: Legenda Dunia Data
    sub_y = title_y + 140
    draw_text_with_outline(draw, (title_x + 5, sub_y), "LEGENDA DUNIA DATA", font_title,
                           fill_color=(245, 240, 225), outline_color=(35, 20, 10), outline_width=5)

    # Decorative Divider Line
    div_y = sub_y + 68
    draw.line([(title_x + 5, div_y), (title_x + 650, div_y)], fill=(212, 168, 85, 255), width=4)
    draw.line([(title_x + 5, div_y + 4), (title_x + 550, div_y + 4)], fill=(120, 80, 35, 200), width=2)

    # Genre & Concept Box
    desc_y = div_y + 30
    draw_text_with_outline(draw, (title_x + 5, desc_y), "Top-Down Pixel Action RPG Edukasi", font_sub,
                           fill_color=(180, 230, 255), outline_color=(15, 25, 40), outline_width=4)

    # Chapters Feature Badges (5 Data Structures)
    chapters = [
        ("Ch.1", "ARRAY", (100, 200, 130)),
        ("Ch.2", "STACK", (230, 140, 90)),
        ("Ch.3", "QUEUE", (90, 190, 230)),
        ("Ch.4", "LINKED LIST", (200, 140, 230)),
        ("Ch.5", "TREE", (235, 195, 95))
    ]

    card_y = desc_y + 55
    cx = title_x + 5
    for num, name, col in chapters:
        cw = 145 if len(name) > 6 else 125
        if name == "LINKED LIST":
            cw = 165
        draw.rounded_rectangle([cx, card_y, cx + cw, card_y + 54], radius=8,
                               fill=(20, 25, 38, 220), outline=col, width=2)
        draw.text((cx + 12, card_y + 6), num, font=font_small, fill=(180, 190, 205))
        draw.text((cx + 12, card_y + 26), name, font=font_small, fill=col)
        cx += cw + 12

    # Narrative Blurb / Feature Summary Box
    info_y = card_y + 90
    info_box_w = 780
    info_box_h = 245
    draw.rounded_rectangle([title_x + 5, info_y, title_x + 5 + info_box_w, info_y + info_box_h],
                           radius=12, fill=(15, 20, 32, 210), outline=(70, 90, 120, 255), width=2)

    synopsis_lines = [
        "Jelajahi Kerajaan Algoria dan pulihkan 5 Kristal Struktur yang dirusak King Subiyan!",
        "Kendalikan Raka, murid pandai besi, memecahkan teka-teki logika interaktif,",
        "menjawab kuis materi algoritma, serta hadapi boss penguasa wilayah dalam",
        "pertarungan aksi real-time bernuansa retro pixel art."
    ]
    cur_sy = info_y + 20
    for s_line in synopsis_lines:
        draw.text((title_x + 25, cur_sy), s_line, font=font_body, fill=(225, 230, 240))
        cur_sy += 36

    # Bottom Footer Badges: Team & Engine
    foot_y = info_y + info_box_h + 30
    draw.rounded_rectangle([title_x + 5, foot_y, title_x + 460, foot_y + 50],
                           radius=8, fill=(40, 28, 15, 240), outline=(212, 168, 85, 255), width=2)
    draw.text((title_x + 22, foot_y + 14), "KELOMPOK 10 · CAPSTONE WORKSHOP PPLG - A", font=font_small, fill=(255, 220, 140))

    # Engine badge
    eng_x = title_x + 480
    draw.rounded_rectangle([eng_x, foot_y, eng_x + 305, foot_y + 50],
                           radius=8, fill=(20, 35, 55, 240), outline=(80, 140, 210, 255), width=2)
    draw.text((eng_x + 20, foot_y + 14), "GODOT ENGINE 4 · WEB HTML5", font=font_small, fill=(180, 220, 255))

    # Save output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    poster.convert('RGB').save(OUTPUT_PATH, quality=95)
    print(f"Poster successfully saved to: {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
