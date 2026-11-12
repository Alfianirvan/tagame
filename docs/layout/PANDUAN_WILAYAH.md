# Panduan Wilayah: bentuk peta + desa per chapter

Dokumen ini dibaca bersama `CLAUDE.md`. Isinya aturan untuk membangun ulang scene wilayah
(`Village.tscn` = Ch0, `Ch1_HutanIndeks.tscn` … `Ch5_PohonDunia.tscn`) supaya **bentuk dan ukurannya
sama dengan wilayahnya di Peta Dunia** (`res://assets/worldmap/peta_dunia.png`), dan supaya setiap chapter
punya alur **desa → masalah → temui warga → quest → perjalanan → boss**.

## 1. Bentuk & ukuran = Peta Dunia

File panduan di folder ini:
- `ChX_<Nama>_layout.png`: bentuk wilayah. Hijau/cokelat/ungu = area wilayah, merah = tepi/penghalang
  (sungai, tebing, jurang), abu-abu = wilayah lain (tidak boleh dimasuki), biru = laut. Garis krem = jalan utama.
  Grid tiap 10 tile.
- `region_layout.json`: data yang sama dalam angka. Per wilayah ada `ukuran_tile`, `ukuran_px`,
  `titik_tile` (entry, village_center, bonfire_village, journey_start, puzzle, bonfire_preboss, boss_arena, exit),
  `jalan_tile` (polyline jalan), dan `mask` (baris string; `#` = di dalam wilayah, `.` = di luar).

Skala: **1 piksel peta 270×480 = 1 tile 16×16 px** (= 3 piksel di `peta_dunia.png` 810×1440).
Koordinat tile di JSON relatif ke pojok kiri atas bbox wilayah.

| Scene | Ukuran (tile) | Ukuran (px) |
|---|---|---|
| Village (Ch0 Desa Algoria) | 139×90 | 2224×1440 |
| Ch1_HutanIndeks | 203×144 | 3248×2304 |
| Ch2_TambangTumpuk | 161×161 | 2576×2576 |
| Ch3_PelabuhanAntre | 136×184 | 2176×2944 |
| Ch4_GuaRantai | 165×128 | 2640×2048 |
| Ch5_PohonDunia | 152×117 | 2432×1872 |

Aturan bentuk:
1. Garis luar wilayah mengikuti `mask` (boleh dihaluskan 1–2 tile). Di luar mask: laut, tebing, atau hutan
   lebat yang tidak bisa dilewati, dengan collision.
2. **Skala tetap 1.0 (JANGAN dikecilkan).** Jalan utama mengikuti `jalan_tile` dari `entry` ke `exit` (lebar 3–5 tile). Arah jalan harus sama dengan
   di Peta Dunia (misal Hutan Indeks: masuk dari bawah, keluar di atas).
3. **Area yang bisa dijelajahi**: koridor ±15–25 tile di kiri-kanan jalan, ditambah tanah lapang desa, area puzzle,
   arena boss, dan 2–3 jalan cabang pendek (peti, Herb, Ore, rahasia). Sisa area di dalam mask diisi dekorasi
   padat (pohon, batu, air) yang tidak bisa dilewati, supaya bentuknya tetap sama tapi map tidak kosong dan
   performa Web tetap ringan.
4. Penghalang merah di tepi wilayah dibuat sesuai biome: sungai + **jembatan** di titik `entry`/`exit` bila
   jalan menyeberang (Ch1, Ch3), tebing/terowongan (Ch2), jurang + jembatan es (Ch4).
5. `Bounds` dan batas kamera (Camera2D limit) = `ukuran_px`. `PlayerStart` di `entry`; `RegionExit` di `exit`.

## 2. Alur setiap chapter (Ch1–Ch5)

1. **Masuk wilayah** → kartu judul nama wilayah.
2. **Desa** (sekitar `village_center`): suasana normal tapi ada tanda masalah (warga panik, rak berantakan,
   jalan diblokir). Gerbang keluar desa ke `journey_start` **terkunci** sampai Quest Awal selesai
   (penjaga/pagar/kayu tumbang menghalangi).
3. **Temui warga**: 3 warga biasa memberi potongan cerita (ikon "?"). Setelah Raka bicara dengan minimal 2 warga,
   NPC utama chapter mendapat ikon "!" → **Quest Awal** (cerita + 3 soal pilihan ganda → hadiah senjata/armor/heal).
   Pelacak tujuan menuntun langkah demi langkah ("Tanya warga tentang masalah desa (1/2)" → "Temui Arman").
4. **Perjalanan**: gerbang desa terbuka. Musuh biasa, peti, Herb/Ore, Bonfire desa.
5. **Quest Tengah** di titik `puzzle` (puzzle materi chapter, scene di `scenes/puzzles/`).
6. **Bonfire sebelum boss** → **arena boss** (terkunci sampai Quest Tengah selesai).
7. Setelah boss kalah: Kristal didapat → jalan pintas ke desa terbuka → **kembali ke desa** → **Quest Akhir** di NPC utama
   (2 soal evaluasi) → Data Fragment + Gold → jalan ke wilayah berikutnya terbuka di `exit` (lihat 2b).


## 2b. Aturan jarak & logika (WAJIB)

- **Zona aman desa**: tidak ada musuh dalam radius **45 tile** (±2 layar) dari tepi desa. Musuh pertama baru
  muncul setelah gerbang desa + jalan hutan ±1,5 layar.
- **Jarak desa → arena boss** minimal **120 tile** jalan kaki, melewati 3–4 kelompok musuh, puzzle, dan Bonfire.
- Dalam viewport 640×360 (40×22 tile) **tidak boleh** terlihat warga dan musuh sekaligus.
- **Quest Akhir TIDAK di sebelah arena boss.** NPC utama tetap di desa. Setelah boss kalah:
  1. Kristal jatuh, muncul **jalan pintas** (gerbang/jembatan/tali yang terbuka) dari arena boss kembali ke desa,
     plus opsi **teleport lewat Bonfire** ("Kembali ke Desa").
  2. Pelacak tujuan: "Bawa Kristal ke <NPC> di <Desa>". Ikon "!" di NPC dan penanda di minimap/panah.
  3. Di desa: dialog + 2 soal evaluasi → Data Fragment + Gold → NPC berkata jalan ke wilayah berikutnya terbuka.
  4. Jalan ke `exit` (di belakang arena boss) terbuka; Raka bisa lewat jalan pintas lagi atau teleport Bonfire.
  Node `FinalNPCs` di dekat arena **dihapus**; posisi Quest Akhir = rumah/tempat NPC utama di desa.

## 2c. Tata letak desa (pusat desa + pinggiran yang bisa dijelajahi)

Referensi: desa bergaya alun-alun (lihat `village_reference_*.png`). Ukuran desa ±**70×55 tile**.
- **Pusat desa (alun-alun)**: sumur/air mancur di tengah, lantai batu, 4 jalan bersilang (utara–selatan–timur–barat),
  papan pengumuman, 2–3 lapak pasar (tenda kain), bendera/umbul-umbul, lampu jalan, bangku. Warga paling ramai di sini.
- **Cincin rumah**: 6–9 bangunan mengelilingi alun-alun, menghadap jalan, variasi atap (merah, hijau, biru, cokelat),
  tiap rumah punya pekarangan: pagar kayu, kebun bunga/sayur, tong, peti, jemuran, cerobong berasap.
- **Pinggiran (bisa dijelajahi, aman tanpa musuh)**, minimal 3 area di sisi-sisi desa, misalnya:
  ladang + lumbung, kolam/danau + dermaga pancing, kebun buah/makam tua/kandang, tepi hutan + pondok penebang.
  Pinggiran dihubungkan jalan setapak tanah dari jalan utama.
- **Gerbang desa** di ujung jalan menuju perjalanan (terkunci sampai Quest Awal selesai).

## 2d. Quest Awal diperluas: cari petunjuk

1. Masuk desa → cutscene singkat masalah.
2. Bicara dengan 3 warga di alun-alun (ikon "?"), masing-masing menunjuk satu tempat di pinggiran.
3. **Cari 3 petunjuk** di pinggiran desa (objek berkilau, interaksi E): misal jejak kaki, catatan sobek, barang hilang.
   Setiap petunjuk memunculkan teks singkat yang terkait materi chapter (Ch1: nomor indeks rak/lumbung, dst.).
4. Setelah 3 petunjuk → NPC utama dapat "!" → cerita + 3 soal → hadiah → gerbang desa terbuka.
Pelacak tujuan: "Tanya warga (1/3)" → "Cari petunjuk di sekitar desa (0/3)" → "Laporkan ke <NPC>".

## 3. Desa tiap wilayah

| Wilayah | Desa | NPC utama | Masalah yang ditemukan | Warga (3) | Aset Pixel Crawler yang wajib dipakai |
|---|---|---|---|---|---|
| Ch0 Desa Algoria | Desa Algoria (start) | Joko | Prolog: kristal pecah, Raka diutus | 2–3 warga latar | rumah Raka + rumah Joko (Walls/Roofs), Farm (ladang), Bonfire, dermaga kecil |
| Ch1 Hutan Indeks | **Dusun Larik** (desa penebang & petani di tepi hutan) | Arman | Lumbung berisi rak bernomor kacau, hasil panen hilang, Golem muncul di hutan | penjaga lumbung, penebang kayu, pedagang sayur | Sawmill, Farm, Cooking Station/Grill (dapur umum), Workbench, Trees Model_01–03, Vegetation |
| Ch2 Tambang Tumpuk | **Kampung Tumpuk** (kampung penambang) | Lilbah | Peti tambang ditumpuk salah, terowongan runtuh, penambang terjebak | mandor tambang, istri penambang, pengangkut peti | **Anvil_01–03, Furnace (Bricks/Iron/Stone), Workbench** (bengkel Lilbah), Rocks, Resources, Tools, Dungeon_Tiles untuk mulut tambang; Ninja Adventure TilesetDesert/Relief |
| Ch3 Pelabuhan Antre | **Kota Pelabuhan Antre** | Dadang | Antrean penumpang kapal kacau, kapal tidak berangkat, Kapten bajak laut menguasai dermaga | penjual tiket, nelayan, penumpang | **Kedai Dadang = interior Tavern** (contoh susunan: `MockUps/Tavern.png`), Cooking Station (Butchery, Grill, Cooker), Meat, Pan, Furniture, Water_tiles; Ninja Adventure Water/Boat/Sail |
| Ch4 Gua Rantai | **Desa Simpul** (rumah-rumah dihubungkan jembatan tali) | Megas | Portal penghubung antar-rumah putus, warga tersesat di gua | penjaga jembatan, murid sihir, pencari kristal | **Alchemy_Table_01–03** (rumah Megas), Esoteric, Dungeon_Tiles + Dungeon_Props untuk gua; Ninja Adventure Dungeon/Hole, CanvasModulate ungu |
| Ch5 Pohon Dunia | **Desa Akar** (desa di akar raksasa) | Tedy | Cabang Pohon Dunia dikuasai pasukan King Subiyan | penjaga akar, tetua desa, prajurit muda | Trees, Vegetation, Esoteric, Bonfire_09/10, Ninja Adventure Nature/Flower; atmosfer cahaya |

Aturan desa:
- Tiap desa: 6–9 bangunan (lihat 2c) dari `Structures/Buildings` (Walls + Roofs + Props + Shadows, variasi atap hijau &
  cokelat), pagar, lampu, sumur/papan, ladang/gudang sesuai tema, minimal 1 Bonfire.
- **Interior**: setiap desa minimal 1 bangunan yang bisa dimasuki (rumah/bengkel NPC utama; di Ch3 kedai Dadang)
  memakai `Interior_Walls_01.png` + `Interior_Props_01.png` + `Furniture.png`. Masuk lewat pintu (Area2D) →
  scene interior kecil → keluar kembali ke depan pintu.
- Warga memakai sprite Citizen_A, Peasant_A, Tavern_A/B, Rogue, Knight, Wizzard dari Pixel Crawler
  (boleh recolor seperti NPC lain). Warga boleh berjalan bolak-balik pendek (patrol 2 titik).
- Dialog warga di `res://data/dialogs/<chapter>_<warga>.json`, isinya menjelaskan masalah dan menyinggung
  materi chapter secara ringan.

## 4. Dekorasi perjalanan (pakai aset semaksimal mungkin)

- Ch1: hutan lebat tiga model pohon, semak, bunga, batang kayu, sungai + jembatan kayu, kamp penebang.
- Ch2: ngarai, batu besar, rel & gerobak tambang (Tools/Resources), tumpukan peti, obor, mulut tambang gelap.
- Ch3: pantai, dermaga kayu, kapal (Boat/Sail), peti kargo, jaring ikan, mercusuar kecil.
- Ch4: gunung salju, kristal ungu, mulut gua dengan Dungeon_Tiles, rantai, jembatan es di celah.
- Ch5: akar raksasa, jamur bercahaya, altar (Esoteric), tangga menuju puncak pohon (arena King Subiyan).

## 5. Aset tambahan (sudah ada di res://assets)

| Aset | Lokasi | Dipakai untuk |
|---|---|---|
| Free 2D Top-Down Pixel Dungeon (CraftPix, tile 16×16): dinding & lantai batu, pintu/tuas/peti beranimasi, jebakan duri, obor & api, air gua | `assets/tilesets/dungeon_craftpix/` | Ch2 bagian dalam tambang + arena Golem/Penyihir; Ch4 lorong Gua Rantai + puzzle portal; Ch5 menara/aula King Subiyan. Peti beranimasi untuk Chest, tuas untuk gerbang puzzle, jebakan duri sebagai rintangan perjalanan |
| Tiny RPG Orc (Zerie, frame 100×100: Idle, Walk, Attack01/02, Hurt, Death) | `assets/enemies/tiny_orc/` | Musuh biasa kecil (goblin hutan Ch1, perampok tambang Ch2). Sprite-nya lebih kecil dari Raka, tampilkan dengan scale ±1.3 dan offset kaki yang benar |
| Tiny RPG Soldier (frame 100×100 + panah) | `assets/characters/npc/tiny_soldier/` | Penjaga gerbang desa (yang menghalangi sebelum Quest Awal selesai), prajurit Desa Akar Ch5; panahnya bisa jadi proyektil musuh pemanah (recolor) |

Lisensi: keduanya boleh dipakai & dimodifikasi untuk proyek ini, tidak boleh dijual/disebarkan ulang. Catat di CREDITS.md
(Zerie: Tiny RPG Character Asset Pack; Free Game Assets / CraftPix: Free Top-Down Pixel Dungeon).

## 6. KHUSUS Chapter 1 Hutan Indeks: 4 desa (menggantikan aturan 1 desa untuk Ch1)

Gambar: `Ch1_HutanIndeks_rencana_4desa.png`. Titik (tile) ada di `region_layout.json` → Ch1 `titik_tile`.

| Urutan | Lokasi (tile) | Isi | Musuh di sekitar | Peran quest (materi Array) |
|---|---|---|---|---|
| Opening | – | Opening credit scene (teks + ilustrasi) tentang Kristal Struktur & King Subiyan, lalu pemain muncul di START (selatan, setelah jembatan) | – | Pengenalan cerita |
| Desa 1 – Dusun Larik | desa1 (95,92), selatan | Desa utuh dengan alun-alun (aturan 2c). Warga panik diserang Goblin. Arman = NPC utama | Goblin (`tiny_orc` / Orc Pixel Crawler) menyerbu pinggir desa | **Quest Awal**: usir Goblin, tanya warga, cari petunjuk, kuis 3 soal Array → jalan ke timur & barat terbuka |
| Desa 2 | desa2 (156,79), timur | Desa kecil (3–4 rumah) yang tanah & airnya tercemar (warna ungu/hijau gelap) | Slime beracun (Ninja Adventure `Slime`, `Slime2`) + jamur beracun (`Mushroom`) | **Quest Tengah bagian 1**: puzzle rak lumbung berindeks (taruh benih sesuai indeks mulai 0) untuk memurnikan sumur |
| Desa 3 (porak-poranda) | desa3 (43,87), barat | Rumah rusak/terbakar (tileset VillageAbandoned, puing, asap), penyintas bersembunyi | Goblin + Slime campuran | Selamatkan 3 penyintas; tiap penyintas memberi **petunjuk** berupa nomor indeks |
| Desa 4 (reruntuhan) | desa4 (136,22), utara | Reruntuhan total, altar segel di tengah | Gelombang musuh terkuat | **Quest Tengah bagian 2**: nyalakan obor sesuai urutan indeks dari petunjuk Desa 3 → dapat **Kunci Segel** |
| Boss | boss_arena (124,50), pusat hutan | Arena melingkar di tengah hutan, gerbang bersegel | Golem Batu | Gerbang arena hanya terbuka dengan Kunci Segel |
| Setelah boss | – | Kristal jatuh → jalan pintas ke Desa 1 terbuka (+ teleport Bonfire) | – | **Quest Akhir** di Desa 1 (Arman, 2 soal evaluasi) → **awan/fog of war** di Peta Dunia tersingkap otomatis → jalan ke Tambang Tumpuk (exit utara) terbuka |

Aturan tambahan Ch1:
- Jalan: START → Desa 1 → cabang timur ke Desa 2 → kembali → cabang barat ke Desa 3 → jalan hutan ke utara ke Desa 4 → turun ke arena boss di pusat → exit utara. Jalur antar-desa berupa jalan setapak berkelok (bukan garis lurus) lewat hutan, dengan musuh, peti, Herb, dan Bonfire di tengah tiap jalur.
- Desa 2–4 lebih kecil dari Desa 1 (±35×30 tile) supaya pengerjaan cepat; Desa 3 & 4 memakai versi rusak dari bangunan yang sama + puing.
- Gerbang ke Desa 2/3 terbuka setelah Quest Awal; jalan ke Desa 4 terbuka setelah petunjuk Desa 3 lengkap; arena boss butuh Kunci Segel.
- Zona aman 2b tetap berlaku untuk Desa 1 setelah Goblin diusir (sebelumnya Goblin menyerbu sebagai bagian quest). Desa 2–4 memang wilayah berbahaya.
- Target durasi Ch1 menjadi ±15 menit.
- Musuh Ninja Adventure berukuran 16×16: tampilkan dengan scale 2 agar seimbang dengan Raka.
