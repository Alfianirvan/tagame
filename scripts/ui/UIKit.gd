class_name UIKit
extends RefCounted
## Helper tampilan bersama untuk layar menu (StartScreen, WorldMap, Pause, dst.) supaya gayanya seragam
## dengan Inventory/QuestLog: panel krem berbingkai cokelat, font Square-Black.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const INK := Color(0.2, 0.12, 0.1)
const TITLE := Color(0.55, 0.33, 0.2)
const PAPER := Color(0.96, 0.9, 0.76)
const BORDER := Color(0.45, 0.28, 0.16)


static func box(bg: Color = PAPER, border: Color = BORDER, border_w: int = 4, margin: int = 10) -> StyleBoxFlat:
	var s: StyleBoxFlat = StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(border_w)
	s.set_corner_radius_all(4)
	s.set_content_margin_all(margin)
	return s


static func label(text: String, size: int = 11, color: Color = INK, center: bool = false) -> Label:
	var l: Label = Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if center:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


static func button(text: String, min_size: Vector2 = Vector2(150, 26)) -> Button:
	var b: Button = Button.new()
	b.text = text
	b.custom_minimum_size = min_size
	b.focus_mode = Control.FOCUS_ALL
	b.add_theme_font_override("font", FONT)
	b.add_theme_font_size_override("font_size", 11)
	b.add_theme_color_override("font_color", INK)
	b.add_theme_color_override("font_hover_color", Color(0.1, 0.05, 0.02))
	b.add_theme_color_override("font_disabled_color", Color(0.5, 0.42, 0.34))
	b.add_theme_stylebox_override("normal", box(Color(0.88, 0.76, 0.55), BORDER, 2, 4))
	b.add_theme_stylebox_override("hover", box(Color(0.98, 0.86, 0.6), Color(0.7, 0.4, 0.15), 2, 4))
	b.add_theme_stylebox_override("pressed", box(Color(0.78, 0.62, 0.4), BORDER, 2, 4))
	b.add_theme_stylebox_override("focus", box(Color(0.98, 0.86, 0.6), Color(0.85, 0.5, 0.1), 2, 4))
	b.add_theme_stylebox_override("disabled", box(Color(0.75, 0.7, 0.62), Color(0.55, 0.5, 0.45), 2, 4))
	b.pressed.connect(func() -> void: AudioManager.play_sfx("menu_pilih"))
	return b


## Latar gelap transparan satu layar penuh.
static func dim(alpha: float = 0.55) -> ColorRect:
	var d: ColorRect = ColorRect.new()
	d.set_anchors_preset(Control.PRESET_FULL_RECT)
	d.color = Color(0, 0, 0, alpha)
	return d


## Panel di tengah layar 640x360. Mengembalikan VBoxContainer isi panel.
static func centered_panel(parent: Control, size: Vector2) -> VBoxContainer:
	var panel: PanelContainer = PanelContainer.new()
	panel.position = (Vector2(640, 360) - size) / 2.0
	panel.custom_minimum_size = size
	panel.size = size
	panel.add_theme_stylebox_override("panel", box())
	parent.add_child(panel)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	panel.add_child(v)
	return v
