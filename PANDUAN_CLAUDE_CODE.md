# Panduan Pengerjaan dengan Claude Code (Terminal)
**Struktura: Legenda Dunia Data** · Kelompok 10

Panduan ini berisi langkah persiapan, cara kerja, dan **prompt siap-tempel untuk setiap tahap**.
Konteks lengkap proyek ada di file **CLAUDE.md** — Claude Code membacanya otomatis, jadi prompt per tahap bisa singkat.

---

## A. Persiapan (sekali saja)

### 1. Yang perlu terpasang
| Program | Keterangan |
|---|---|
| **Godot 4.x** (versi standar, bukan .NET) | Unduh dari godotengine.org. Catat lokasi `Godot_v4.x-stable_win64.exe`. |
| **Export template Web** | Di Godot: Editor → Manage Export Templates → Download. |
| **Git for Windows** (disarankan) | Agar Claude Code bisa memakai Git Bash, dan untuk GitHub. |
| **Claude Code** | Lihat langkah 2. |

### 2. Pasang Claude Code
Buka **PowerShell** (Win + X → Windows PowerShell / Terminal), lalu jalankan:
```powershell
irm https://claude.ai/install.ps1 | iex
```
Kalau terminalnya CMD (tidak ada tulisan `PS` di depan), pakai:
```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```
Tutup terminal, buka lagi, cek dengan `claude --version`. Saat pertama kali menjalankan `claude`, login dengan akun Claude.

### 3. Siapkan folder proyek
Struktur yang diharapkan:
```
C:\TA GAME\
├── Pixel Crawler - Free Pack 2.11\   (aset utama)
├── assets\                           (aset lama: font, musik, SFX, Apple)
├── boss_preview\                     (sprite boss buatan kelompok)
├── player_preview\                   (sprite Raka buatan kelompok)
├── audio_ui\                         (musik, SFX, UI dari Ninja Adventure, CC0)
├── portraits\                        (potret dialog NPC hasil AI, sudah dirapikan)
├── npc\                              (sprite NPC Joko, Arman, Lilbah, Dadang, Tedy)
├── Gambaran_Alur_Game_Struktura.docx
├── PANDUAN_CLAUDE_CODE.md            (file ini)
└── struktura\                        ← folder proyek Godot (dibuat di Tahap 0)
    └── CLAUDE.md                     ← salin CLAUDE.md ke sini
```
1. Buat folder `C:\TA GAME\struktura`.
2. Salin **CLAUDE.md** ke dalam `C:\TA GAME\struktura\`.
3. (Opsional tapi disarankan) agar Claude Code bisa menjalankan Godot dari terminal, tambahkan folder Godot ke PATH, atau ganti nama exe menjadi `godot.exe` dan taruh di folder yang ada di PATH. Cek dengan `godot --version`.

### 4. Hubungkan ke GitHub (repo private)
```powershell
cd "C:\TA GAME\struktura"
git init
git branch -M main
git remote add origin https://github.com/<akun>/struktura.git
```
Undang semua anggota, dosen, dan asisten ke repo (sesuai spesifikasi tugas). Hubungkan board Trello ke repo.

---

## B. Cara kerja sehari-hari

1. Buka PowerShell, lalu:
   ```powershell
   cd "C:\TA GAME\struktura"
   claude
   ```
2. Tempel **prompt tahap** yang sedang dikerjakan (Bagian C).
3. Claude Code akan menjelaskan rencana dan meminta izin sebelum mengubah file/menjalankan perintah. **Baca dulu, baru setujui.**
4. Setelah tahap selesai: buka proyek di Godot, **tekan F5 untuk tes**, cocokkan dengan "Cek selesai" di tiap tahap.
5. Kalau ada error, salin pesan error dari panel Output/Debugger Godot ke Claude Code: *"Ada error ini saat run: …, tolong perbaiki."*
6. Kalau sudah beres, minta commit: *"Commit perubahan tahap ini dengan pesan yang jelas."* Lalu `git push` sendiri.
7. Pindahkan kartu Trello tahap tersebut ke **Done**.

**Tips:**
- Ketik `/clear` sebelum mulai tahap baru agar percakapan bersih (konteks proyek tetap terbaca dari CLAUDE.md).
- `claude -c` untuk melanjutkan percakapan terakhir.
- Tekan **Esc** untuk menghentikan Claude Code kalau arahnya salah, lalu jelaskan koreksinya.
- Satu tahap = satu sesi. Jangan menumpuk banyak tahap dalam satu prompt.
- Kerja paralel 3 orang: tiap anggota memakai **branch sendiri** (`git checkout -b fitur-dialog`), lalu merge ke `main` setelah dites. Hindari dua orang mengubah scene yang sama bersamaan.

---

## C. Prompt per tahap

> Salin isi kotak prompt apa adanya ke Claude Code. Urutan tahap disarankan diikuti karena saling bergantung.
> Kolom **PJ** = penanggung jawab menurut pembagian tugas di dokumen (A1 = combat/musuh/boss, A2 = NPC/dialog/quest/shop, A3 = map/UI/audio/dokumen).

### Tahap 0 — Setup proyek & impor aset (PJ: A3)
```
Baca CLAUDE.md. Kerjakan Tahap 0: setup proyek Godot dan impor aset.

1. Buat project.godot di folder ini (Godot 4.x, renderer Compatibility, nama "Struktura: Legenda Dunia Data"),
   dengan pengaturan display, texture filter, dan Input Map sesuai CLAUDE.md Bagian 3.
2. Buat struktur folder sesuai CLAUDE.md Bagian 4.
3. Salin aset dari folder induk (..\) ke res://assets/ sesuai Bagian 4–5:
   - Player: semua Raka_*-Sheet.png dari ..\player_preview\ ke res://assets/characters/player/ (JANGAN pakai Body_A polos).
   - Pixel Crawler: NPC, musuh Orc Crew & Skeleton Crew,
     senjata, Resources.png, tileset, props, stations, bangunan.
   - Aset lama: Square-Black.ttf, music.ogg, collect_apple.wav, death.wav, jump.wav, Apple.png, Collected.png.
   - Semua file .png dari ..\boss_preview\ ke res://assets/bosses/ (kecuali Perbandingan_Boss.png dan file A_*).
   - Dari ..\audio_ui\: music\*.ogg ke res://assets/audio/music/, sfx\*.wav ke res://assets/audio/sfx/,
     ui\ (dialog, theme, icons, NormalFont.ttf) ke res://assets/ui/.
   - Semua portrait_*.png dari ..\portraits\ ke res://assets/portraits/.
   - Semua *-Sheet.png dari ..\npc\ ke res://assets/characters/npc/ (kecuali Pratinjau_NPC.png). Baca ..\audio_ui\README.md untuk peruntukan tiap file.
   Jangan salin .aseprite, .import, .tres lama, Pink Man, Background, Terrain.
4. Buat .gitignore untuk Godot (abaikan .godot/, export/, *.tmp).
5. Buat README.md singkat (judul, anggota, cara run) dan CREDITS.md (Pixel Crawler oleh Anokolisa, aset lama, dll).
6. Tampilkan ringkasan isi res://assets/ (jumlah file per folder).
```
**Cek selesai:** proyek bisa dibuka di Godot tanpa error; semua aset muncul di FileSystem dan terlihat tajam (tidak blur).

### Tahap 1 — Autoload inti (PJ: A1 + A2)
```
Kerjakan Tahap 1: buat autoload inti sesuai CLAUDE.md Bagian 8.
- GameManager.gd: atribut (HP, HP maks, Stamina, Stamina maks, Gold, XP, Level), inventory (item + jumlah),
  equipment (5 slot), progres chapter (chapter terbuka, quest per chapter, kristal), dengan signal untuk setiap perubahan.
  Fungsi: add_gold, spend_gold, add_item, remove_item, add_xp (naik level otomatis), take_damage, heal, equip.
- SaveManager.gd: simpan/muat ke user://save.json, fungsi has_save(), save_game(), load_game(), new_game().
- AudioManager.gd: bus Master/Music/SFX, play_music(nama) dengan crossfade, play_sfx(nama), volume tersimpan.
- SceneManager.gd: pindah scene dengan transisi fade (CanvasLayer + ColorRect + Tween).
- QuestManager.gd dan DialogManager.gd: kerangka dulu (state + signal), isi detail di tahap berikutnya.
Daftarkan semua di project.godot sebagai autoload. Buat juga res://data/items.json, weapons.json, armors.json,
upgrades.json berisi data awal sesuai CLAUDE.md Bagian 8–9.
```
**Cek selesai:** proyek jalan tanpa error; autoload terlihat di Project Settings → Globals.

### Tahap 2 — Player (PJ: A1)
```
Kerjakan Tahap 2: scene Player (CharacterBody2D) di res://scenes/entities/Player.tscn.
- AnimatedSprite2D memakai sprite Raka_*-Sheet.png (frame 64x64, jumlah frame = lebar/64). Animasi 4 arah:
  idle, walk, run, slice, pierce, crush, hit, death. Arah kiri = Side + flip_h. Pierce atas memakai file Top.
- Gerak 4/8 arah dengan WASD, lari dengan menahan Shift (opsional), dodge (Spasi) dengan i-frame singkat dan memakai Stamina.
- Serang (J/klik kiri): animasi mengikuti jenis senjata yang dipakai (pedang=slice, tombak=pierce, palu=crush),
  Area2D hitbox di depan arah hadap, damage dari GameManager + equipment.
- Hurtbox, knockback, kedip saat terkena, mati → sinyal ke game (layar Kalah).
- Camera2D mengikuti player dengan smoothing dan limit map.
Buat scene tes res://scenes/world/TestArena.tscn berisi lantai rumput sederhana dan player.
```
**Cek selesai:** di TestArena, Raka bisa jalan 4 arah dengan animasi benar, menyerang, dan dodge.

### Tahap 3 — Tileset & Desa Algoria (PJ: A3)
```
Kerjakan Tahap 3: buat TileSet dari Floors_Tiles.png, Wall_Tiles.png, Wall_Variations.png, Water_tiles.png
(tile 16x16) dengan collision untuk dinding/air dan terrain set untuk rumput/tanah/jalan bila memungkinkan.
Lalu buat scene Desa Algoria (res://scenes/world/Village.tscn) memakai TileMapLayer:
area rumput, jalan tanah, beberapa rumah (Walls/Roofs), pohon & tanaman (Vegetation, Trees), Anvil milik Lilbah,
meja Alchemy, Bonfire, papan Peta Dunia di gerbang desa, dan titik posisi NPC (Marker2D) untuk Joko, Lilbah, Arman, Dadang.
Atur urutan gambar (y-sort) agar Raka bisa berjalan di belakang pohon/rumah.
Jelaskan bagian mana yang sebaiknya saya rapikan manual di editor.
```
**Cek selesai:** Raka bisa berjalan di desa, tertahan dinding/air, dan tampil benar di depan/belakang objek.

### Tahap 4 — NPC & sistem dialog (PJ: A2)
```
Kerjakan Tahap 4: NPC dan dialog gaya Stardew (CLAUDE.md Bagian 8, "Dialog").
- Scene NPC.tscn (sprite idle, area interaksi, ikon "!" saat punya quest baru). Tekan E di dekat NPC → dialog.
- DialogBox.tscn: kotak teks di bawah layar, potret + nama di kanan (pakai res://assets/portraits/portrait_<nama>_80.png,
  kotak dialog dari res://assets/ui/dialog/), efek ketik, E untuk lanjut, mendukung pilihan jawaban.
- Dialog dibaca dari res://data/dialogs/<npc>.json. Buat dialog untuk Joko (prolog + tutorial kontrol)
  dan Arman (cerita Chapter 1). Player tidak bisa bergerak saat dialog.
Sprite NPC sesuai tabel tokoh di CLAUDE.md Bagian 6. Pasang NPC Joko dan Arman di Village.
```
**Cek selesai:** bicara dengan Joko dan Arman menampilkan dialog dengan nama dan potret placeholder.

### Tahap 5 — Kuis & sistem quest 3 tahap (PJ: A2)
```
Kerjakan Tahap 5: QuizPanel dan QuestManager lengkap (CLAUDE.md Bagian 8 "Quest" dan Bagian 9).
- res://data/quiz.json: 3 soal Quest Awal dan 2 soal Quest Akhir untuk setiap chapter (pakai contoh di Bagian 9,
  lengkapi sisanya dengan soal yang sesuai materi), plus prolog Joko. Setiap soal punya petunjuk.
- QuizPanel: pilihan ganda, salah → tampilkan petunjuk lalu ulang, benar semua → hadiah;
  benar semua di percobaan pertama → bonus Gold & XP.
- res://data/quests.json + QuestManager: Quest Awal → Quest Tengah → Quest Akhir per chapter, status tersimpan.
- QuestLog.tscn (tombol Q): daftar quest aktif, tujuan, progres.
Sambungkan ke dialog Joko (prolog) dan Arman (Quest Awal Chapter 1).
```
**Cek selesai:** prolog Joko memberi Pedang Kayu + 2 Potion; kuis Arman berjalan; Quest Log menampilkan quest.

### Tahap 6 — HUD, inventory, collectible (PJ: A3 + A2)
```
Kerjakan Tahap 6:
- HUD.tscn: bar HP, bar Stamina, Gold, Level/XP, chapter aktif. Update lewat signal GameManager. Font Square-Black.
- Collectible.tscn (base) + turunan: Gold Coin, Ore, Herb (sprite Apple), Data Fragment, Potion; ambil otomatis
  saat disentuh, efek Collected.png, SFX collect_apple.wav.
- Chest.tscn (peti berisi item acak sesuai tabel).
- Inventory.tscn (tombol I): grid item + 5 slot equipment, bisa equip dan memakai potion.
```
**Cek selesai:** item yang diambil masuk inventory, HUD berubah, equip mengubah damage/pertahanan.

### Tahap 7 — Musuh biasa (PJ: A1)
```
Kerjakan Tahap 7: Enemy.tscn (base) memakai sprite Orc/Skeleton (Idle, Run 32x32; Death ukuran frame sesuai file).
- State: idle/patroli → kejar saat player dalam jarak → serang (menerjang + hitbox, tanda kedip sebelum menyerang)
  → kena hit (kedip putih, knockback) → mati (animasi Death, drop Gold/Ore/Herb, beri XP).
- Data per jenis (HP, damage, kecepatan, drop) di res://data/enemies.json.
- Buat 4 varian awal: Skeleton Base, Skeleton Rogue, Orc, Orc Rogue. Taruh beberapa di TestArena.
```
**Cek selesai:** musuh mengejar, menyerang, bisa dikalahkan, dan menjatuhkan item.

### Tahap 8 — Boss (PJ: A1)
```
Kerjakan Tahap 8: Boss.tscn (base) + 5 boss sesuai CLAUDE.md Bagian 10, sprite di res://assets/bosses/.
- Animasi idle, attack/cast, hit (HitFlash), death dengan ukuran frame dan "titik kaki" sesuai tabel Bagian 10
  agar posisi tidak loncat saat ganti animasi.
- Bar HP boss di atas layar dengan nama boss.
- Pola serangan per boss sesuai tabel (dengan tanda peringatan merah di lantai sebelum serangan besar):
  Golem Batu (hantaman + gelombang kejut, titik lemah urutan indeks), Penyihir Menara (3 bola ditumpuk, LIFO),
  Kapten Bajak Laut (terjang jauh + panggil anak buah FIFO), Ksatria Rantai (bola berantai + kristal rantai),
  King Subiyan (bola sihir + bayangan bercabang).
- Hitbox mengikuti frame animasi. Proyektil memakai *_Projectile-Sheet.png.
- Setelah animasi mati selesai: spawn item Kristal Struktur, autosave.
Mulai dari Golem Batu dulu, tes, lalu lanjut ke boss lain satu per satu.
```
**Cek selesai:** tiap boss bisa dilawan di arena tes; tidak ada sprite yang "loncat" saat ganti animasi.

### Tahap 9 — Puzzle materi (Quest Tengah) (PJ: A2)
```
Kerjakan Tahap 9: 5 puzzle materi di res://scenes/puzzles/ sesuai CLAUDE.md Bagian 9 (kolom Quest Tengah):
ArrayShelf (rak benih berindeks mulai 0 + obor berurutan), StackCrates (tumpukan peti, push/pop),
QueueCustomers (layani pelanggan sesuai urutan datang), LinkedPortals (portal dengan penunjuk next,
sisip node hilang, buang node jebakan), TreeMaze (labirin bercabang ala BST).
Setiap puzzle menampilkan visual struktur datanya (misal label indeks di atas rak, tumpukan terlihat),
memberi pesan saat salah, dan mengirim sinyal selesai ke QuestManager. Buat juga scene tes untuk tiap puzzle.
```
**Cek selesai:** kelima puzzle bisa diselesaikan dan menandai Quest Tengah selesai.

### Tahap 10 — Peta 5 wilayah (PJ: A3)
```
Kerjakan Tahap 10: buat 5 scene wilayah (Ch1_HutanIndeks … Ch5_PohonDunia) dengan TileSet yang sudah ada.
Tiap wilayah: titik masuk, Bonfire, checkpoint, musuh sesuai tingkat kesulitan, puzzle Quest Tengah,
gerbang ke arena boss (terbuka setelah Quest Tengah), dan Marker NPC chapter (Arman, Lilbah, Dadang, Megas, Tedy).
Ukuran dan isi disesuaikan target durasi: Ch1 ±8 menit … Ch5 maks 15 menit (CLAUDE.md Bagian 8).
Kerjakan satu wilayah per sesi, mulai dari Ch1.
```
**Cek selesai:** Chapter 1 bisa dimainkan dari masuk sampai boss kalah.

### Tahap 11 — Layar menu, Peta Dunia, save (PJ: A3)
```
Kerjakan Tahap 11: StartScreen (Mulai, Lanjutkan—aktif bila ada save, Pengaturan, About, Keluar),
WorldMap (gambar peta dengan Desa + 5 wilayah, awan + gembok di wilayah terkunci, animasi awan menghilang
saat wilayah terbuka, buka dengan tombol M atau papan di desa), Settings (volume musik & SFX),
About (nama + foto 3 anggota + dosen: pakai placeholder dulu, plus credit aset),
PauseMenu, WinScreen (rangkuman materi + hadiah), LoseScreen (Coba Lagi dari checkpoint / Menu).
Hubungkan autosave (checkpoint, quest selesai, boss kalah) dan Bonfire (pulihkan HP/Stamina, simpan, Simpan & Keluar).
```
**Cek selesai:** alur Start → Peta Dunia → wilayah → Menang/Kalah → kembali berjalan; Lanjutkan memuat progres.

### Tahap 12 — Shop, Anvil, ramuan (PJ: A2)
```
Kerjakan Tahap 12: Shop (beli senjata/armor/potion), AnvilUpgrade milik Lilbah (stat sebelum/sesudah, biaya,
batas level per chapter, animasi + SFX tempa), meja ramuan (3 Herb → Potion), dan skill spesial dari
Data Fragment (serangan putar / dash). Data dari JSON. Sesuaikan dengan CLAUDE.md Bagian 8.
```
**Cek selesai:** Gold/Ore berkurang dengan benar, item naik level, batas upgrade per chapter berlaku.

### Tahap 13 — Audio (PJ: A3)
```
Kerjakan Tahap 13: pasang musik dan SFX memakai AudioManager sesuai res://assets/audio/ (daftar peruntukan
ada di ..\audio_ui\README.md): musik per lokasi (menu, prolog, desa, peta dunia, ch1–ch5, boss, boss final,
menang, kalah, kredit) dengan crossfade, dan SFX (tebas, kena hit, dodge, hantam tanah, sihir, ambil koin/item,
heal, menu, kuis benar/salah, peringatan boss, bunyi ketik dialog, tempa anvil, jingle naik level/quest selesai/
wilayah terbuka/game over). Tambahkan juga SFX lama: collect_apple.wav (ambil Herb), death.wav (Raka mati).
Pastikan audio baru diputar setelah interaksi pertama (aturan browser). Tambahkan credit Ninja Adventure di About.
```

### Tahap 14 — Export Web & uji (PJ: semua)
```
Kerjakan Tahap 14:
1. Buat export_presets.cfg untuk Web, output ke export/web/index.html. Jika Godot CLI tersedia,
   jalankan export headless dan laporkan hasilnya.
2. Buat docs/Functional_Test.md: tabel ID, fitur, langkah uji, hasil yang diharapkan, hasil aktual, status,
   mencakup semua fitur wajib di CLAUDE.md Bagian 11.
3. Buat docs/Alpha_Test.md: kuesioner Likert 1–5 (kontrol, kesulitan, audio, UI, kesenangan, nilai edukasi)
   + pertanyaan terbuka.
4. Periksa performa: hindari node/partikel berlebih, pakai CPUParticles2D untuk Web.
```
**Cek selesai:** folder `export/web` bisa dijalankan di browser lewat server lokal (misal `python -m http.server` di folder itu, buka `localhost:8000`).

---

## D. Jika ada masalah
| Masalah | Yang dilakukan |
|---|---|
| Sprite blur | Minta: "Pastikan default texture filter Nearest dan import pixel art tanpa filter." |
| Animasi loncat posisi | Minta pakai "titik kaki" di CLAUDE.md Bagian 10 untuk offset tiap animasi. |
| Scene rusak setelah diedit Claude Code | Buka di editor, simpan ulang; atau `git checkout -- <file>` untuk kembali ke versi terakhir. |
| Claude Code mengerjakan terlalu banyak | Tekan Esc, ingatkan: "Kerjakan hanya Tahap X." |
| Lupa konteks setelah `/clear` | Normal; CLAUDE.md tetap dibaca. Sebutkan tahap yang sedang dikerjakan. |
| Web export tidak jalan dibuka langsung (file://) | Harus lewat server lokal / webhost lab, bukan klik ganda index.html. |

## E. Keputusan yang masih terbuka
- Pembagian tugas final 3 anggota.
- Foto anggota dan dosen untuk layar About.

Sumber instalasi Claude Code: https://code.claude.com/docs/en/setup
