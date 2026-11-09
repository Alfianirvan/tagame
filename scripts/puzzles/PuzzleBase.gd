class_name PuzzleBase
extends CanvasLayer
## Dasar semua puzzle materi (Quest Tengah). Menyediakan: bingkai panel, pesan benar/salah,
## buka/tutup (mengunci kontrol Raka), dan penyelesaian quest lewat QuestManager.
##
## Subclass mengisi: _build_content() (membuat isi di `content`), _reset() (mulai ulang puzzle),
## dan memanggil complete_puzzle() saat puzzle selesai. Gunakan show_message() untuk pesan salah/benar.
## Mode uji (test_mode = true) tidak mengubah quest/save sama sekali.

signal solved
signal closed

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const INK := Color(0.2, 0.12, 0.1)
const GOOD := Color(0.15, 0.5, 0.2)
const BAD := Color(0.7, 0.15, 0.1)
const INPUT_GUARD_MSEC := 200
const CONTENT_SIZE := Vector2(576, 200)

## Chapter pemilik puzzle ini (Quest Tengah = tahap 2 chapter tersebut).
@export var chapter: int = 1
@export var puzzle_title: String = "Puzzle"
@export_multiline var instruction: String = ""

var test_mode: bool = false
var is_solved: bool = false
var content: Control

var _root: Control
var _title_label: Label
var _info_label: Label
var _message_label: Label
var _footer_label: Label
var _opened_msec: int = 0


func _ready() -> void:
	layer = 60
	_build_frame()
	_root.visible = false
	_build_content()


# ---------------------------------------------------------------- Hook untuk subclass

func _build_content() -> void:
	pass


func _reset() -> void:
	pass


## Tombol keyboard khusus puzzle. Kembalikan true bila event sudah dipakai.
func _handle_key(_event: InputEvent) -> bool:
	return false


## Dipanggil saat panel ditutup (hentikan timer dsb).
func _on_closed() -> void:
	pass


# ---------------------------------------------------------------- Buka / tutup / selesai

func is_open() -> bool:
	return _root != null and _root.visible


## Alasan puzzle belum bisa dibuka ("" = boleh).
func block_reason() -> String:
	if test_mode:
		return ""
	if GameManager.get_quest_stage(chapter) < 1:
		return "Selesaikan Quest Awal chapter ini dulu."
	return ""


func open_puzzle() -> void:
	is_solved = false
	_opened_msec = Time.get_ticks_msec()
	_title_label.text = puzzle_title
	_info_label.text = instruction
	_message_label.text = ""
	_footer_label.text = "Klik untuk bermain   Esc: tutup"
	_reset()
	_root.visible = true
	_set_player_controls(false)


func close_puzzle() -> void:
	if not is_open():
		return
	_root.visible = false
	_on_closed()
	_set_player_controls(true)
	closed.emit()


## Dipanggil subclass saat puzzle beres: beri hadiah Quest Tengah sekali saja.
func complete_puzzle() -> void:
	if is_solved:
		return
	is_solved = true
	var lines: Array[String] = []
	if not test_mode and GameManager.get_quest_stage(chapter) == 1:
		lines = QuestManager.complete_quest(chapter, 2)
	var text: String = "Puzzle selesai!"
	if not lines.is_empty():
		text += "  Hadiah: " + ", ".join(lines)
	elif not test_mode:
		text += "  (Quest ini sudah pernah diselesaikan.)"
	show_message(text, true)
	_footer_label.text = "E: tutup"
	solved.emit()


## Melaporkan progres ke Quest Log (diabaikan pada mode uji).
func report_progress(done: int, total: int) -> void:
	if not test_mode:
		QuestManager.set_progress(QuestManager.make_id(chapter, 2), done, total)


func show_message(text: String, good: bool = false) -> void:
	_message_label.text = text
	_message_label.add_theme_color_override("font_color", GOOD if good else BAD)


# ---------------------------------------------------------------- Input

func _unhandled_input(event: InputEvent) -> void:
	if not is_open() or Time.get_ticks_msec() - _opened_msec < INPUT_GUARD_MSEC:
		return
	if event.is_action_pressed("pause"):
		close_puzzle()
	elif is_solved and event.is_action_pressed("interact"):
		close_puzzle()
	elif not is_solved and _handle_key(event):
		pass
	else:
		return
	get_viewport().set_input_as_handled()


func _set_player_controls(enabled: bool) -> void:
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(enabled)


# ---------------------------------------------------------------- Pembangun UI (dipakai subclass juga)

func _build_frame() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)

	var dim: ColorRect = ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.6)
	_root.add_child(dim)

	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(20, 8)
	panel.size = Vector2(600, 344)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.96, 0.9, 0.76)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(4)
	style.set_corner_radius_all(4)
	style.set_content_margin_all(10)
	panel.add_theme_stylebox_override("panel", style)
	_root.add_child(panel)

	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	panel.add_child(box)

	_title_label = make_label("", 15, Color(0.55, 0.33, 0.2))
	box.add_child(_title_label)
	_info_label = make_label("", 11, INK)
	_info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info_label.custom_minimum_size = Vector2(576, 30)
	box.add_child(_info_label)

	content = Control.new()
	content.custom_minimum_size = CONTENT_SIZE
	content.clip_contents = true
	box.add_child(content)

	_message_label = make_label("", 12, BAD)
	_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_message_label.custom_minimum_size = Vector2(576, 34)
	box.add_child(_message_label)
	_footer_label = make_label("", 10, Color(0.45, 0.35, 0.3))
	box.add_child(_footer_label)


static func make_label(text: String, size: int, color: Color) -> Label:
	var label: Label = Label.new()
	label.text = text
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	return label


## Tombol bergaya kayu. `color` mengubah warna dasar (mis. warna benih/peti).
static func make_button(text: String, min_size: Vector2, color: Color = Color(0.82, 0.64, 0.4)) -> Button:
	var button: Button = Button.new()
	button.text = text
	button.custom_minimum_size = min_size
	button.size = min_size
	button.focus_mode = Control.FOCUS_NONE
	button.add_theme_font_override("font", FONT)
	button.add_theme_font_size_override("font_size", 11)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_disabled_color", "font_focus_color"]:
		button.add_theme_color_override(key, INK)
	button.add_theme_stylebox_override("normal", _box(color))
	button.add_theme_stylebox_override("hover", _box(color.lightened(0.2)))
	button.add_theme_stylebox_override("pressed", _box(color.darkened(0.15)))
	button.add_theme_stylebox_override("disabled", _box(color.darkened(0.35)))
	return button


## Mengganti warna dasar tombol yang sudah dibuat (mis. menandai terpilih/benar).
static func recolor_button(button: Button, color: Color) -> void:
	button.add_theme_stylebox_override("normal", _box(color))
	button.add_theme_stylebox_override("hover", _box(color.lightened(0.2)))
	button.add_theme_stylebox_override("pressed", _box(color.darkened(0.15)))
	button.add_theme_stylebox_override("disabled", _box(color.darkened(0.35)))


static func _box(color: Color) -> StyleBoxFlat:
	var s: StyleBoxFlat = StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = Color(0.35, 0.2, 0.1)
	s.set_border_width_all(2)
	s.set_corner_radius_all(3)
	s.set_content_margin_all(3)
	return s


## Membersihkan isi `content` (dipakai _reset / pergantian fase).
func clear_content() -> void:
	for child in content.get_children():
		child.queue_free()
		content.remove_child(child)


## Control penggambar kustom: memanggil Callable(canvas) setiap _draw.
class DrawArea extends Control:
	var draw_fn: Callable

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		if draw_fn.is_valid():
			draw_fn.call(self)
