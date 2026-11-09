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

## 4. Struktur folder
```
res://
├── assets/
│   ├── characters/player/      (Pixel Crawler Body_A/Animations)
│   ├── characters/npc/         (Knight, Rogue, Wizzard, Citizen_F)
│   ├── enemies/orc/, enemies/skeleton/
│   ├── bosses/                 (dari folder boss_preview)
│   ├── weapons/                (Wood.png, Bone.png)
│   ├── items/                  (Resources.png, Apple.png)
│   ├── tilesets/               (Floors, Wall, Wall_Variations, Dungeon, Water)
│   ├── props/                  (Vegetation, Trees, Furniture, Rocks, Farm, Stations, Buildings)
│   ├── portraits/              (potret NPC dari AI, diisi belakangan)
│   ├── ui/                     (diisi belakangan: Kenney UI / Ninja Adventure, CC0)
│   ├── fonts/                  (Square-Black.ttf)
│   └── audio/music/, audio/sfx/
├── data/        items.json, weapons.json, armors.json, upgrades.json,
│                quests.json, quiz.json, dialogs/*.json, chapters.json
├── scenes/
│   ├── ui/      StartScreen, WorldMap, Settings, About, HUD, DialogBox, QuizPanel,
│   │            Inventory, QuestLog, Shop, AnvilUpgrade, PauseMenu, WinScreen, LoseScreen
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
- `boss_preview/` — sprite boss buatan kelompok (lihat Bagian 9).

### Catatan sprite Pixel Crawler
- **Player** `Entities/Characters/Body_A/Animations/<Aksi>_Base/<Aksi>_<Arah>-Sheet.png`. Frame **64×64**, jumlah frame = lebar ÷ 64. Arah: `Down`, `Side`, `Up` (Pierce memakai `Top` untuk atas). Arah kiri = `Side` di-flip (`flip_h`).
  Aksi: Idle, Walk, Run, Slice (tebas: pedang/kapak), Pierce (tusuk: tombak), Crush (hantam: palu), Hit, Death, Collect, Carry_*.
  Catatan: Body_A adalah badan dasar tanpa baju (keputusan visual menyusul; jangan diblok karena ini).
- **Musuh** `Entities/Mobs/Orc Crew/<Orc|Orc - Rogue|Orc - Shaman|Orc - Warrior>/` dan `Skeleton Crew/<Skeleton - Base|Mage|Rogue|Warrior>/`, masing-masing `Idle/Idle-Sheet.png`, `Run/Run-Sheet.png` (frame 32×32), `Death/Death-Sheet.png` (ukuran frame berbeda-beda: cek dengan `lebar ÷ jumlah frame`). Musuh biasa tidak punya animasi menyerang: serangan memakai gerakan menerjang + hitbox + kedip.
- **NPC** `Entities/Npc's/Knight|Rogue|Wizzard/<Idle|Run|Death>/…-Sheet.png`, `Citizen_F/Citizen_A|Peasant_A|Tavern_A|Tavern_B/…`.
- **Item** `Environment/Props/Static/Resources.png` (koin, kunci, bijih/ore, 4 botol potion, kayu, daun/herb). Senjata `Weapons/Wood/Wood.png`, `Weapons/Bone/Bone.png`.
- **Stations** `Environment/Structures/Stations/Anvil|Alchemy|Bonfire|Furnace|Workbench|…`.
- **Tileset** `Environment/Tilesets/Floors_Tiles.png` (rumput, tanah, jalan, batu, salju, pasir), `Wall_Tiles.png`, `Wall_Variations.png`, `Dungeon_Tiles.png`, `Water_tiles.png`. Tile 16×16.

## 6. Cerita, tokoh, tempat
King Subiyan menghancurkan 5 Kristal Struktur penjaga keteraturan Kerajaan Algoria. **Raka**, murid pandai besi Lilbah, berkelana ke 5 wilayah untuk memulihkannya.

| Nama | Peran | Sprite |
|---|---|---|
| Raka | Tokoh utama (player) | Body_A |
| Joko | Kepala Desa, NPC pembuka awal game + tutorial | Citizen/Peasant |
| Arman | Petani, NPC Chapter 1 | Peasant_A |
| Lilbah | Pandai Besi, NPC Chapter 2, pemilik Anvil (upgrade) | Citizen/Tavern |
| Dadang | Pemilik Kedai, NPC Chapter 3 | Tavern_A/B |
| Megas | Penyihir, NPC Chapter 4 | Wizzard |
| Tedy | Ksatria, NPC Chapter 5 | Knight |
| King Subiyan | Musuh utama, boss terakhir | boss_preview |

| Tempat | Jenis |
|---|---|
| Desa Algoria | Hub (NPC, Anvil, pedagang, meja ramuan, Bonfire) |
| Hutan Indeks | Chapter 1 – Array |
| Tambang Tumpuk | Chapter 2 – Stack |
| Pelabuhan Antre | Chapter 3 – Queue |
| Gua Rantai | Chapter 4 – Linked List |
| Pohon Dunia | Chapter 5 – Tree |

## 7. Struktur layar dan alur
Start Screen (Mulai, Lanjutkan, Pengaturan, About, Keluar) → **Peta Dunia** (Level Select) → Game Session (Desa / wilayah / boss) → End Session **Menang** (rangkuman materi + hadiah) atau **Kalah** (Coba Lagi dari checkpoint / Menu). About berisi nama + foto 3 anggota dan dosen, plus credit aset.

**Peta Dunia:** satu gambar ilustrasi berisi Desa Algoria + 5 wilayah. Awalnya hanya Desa dan Chapter 1 terbuka; wilayah lain tertutup **awan + ikon gembok**. Setelah Quest Akhir chapter selesai, animasi awan menghilang dan wilayah berikutnya terbuka. Dibuka dari Start Screen, papan di gerbang desa, atau tombol M. Wilayah selesai bisa dikunjungi ulang.

## 8. Sistem game
**Atribut:** HP, Stamina (serangan kuat & dodge, regen perlahan), Gold, XP/Level (naik level → HP & Stamina maks naik).

**Collectible & economy:**
| Item | Sumber | Konversi |
|---|---|---|
| Gold Coin | musuh, peti | beli senjata/armor/potion |
| Ore | batu tambang, musuh | Ore + Gold → upgrade di Anvil |
| Herb | semak (pakai sprite Apple/daun) | 3 Herb → Potion di meja ramuan |
| Data Fragment | puzzle, boss | buka skill spesial (serangan putar / dash) |

**Perlengkapan:** slot Senjata, Helm, Armor, Perisai, Aksesori. Senjata = damage, lainnya = pertahanan/HP maks. Jenis senjata: pedang (Slice), tombak (Pierce, jangkauan panjang), palu/kapak (Crush, lambat kuat), busur (jarak jauh). Armor hanya ikon + stat (tidak mengubah sprite).

**Upgrade di Anvil (Lilbah):** pilih item → tampil stat sebelum/sesudah + biaya → Tempa.
| Level | Biaya | Efek |
|---|---|---|
| +1 | 50 Gold + 3 Ore | +20% |
| +2 | 120 Gold + 6 Ore | +40% |
| +3 | 250 Gold + 10 Ore + 1 Data Fragment | +70% + efek khusus |
Batas: Chapter 1 maks +1, Chapter 2 maks +2, Chapter 3+ maks +3. Senjata baru hanya dari quest, drop boss, atau pedagang.

**Quest (3 per chapter, berurutan):**
1. **Quest Awal** — NPC pembuka (ikon "!") menceritakan masalah, lalu memberi **3 soal pilihan ganda**. Salah → petunjuk singkat, jawab ulang (tanpa game over). Semua benar → hadiah + jalan wilayah terbuka. Benar semua di percobaan pertama → bonus Gold & XP.
2. **Quest Tengah** — puzzle materi di wilayah, membuka jalan ke boss.
3. **Quest Akhir** — setelah boss kalah, serahkan Kristal ke NPC, dengar rangkuman, jawab **2 soal evaluasi** → Data Fragment + Gold, awan wilayah berikutnya hilang.

**Dialog:** kotak teks di bawah layar, potret + nama NPC di kanan (gaya Stardew), efek ketik, tombol E untuk lanjut, pilihan jawaban untuk kuis.

**Save:** autosave di checkpoint, setelah quest selesai, dan setelah boss kalah. **Bonfire** (desa + tiap wilayah): pulihkan HP/Stamina, simpan, opsi **Simpan & Keluar**. Tombol Lanjutkan memuat save terakhir. Simpan ke `user://save.json` (di Web otomatis tersimpan di penyimpanan browser).

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
