class_name BossHealthBar
extends CanvasLayer
## Bar HP boss di atas layar beserta nama boss. Dibuat dan diperbarui oleh Boss lewat signal.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const BAR_SIZE := Vector2(300, 10)

var _name_label: Label
var _fill: ColorRect


func _ready() -> void:
	layer = 20
	var root: Control = Control.new()
	root.set_anchors_preset(Control.PRESET_TOP_WIDE)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_name_label = Label.new()
	_name_label.add_theme_font_override("font", FONT)
	_name_label.add_theme_font_size_override("font_size", 10)
	_name_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_name_label.add_theme_constant_override("outline_size", 3)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_name_label.position.y = 14
	root.add_child(_name_label)

	var frame: ColorRect = ColorRect.new()
	frame.color = Color(0, 0, 0, 0.85)
	frame.size = BAR_SIZE + Vector2(4, 4)
	frame.position = Vector2((640 - BAR_SIZE.x) / 2.0 - 2.0, 28)
	root.add_child(frame)

	_fill = ColorRect.new()
	_fill.color = Color(0.8, 0.2, 0.2)
	_fill.size = BAR_SIZE
	_fill.position = Vector2(2, 2)
	frame.add_child(_fill)


func setup(boss_name: String) -> void:
	_name_label.text = boss_name


## Dipanggil lewat signal Boss.damaged.
func set_hp(hp: int, max_hp: int) -> void:
	_fill.size.x = BAR_SIZE.x * clampf(float(hp) / float(max_hp), 0.0, 1.0)
