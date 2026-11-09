# Functional Test — Struktura: Legenda Dunia Data

Kelompok 10 · Workshop PPLG (GameProg)

**Cara pakai:** jalankan game (Godot F5 atau build Web), kerjakan tiap langkah uji, lalu isi kolom **Hasil aktual** dan **Status**
(`Lulus` / `Gagal` / `Sebagian`). Kolom **Catatan** diisi bila gagal (sertakan pesan error dari panel Output).
Semua baris dimulai dengan status **Belum diuji**. Baris bertanda ⚙ sudah diperiksa otomatis (Godot headless) saat pengembangan,
tetapi tetap perlu diuji manual di game yang berjalan.

Penguji: ____________________  Tanggal: ____________  Versi/commit: ____________  Platform: ☐ Editor ☐ Web (browser: ________)

## A. Spesifikasi tugas wajib (CLAUDE.md Bagian 11)

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| SP-01 | Minimal 3 atribut | Main sebentar; lihat HUD (pojok layar) | HP, Stamina, Gold, XP/Level tampil dan berubah sesuai aksi | | Belum diuji |
| SP-02 | Minimal 3 collectible yang dikonversi | Ambil Gold, Ore, Herb, Data Fragment; gunakan di Toko/Tempa/Racik/Skill | Tiap collectible bisa dipakai: Gold → beli, Ore+Gold → tempa, 3 Herb → Potion, Data Fragment → skill/tempa +3 | | Belum diuji |
| SP-03 | In-game economy | Kalahkan musuh, buka peti, beli di Toko, jual di tab Jual | Gold bertambah dari musuh/peti dan berkurang saat belanja/tempa; harga jual lebih rendah dari harga beli | | Belum diuji |
| SP-04 | Audio & musik latar | Pindah antar layar/wilayah, serang, kena hit, ambil item | Musik berganti per lokasi (crossfade), SFX berbunyi sesuai aksi | | Belum diuji |
| SP-05 | Aset berlisensi free/AI | Buka layar About; baca `CREDITS.md` | Sumber aset dan lisensi tercantum (Pixel Crawler, Ninja Adventure CC0, potret AI) | | Belum diuji |
| SP-06 | Minimal 3 level + cerita terkait materi | Mainkan Ch1–Ch3 | Tiap chapter punya NPC, cerita, kuis, puzzle, boss yang sesuai materi (Array, Stack, Queue) | | Belum diuji |
| SP-07 | Start Screen | Jalankan game | Muncul Mulai, Lanjutkan, Peta Dunia, Pengaturan, About, Keluar | | Belum diuji |
| SP-08 | Level Select (Peta Dunia) | Tekan M di game / tombol Peta Dunia di menu | Peta tampil; wilayah terkunci berawan + gembok | | Belum diuji |
| SP-09 | Game session | Mulai game baru | Raka muncul di Desa Algoria dan bisa dikendalikan | | Belum diuji |
| SP-10 | End session Menang | Selesaikan Quest Akhir chapter mana pun | Layar Menang: rangkuman materi + hadiah | | Belum diuji |
| SP-11 | End session Kalah | Biarkan HP Raka habis | Layar Kalah: Coba Lagi (dari checkpoint) dan Menu Utama | | Belum diuji |
| SP-12 | About | Buka About dari Start Screen | Nama + foto 3 anggota dan dosen (placeholder boleh), credit aset | | Belum diuji |
| SP-13 | Output Web | Export ke Web, jalankan lewat server lokal | Game berjalan di browser tanpa error fatal | | Belum diuji |

## B. Kontrol & pemain

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| PL-01 ⚙ | Gerak | Tekan W/A/S/D dan panah | Raka bergerak 4 arah, animasi walk sesuai arah, kiri = flip sprite | | Belum diuji |
| PL-02 | Lari | Tahan Shift sambil bergerak | Kecepatan naik, animasi run | | Belum diuji |
| PL-03 | Serang | Tekan J / klik kiri | Animasi tebas, musuh di depan terkena damage, SFX berbunyi | | Belum diuji |
| PL-04 | Dodge | Tekan Spasi | Raka melesat pendek, kebal sesaat, stamina berkurang 20 | | Belum diuji |
| PL-05 | Stamina regen | Habiskan stamina lalu diam | Stamina pulih perlahan setelah jeda ±1 detik | | Belum diuji |
| PL-06 | Level up | Kalahkan musuh sampai XP penuh | Level naik, HP & Stamina maks naik, HP terisi penuh, jingle naik level | | Belum diuji |
| PL-07 | Interaksi | Dekati NPC/papan/Bonfire, tekan E | Dialog/aksi muncul; petunjuk "E: …" tampil saat dekat | | Belum diuji |
| PL-08 | Tombol menu | Tekan I, Q, M, Tab, Esc | Tas, Catatan Misi, Peta Dunia, Kantong Pedagang, Menu Jeda terbuka; Esc/tombol sama menutup; hanya satu terbuka | | Belum diuji |

## C. Dialog, kuis, quest

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| DQ-01 | Dialog | Bicara dengan Joko | Kotak dialog di bawah, potret + nama, efek ketik + bunyi ketik; E mempercepat/lanjut | | Belum diuji |
| DQ-02 | Kuis benar/salah | Jawab soal Quest Awal: salah dulu lalu benar | Salah → petunjuk singkat, jawab ulang tanpa game over; benar → lanjut | | Belum diuji |
| DQ-03 | Bonus percobaan pertama | Jawab semua soal benar di percobaan pertama | Bonus Gold & XP muncul di hadiah | | Belum diuji |
| DQ-04 | Quest 3 tahap (Ch1) | Selesaikan Awal → Tengah (puzzle) → boss → Akhir | Tiap tahap tercatat di Catatan Misi; Quest Akhir butuh Kristal; wilayah berikutnya terbuka | | Belum diuji |
| DQ-05 | Ikon quest NPC | Lihat NPC pemberi quest | "!" untuk quest baru, "?" untuk siap diserahkan | | Belum diuji |
| DQ-06 | Pelacak tujuan & panah | Aktifkan quest, lihat HUD | Tujuan tampil di pojok kiri atas; panah penunjuk di tepi layar bila target di luar layar | | Belum diuji |
| DQ-07 | Prolog Joko | Mulai game baru, bicara dengan Joko | Pedang Kayu + 2 Potion diterima; gerbang ke Hutan Indeks terbuka | | Belum diuji |

## D. Pertempuran

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| CB-01 | Musuh biasa | Dekati musuh di Hutan Indeks | Musuh mengejar, menyerang, bisa dikalahkan; drop loot (Gold/Ore/Herb) | | Belum diuji |
| CB-02 | Boss Golem Batu (Ch1) | Masuk arena lewat gerbang boss | Peringatan merah sebelum serang besar; titik lemah dipukul sesuai urutan indeks; Kristal muncul saat kalah | | Belum diuji |
| CB-03 | Boss Ch2–Ch5 | Kalahkan Penyihir Menara, Kapten Bajak Laut, Ksatria Rantai, King Subiyan | Pola serangan sesuai materi (LIFO, FIFO, node berantai, tree bayangan) | | Belum diuji |
| CB-04 | Skill spesial | Buka skill di tab Skill, tekan K dan L | Serangan Putar melukai musuh sekitar; Dash menerjang dan kebal; stamina berkurang; ada jeda | | Belum diuji |
| CB-05 | Checkpoint & respawn | Aktifkan Checkpoint/Bonfire, mati, pilih Coba Lagi | Raka hidup lagi di titik terakhir dengan HP penuh | | Belum diuji |

## E. Puzzle materi (Quest Tengah)

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| PZ-01 | Array (Ch1) | Taruh benih di rak sesuai indeks mulai 0; nyalakan obor berurutan | Puzzle selesai, Quest Tengah tercatat, gerbang boss terbuka | | Belum diuji |
| PZ-02 | Stack (Ch2) | Ambil peti dari atas tumpukan (pop) sampai pedang di dasar | Urutan salah ditolak; selesai membuka gerbang boss | | Belum diuji |
| PZ-03 | Queue (Ch3) | Layani pelanggan sesuai urutan datang | Urutan benar (FIFO) menyelesaikan puzzle | | Belum diuji |
| PZ-04 | Linked List (Ch4) | Sambung portal (next), sisipkan node hilang, buang node jebakan | Rantai benar menyelesaikan puzzle | | Belum diuji |
| PZ-05 | Tree (Ch5) | Lewati labirin ala BST (kecil kiri, besar kanan) | Jalur benar menyelesaikan puzzle | | Belum diuji |

## F. Dunia & navigasi

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| WD-01 ⚙ | Scene wilayah dimuat | Pindah Desa → Ch1 → … → Ch5 lewat papan/gerbang | Semua wilayah termuat tanpa error; bentuk area organik (tidak persegi), tepi ditutup air/tebing | | Belum diuji |
| WD-02 | Gerbang terkunci | Dekati papan ke wilayah berikutnya sebelum Quest Akhir | Pesan "Terkunci: …"; tidak pindah | | Belum diuji |
| WD-03 | Peta Dunia: awan & gembok | Buka peta dengan M di awal game | Hanya Desa & Hutan Indeks terbuka (Hutan setelah prolog); lainnya berawan + gembok | | Belum diuji |
| WD-04 | Peta Dunia: animasi buka | Selesaikan Quest Akhir lalu buka peta | Awan wilayah baru menghilang dengan animasi; jingle wilayah terbuka | | Belum diuji |
| WD-05 | Peta Dunia: geser/zoom/klik | Seret, putar roda mouse, klik wilayah terbuka | Peta bergeser dan zoom; klik memindahkan ke wilayah | | Belum diuji |
| WD-06 | Kartu judul wilayah | Masuk wilayah baru | Kartu singkat nama wilayah + materi (bila sudah dibuat) | | Belum diuji |
| WD-07 | Bonfire | Tekan E di Bonfire | Pilihan Istirahat / Simpan & Keluar / Batal; Istirahat memulihkan HP & Stamina dan menyimpan | | Belum diuji |

## G. Ekonomi: Toko, Tempa, Racik

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| EC-01 ⚙ | Beli di Toko | Tab Toko → pilih Potion → Beli | Gold berkurang sesuai harga, Potion bertambah; tombol nonaktif bila Gold kurang | | Belum diuji |
| EC-02 ⚙ | Jual | Tab Jual → jual 1 Herb/Ore | Gold bertambah sesuai harga jual; jumlah item berkurang | | Belum diuji |
| EC-03 ⚙ | Racik | Punya 3 Herb → tab Racik → Racik | 3 Herb berkurang, 1 Potion bertambah | | Belum diuji |
| EC-04 ⚙ | Tempa +1/+2/+3 | Tab Tempa → Tempa Pedang Kayu berulang | Gold/Ore/Fragment berkurang sesuai tabel (+1: 50G+3 Ore; +2: 120G+6 Ore; +3: 250G+10 Ore+1 Fragment); damage naik 20%/40%/70%; animasi + SFX tempa | | Belum diuji |
| EC-05 | Batas tempa per chapter | Di Chapter 1 coba tempa ke +2 | Ditolak dengan pesan batas chapter (Ch1 maks +1, Ch2 maks +2, Ch3+ maks +3) | | Belum diuji |
| EC-06 | Dikunci saat bertarung | Tekan Tab dekat musuh | Pesan "Tidak bisa saat bertarung!"; menu tidak terbuka | | Belum diuji |
| EC-07 | Tas & perlengkapan | Tekan I; pasang/lepas senjata, helm, armor | Slot terisi/kosong; stat (damage/pertahanan/HP maks) berubah | | Belum diuji |
| EC-08 | Potion | Pakai Potion dari Tas saat HP kurang | HP bertambah, Potion berkurang, SFX heal | | Belum diuji |

## H. Menu, pengaturan, simpan

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| MN-01 | Mulai game baru | Start Screen → Mulai | Masuk Desa Algoria dengan state baru; bila ada save, muncul konfirmasi | | Belum diuji |
| MN-02 | Lanjutkan | Simpan (Bonfire), tutup, buka lagi → Lanjutkan | Progres (Gold, item, quest, posisi/checkpoint) kembali; tombol nonaktif bila tak ada save | | Belum diuji |
| MN-03 | Menu Jeda | Tekan Esc saat bermain | Game berhenti; Lanjutkan, Peta Dunia, Kantong Pedagang, Pengaturan, Simpan, Simpan & ke Menu bekerja | | Belum diuji |
| MN-04 | Simpan dibatasi | Buka Menu Jeda dekat musuh | Tombol Simpan nonaktif + pesan | | Belum diuji |
| MN-05 | Pengaturan volume | Geser slider Musik/SFX | Volume berubah langsung; nilai tersimpan setelah game dibuka ulang | | Belum diuji |
| MN-06 | Autosave | Selesaikan quest / sentuh Checkpoint / kalahkan boss | Game tersimpan otomatis (cek dengan Lanjutkan) | | Belum diuji |
| MN-07 | Keluar | Klik Keluar di Start Screen (desktop) | Game tertutup; tombol tidak muncul di versi Web | | Belum diuji |

## I. Audio

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| AU-01 ⚙ | Musik per lokasi | Menu → Desa → Peta → Ch1 → boss → Menang/Kalah | Musik berganti dengan crossfade sesuai daftar `audio_ui/README.md` | | Belum diuji |
| AU-02 | Musik prolog & kredit | Bicara dengan Joko; buka About | Musik prolog saat dialog Joko lalu kembali ke musik desa; musik kredit di About lalu kembali | | Belum diuji |
| AU-03 | SFX | Serang, kena hit, dodge, ambil item/koin/herb, kuis benar/salah, dialog | Semua berbunyi; bunyi ketik tiap beberapa huruf | | Belum diuji |
| AU-04 | Audio di browser | Buka build Web, klik sekali | Musik menu berbunyi setelah interaksi pertama | | Belum diuji |

## J. Web & performa

| ID | Fitur | Langkah uji | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| WB-01 | Build Web berjalan | Export, `python -m http.server` di `export/web`, buka `localhost:8000` | Game termuat sampai Start Screen; tanpa error di Console browser | | Belum diuji |
| WB-02 | Simpan di browser | Simpan, muat ulang halaman, Lanjutkan | Progres kembali (penyimpanan browser) | | Belum diuji |
| WB-03 | FPS wilayah padat | Jalan di Ch1 dan Ch5 (±2300–2800 node) | Stabil ≥ 30 FPS di laptop kelas menengah | | Belum diuji |
| WB-04 | Waktu muat | Ukur dari buka halaman sampai Start Screen | ≤ 20 detik di koneksi lab | | Belum diuji |
| WB-05 | Pixel art tajam | Lihat sprite/tile di jendela diperbesar | Tidak blur (filter Nearest), tidak ada garis celah antar-tile | | Belum diuji |
| WB-06 | Kontrol mouse & keyboard | Seret peta, klik tombol, tekan semua tombol di Bagian B | Respons normal di browser (fokus kanvas aktif) | | Belum diuji |

## Ringkasan hasil

| Bagian | Jumlah uji | Lulus | Gagal | Sebagian |
|---|---|---|---|---|
| A. Spesifikasi tugas | 13 | | | |
| B. Kontrol & pemain | 8 | | | |
| C. Dialog, kuis, quest | 7 | | | |
| D. Pertempuran | 5 | | | |
| E. Puzzle materi | 5 | | | |
| F. Dunia & navigasi | 7 | | | |
| G. Ekonomi | 8 | | | |
| H. Menu & simpan | 7 | | | |
| I. Audio | 4 | | | |
| J. Web & performa | 6 | | | |
| **Total** | **70** | | | |
