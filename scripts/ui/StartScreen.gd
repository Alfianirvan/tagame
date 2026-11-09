extends Control
## StartScreen: Mulai, Lanjutkan (aktif bila ada save), Peta Dunia (level select, butuh save), Pengaturan, About, Keluar.

const WORLD_MAP_SCENE := "res://scenes/ui/WorldMap.tscn"
const BG := preload("res://assets/worldmap/peta_dunia_preview.png")
const SettingsScript := preload("res://scripts/ui/Settings.gd")
const AboutScript := preload("res://scripts/ui/About.gd")

var _buttons: VBoxContainer
var _continue: Button
var _map_btn: Button
var _confirm: Control


func _ready() -> void:
	AudioManager.play_music("menu_utama")
	get_tree().paused = false
	_build_ui()


func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg: TextureRect = TextureRect.new()      # peta dunia sebagai latar, digeser pelan ke atas
	bg.texture = BG
	bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bg.stretch_mode = TextureRect.STRETCH_KEEP
	bg.size = Vector2(810, 1440)
	bg.position = Vector2(-85, -700)
	add_child(bg)
	var tw: Tween = create_tween().set_loops().set_trans(Tween.TRANS_SINE)
	tw.tween_property(bg, "position:y", -980.0, 40.0)
	tw.tween_property(bg, "position:y", -300.0, 40.0)
	add_child(UIKit.dim(0.6))

	var title: Label = UIKit.label("STRUKTURA", 34, Color(1, 0.9, 0.55), true)
	title.add_theme_color_override("font_outline_color", Color(0.25, 0.12, 0.05))
	title.add_theme_constant_override("outline_size", 8)
	title.position = Vector2(0, 40)
	title.size = Vector2(640, 48)
	add_child(title)
	var sub: Label = UIKit.label("Legenda Dunia Data", 14, Color(0.95, 0.9, 0.8), true)
	sub.add_theme_color_override("font_outline_color", Color(0.1, 0.05, 0.02))
	sub.add_theme_constant_override("outline_size", 5)
	sub.position = Vector2(0, 90)
	sub.size = Vector2(640, 22)
	add_child(sub)

	_buttons = VBoxContainer.new()
	_buttons.add_theme_constant_override("separation", 5)
	_buttons.position = Vector2(245, 130)
	add_child(_buttons)
	var start: Button = _add("Mulai", _on_start)
	_continue = _add("Lanjutkan", _on_continue)
	_map_btn = _add("Peta Dunia", _on_world_map)
	_add("Pengaturan", func() -> void: _open_overlay(SettingsScript))
	_add("About", func() -> void: _open_overlay(AboutScript))
	if not OS.has_feature("web"):
		_add("Keluar", func() -> void: get_tree().quit())
	var has_save: bool = SaveManager.has_save()
	_continue.disabled = not has_save
	_map_btn.disabled = not has_save
	(start if not has_save else _continue).grab_focus()

	var foot: Label = UIKit.label("Kelompok 10 · Workshop PPLG · WASD gerak · J serang · 1-6 ganti senjata (1 tinju, 2 pedang) · Spasi dodge · E interaksi · M peta", 9, Color(0.9, 0.85, 0.75), true)
	foot.position = Vector2(0, 340)
	foot.size = Vector2(640, 14)
	add_child(foot)


func _add(text: String, action: Callable) -> Button:
	var b: Button = UIKit.button(text, Vector2(150, 26))
	b.pressed.connect(action)
	_buttons.add_child(b)
	return b


func _open_overlay(script: GDScript) -> void:
	var o: CanvasLayer = script.new()
	add_child(o)


func _on_start() -> void:
	if SaveManager.has_save():
		_ask_overwrite()
		return
	_begin_new_game()


func _begin_new_game() -> void:
	SaveManager.new_game()
	WorldMap.seen_open.clear()
	SceneManager.change_scene(GameManager.START_SCENE)


func _on_continue() -> void:
	if SaveManager.load_game():
		SceneManager.change_scene(GameManager.checkpoint_scene)


func _on_world_map() -> void:
	if SaveManager.load_game():
		SceneManager.change_scene(WORLD_MAP_SCENE)


## Konfirmasi sebelum game baru menimpa progres lama.
func _ask_overwrite() -> void:
	if _confirm:
		return
	_confirm = Control.new()
	_confirm.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_confirm)
	_confirm.add_child(UIKit.dim(0.6))
	var v: VBoxContainer = UIKit.centered_panel(_confirm, Vector2(300, 110))
	v.add_child(UIKit.label("Mulai game baru? Progres tersimpan akan tertimpa saat kamu menyimpan.", 11, UIKit.INK, true))
	var row: HBoxContainer = HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	var yes: Button = UIKit.button("Ya, mulai baru", Vector2(110, 24))
	var no: Button = UIKit.button("Batal", Vector2(80, 24))
	yes.pressed.connect(_begin_new_game)
	no.pressed.connect(func() -> void:
		_confirm.queue_free()
		_confirm = null)
	row.add_child(yes)
	row.add_child(no)
	v.add_child(row)
	no.grab_focus()
