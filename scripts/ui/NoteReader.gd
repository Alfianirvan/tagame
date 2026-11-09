class_name NoteReader
extends CanvasLayer
## Panel baca kertas catatan materi (data dari res://data/notes.json).
## Halaman diganti dengan tombol Lanjut/Kembali atau A/D; ditutup dengan Tutup, E, atau Esc.

const FONT := preload("res://assets/fonts/Square-Black.ttf")

var _title: String = ""
var _pages: Array = []
var _index: int = 0

var _text: RichTextLabel
var _page_label: Label
var _prev: Button
var _next: Button


## Membuat panel untuk chapter tertentu.
static func create(chapter: int) -> NoteReader:
	var r: NoteReader = NoteReader.new()
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "notes.json")
	if data is Dictionary and data.has(str(chapter)):
		r._title = String(data[str(chapter)].get("title", "Catatan"))
		r._pages = data[str(chapter)].get("pages", [])
	if r._pages.is_empty():
		r._title = "Catatan"
		r._pages = ["Kertas ini kosong."]
	return r


func _ready() -> void:
	layer = 70
	add_to_group("ui_overlay")
	_build_ui()
	_show_page()


func _build_ui() -> void:
	var root: Control = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)
	var dim: ColorRect = ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.55)
	root.add_child(dim)

	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(110, 30)
	panel.size = Vector2(420, 300)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.96, 0.9, 0.74)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(4)
	style.set_corner_radius_all(3)
	style.set_content_margin_all(14)
	panel.add_theme_stylebox_override("panel", style)
	root.add_child(panel)

	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)

	var title: Label = Label.new()
	title.text = _title
	title.add_theme_font_override("font", FONT)
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", Color(0.55, 0.33, 0.2))
	box.add_child(title)

	_text = RichTextLabel.new()
	_text.bbcode_enabled = true
	_text.fit_content = false
	_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_text.custom_minimum_size = Vector2(0, 190)
	_text.add_theme_font_override("normal_font", FONT)
	_text.add_theme_font_override("bold_font", FONT)
	_text.add_theme_font_size_override("normal_font_size", 11)
	_text.add_theme_font_size_override("bold_font_size", 12)
	_text.add_theme_color_override("default_color", Color(0.2, 0.12, 0.1))
	box.add_child(_text)

	var bar: HBoxContainer = HBoxContainer.new()
	bar.add_theme_constant_override("separation", 8)
	box.add_child(bar)
	_prev = _button("Kembali", func() -> void: _go(-1))
	bar.add_child(_prev)
	_page_label = Label.new()
	_page_label.add_theme_font_override("font", FONT)
	_page_label.add_theme_font_size_override("font_size", 10)
	_page_label.add_theme_color_override("font_color", Color(0.2, 0.12, 0.1))
	_page_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_page_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bar.add_child(_page_label)
	_next = _button("Lanjut", func() -> void: _go(1))
	bar.add_child(_next)
	bar.add_child(_button("Tutup", _close))


func _button(label: String, action: Callable) -> Button:
	var b: Button = Button.new()
	b.text = label
	b.add_theme_font_override("font", FONT)
	b.add_theme_font_size_override("font_size", 10)
	b.pressed.connect(action)
	return b


func _go(step: int) -> void:
	_index = clampi(_index + step, 0, _pages.size() - 1)
	AudioManager.play_sfx("menu_pilih")
	_show_page()


func _show_page() -> void:
	_text.text = String(_pages[_index])
	_page_label.text = "%d / %d" % [_index + 1, _pages.size()]
	_prev.disabled = _index == 0
	_next.disabled = _index >= _pages.size() - 1


func _close() -> void:
	AudioManager.play_sfx("menu_batal")
	queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") or event.is_action_pressed("interact"):
		_close()
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_D or event.keycode == KEY_RIGHT:
			_go(1)
		elif event.keycode == KEY_A or event.keycode == KEY_LEFT:
			_go(-1)
	else:
		return
	get_viewport().set_input_as_handled()
