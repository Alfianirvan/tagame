class_name StackCrates
extends PuzzleBase
## Puzzle Chapter 2 – Stack (LIFO). Pedang berada di peti paling bawah. Hanya peti paling atas yang boleh
## di-POP; peti yang sudah diambil bisa di-PUSH kembali. Pop semua peti di atas sampai pedang terambil.

const LABELS: Array[String] = ["Apel", "Kayu", "Batu", "Jamur", "Kain", "Tali", "Tulang"]
const CRATE_SIZE := Vector2(140, 28)

var crates: Array[String] = []          # indeks 0 = dasar, terakhir = puncak
var popped: Array[String] = []          # riwayat peti yang diambil (puncak = terakhir)
var crate_buttons: Array[Button] = []
var _stack_box: Control
var _log_label: Label
var _push_button: Button
var _pop_button: Button


func _init() -> void:
	puzzle_title = "Pedang di Dasar Tumpukan"
	instruction = "Tumpukan peti ini adalah STACK (LIFO: yang terakhir masuk, keluar pertama). Ambil pedang di peti paling bawah dengan POP peti dari atas."


func _build_content() -> void:
	_stack_box = Control.new()
	_stack_box.position = Vector2(150, 0)
	content.add_child(_stack_box)
	_pop_button = make_button("POP (ambil atas)", Vector2(150, 30), Color(0.85, 0.55, 0.35))
	_pop_button.position = Vector2(4, 50)
	_pop_button.pressed.connect(_pop_top)
	content.add_child(_pop_button)
	_push_button = make_button("PUSH (kembalikan)", Vector2(150, 30), Color(0.5, 0.75, 0.5))
	_push_button.position = Vector2(4, 90)
	_push_button.pressed.connect(_push_back)
	content.add_child(_push_button)
	_log_label = make_label("", 11, INK)
	_log_label.position = Vector2(340, 8)
	_log_label.custom_minimum_size = Vector2(230, 180)
	_log_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(_log_label)


func _reset() -> void:
	var pool: Array[String] = LABELS.duplicate()
	pool.shuffle()
	crates = ["Pedang"]
	crates.append_array(pool.slice(0, 4))   # dasar = pedang, di atasnya 4 peti acak
	popped.clear()
	_refresh()
	report_progress(0, 4)


func _refresh() -> void:
	_clear_stack_nodes()
	crate_buttons.clear()
	# Dasar di bawah, puncak di atas
	for i in crates.size():
		var color: Color = Color(0.7, 0.75, 0.9) if crates[i] == "Pedang" else Color(0.75, 0.55, 0.32)
		var b: Button = make_button(crates[i], CRATE_SIZE, color)
		b.position = Vector2(0, 168 - i * 32)
		b.pressed.connect(_on_crate_pressed.bind(i))
		_stack_box.add_child(b)
		crate_buttons.append(b)
	if not crates.is_empty():
		var top: Label = make_label("<- TOP", 11, BAD)
		top.position = Vector2(CRATE_SIZE.x + 6, 172 - (crates.size() - 1) * 32)
		_stack_box.add_child(top)
	_push_button.disabled = popped.is_empty() or is_solved
	_pop_button.disabled = crates.is_empty() or is_solved
	var lines: String = "Riwayat:\n"
	for item in popped:
		lines += "pop -> %s\n" % item
	_log_label.text = lines + "\nTinggi stack: %d" % crates.size()


func _clear_stack_nodes() -> void:
	for child in _stack_box.get_children():
		child.queue_free()
		_stack_box.remove_child(child)


func _on_crate_pressed(index: int) -> void:
	if index != crates.size() - 1:
		show_message("Peti itu tertindih! Pada stack hanya peti paling ATAS yang bisa diambil (LIFO). POP peti di atasnya dulu.")
		return
	_pop_top()


func _pop_top() -> void:
	if crates.is_empty() or is_solved:
		return
	var item: String = crates.pop_back()
	popped.append(item)
	_refresh()
	report_progress(popped.size(), 4)
	if item == "Pedang":
		show_message("Kamu mengambil Pedang di dasar tumpukan! Peti terakhir yang masuk keluar paling dulu (LIFO).", true)
		complete_puzzle()
		_refresh()
	else:
		show_message("POP: peti %s diambil dari puncak." % item, true)


func _push_back() -> void:
	if popped.is_empty() or is_solved:
		return
	var item: String = popped.pop_back()
	crates.append(item)
	_refresh()
	show_message("PUSH: peti %s ditaruh lagi di puncak." % item, true)
