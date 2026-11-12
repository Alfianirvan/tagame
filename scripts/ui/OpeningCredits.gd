extends CanvasLayer
## Opening credit scene: layar hitam, teks cerita bergulir naik dengan potret di sisi kiri.
## Bisa dilewati dengan E / Esc / Spasi / klik. Memancarkan `finished` saat selesai atau dilewati.

signal finished

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const LINES: Array = [
	{"p": "king_subiyan", "t": "Dahulu, Kerajaan Algoria dijaga oleh lima Kristal Struktur."},
	{"p": "king_subiyan", "t": "Kristal-kristal itu menjaga keteraturan dunia:\nsetiap benda punya tempat, setiap data punya urutan."},
	{"p": "king_subiyan", "t": "Lalu datang King Subiyan.\nIa menghancurkan kelima Kristal, dan dunia pun kacau."},
	{"p": "joko", "t": "Raka, murid pandai besi Lilbah, diutus berkelana\nmemulihkan Kristal satu demi satu."},
	{"p": "raka", "t": "Perjalanan pertama: Hutan Indeks,\ntempat semua benda diberi nomor urut..."},
]
const SEC_PER_LINE := 4.2

var _idx: int = -1
var _text: Label
var _portrait: TextureRect
var _skip_hint: Label
var _done: bool = false


func _ready() -> void:
	layer = 95
	process_mode = Node.PROCESS_MODE_ALWAYS
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_portrait = TextureRect.new()
	_portrait.position = Vector2(60, 110)
	_portrait.custom_minimum_size = Vector2(160, 160)
	_portrait.size = Vector2(160, 160)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_portrait)
	_text = Label.new()
	_text.position = Vector2(250, 130)
	_text.size = Vector2(350, 120)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.add_theme_font_override("font", FONT)
	_text.add_theme_font_size_override("font_size", 12)
	_text.add_theme_color_override("font_color", Color(0.95, 0.9, 0.75))
	add_child(_text)
	_skip_hint = Label.new()
	_skip_hint.text = "E / Esc: lewati"
	_skip_hint.position = Vector2(500, 336)
	_skip_hint.add_theme_font_override("font", FONT)
	_skip_hint.add_theme_font_size_override("font_size", 8)
	_skip_hint.modulate = Color(1, 1, 1, 0.5)
	add_child(_skip_hint)
	_next_line()


func _next_line() -> void:
	if _done:
		return
	_idx += 1
	if _idx >= LINES.size():
		_finish()
		return
	var line: Dictionary = LINES[_idx]
	var path: String = "res://assets/portraits/portrait_%s_80.png" % line["p"]
	_portrait.texture = load(path) if ResourceLoader.exists(path) else null
	_text.text = line["t"]
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
