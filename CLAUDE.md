# CLAUDE.md — Struktura: Legenda Dunia Data

File ini dibaca otomatis oleh Claude Code setiap kali dijalankan di folder proyek.
Isinya adalah konteks tetap proyek. Jangan dihapus; perbarui bila ada keputusan baru.

## 1. Ringkasan proyek
- **Judul:** Struktura: Legenda Dunia Data
- **Jenis:** proyek akhir mata kuliah GameProg (Workshop PPLG), Kelompok 10, 3 anggota.
- **Genre:** top-down pixel RPG dengan cerita (gaya visual seperti Stardew Valley, pertarungan real-time seperti Zelda).
- **Materi:** struktur data. 1 chapter = 1 materi: Array, Stack (LIFO), Queue (FIFO), Linked List, Tree.
- **Engine:** Godot 4.x, bahasa **GDScript** (bukan C#).
- **Target export:** **Web (HTML5)**. Gunakan renderer **Compatibility**.
- **Kontrol:** keyboard dan mouse.

## 2. Aturan kerja untuk Claude Code
1. Kerjakan **per tahap** sesuai prompt yang diberikan. Jangan mengerjakan tahap lain tanpa diminta.
2. Sebelum menulis kode besar, jelaskan rencana singkat (file apa saja yang dibuat/diubah).
3. Kode **modular**, satu script satu tanggung jawab, **komentar berbahasa Indonesia**.
4. Gunakan **signal** untuk komunikasi antar-node (HUD, quest, atribut), bukan polling di `_process`.
5. Data game (item, quest, dialog, kuis, upgrade) disimpan di **file JSON** di `res://data/`, bukan di-hardcode.
6. Jangan mengubah file aset asli (PNG). Jika perlu sprite baru, buat file baru.
7. Scene `.tscn` boleh dibuat langsung sebagai teks. Setelah membuat/mengubah scene, sebutkan apa yang perlu dicek manual di editor Godot.
8. Setelah setiap tahap: jalankan pengecekan sintaks bila Godot CLI tersedia (`godot --headless --check-only` atau membuka proyek dengan `--headless --quit`), lalu ringkas apa yang sudah dibuat dan apa yang perlu dites manual.
9. Jangan menjalankan `git push` tanpa diminta. Commit lokal boleh bila diminta.
10. Bila ada keraguan desain, ikuti dokumen `Gambaran_Alur_Game_Struktura.docx` di folder induk; bila tetap ragu, tanyakan.

## 3. Pengaturan proyek Godot
- Viewport 640×360, stretch mode `canvas_items`, aspect `keep`.
- Default texture filter **Nearest** (pixel art), snap 2D transform/vertex ke pixel aktif.
- Renderer: Compatibility (wajib untuk Web).
- Input Map:
  | Aksi | Tombol |
  |---|---|
  | `move_up/down/left/right` | W A S D (+ panah) |
  | `attack` | J / klik kiri |
  | `dodge` | Spasi |
  | `interact` | E |
  | `inventory` | I |
  | `quest_log` | Q |
  | `world_map` | M |
  | `pause` | Esc |

### Catatan laptop Alfian (penting saat menjalankan Godot dari terminal)
- Godot: `Godot_v4.7.2-stable_win64.exe`. GPU NVIDIA di laptop ini bermasalah, jadi Godot harus dijalankan dengan
  `--rendering-driver d3d12` (memakai GPU Intel). Jika proyek memakai renderer Compatibility dan editor gagal terbuka,
  gunakan `--rendering-driver opengl3_angle`. Pastikan Project Settings `rendering/gl_compatibility/fallback_to_angle = true`.
- Perintah headless (cek/export) tidak butuh GPU: `--headless` boleh dipakai tanpa opsi driver.

## 4. Struktur folder
```
res://
├── assets/
│   ├── characters/player/      (Raka_*-Sheet.png dari ..\\player_preview)
│   ├── characters/npc/         (dari ..\\npc + Wizzard, Rogue, Citizen_F Pixel Crawler)
│   ├── enemies/orc/, enemies/skeleton/
│   ├── bosses/                 (dari folder boss_preview)
│   ├── weapons/                (Wood.png, Bone.png)
│   ├── items/                  (Resources.png, Apple.png)
│   ├── tilesets/               (Pixel Crawler: Floors, Wall, Wall_Variations, Dungeon, Water)
│   ├── tilesets_biome/         (dari ..\\tilesets_biome: Ninja Adventure Desert, Nature, Relief, Water, Floor, dll.)
│   ├── worldmap/               (gambar Peta Dunia + awan)
│   ├── props/                  (Vegetation, Trees, Furniture, Rocks, Farm, Stations, Buildings)
│   ├── portraits/              (dari ..\\portraits: portrait_<nama>_80.png & _40.png)
│   ├── ui/                     (dari ..\\audio_ui\\ui)
│   ├── fonts/                  (Square-Black.ttf)
│   └── audio/music/, audio/sfx/ (dari ..\\audio_ui\\music dan sfx + SFX lama)
├── data/        items.json, weapons.json, armors.json, upgrades.json,
│                quests.json, quiz.json, dialogs/*.json, chapters.json
├── scenes/
│   ├── ui/      StartScreen, WorldMap, Settings, About, HUD, DialogBox, QuizPanel,
│   │            GameMenu (tab Inventori/Perlengkapan/Quest/Toko/Tempa/Simpan), QuestTracker, WinScreen, LoseScreen
│   ├── world/   Village (Desa Algoria), Ch1_HutanIndeks, Ch2_TambangTumpuk,
│   │            Ch3_PelabuhanAntre, Ch4_GuaRantai, Ch5_PohonDunia
│   ├── entities/ Player, NPC, Enemy, Boss (+5 turunan), Projectile,
│   │            Collectible, Bonfire, Checkpoint, Chest
│   └── puzzles/ ArrayShelf, StackCrates, QueueCustomers, LinkedPortals, TreeMaze
└── scripts/
    ├── autoload/ GameManager.gd, SaveManager.gd, AudioManager.gd, SceneManager.gd,
    │             QuestManager.gd, DialogManager.gd
    └── (mengikuti struktur scenes/)
```
File `.aseprite` dan `.import` lama **tidak** disalin ke proyek.

## 5. Sumber aset (folder induk `C:\TA GAME\`)
- `Pixel Crawler - Free Pack 2.11/Pixel Crawler - Free Pack/` — aset utama. Lisensi (Terms.txt): boleh untuk proyek apa pun termasuk komersial dan studi, boleh dimodifikasi, tidak boleh dijual ulang sebagai aset, credit tidak wajib.
- `assets/` — aset lama: `fonts/Square-Black.ttf`, `sounds/music.ogg`, `sounds/collect_apple.wav`, `sounds/death.wav`, `sounds/jump.wav`, `images/Collectibles/Apple.png` + `Collected.png`. Folder Pink Man, Background, Terrain, dan file `.tres` lama **tidak dipakai**.
- `boss_preview/` — sprite boss buatan kelompok (lihat Bagian 10).
- `player_preview/` — sprite Raka (lihat catatan Player di bawah).
- `npc/` — sprite NPC buatan kelompok (Joko, Arman, Dadang dibuat dari Body_A; Lilbah dari Peasant_A; Tedy dari Knight). Warga lain / pelanggan antrean Chapter 3 pakai Tavern_A, Tavern_B, Peasant_A, Rogue dari Pixel Crawler (boleh diwarnai ulang dengan modulate).
- `portraits/` — potret dialog hasil AI yang sudah dirapikan: `portrait_<raka|joko|arman|lilbah|dadang|megas|tedy|king_subiyan>_80.png` (utama, 80×80, latar transparan) dan versi `_40.png` (40×40). Pakai versi 80 di kotak dialog (kotak potret FacesetBox 48×48 digambar 2× atau dibuat 96×96).
- `audio_ui/` — musik, SFX, dan UI dari **Ninja Adventure** (pixel-boy & AAA, lisensi **CC0**). File sudah diberi nama sesuai pemakaian; daftar lengkap dan peruntukannya ada di `audio_ui/README.md`. Musik: `music/<lokasi>.ogg` (menu_utama, cerita_prolog, desa_algoria, peta_dunia, ch1…ch5, boss, boss_final_king_subiyan, menang_tamat, kalah, kredit_about). SFX: `sfx/*.wav`. UI: `ui/dialog/` (kotak dialog + tempat potret, kotak pilihan), `ui/theme/` (tema kayu: tombol, panel nine-patch, sel inventory, slider), `ui/icons/` (ikon slot equipment, hati HP, emote).

### Catatan sprite Pixel Crawler
- **Player (Raka)** pakai sprite buatan kelompok di `..\player_preview\Raka_<Aksi>_<Arah>-Sheet.png` (Body_A Pixel Crawler yang sudah diberi rambut hitam jabrik, tank top krem, celana cokelat, lengan lebih berotot). **Jangan pakai Body_A polos.** Frame **64×64**, jumlah frame = lebar ÷ 64. Arah: `Down`, `Side`, `Up` (Pierce memakai `Top` untuk atas). `Side` menghadap kanan; arah kiri = `Side` di-flip (`flip_h`).
  Aksi tersedia: Idle (4), Walk (6), Run (6), Slice (8, tebas: pedang/kapak), Pierce (8, tusuk: tombak), Crush (8, hantam: palu/beliung), Hit (4), Death (8), Collect (8). Senjata kayu sudah tergambar di animasi serang.
- **Musuh** `Entities/Mobs/Orc Crew/<Orc|Orc - Rogue|Orc - Shaman|Orc - Warrior>/` dan `Skeleton Crew/<Skeleton - Base|Mage|Rogue|Warrior>/`, masing-masing `Idle/Idle-Sheet.png`, `Run/Run-Sheet.png` (frame 32×32), `Death/Death-Sheet.png` (ukuran frame berbeda-beda: cek dengan `lebar ÷ jumlah frame`). Musuh biasa tidak punya animasi menyerang: serangan memakai gerakan menerjang + hitbox + kedip.
- **NPC** `Entities/Npc's/Knight|Rogue|Wizzard/<Idle|Run|Death>/…-Sheet.png`, `Citizen_F/Citizen_A|Peasant_A|Tavern_A|Tavern_B/…`.
- **Item** `Environment/Props/Static/Resources.png` (koin, kunci, bijih/ore, 4 botol potion, kayu, daun/herb). Senjata `Weapons/Wood/Wood.png`, `Weapons/Bone/Bone.png`.
- **Stations** `Environment/Structures/Stations/Anvil|Alchemy|Bonfire|Furnace|Workbench|…`.
- **Tileset** `Environment/Tilesets/Floors_Tiles.png` (rumput, tanah, jalan, batu, salju, pasir), `Wall_Tiles.png`, `Wall_Variations.png`, `Dungeon_Tiles.png`, `Water_tiles.png`. Tile 16×16.

## 6. Cerita, tokoh, tempat
King Subiyan menghancurkan 5 Kristal Struktur penjaga keteraturan Kerajaan Algoria. **Raka**, murid pandai besi Lilbah, berkelana ke 5 wilayah untuk memulihkannya.

| Nama | Peran | Sprite |
|---|---|---|
| Raka | Tokoh utama (player) | Raka_*-Sheet.png |
| Joko | Kepala Desa, NPC pembuka awal game + tutorial | `npc/Joko_<Idle|Walk>_<Down|Side|Up>-Sheet.png` (64×64) |
| Arman | Petani, NPC Chapter 1 | `npc/Arman_<Idle|Walk>_<Arah>-Sheet.png` (64×64) |
| Lilbah | Pandai Besi & guru Raka, NPC Chapter 2 (Tambang Tumpuk) | `npc/Lilbah_<Idle|Walk>-Sheet.png` (64×64, menghadap samping) |
| Dadang | Pemilik Kedai, NPC Chapter 3 | `npc/Dadang_<Idle|Walk>_<Arah>-Sheet.png` (64×64) |
| Megas | Penyihir, NPC Chapter 4 | Pixel Crawler `Npc's/Wizzard` (32×32, menghadap samping) |
| Tedy | Ksatria, NPC Chapter 5 | `npc/Tedy_<Idle|Run|Death>-Sheet.png` (Knight diwarnai silver-merah, 32×32 / Run 64×64) |
| King Subiyan | Musuh utama, boss terakhir | boss_preview |

| Tempat | Jenis | Latar (biome) | Tile utama |
|---|---|---|---|
| Desa Algoria | Start (ujung bawah peta) | desa kecil tepi pantai, padang rumput, rumah kayu | Pixel Crawler Floors (rumput/jalan), Buildings, Water |
| Hutan Indeks | Chapter 1 – Array | hutan hijau lebat, jalan setapak | Pixel Crawler Floors + Vegetation/Trees, Ninja Nature (pohon hijau) |
| Tambang Tumpuk | Chapter 2 – Stack | ngarai gurun batu merah-oranye, mulut tambang | Ninja Desert + Relief + Floor (pasir/oranye), Pixel Crawler Dungeon_Tiles (dalam tambang) |
| Pelabuhan Antre | Chapter 3 – Queue | pantai berpasir, dermaga kayu, laut, kapal | Pixel Crawler Floors (pasir) + Water, Ninja Water + Boat/Sail + palem (Desert) |
| Gua Rantai | Chapter 4 – Linked List | pegunungan bersalju, gua es | Ninja Floor (salju/es) + Nature (pohon salju) + Relief, Pixel Crawler Dungeon_Tiles |
| Pohon Dunia | Chapter 5 – Tree | hutan ajaib ungu/merah muda, pohon raksasa di tengah | Ninja Nature (pohon sakura & musim gugur), Water (air ungu), VillageAbandoned |
Tileset biome tambahan ada di `..\tilesets_biome\` (lihat README di sana). Tiap wilayah boleh diberi `CanvasModulate` tipis untuk suasana (misal kebiruan di salju, ungu di Pohon Dunia).

### Rute petualangan (RUTE LURUS dari satu ujung peta ke ujung lain)
Peta Dunia berbentuk satu jalan yang berkelok dari **ujung bawah pulau (START)** naik ke **puncak pulau (FINAL)**. Peta vertikal 810×1440 (`peta_dunia.png`), digeser naik-turun; penanda wilayah = lingkaran biru bernomor S,1,2,3,4,F + label nama (dibuat di Godot, bukan di gambar). Koordinat pusat penanda di gambar 810×1440: S(324,1281) 1(378,1020) 2(243,762) 3(501,576) 4(324,360) F(420,144).
Setiap wilayah hanya tersambung ke wilayah sebelum dan sesudahnya lewat satu **titik sempit** (jembatan, terowongan, kapal, celah gunung, jembatan es). Wilayah lain dipisahkan penghalang alam (sungai lebar, tebing, laut, pegunungan), jadi secara geografis memang tidak bisa melompat ke wilayah lain.
| Urutan | Wilayah | Posisi di peta | Titik sempit ke wilayah berikutnya (terbuka setelah Kristal didapat) |
|---|---|---|---|
| START | Desa Algoria (desa kecil di tepi pantai) | bawah | Gerbang desa → jalan ke hutan (terbuka setelah prolog Joko) |
| 1 | Hutan Indeks (hutan hijau) | bawah-tengah | **Jembatan kayu** di atas sungai lebar yang tadinya putus |
| 2 | Tambang Tumpuk (pegunungan batu cokelat) | tengah | **Terowongan tambang** yang tadinya runtuh, tembus ke teluk |
| 3 | Pelabuhan Antre (pantai & dermaga di teluk) | tengah-atas, teluk kanan | **Kapal Dadang** menyeberangi teluk ke seberang |
| 4 | Gua Rantai (gunung salju & kristal ungu) | atas | **Jembatan es** di celah gunung menuju dataran Pohon Dunia |
| FINAL | Pohon Dunia (dataran tinggi, pohon raksasa bercahaya) | puncak | — boss terakhir King Subiyan di puncak pohon |
Wilayah yang sudah selesai bisa dikunjungi ulang lewat Peta Dunia (fast travel). Wilayah yang belum terbuka tertutup awan + gembok di Peta Dunia.

### Panduan arah untuk pemain
- **Pelacak tujuan** di pojok kiri atas HUD: teks tujuan quest aktif (misal "Temui Arman di Hutan Indeks").
- **Panah penunjuk** di tepi layar yang mengarah ke target quest (NPC/puzzle/gerbang boss) saat target di luar layar.
- NPC pemberi quest memakai ikon **"!"** (quest baru) dan **"?"** (quest siap diserahkan).
- Di Peta Dunia, wilayah tujuan berikutnya diberi **penanda berkedip**; jalan yang sudah dilewati diberi garis.
- Saat masuk wilayah baru: kartu judul singkat (nama wilayah + materi chapter).

## 7. Struktur layar dan alur
Start Screen (Mulai, Lanjutkan, Pengaturan, About, Keluar) → **Peta Dunia** (Level Select) → Game Session (Desa / wilayah / boss) → End Session **Menang** (rangkuman materi + hadiah) atau **Kalah** (Coba Lagi dari checkpoint / Menu). About berisi nama + foto 3 anggota dan dosen, plus credit aset.

**Peta Dunia:** satu gambar ilustrasi **besar** (`..\\worldmap\\peta_dunia.png`) bergaya pixel art dengan **rute lurus** dari Desa Algoria (bawah) ke Pohon Dunia (puncak), lihat tabel rute di Bagian 6. Peta bisa digeser (pan) dan sedikit di-zoom; setiap wilayah punya area klik + label nama. Awalnya hanya Desa dan Hutan Indeks yang terbuka; wilayah berikutnya terbuka (animasi awan menghilang) setelah Quest Akhir chapter sebelumnya selesai. Dibuka dari Start Screen, dari menu game, atau tombol M.

## 8. Sistem game
**Atribut:** HP, Stamina (serangan kuat & dodge, regen perlahan), Gold, XP/Level (naik level → HP & Stamina maks naik).

**Collectible & economy:**
| Item | Sumber | Konversi |
|---|---|---|
| Gold Coin | musuh, peti | beli senjata/armor/potion |
| Ore | batu tambang, musuh | Ore + Gold → upgrade di tab Tempa |
| Herb | semak (pakai sprite Apple/daun) | 3 Herb → Potion (racik di tab Toko/Inventori) |
| Data Fragment | puzzle, boss | buka skill spesial (serangan putar / dash) |

**Perlengkapan:** slot Senjata, Helm, Armor, Perisai, Aksesori. Senjata = damage, lainnya = pertahanan/HP maks. Jenis senjata: pedang (Slice), tombak (Pierce, jangkauan panjang), palu/kapak (Crush, lambat kuat), busur (jarak jauh). Armor hanya ikon + stat (tidak mengubah sprite).

**Menu Game (tombol Esc / Tab):** tab Inventori, Perlengkapan, Quest, **Toko**, **Tempa**, **Simpan**, Pengaturan. Toko, Tempa, dan Simpan bisa dipakai di mana saja kecuali saat bertarung (ada musuh dalam jarak dekat / di arena boss). Lore: Raka murid pandai besi, jadi ia membawa palu & landasan kecil untuk menempa sendiri; Toko adalah "kantong pedagang" kiriman Dadang/Joko.
**Tempa (upgrade):** pilih item → tampil stat sebelum/sesudah + biaya → Tempa.
| Level | Biaya | Efek |
|---|---|---|
| +1 | 50 Gold + 3 Ore | +20% |
| +2 | 120 Gold + 6 Ore | +40% |
| +3 | 250 Gold + 10 Ore + 1 Data Fragment | +70% + efek khusus |
Batas: Chapter 1 maks +1, Chapter 2 maks +2, Chapter 3+ maks +3. Senjata baru hanya dari quest, drop boss, atau Toko.

**Quest (3 per chapter, berurutan):**
1. **Quest Awal** — NPC pembuka (ikon "!") menceritakan masalah, lalu memberi **3 soal pilihan ganda**. Salah → petunjuk singkat, jawab ulang (tanpa game over). Semua benar → hadiah + jalan wilayah terbuka. Benar semua di percobaan pertama → bonus Gold & XP.
2. **Quest Tengah** — puzzle materi di wilayah, membuka jalan ke boss.
3. **Quest Akhir** — setelah boss kalah, jalan pintas ke desa terbuka; Raka **kembali ke desa** (jalan kaki atau teleport Bonfire) dan serahkan Kristal ke NPC utama di desa (NPC TIDAK muncul di arena boss; detail di docs/layout/PANDUAN_WILAYAH.md), dengar rangkuman, jawab **2 soal evaluasi** → Data Fragment + Gold, awan wilayah berikutnya hilang.

**Dialog:** kotak teks di bawah layar, potret + nama NPC di kanan (gaya Stardew), efek ketik, tombol E untuk lanjut, pilihan jawaban untuk kuis.

Struktur tiap wilayah (desa alun-alun, cari petunjuk, zona aman, skala map): ikuti `docs/layout/PANDUAN_WILAYAH.md`.

**Checkpoint = Bendera:** titik autosave ditandai bendera (res://assets/craftpix/fields/animated/1 Flag, atau ninja/animated/Flag). Belum aktif: bendera abu-abu/terlipat diam. Saat Raka menyentuhnya: bendera berkibar (animasi), warna berubah, SFX + teks "Progres tersimpan", autosave, dan jadi titik respawn terdekat. Bonfire tetap untuk istirahat (pulihkan HP/Stamina, respawn musuh).

**Save:** autosave di checkpoint, setelah quest selesai, dan setelah boss kalah, plus **Simpan manual** di Menu Game. **Bonfire** di tiap wilayah: pulihkan HP/Stamina dan jadi titik respawn. Tombol Lanjutkan di Start Screen memuat save terakhir. Simpan ke `user://save.json` (di Web otomatis tersimpan di penyimpanan browser).

**Target durasi:** Ch1 ±8 menit, Ch2 ±10, Ch3 ±12, Ch4 ±13, Ch5 maks 15.

## 9. Isi tiap chapter
| Ch | NPC | Quest Awal (contoh soal) | Hadiah awal | Quest Tengah (puzzle) | Boss | Hadiah tengah | Quest Akhir (contoh soal evaluasi) |
|---|---|---|---|---|---|---|---|
| Awal game | Joko | "Apa fungsi struktur data?" | Pedang Kayu + 2 Potion | – | – | – | – |
| 1 Array | Arman | "Array 5 elemen, indeks terakhir?" (4) | Helm Kulit + 2 Potion | Taruh benih di rak sesuai indeks (mulai 0); nyalakan obor berurutan | Golem Batu | Pedang Kayu +1 | "Ambil elemen ke-3, indeks berapa?" (2) |
| 2 Stack | Lilbah | "Push A,B,C lalu pop sekali?" (C) | Perisai Kayu | Ambil pedang di dasar tumpukan peti (pop dulu yang atas) | Penyihir Menara | Pedang Besi | "Contoh stack di aplikasi?" (Undo) |
| 3 Queue | Dadang | "A,B,C antre, siapa dilayani pertama?" (A) | Zirah Kulit + 3 Potion | Layani pelanggan sesuai urutan datang | Kapten Bajak Laut | Zirah Rantai + Potion | "Struktur data untuk antrean printer?" (queue) |
| 4 Linked List | Megas | "Selain data, node menyimpan apa?" (penunjuk ke node berikutnya) | Tongkat Sihir | Sambung batu portal (next), sisipkan node hilang, buang node jebakan | Ksatria Rantai | Tongkat Sihir+ | "Kelebihan linked list saat sisip di tengah?" (tidak perlu geser elemen) |
| 5 Tree | Tedy | "Node paling atas pada tree?" (root) | Armor Besi + Potion Besar | Labirin bercabang ala BST (kecil kiri, besar kanan) | King Subiyan | Perisai & Armor Legendaris | "Node tanpa anak disebut?" (leaf) → tamat |

**Ch1 (keputusan Tahap 3, menggantikan baris Ch1 di atas):** alur 4 desa: Goblin menyerbu Desa 1 → tanya 3 warga → 3 petunjuk → kuis Arman (Quest Awal) → rak lumbung Desa 2 memurnikan sumur → lapor Arman → selamatkan 3 penyintas Desa 3 → Arman menyusun petunjuk → obor segel [0]..[4] di gerbang arena (Quest Tengah) → Golem → Kristal di altar Desa 4 (kubah segel pudar) → **Quest Akhir dari Tetua Desa 4** (2 soal) → awan perbatasan hilang. Quest berlangkah memakai `steps` di quests.json + flag cerita (`GameManager.story_flags`, ikut tersimpan); uji alur: `tools/test_ch1_flow.tscn` (headless).

**Ch2 (keputusan, dikerjakan 3 tahap):** peta dibangun ulang 161×161 sesuai region_layout (generator `tools/gen_ch2_v2.py`; prototipe lama
dicadangkan di `..\_backup_scenes_organik\`). Batas = laut (barat) + dataran tinggi bertebing (TilesetRelief, `canyon_tileset.tres`),
awan hanya di titik keluar. 1 desa (Kampung Tumpuk) + tambang. Quest Awal: tanya 3 warga (Mandor, Bu Mirah, Udin) → 3 petunjuk Stack →
kuis Lilbah → kabut debu gerbang desa hilang. Uji alur: `tools/test_ch2_flow.tscn` (headless).
Tahap 2: rute desa → kantong utara → NGARAI BARAT (punggung tebing A/C/D = dataran tinggi di dalam wilayah) → mulut tambang
(stasiun tumpukan peti) → LORONG TAMBANG (kolom peti `StageBlocker`, hilang di quest_stage 2) → AULA TAMBANG berlantai abu
(Bonfire pra-boss, arena Penyihir Menara) → keluar. ±134 tile desa→arena. Jalan pintas aula→desa = longsoran batu (`StageBlocker`
mode crystal). Musuh: Orc (perampok) di ngarai, Skeleton di aula tambang.
Tahap 3: Quest Tengah = puzzle tumpukan peti di mulut tambang → hadiah **Pedang Besi** (pedang di dasar tumpukan) + peti lorong hilang.
Quest Akhir berlangkah: kalahkan Penyihir Menara (Kristal) → longsoran jalan pintas terbuka → **Lilbah tetap di Kampung Tumpuk**
(2 soal) → Data Fragment + Gold → awan perbatasan ke Pelabuhan Antre hilang. Panah memakai `Region.shortcut_route` setelah Kristal.
Tambahan (permintaan Alfian): **DUSUN CADAS** di ngarai barat laut (pusat tile (42,34), cabang jalan dari ngarai barat; Sesepuh
Cadas, Raras, Bimo; kemah perampok Orc di utaranya). Quest Tengah Ch2 kini berlangkah: temui Sesepuh → susun ulang **Tugu Batu**
(puzzle `StackTower`: POP/PUSH dari puncak sesuai pola, flag `ch2_tugu_cadas`) → baru stasiun tumpukan peti di mulut tambang
terbuka (`PuzzleStation` menolak puzzle akhir Quest Tengah selama masih ada langkah yang belum beres).

**Ch3 (keputusan, dikerjakan 3 tahap):** peta dibangun ulang 136×184 sesuai region_layout (generator `tools/gen_ch3_v2.py`, tileset
`tools/gen_coast_tileset.py` → `coast_tileset.tres`; prototipe lama dicadangkan di `..\_backup_scenes_organik\`). **Kota Pelabuhan Antre
digeser ke pesisir timur** (pusat tile (72,122), bukan village_center layout) supaya punya dermaga. Batas = laut (timur) + tebing berpuncak
rumput tua; punggung tebing di utara kota dengan satu celah = gerbang kota (kabut laut, terbuka di quest_stage 1). Kota: alun-alun + sumur,
**Kedai Dadang** (bisa dimasuki, `Interior_KedaiDadang.tscn`), pasar tenda, gudang + loket tiket + tali antrean di pangkal dermaga penumpang
(kapal layar), dermaga ikan. Pinggiran: mercusuar (tanjung selatan), kebun kelapa (barat). Quest Awal: tanya 3 warga (Wulan penjual tiket,
Pak Bahar nelayan, Nina penumpang) → 3 petunjuk Queue → kuis Dadang. Uji alur: `tools/test_ch3_flow.tscn` (headless).
Tahap 2: rute gerbang kota → barat di antara punggung tebing N & L → TONJOLAN BARAT → jalan sempit utara punggung L → KORIDOR BARAT
(di antara tebing batas & punggung M) → warung pinggir jalan (stasiun antrean, puzzle dipindah ke tile (53,46)) → BARIKADE BAJAK LAUT
(`StageBlocker`, hilang di quest_stage 2) → Bonfire pra-boss → DERMAGA BAJAK LAUT (arena Kapten berlantai papan, dipindah ke (70,22))
→ dermaga keluar di teluk utara (Kapal Dadang, exit dipindah ke (91,12)). ±189 tile kota→arena. Jalan pintas arena→kota = pesisir timur,
ditutup PERAHU KARAM (`StageBlocker` mode crystal). Musuh: awak bajak laut (Orc) + slime pantai, 25 ekor.

## 10. Boss (sprite di `boss_preview/`, sudah diperbesar 2×)
| Boss | Idle (frame) | Serang (frame) | Mati (frame) | Pola serangan |
|---|---|---|---|---|
| Golem Batu | `B_Golem_OrcWarrior_x2_Idle-Sheet.png` 64×64 ×4 | `B_Golem_Batu_Attack-Sheet.png` 208×80 ×9 | `B_Golem_Batu_Death-Sheet.png` 192×160 ×11 | Hantam tanah + gelombang kejut merambat; titik lemah menyala bergantian, dipukul sesuai urutan indeks |
| Penyihir Menara | `B_PenyihirMenara_OrcShaman_x2_Idle-Sheet.png` 64×64 ×4 | `B_PenyihirMenara_Cast-Sheet.png` 208×96 ×9 + `…_Projectile-Sheet.png` 20×20 ×4 | `B_PenyihirMenara_Death-Sheet.png` 128×128 ×12 | Menumpuk 3 bola sihir, yang terakhir ditumpuk dilempar duluan (LIFO) |
| Kapten Bajak Laut | `B_KaptenBajakLaut_OrcRogue_x2_Idle-Sheet.png` 64×64 ×4 | `B_KaptenBajakLaut_Attack-Sheet.png` 208×80 ×6 | `B_KaptenBajakLaut_Death-Sheet.png` 128×128 ×11 | Terjang jauh + tebas; memanggil anak buah berurutan (FIFO) |
| Ksatria Rantai | `B_KsatriaRantai_SkeletonWarrior_x2_Idle-Sheet.png` 64×64 ×4 | `B_KsatriaRantai_Attack-Sheet.png` 208×88 ×7 | `B_KsatriaRantai_Death-Sheet.png` 128×96 ×11 | Ayun bola berantai jarak jauh; terhubung ke kristal rantai (node) yang harus diputus dari ujung |
| King Subiyan | `B_KingSubiyan_SkeletonMage_x2_Idle-Sheet.png` 64×76 ×4 | `B_KingSubiyan_Cast-Sheet.png` 208×88 ×8 + `…_Projectile-Sheet.png` 24×24 ×4 | `B_KingSubiyan_Death-Sheet.png` 128×128 ×11 | Bola sihir; saat HP turun memanggil 2 bayangan yang masing-masing memanggil 2 lagi (tree), kalahkan dari daun |

Semua boss juga punya `…_HitFlash.png` (1 frame putih untuk kedip saat terkena).
**Titik kaki** (x, y dalam frame, untuk menyamakan posisi antar-animasi; set `offset` AnimatedSprite2D agar titik ini berada di origin node):
| Boss | Idle | Serang/Cast | Mati |
|---|---|---|---|
| Golem Batu | (29, 64) | (45, 76) | (91, 160) |
| Penyihir Menara | (37, 64) | (49, 92) | (69, 128) |
| Kapten Bajak Laut | (30, 64) | (34, 76) | (62, 128) |
| Ksatria Rantai | (28, 64) | (36, 84) | (60, 96) |
| King Subiyan | (32, 76) | (40, 84) | (64, 128) |
5 frame terakhir animasi mati: kilau → memudar → **Kristal Struktur** tertinggal (King Subiyan: + mahkota). Setelah animasi selesai, spawn item Kristal yang bisa diambil.
Animasi serangan adalah efek visual; area kena serangan diatur dengan **hitbox** yang mengikuti frame (misal hitbox gelombang kejut Golem bergerak sesuai frame). Beri **tanda peringatan merah** di lantai sebelum serangan besar.

## 11. Kesesuaian spesifikasi tugas (jangan sampai hilang)
Min. 3 atribut ✔ · min. 3 collectible yang dikonversi ✔ · in-game economy ✔ · audio & musik latar ✔ · aset berlisensi free/AI ✔ · min. 3 level dengan cerita terkait materi ✔ · Start, Level Select, Game, End (Menang/Kalah), About ✔ · output Web ✔.
