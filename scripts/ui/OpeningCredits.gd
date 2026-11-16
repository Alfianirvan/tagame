class_name OpeningCredits
extends CanvasLayer
## Credit scene cerita: layar hitam, kartu judul (mis. "Chapter 2 — Tambang Tumpuk" + materi), lalu baris cerita satu per satu
## dengan potret di sisi kiri. Isi diambil dari res://data/credits.json dengan kunci `credits_key` (opening_ch1..opening_ch5, ending).
## Bisa dilewati dengan E / Esc / Spasi / klik. Memancarkan `finished` saat selesai atau dilewati.

signal finished

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const DATA_PATH := "res://data/credits.json"
const SEC_PER_LINE := 4.2
const SEC_TITLE := 2.8

## Kunci data di credits.json (diisi pemanggil sebelum add_child).
var credits_key: String = "opening_ch1"

var _lines: Array = []
var _title: String = ""
var _subtitle: String = ""
var _idx: int = -1
var _text: Label
var _portrait: TextureRect
var _title_label: Label
var _sub_label: Label
var _skip_hint: Label
var _done: bool = false


## Isi credits.json (kosong bila file tidak ada / rusak).
static func load_data() -> Dictionary:
	if not FileAccess.file_exists(DATA_PATH):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	return parsed if parsed is Dictionary else {}


## Ada credit scene untuk kunci ini?
static func has_scene(key: String) -> bool:
	var entry: Variant = load_data().get(key, null)
	return entry is Dictionary and not (entry as Dictionary).get("lines", []).is_empty()


func _ready() -> void:
	layer = 95
	process_mode = Node.PROCESS_MODE_ALWAYS
	var entry: Dictionary = load_data().get(credits_key, {})
	_lines = entry.get("lines", [])
	_title = String(entry.get("title", ""))
	_subtitle = String(entry.get("subtitle", ""))
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_title_label = _make_label(Vector2(0, 140), Vector2(640, 30), 18, Color(1.0, 0.85, 0.4))
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub_label = _make_label(Vector2(0, 176), Vector2(640, 20), 11, Color(0.8, 0.8, 0.85))
	_sub_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_portrait = TextureRect.new()
	_portrait.position = Vector2(60, 110)
	_portrait.custom_minimum_size = Vector2(160, 160)
	_portrait.size = Vector2(160, 160)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_portrait)
	_text = _make_label(Vector2(250, 130), Vector2(350, 120), 12, Color(0.95, 0.9, 0.75))
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_skip_hint = _make_label(Vector2(500, 336), Vector2(130, 14), 8, Color.WHITE)
	_skip_hint.text = "E / Esc: lewati"
	_skip_hint.modulate = Color(1, 1, 1, 0.5)
	if _lines.is_empty():
		_finish.call_deferred()
		return
	_show_title()


func _make_label(pos: Vector2, size: Vector2, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.position = pos
	l.size = size
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	return l


## Kartu judul chapter (bila ada), lalu baris cerita.
func _show_title() -> void:
	if _title == "":
		_next_line()
		return
	_title_label.text = _title
	_sub_label.text = _subtitle
	for l: Label in [_title_label, _sub_label]:
		l.modulate.a = 0.0
	var tw: Tween = create_tween()
	tw.tween_property(_title_label, "modulate:a", 1.0, 0.8)
	tw.parallel().tween_property(_sub_label, "modulate:a", 1.0, 1.0)
	tw.tween_interval(SEC_TITLE)
	tw.tween_property(_title_label, "modulate:a", 0.0, 0.5)
	tw.parallel().tween_property(_sub_label, "modulate:a", 0.0, 0.5)
	tw.tween_callback(_next_line)


func _next_line() -> void:
	if _done:
		return
	_idx += 1
	if _idx >= _lines.size():
		_finish()
		return
	var line: Dictionary = _lines[_idx]
	var path: String = "res://assets/portraits/portrait_%s_80.png" % String(line.get("p", ""))
	_portrait.texture = load(path) if line.get("p", "") != "" and ResourceLoader.exists(path) else null
	_text.text = String(line.get("t", ""))
	_text.modulate.a = 0.0
	_portrait.modulate.a = 0.0
	var tw: Tween = create_tween().set_parallel(true)
	tw.tween_property(_text, "modulate:a", 1.0, 0.8)
	tw.tween_property(_portrait, "modulate:a", 1.0, 0.8)
	var t2: Tween = create_tween()
	t2.tween_interval(SEC_PER_LINE)
	t2.tween_callback(_next_line)


func _unhandled_input(event: InputEvent) -> void:
	if _done:
		return
	var skip: bool = event.is_action_pressed("interact") or event.is_action_pressed("pause") \
		or (event is InputEventKey and event.pressed and event.keycode == KEY_SPACE) \
		or (event is InputEventMouseButton and event.pressed)
	if skip:
		get_viewport().set_input_as_handled()
		_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	var fade: Tween = create_tween()
	for c in get_children():
		if c is CanvasItem:
			fade.parallel().tween_property(c, "modulate:a", 0.0, 0.6)
	fade.tween_callback(func() -> void:
		finished.emit()
		queue_free())
