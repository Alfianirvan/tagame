# Kit Aset Chapter 1 (Hutan Indeks)

Semua di `res://assets/ninja/` (Ninja Adventure, lisensi CC0) + aset yang sudah ada. Pratinjau: `docs/layout/kit_ch1_preview.png`.
Aturan potong sprite: pakai region_rect yang tepat untuk SATU objek utuh, tanpa rotasi/skala aneh; cek tiap prefab dengan screenshot dulu.

## Format sprite Ninja Adventure
- Monster & hewan (`monsters/*/<Nama>.png`, `animals/*/SpriteSheet*.png`): grid 16×16. Monster 64×64 = 4 kolom arah
  (bawah, atas, kiri, kanan) × 4 baris frame jalan. Tampilkan dengan **scale 2** agar seimbang dengan Raka.
- Boss `boss/GiantSlime/Idle.png` (310×52, 5 frame ±62×52), `Jump.png`, `Hit.png`.
- FX berupa strip horizontal (tinggi = ukuran frame): mis. `fx/Flam/Flam.png` 200×30 → frame 20×30? hitung dari lebar÷jumlah frame di Preview.gif.

## Pemetaan ke Chapter 1

| Kebutuhan | Aset |
|---|---|
| Goblin (Desa 1, jalur barat) | `assets/enemies/orc/` (Orc Crew Pixel Crawler, gaya paling cocok dengan Raka); `tiny_orc` hanya cadangan |
| Slime beracun (Desa 2) | `ninja/monsters/Slime2` (hijau, beracun), `Slime`, `Slime3` |
| Jamur beracun (Desa 2) | `ninja/monsters/Mushroom`, `Mushroom2` |
| Mini-boss opsional Desa 2 | `ninja/boss/GiantSlime` (Slime raksasa di sumur tercemar) |
| Hewan desa (suasana hidup) | `ninja/animals/Chicken, Cow, Pig, Dog, Cat, Horse, Frog` (jalan acak pelan di pekarangan/ladang, Frog di kolam) |
| Desa 1 Dusun Larik | Bangunan Pixel Crawler (Walls/Roofs) + dari `ninja/tilesets/TilesetHouse.png`: lapak pasar beratap kain, pagar, papan nama, spanduk, gentong, peti; `ninja/animated/Flag` di alun-alun; `ninja/animated/MillPropeller` (kincir angin) di ladang; `ninja/tilesets/TilesetField.png` untuk petak sawah/ladang |
| Desa 2 (tercemar, tepi sungai) | `ninja/animated/WaterMill` (kincir air), `Water Ripples` (bisa SpriteSheetPurple untuk air beracun), tanah gelap + Herb mati, CanvasModulate kehijauan di area tercemar |
| Desa 3 (porak-poranda) | `ninja/tilesets/TilesetVillageAbandoned.png` (rumah berlumut/rusak, puing, batang tumbang), `ninja/tilesets/tileset_camp.png` (tenda pengungsi + api unggun untuk penyintas), `ninja/fx/Flam` + `ninja/fx/Smoke` (sisa kebakaran) |
| Desa 4 (disegel) | VillageAbandoned + patung/pilar dari TilesetHouse; kubah segel: `ninja/fx/Magic/Shield/SpriteSheetBlue.png` (di-modulate ungu) + `ninja/fx/Magic/Circle`; hilang dengan `ninja/fx/Magic/Spark` |
| Puzzle segel / gerbang arena | `ninja/fx/Magic/Circle`, `Aura`; obor Pixel Crawler / `free-2d dungeon fire_animation` |
| Awan pembatas ber-collision | `ninja/fx/Particle/Clouds.png` (awan putih 80×36) disusun bertumpuk & sedikit acak skala 2–3 + StaticBody2D; tambahkan `ninja/fx/Environment/Fog.png` di belakangnya; animasi fade saat Chapter 1 selesai |
| Suasana hutan | `ninja/fx/Environment/Raylight.png` (berkas cahaya, blend add, alpha rendah), `ninja/fx/Particle/Leaf.png` (daun jatuh, GPUParticles2D/CPUParticles2D), `ninja/animated/Flower`, `Plant` |
| Air & sungai | `ninja/tilesets/TilesetWater.png` + `ninja/animated/Water Ripples`, `Waterfall` (jika ada tebing) |
| Item & hadiah | `ninja/items/Treasure` (BigTreasureChest, LittleTreasureChest, GoldCoin, GoldKey), `Resource` (Rock, Branch, Grass, Gem*), `Potion`, `Food` (hadiah warga) |
| FX tebasan/kena pukul | `ninja/fx/Slash/SlashCurved`, `Cut`; serpihan `ninja/fx/Particle/Rock, Wood, Grass` saat memukul batu/kayu/semak |

Catatan gaya: bangunan utama tetap Pixel Crawler (lebih detail); aset Ninja dipakai untuk props, reruntuhan, tenda, hewan, monster, dan FX. Jangan campur dua gaya rumah dalam satu desa.
Kredit: tambahkan "Ninja Adventure Asset Pack – Pixel-boy & AAA (CC0)" di CREDITS.md.

## Tambahan (CraftPix gratis) di `res://assets/craftpix/`

| Aset | Dipakai untuk |
|---|---|
| `cursed_land/` (Ground, details, Objects + objects/ terpisah: Veins, Bones, Ruins, Rock_eyes, Eye_plant, Spike_plant, Tentacle_plant, Tubular_plant, Many_eyes_plant, Rock1–3) | **Tanah terkutuk Golem**: area di sekitar arena boss (pusat hutan) dan di dalam kubah segel Desa 4. Akar merah/urat menjalar keluar dari arena sebagai tanda bahaya, tulang & reruntuhan di Desa 4, tanaman bermata sebagai dekorasi seram (tidak berbahaya). Setelah boss kalah, efek kutukan di Desa 4 memudar (fade ke tanah normal). Jangan pakai di desa yang masih hidup |
| `cursed_land/bridges.png`, `Water_coasts.png` | Jembatan & tepi air gelap di dekat arena boss bila ada sungai |
| `fields/objects/3 Pointer` | **Papan penunjuk arah** di persimpangan jalan antar-desa (bagian dari panduan arah) |
| `fields/animated/1 Flag` (bendera biru beranimasi), `2 Campfire` (api unggun + asap) | Bendera di alun-alun Desa 1 / gerbang desa; api unggun di kamp penyintas Desa 3 dan pos jalan |
| `fields/objects/8 Camp` (tenda), `2 Fence`, `4 Stone`, `5 Grass`, `6 Flower`, `9 Bush`, `7 Decor` | Kamp penyintas Desa 3, pagar ladang, variasi batu/semak/bunga di jalan setapak |

Catatan: `fields/FieldsTileset.png` (lantai batu oranye) warnanya terlalu mencolok dibanding Pixel Crawler; pakai hanya bila sudah di-recolor. Objek Cursed Land berukuran besar (mis. Veins 256×256): cek ukuran dan sesuaikan scale sebelum dipasang. Lisensi CraftPix: boleh dipakai di gim, tidak boleh disebarkan ulang; tambahkan kredit di CREDITS.md.
