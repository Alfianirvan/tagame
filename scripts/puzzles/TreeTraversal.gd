class_name TreeTraversal
extends PuzzleBase
## Puzzle Dusun Ranting (Chapter 5, langkah Quest Tengah) – Tree: PENELUSURAN PRE-ORDER.
## Tujuh lentera tergantung seperti pohon biner. Nyalakan sesuai urutan pre-order: simpul sendiri dulu, lalu seluruh
## cabang KIRI sampai habis, baru cabang KANAN. Salah urutan = semua lentera padam, ulang dari akar.

const NODE_R := 14.0
const TREE_TOP := 26.0
const LEVEL_STEP := 54.0
const LABELS: Array[String] = ["A", "B", "C", "D", "E", "F", "G"]   # indeks heap: anak kiri 2i+1, kanan 2i+2
const PREORDER: Array[int] = [0, 1, 3, 4, 2, 5, 6]

var lit: Array[int] = []                # urutan lentera yang sudah menyala
var _canvas: PuzzleBase.DrawArea
var _buttons: Array[Button] = []
var _order_label: Label


func _init() -> void:
	puzzle_title = "Lentera Ranting"
	instruction = "Nyalakan lentera sesuai PENELUSURAN PRE-ORDER: simpul itu sendiri dulu, lalu seluruh cabang KIRI sampai habis, baru cabang KANAN. Mulai dari akar."


## Posisi simpul (indeks heap) pada kanvas.
func _pos(i: int) -> Vector2:
	var level: int = 0
	var first: int = 0
	while i >= first + (1 << level):
		first += 1 << level
		level += 1
	var count: int = 1 << level
	var slot: int = i - first
	var width: float = CONTENT_SIZE.x - 60.0
	return Vector2(30.0 + width * (slot + 0.5) / count, TREE_TOP + level * LEVEL_STEP)


func _build_content() -> void:
	_canvas = PuzzleBase.DrawArea.new()
	_canvas.size = CONTENT_SIZE
	_canvas.draw_fn = _draw_tree
	content.add_child(_canvas)
	for i in LABELS.size():
		var b: Button = make_button(LABELS[i], Vector2(NODE_R * 2 + 4, NODE_R * 2 + 4), Color(0.45, 0.4, 0.5))
		b.position = _pos(i) - Vector2(NODE_R + 2, NODE_R + 2)
		b.pressed.connect(_on_lantern.bind(i))
		content.add_child(b)
		_buttons.append(b)
	_order_label = make_label("", 11, INK)
	_order_label.position = Vector2(4, 178)
	content.add_child(_order_label)


func _reset() -> void:
	lit.clear()
	_refresh()


func _draw_tree(c: Control) -> void:
	for i in LABELS.size():
		for child in [2 * i + 1, 2 * i + 2]:
			if child < LABELS.size():
				var on: bool = i in lit and child in lit
				c.draw_line(_pos(i), _pos(child), Color(0.95, 0.75, 0.3) if on else Color(0.45, 0.3, 0.2), 3.0)
	for i in lit:     # cahaya lentera menyala
		c.draw_circle(_pos(i), NODE_R + 6, Color(1.0, 0.85, 0.35, 0.35))


func _refresh() -> void:
	for i in _buttons.size():
		recolor_button(_buttons[i], Color(1.0, 0.82, 0.35) if i in lit else Color(0.45, 0.4, 0.5))
		_buttons[i].disabled = is_solved
	var names: Array[String] = []
	for i in lit:
		names.append(LABELS[i])
	_order_label.text = "Urutan menyala: " + (" -> ".join(names) if not names.is_empty() else "(belum ada)")
	_canvas.queue_redraw()


func _on_lantern(i: int) -> void:
	if is_solved or i in lit:
		return
	var expected: int = PREORDER[lit.size()]
	if i != expected:
		var hint: String = "Salah urutan! Semua lentera padam. Pre-order: simpul dulu, lalu cabang KIRI sampai habis, baru KANAN."
		if lit.is_empty():
			hint = "Penelusuran pre-order selalu dimulai dari AKAR (simpul paling atas)."
		lit.clear()
		_refresh()
		show_message(hint)
		return
	lit.append(i)
	_refresh()
	if lit.size() == PREORDER.size():
		show_message("Semua lentera ranting menyala: A -> B -> D -> E -> C -> F -> G. Itulah penelusuran pre-order!", true)
		complete_puzzle()
		_refresh()
	else:
		show_message("Lentera %s menyala." % LABELS[i], true)
