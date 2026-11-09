class_name ArrayShelf
extends PuzzleBase
## Puzzle Chapter 1 – Array. Dua fase:
## 1) Taruh 5 benih di rak sesuai pesanan "rak ke-N dari kiri" (rak berindeks mulai 0, jadi rak ke-N = indeks N-1).
## 2) Nyalakan 5 obor berurutan dari indeks 0 sampai 4 (obor ditata acak, harus dicari berdasarkan indeks).

const SEED_NAMES: Array[String] = ["Wortel", "Bayam", "Jagung", "Tomat", "Padi"]
const SEED_COLORS: Array[Color] = [
	Color(0.95, 0.55, 0.2), Color(0.35, 0.7, 0.3), Color(0.95, 0.85, 0.3), Color(0.85, 0.25, 0.25), Color(0.8, 0.75, 0.55)]
const SLOT_COUNT := 5

var phase: int = 0                       # 0 = benih, 1 = obor
var seed_pos: Array[int] = []            # posisi (mulai 1) tiap benih
var slot_buttons: Array[Button] = []
var seed_buttons: Array[Button] = []
var torch_buttons: Dictionary = {}       # indeks array -> Button
var selected_seed: int = -1
var placed: int = 0
var next_torch: int = 0


func _init() -> void:
	puzzle_title = "Susun Rak Benih"
	instruction = "Rak ini adalah ARRAY. Taruh tiap benih di rak sesuai pesanan, lalu nyalakan obor berurutan dari indeks 0."


func _reset() -> void:
	phase = 0
	placed = 0
	next_torch = 0
	selected_seed = -1
	# Posisi 1..5 diacak dan dibagikan ke 5 benih.
	var order: Array[int] = [1, 2, 3, 4, 5]
	order.shuffle()
	seed_pos = order
	_build_seed_phase()
	report_progress(0, 10)


# ---------------------------------------------------------------- Fase 1: benih

func _build_seed_phase() -> void:
	clear_content()
	slot_buttons.clear()
	seed_buttons.clear()
	# Daftar pesanan di kiri
	var orders: Label = make_label("Pesanan:", 12, Color(0.55, 0.33, 0.2))
	orders.position = Vector2(4, 0)
	content.add_child(orders)
	for i in SEED_NAMES.size():
		var line: Label = make_label("%s  ->  rak ke-%d" % [SEED_NAMES[i], seed_pos[i]], 11, INK)
		line.position = Vector2(4, 20 + i * 18)
		content.add_child(line)
	# Rak (array) di kanan
	for i in SLOT_COUNT:
		var slot: Button = make_button("", Vector2(70, 56), Color(0.6, 0.45, 0.3))
		slot.position = Vector2(200 + i * 76, 20)
		slot.pressed.connect(_on_slot_pressed.bind(i))
		content.add_child(slot)
		slot_buttons.append(slot)
		var idx: Label = make_label("[%d]" % i, 12, INK)
		idx.position = Vector2(222 + i * 76, 80)
		content.add_child(idx)
	var ends: Label = make_label("kiri", 10, Color(0.45, 0.35, 0.3))
	ends.position = Vector2(200, 100)
	content.add_child(ends)
	# Palet benih
	var palette: Label = make_label("Pilih benih, lalu klik rak:", 11, INK)
	palette.position = Vector2(200, 124)
	content.add_child(palette)
	for i in SEED_NAMES.size():
		var b: Button = make_button(SEED_NAMES[i], Vector2(70, 34), SEED_COLORS[i])
		b.position = Vector2(200 + i * 76, 146)
		b.pressed.connect(_on_seed_pressed.bind(i))
		content.add_child(b)
		seed_buttons.append(b)


func _on_seed_pressed(seed_index: int) -> void:
	selected_seed = seed_index
	for i in seed_buttons.size():
		seed_buttons[i].modulate = Color(1, 1, 1) if i == seed_index else Color(0.8, 0.8, 0.8)
	show_message("Benih %s dipilih. Klik rak tujuannya." % SEED_NAMES[seed_index], true)


func _on_slot_pressed(slot_index: int) -> void:
	if selected_seed < 0:
		show_message("Pilih benih dulu.")
		return
	if not slot_buttons[slot_index].text.is_empty():
		show_message("Rak itu sudah terisi.")
		return
	if slot_index != seed_pos[selected_seed] - 1:
		show_message("Belum tepat. Ingat: indeks array mulai dari 0, jadi rak ke-1 berindeks 0, rak ke-2 berindeks 1, dan seterusnya.")
		return
	slot_buttons[slot_index].text = SEED_NAMES[selected_seed]
	recolor_button(slot_buttons[slot_index], SEED_COLORS[selected_seed])
	seed_buttons[selected_seed].visible = false
	seed_buttons[selected_seed].disabled = true
	selected_seed = -1
	placed += 1
	report_progress(placed, 10)
	show_message("Pas! Rak ke-%d berindeks %d." % [slot_index + 1, slot_index], true)
	if placed == SLOT_COUNT:
		_start_torch_phase()


# ---------------------------------------------------------------- Fase 2: obor

func _start_torch_phase() -> void:
	phase = 1
	next_torch = 0
	clear_content()
	torch_buttons.clear()
	var title: Label = make_label("Nyalakan obor dari indeks 0 sampai 4, berurutan!", 12, Color(0.55, 0.33, 0.2))
	title.position = Vector2(4, 4)
	content.add_child(title)
	var order: Array[int] = [0, 1, 2, 3, 4]
	order.shuffle()   # posisi di layar diacak, jadi harus dicari lewat indeksnya
	for i in order.size():
		var idx: int = order[i]
		var b: Button = make_button("Obor\n[%d]" % idx, Vector2(86, 80), Color(0.5, 0.42, 0.38))
		b.position = Vector2(20 + i * 108, 50)
		b.pressed.connect(_on_torch_pressed.bind(idx))
		content.add_child(b)
		torch_buttons[idx] = b
	show_message("Fase 2: urutan menyalakan obor menurut indeks.", true)


func _on_torch_pressed(idx: int) -> void:
	if idx != next_torch:
		for b: Button in torch_buttons.values():
			recolor_button(b, Color(0.5, 0.42, 0.38))
			b.text = b.text.replace("NYALA\n", "Obor\n")
		next_torch = 0
		report_progress(SLOT_COUNT, 10)
		show_message("Salah urutan! Obor padam. Mulai lagi dari indeks 0.")
		return
	var button: Button = torch_buttons[idx]
	recolor_button(button, Color(1.0, 0.7, 0.2))
	button.text = "NYALA\n[%d]" % idx
	next_torch += 1
	report_progress(SLOT_COUNT + next_torch, 10)
	show_message("Obor [%d] menyala." % idx, true)
	if next_torch == SLOT_COUNT:
		complete_puzzle()
