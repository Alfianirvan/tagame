class_name EndCredits
extends CanvasLayer
## Ending credit setelah King Subiyan kalah & Kristal terakhir diserahkan: epilog cerita (OpeningCredits dengan kunci "ending"),
## lalu CREDIT BERGULIR (judul, tim, dosen, materi, aset) dari res://data/credits.json ("roll" + "team").
## Bisa dilewati dengan E / Esc / Spasi / klik. Memancarkan `finished` setelah selesai atau dilewati.

signal finished

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const SCROLL_SPEED := 26.0       # piksel per detik
const HEAD_COLOR := Color(1.0, 0.85, 0.4)
const TEXT_COLOR := Color(0.92, 0.9, 0.85)

var _roll: VBoxContainer
var _tween: Tween
var _done: bool = false
var _rolling: bool = false


func _ready() -> void:
	layer = 96
	process_mode = Node.PROCESS_MODE_ALWAYS
	AudioManager.play_music("kredit_about", 1.0)
	var epilog: OpeningCredits = OpeningCredits.new()
	epilog.credits_key = "ending"
	epilog.finished.connect(_start_roll)
	add_child(epilog)


## Bagian 2: daftar credit bergulir naik di layar hitam.
func _start_roll() -> void:
	if _done:
		return
	_rolling = true
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_roll = VBoxContainer.new()
	_roll.position = Vector2(0, 370)
	_roll.custom_minimum_size = Vector2(640, 0)
	_roll.add_theme_constant_override("separation", 6)
	add_child(_roll)
	var data: Dictionary = OpeningCredits.load_data()
	var team: Dictionary = data.get("team", {})
	for e: Dictionary in data.get("roll", []):
		if e.get("gap", false):
			var gap := Control.new()
			gap.custom_minimum_size = Vector2(0, 22)
			_roll.add_child(gap)
			continue
		if e.has("h"):
			_add_line(String(e["h"]), 15, HEAD_COLOR)
		if e.has("t"):
			_add_line(String(e["t"]), 11, TEXT_COLOR)
		if e.get("team", false):
			for m: Dictionary in team.get("members", []):
				_add_line("%s — %s" % [String(m.get("name", "")), String(m.get("role", ""))], 11, TEXT_COLOR)
		if e.get("lecturer", false):
			_add_line(String(team.get("lecturer", {}).get("name", "")), 11, TEXT_COLOR)
	await get_tree().process_frame          # ukur tinggi daftar setelah tata letak
	var dist: float = 370.0 + _roll.size.y + 20.0
	_tween = create_tween()
	_tween.tween_property(_roll, "position:y", -_roll.size.y - 20.0, dist / SCROLL_SPEED)
	_tween.tween_interval(1.0)
	_tween.tween_callback(_finish)
	var hint := Label.new()
	hint.text = "E / Esc: lewati"
	hint.position = Vector2(500, 336)
	hint.add_theme_font_override("font", FONT)
	hint.add_theme_font_size_override("font_size", 8)
	hint.modulate = Color(1, 1, 1, 0.5)
	add_child(hint)


func _add_line(text: String, size: int, color: Color) -> void:
	var l := Label.new()
	l.text = text
	l.custom_minimum_size = Vector2(640, 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	_roll.add_child(l)


func _unhandled_input(event: InputEvent) -> void:
	if _done or not _rolling:
		return       # saat epilog, input dipegang OpeningCredits (lewati epilog -> credit bergulir)
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
	if _tween != null:
		_tween.kill()
	var fade: Tween = create_tween()
	for c in get_children():
		if c is CanvasItem:
			fade.parallel().tween_property(c, "modulate:a", 0.0, 0.8)
	fade.tween_callback(func() -> void:
		finished.emit()
		queue_free())
