class_name StackTower
extends PuzzleBase
## Puzzle Dusun Cadas (Chapter 2, langkah Quest Tengah) – Stack (LIFO). Tugu batu dusun disusun ulang oleh perampok
## dengan urutan salah. Batu hanya bisa diambil dari PUNCAK (POP ke tanah) dan ditaruh di PUNCAK (PUSH dari tanah).
## Untuk membetulkan batu yang salah di tengah, semua batu di atasnya harus di-POP dulu. Selesai bila tugu = pola ukiran.

const TARGET: Array[String] = ["Alas", "Sungai", "Ngarai", "Tambang", "Mahkota"]   # dasar -> puncak
const STONE_SIZE := Vector2(120, 28)
const STONE_COLOR := Color(0.72, 0.66, 0.58)
const OK_COLOR := Color(0.6, 0.78, 0.55)

var tower: Array[String] = []           # indeks 0 = dasar, terakhir = puncak
var ground: Array[String] = []          # batu yang tergeletak di tanah (bisa di-PUSH)
var moves: int = 0
var _tower_box: Control
var _ground_box: Control
var _pattern_box: Control
var _pop_button: Button
var _info: Label


func _init() -> void:
	puzzle_title = "Tugu Batu Dusun Cadas"
	instruction = "Tugu ini adalah STACK: batu hanya bisa diambil (POP) dan ditaruh (PUSH) di PUNCAK. Susun tugu sesuai pola ukiran di kiri. Batu yang salah di tengah? POP dulu semua batu di atasnya."


func _build_content() -> void:
	var cap: Label = make_label("Pola ukiran", 11, INK)
	cap.position = Vector2(0, 0)
	content.add_child(cap)
	_pattern_box = Control.new()
	_pattern_box.position = Vector2(0, 0)
	content.add_child(_pattern_box)
	var cap2: Label = make_label("Tugu", 11, INK)
	cap2.position = Vector2(150, 0)
	content.add_child(cap2)
	_tower_box = Control.new()
	_tower_box.position = Vector2(150, 0)
	content.add_child(_tower_box)
	_pop_button = make_button("POP (ambil puncak)", Vector2(150, 30), Color(0.85, 0.55, 0.35))
	_pop_button.position = Vector2(330, 4)
	_pop_button.pressed.connect(_pop_top)
	content.add_child(_pop_button)
	var cap3: Label = make_label("Batu di tanah (klik = PUSH ke puncak):", 11, INK)
	cap3.position = Vector2(330, 44)
	content.add_child(cap3)
	_ground_box = Control.new()
	_ground_box.position = Vector2(330, 62)
	content.add_child(_ground_box)
	_info = make_label("", 11, INK)
	_info.position = Vector2(330, 170)
	content.add_child(_info)


func _reset() -> void:
	# dasar 1-2 batu sudah benar; di atasnya batu yang tertukar; sisanya tergeletak di tanah
	var base_ok: int = randi_range(1, 2)
	var rest: Array[String] = TARGET.slice(base_ok)
	rest.shuffle()
	while rest[0] == TARGET[base_ok]:
		rest.shuffle()
	tower = TARGET.slice(0, base_ok)
	tower.append_array(rest.slice(0, 2))
	ground = rest.slice(2)
	moves = 0
	_refresh()


## Banyak batu dari dasar yang sudah sesuai pola.
func _correct_prefix() -> int:
	var n: int = 0
	while n < tower.size() and n < TARGET.size() and tower[n] == TARGET[n]:
		n += 1
	return n


func _refresh() -> void:
	for box: Control in [_pattern_box, _tower_box, _ground_box]:
		for child in box.get_children():
			box.remove_child(child)
			child.queue_free()
	for i in TARGET.size():
		var l: Label = make_label("%d. %s" % [i, TARGET[i]], 11, INK)
		l.position = Vector2(4, 172 - i * 32)
		_pattern_box.add_child(l)
	var ok_n: int = _correct_prefix()
	for i in tower.size():
		var b: Button = make_button(tower[i], STONE_SIZE, OK_COLOR if i < ok_n else STONE_COLOR)
		b.position = Vector2(0, 166 - i * 32)
		b.pressed.connect(_on_stone_pressed.bind(i))
		_tower_box.add_child(b)
	if not tower.is_empty():
		var top: Label = make_label("<- PUNCAK", 10, BAD)
		top.position = Vector2(STONE_SIZE.x + 4, 172 - (tower.size() - 1) * 32)
		_tower_box.add_child(top)
	for i in ground.size():
		var g: Button = make_button(ground[i], Vector2(110, 26), STONE_COLOR)
		g.position = Vector2((i % 2) * 118, (i / 2) * 32)
		g.pressed.connect(_push_stone.bind(i))
		g.disabled = is_solved
		_ground_box.add_child(g)
	_pop_button.disabled = tower.is_empty() or is_solved
	_info.text = "Langkah: %d   Benar dari dasar: %d/%d" % [moves, ok_n, TARGET.size()]


func _on_stone_pressed(index: int) -> void:
	if index != tower.size() - 1:
		show_message("Batu itu tertindih! Pada stack hanya batu di PUNCAK yang bisa diambil. POP batu di atasnya dulu.")
		return
	_pop_top()


func _pop_top() -> void:
	if tower.is_empty() or is_solved:
		return
	var stone: String = tower.pop_back()
	ground.append(stone)
	moves += 1
	_refresh()
	show_message("POP: batu %s diturunkan dari puncak." % stone, true)


func _push_stone(index: int) -> void:
	if is_solved or index >= ground.size():
		return
	var stone: String = ground[index]
	ground.remove_at(index)
	tower.append(stone)
	moves += 1
	_refresh()
	if tower == TARGET:
		show_message("Tugu berdiri lagi sesuai ukiran! Yang terakhir di-PUSH (Mahkota) adalah yang pertama bisa di-POP.", true)
		complete_puzzle()
		_refresh()
	elif _correct_prefix() < tower.size():
		show_message("PUSH: %s di puncak, tapi tidak sesuai pola. POP lagi bila perlu." % stone)
	else:
		show_message("PUSH: batu %s ditaruh di puncak. Sesuai pola!" % stone, true)
