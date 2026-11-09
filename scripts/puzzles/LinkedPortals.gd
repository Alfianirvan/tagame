class_name LinkedPortals
extends PuzzleBase
## Puzzle Chapter 4 – Linked List. Tiga tahap, tiap node punya penunjuk "next":
## 1) Sambung: hubungkan Batu 1 -> 2 -> 3 -> 4 -> NULL (klik node asal, lalu node tujuan).
## 2) Sisipkan: masukkan Batu 3 yang hilang di antara Batu 2 dan Batu 4 (tanpa menggeser node lain).
## 3) Buang jebakan: arahkan next node SEBELUM jebakan agar melewatinya.

const NODE_SIZE := Vector2(78, 40)
const SLOT_STEP := 94.0
const ROW_Y := 76.0
const LOW_Y := 150.0
const LINK_COLOR := Color(0.2, 0.12, 0.1)

var stage: int = 1
var items: Dictionary = {}              # id -> {rect, label, next, button}
var selected: String = ""
var _canvas: PuzzleBase.DrawArea
var _item_layer: Control
var _stage_label: Label
var _gap_visible: bool = false          # kotak putus-putus tempat node hilang (tahap 2)


func _init() -> void:
	puzzle_title = "Sambung Batu Portal"
	instruction = "Setiap batu portal adalah NODE yang menyimpan data dan penunjuk NEXT ke node berikutnya. Panah = nilai next."


func _build_content() -> void:
	_canvas = PuzzleBase.DrawArea.new()
	_canvas.size = CONTENT_SIZE
	_canvas.draw_fn = _draw_links
	content.add_child(_canvas)
	_item_layer = Control.new()
	content.add_child(_item_layer)
	_stage_label = make_label("", 12, Color(0.55, 0.33, 0.2))
	_stage_label.position = Vector2(4, 2)
	content.add_child(_stage_label)


func _reset() -> void:
	stage = 1
	_setup_stage()
	report_progress(0, 3)


func _slot_rect(slot: int, low: bool = false) -> Rect2:
	return Rect2(Vector2(8.0 + slot * SLOT_STEP, LOW_Y if low else ROW_Y), NODE_SIZE)


func _add_item(id: String, label: String, rect: Rect2, next: String, color: Color) -> void:
	var b: Button = make_button(label, NODE_SIZE, color)
	b.position = rect.position
	b.pressed.connect(_on_item_pressed.bind(id))
	_item_layer.add_child(b)
	items[id] = {"rect": rect, "label": label, "next": next, "button": b}


func _setup_stage() -> void:
	for child in _item_layer.get_children():
		child.queue_free()
		_item_layer.remove_child(child)
	items.clear()
	selected = ""
	_gap_visible = false
	var stone: Color = Color(0.65, 0.7, 0.8)
	var null_color: Color = Color(0.6, 0.55, 0.5)
	match stage:
		1:
			_stage_label.text = "Tahap 1/3: SAMBUNG. Klik node asal, lalu node yang harus ditunjuk next-nya."
			for i in 4:
				_add_item("n%d" % (i + 1), "Batu %d" % (i + 1), _slot_rect(i), "", stone)
			_add_item("null", "NULL", _slot_rect(4), "", null_color)
		2:
			_stage_label.text = "Tahap 2/3: SISIPKAN. Klik Batu 3, lalu klik node tempat ia disisipkan SETELAHNYA."
			_add_item("n1", "Batu 1", _slot_rect(0), "n2", stone)
			_add_item("n2", "Batu 2", _slot_rect(1), "n4", stone)
			_add_item("n4", "Batu 4", _slot_rect(3), "null", stone)
			_add_item("n3", "Batu 3", _slot_rect(2, true), "", Color(0.9, 0.8, 0.4))
			_add_item("null", "NULL", _slot_rect(4), "", null_color)
			_gap_visible = true
		3:
			_stage_label.text = "Tahap 3/3: BUANG JEBAKAN. Klik node SEBELUM jebakan agar next-nya melewati jebakan."
			_add_item("n1", "Batu 1", _slot_rect(0), "n2", stone)
			_add_item("n2", "Batu 2", _slot_rect(1), "t", stone)
			_add_item("t", "JEBAKAN", _slot_rect(2), "n3", Color(0.85, 0.35, 0.35))
			_add_item("n3", "Batu 3", _slot_rect(3), "null", stone)
			_add_item("null", "NULL", _slot_rect(4), "", null_color)
	_canvas.queue_redraw()


# ---------------------------------------------------------------- Klik

func _on_item_pressed(id: String) -> void:
	if is_solved:
		return
	match stage:
		1: _click_connect(id)
		2: _click_insert(id)
		3: _click_remove(id)


func _click_connect(id: String) -> void:
	if selected == "":
		if id == "null":
			show_message("NULL tidak punya next. Pilih sebuah Batu dulu.")
			return
		if items[id]["next"] != "":
			show_message("Next %s sudah terhubung." % items[id]["label"])
			return
		selected = id
		_highlight(id)
		show_message("%s dipilih. Klik node yang harus ditunjuk next-nya." % items[id]["label"], true)
		return
	var source: String = selected
	selected = ""
	_highlight("")
	var order: Array[String] = ["n1", "n2", "n3", "n4", "null"]
	var correct: String = order[order.find(source) + 1]
	if id != correct:
		show_message("Salah. Urutannya Batu 1 -> Batu 2 -> Batu 3 -> Batu 4 -> NULL. Next dari %s harus menunjuk %s." % [items[source]["label"], items[correct]["label"]])
		return
	items[source]["next"] = id
	_canvas.queue_redraw()
	show_message("next dari %s sekarang menunjuk %s." % [items[source]["label"], items[id]["label"]], true)
	if source == "n4":
		_stage_done()


func _click_insert(id: String) -> void:
	if selected == "":
		if id != "n3":
			show_message("Pilih dulu Batu 3, node yang hilang dan perlu disisipkan.")
			return
		selected = "n3"
		_highlight("n3")
		show_message("Batu 3 dipilih. Klik node yang menjadi PENDAHULUNYA.", true)
		return
	if id == "n3" or id == "null":
		selected = ""
		_highlight("")
		show_message("Pilih Batu 3 lagi, lalu klik salah satu node di rantai.")
		return
	if id != "n2":
		selected = ""
		_highlight("")
		show_message("Salah tempat. Batu 3 harus berada di antara Batu 2 dan Batu 4 (urutan 1,2,3,4).")
		return
	# Sisip: n3.next = n2.next lalu n2.next = n3. Node lain tidak perlu bergeser.
	items["n3"]["next"] = items["n2"]["next"]
	items["n2"]["next"] = "n3"
	items["n3"]["rect"] = _slot_rect(2)
	(items["n3"]["button"] as Button).position = _slot_rect(2).position
	selected = ""
	_highlight("")
	_gap_visible = false
	_canvas.queue_redraw()
	show_message("Berhasil! n3.next = n2.next, lalu n2.next = n3. Tidak ada node yang perlu digeser.", true)
	_stage_done()


func _click_remove(id: String) -> void:
	if id == "n2":
		# Lewati jebakan: n2.next = t.next
		items["n2"]["next"] = items["t"]["next"]
		items["t"]["next"] = ""
		items["t"]["rect"] = _slot_rect(2, true)
		(items["t"]["button"] as Button).position = _slot_rect(2, true).position
		(items["t"]["button"] as Button).disabled = true
		_canvas.queue_redraw()
		show_message("Jebakan terlewati! n2.next kini menunjuk node setelah jebakan.", true)
		_stage_done()
	elif id == "t":
		show_message("Jangan hapus langsung. Ubah next node SEBELUM jebakan agar melompati jebakan.")
	elif id == "null":
		show_message("NULL adalah akhir rantai, bukan node.")
	else:
		show_message("Next node itu tidak menunjuk jebakan. Cari node tepat sebelum jebakan.")


func _stage_done() -> void:
	report_progress(stage, 3)
	if stage >= 3:
		complete_puzzle()
		return
	get_tree().create_timer(1.4).timeout.connect(_next_stage.bind(stage))


func _next_stage(from_stage: int) -> void:
	if stage != from_stage or is_solved or not is_open():
		return
	stage += 1
	_setup_stage()


func _highlight(id: String) -> void:
	for key: String in items:
		(items[key]["button"] as Button).modulate = Color(1.2, 1.2, 0.8) if key == id else Color.WHITE


# ---------------------------------------------------------------- Gambar panah

func _draw_links(c: Control) -> void:
	if items.has("n1"):
		var r: Rect2 = items["n1"]["rect"]
		c.draw_string(FONT, r.position + Vector2(0, -26), "HEAD", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, BAD)
		c.draw_line(r.position + Vector2(20, -22), r.position + Vector2(20, -2), BAD, 2.0)
	if _gap_visible:
		var gap: Rect2 = _slot_rect(2)
		c.draw_rect(gap, Color(0.4, 0.3, 0.2, 0.5), false, 2.0)
	for key: String in items:
		var next_id: String = items[key]["next"]
		if next_id != "" and items.has(next_id):
			_draw_arrow(c, items[key]["rect"], items[next_id]["rect"])


func _draw_arrow(c: Control, from: Rect2, to: Rect2) -> void:
	var gap_x: float = to.position.x - from.end.x
	if absf(from.position.y - to.position.y) < 1.0 and gap_x > 0.0 and gap_x < 30.0:
		var a: Vector2 = Vector2(from.end.x, from.position.y + from.size.y / 2.0)
		var b: Vector2 = Vector2(to.position.x, a.y)
		c.draw_line(a, b, LINK_COLOR, 2.0)
		_head(c, b, Vector2.RIGHT)
	else:
		var top: float = minf(from.position.y, to.position.y) - 16.0
		var p1: Vector2 = Vector2(from.position.x + from.size.x / 2.0, from.position.y)
		var p2: Vector2 = Vector2(p1.x, top)
		var p3: Vector2 = Vector2(to.position.x + to.size.x / 2.0, top)
		var p4: Vector2 = Vector2(p3.x, to.position.y)
		c.draw_polyline(PackedVector2Array([p1, p2, p3, p4]), LINK_COLOR, 2.0)
		_head(c, p4, Vector2.DOWN)


func _head(c: Control, tip: Vector2, dir: Vector2) -> void:
	var side: Vector2 = dir.orthogonal()
	c.draw_colored_polygon(PackedVector2Array([tip, tip - dir * 8.0 + side * 4.0, tip - dir * 8.0 - side * 4.0]), LINK_COLOR)
