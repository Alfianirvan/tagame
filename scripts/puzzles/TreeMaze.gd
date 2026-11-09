class_name TreeMaze
extends PuzzleBase
## Puzzle Chapter 5 – Tree (BST). Labirin berupa Binary Search Tree: nilai lebih KECIL ke kiri, lebih BESAR ke kanan.
## Dari akar, pilih KIRI/KANAN di tiap simpul sampai menemukan angka yang dicari. Salah belok = kembali ke akar.
## 3 ronde dengan angka berbeda.

const VALUES: Array[int] = [50, 25, 75, 12, 37, 62, 87, 6, 18, 31, 43, 56, 68, 81, 93]   # pohon lengkap (heap index)
const ROUNDS := 3
const NODE_R := 13.0
const TREE_TOP := 22.0
const LEVEL_STEP := 44.0

var current: int = 0                    # indeks simpul tempat Raka berada
var target_value: int = 0
var round_index: int = 0
var path: Array[int] = []
var targets: Array[int] = []
var _canvas: PuzzleBase.DrawArea
var _target_label: Label
var _left_button: Button
var _right_button: Button


func _init() -> void:
	puzzle_title = "Labirin Bercabang"
	instruction = "Labirin ini adalah BINARY SEARCH TREE: angka lebih KECIL ke kiri, lebih BESAR ke kanan. Temukan angka yang dicari mulai dari akar."


func _build_content() -> void:
	_canvas = PuzzleBase.DrawArea.new()
	_canvas.size = CONTENT_SIZE
	_canvas.draw_fn = _draw_tree
	content.add_child(_canvas)
	_target_label = make_label("", 14, Color(0.55, 0.33, 0.2))
	_target_label.position = Vector2(4, 2)
	content.add_child(_target_label)
	_left_button = make_button("<< KIRI (A)", Vector2(130, 26), Color(0.55, 0.75, 0.9))
	_left_button.position = Vector2(140, 172)
	_left_button.pressed.connect(_move.bind(-1))
	content.add_child(_left_button)
	_right_button = make_button("KANAN (D) >>", Vector2(130, 26), Color(0.9, 0.7, 0.5))
	_right_button.position = Vector2(300, 172)
	_right_button.pressed.connect(_move.bind(1))
	content.add_child(_right_button)


func _reset() -> void:
	round_index = 0
	# Angka yang dicari: 3 simpul selain akar, berbeda-beda.
	var pool: Array[int] = []
	for i in range(1, VALUES.size()):
		pool.append(VALUES[i])
	pool.shuffle()
	targets = pool.slice(0, ROUNDS)
	_start_round()
	report_progress(0, ROUNDS)


func _start_round() -> void:
	target_value = targets[round_index]
	current = 0
	path = [0]
	_target_label.text = "Ronde %d/%d   Cari angka: %d" % [round_index + 1, ROUNDS, target_value]
	_canvas.queue_redraw()


func _handle_key(event: InputEvent) -> bool:
	if event.is_action_pressed("move_left"):
		_move(-1)
		return true
	if event.is_action_pressed("move_right"):
		_move(1)
		return true
	return false


## dir = -1 (kiri) atau +1 (kanan).
func _move(dir: int) -> void:
	if is_solved:
		return
	var here: int = VALUES[current]
	var should_go: int = -1 if target_value < here else 1
	if dir != should_go:
		var word: String = "KIRI (lebih kecil)" if should_go < 0 else "KANAN (lebih besar)"
		show_message("Salah belok! %d %s dari %d, jadi harus ke %s. Labirin mengulang dari akar." % [
			target_value, "lebih kecil" if should_go < 0 else "lebih besar", here, word])
		current = 0
		path = [0]
		_canvas.queue_redraw()
		return
	var child: int = 2 * current + (1 if dir < 0 else 2)
	if child >= VALUES.size():
		show_message("Sudah di ujung (leaf), tidak ada cabang lagi.")
		return
	current = child
	path.append(child)
	_canvas.queue_redraw()
	if VALUES[current] == target_value:
		round_index += 1
		report_progress(round_index, ROUNDS)
		if round_index >= ROUNDS:
			show_message("Ketemu %d! Semua angka ditemukan dengan membandingkan di tiap simpul." % target_value, true)
			complete_puzzle()
		else:
			show_message("Ketemu %d! Lanjut ke angka berikutnya." % target_value, true)
			_start_round()
		return
	show_message("Benar, lanjut ke simpul %d." % VALUES[current], true)


# ---------------------------------------------------------------- Gambar pohon

func _node_pos(index: int) -> Vector2:
	var level: int = int(floor(log(float(index + 1)) / log(2.0)))
	var first: int = (1 << level) - 1
	var count: int = 1 << level
	return Vector2((float(index - first) + 0.5) * CONTENT_SIZE.x / float(count), TREE_TOP + level * LEVEL_STEP)


func _draw_tree(c: Control) -> void:
	for i in range(1, VALUES.size()):
		c.draw_line(_node_pos((i - 1) / 2), _node_pos(i), Color(0.4, 0.3, 0.2), 2.0)
	for i in VALUES.size():
		var pos: Vector2 = _node_pos(i)
		var fill: Color = Color(0.85, 0.72, 0.5)
		if path.has(i):
			fill = Color(0.6, 0.85, 0.55)
		if i == current:
			fill = Color(1.0, 0.85, 0.25)
		c.draw_circle(pos, NODE_R, fill)
		c.draw_arc(pos, NODE_R, 0.0, TAU, 20, Color(0.35, 0.2, 0.1), 2.0)
		var text: String = str(VALUES[i])
		c.draw_string(FONT, pos + Vector2(-NODE_R, 4), text, HORIZONTAL_ALIGNMENT_CENTER, NODE_R * 2.0, 10, INK)
