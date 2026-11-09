# Struktura: Legenda Dunia Data

Game top-down pixel RPG edukasi struktur data (Array, Stack, Queue, Linked List, Tree).
Proyek akhir mata kuliah GameProg (Workshop PPLG) — **Kelompok 10**.

- Engine: Godot 4.x (GDScript), renderer Compatibility
- Target: Web (HTML5)
- Kontrol: keyboard dan mouse (WASD/panah, J/klik kiri = serang, Spasi = dodge, E = interaksi,
  I = inventory, Q = quest log, M = peta dunia, Esc = pause)

## Anggota
| Nama | Tugas |
|---|---|
| (isi nama anggota 1) | Combat, musuh, boss |
| (isi nama anggota 2) | NPC, dialog, quest, shop |
| (isi nama anggota 3) | Map, UI, audio, dokumen |

Dosen pengampu: (isi nama dosen)

## Cara menjalankan
1. Pasang Godot 4.x (versi standar, bukan .NET).
2. Buka Godot → Import → pilih file `project.godot` di folder ini.
3. Tekan **F5** untuk menjalankan.

## Export Web
Lihat tahap 14 pada `PANDUAN_CLAUDE_CODE.md`. Hasil export harus dibuka lewat server lokal
(misal `python -m http.server` di folder `export/web`), bukan klik ganda `index.html`.

## Struktur singkat
- `assets/` — sprite, audio, UI, font
- `data/` — data game dalam JSON (item, quest, kuis, dialog)
- `scenes/` — scene Godot (ui, world, entities, puzzles)
- `scripts/` — script GDScript (autoload dan per scene)

Aset dan lisensi: lihat [CREDITS.md](CREDITS.md).
