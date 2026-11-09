extends CanvasLayer
## PauseMenu (Esc): Lanjut, Peta Dunia, Pengaturan, Simpan, Simpan & ke Menu Utama.
## Esc hanya membuka menu bila Tas / Catatan Misi / Peta Dunia / dialog / kuis tidak sedang terbuka.
## Simpan dinonaktifkan saat ada musuh dekat (sesuai CLAUDE.md Bagian 8).

const SettingsScript := preload("res://scripts/ui/Settings.gd")
const START_SCREEN := "res://scenes/ui/StartScreen.tscn"
const SAFE_DISTANCE := 260.0

var _root: Control
var _note: Label
var _save_btn: Button
var _first: Button
var _was_enabled: bool = true
var _open: bool = false


func _ready() -> void:
	layer = 70
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("ui_overlay")
	add_to_group("pause_menu")
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_root.add_child(UIKit.dim(0.6))
	var v: VBoxContainer = UIKit.centered_panel(_root, Vector2(220, 280))
	v.add_theme_constant_override("separation", 5)
	v.add_child(UIKit.label("Jeda", 14, UIKit.TITLE, true))
	_first = _add(v, "Lanjutkan", close)
	_add(v, "Peta Dunia", _on_world_map)
	_add(v, "Kantong Pedagang (Tab)", _on_trade)
	_add(v, "Pengaturan", func() -> void: add_child(SettingsScript.new()))
	_save_btn = _add(v, "Simpan", _on_save)
	_add(v, "Simpan & ke Menu Utama", _on_quit_to_menu)
	_note = UIKit.label("", 9, Color(0.6, 0.25, 0.15), true)
	v.add_child(_note)
	_root.visible = false


func _add(parent: Control, text: String, action: Callable) -> Button:
	var b: Button = UIKit.button(text, Vector2(190, 24))
	b.pressed.connect(action)
	parent.add_child(b)
	return b


func is_open() -> bool:
	return _open


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("pause"):
		return
	if _open:
		get_viewport().set_input_as_handled()
		close()
		return
	if DialogManager.is_active or QuestManager.quiz_active or get_tree().paused:
		return
	for n in get_tree().get_nodes_in_group("ui_overlay"):
		if n != self and n.has_method("is_open") and n.is_open():
			return
	if get_tree().get_first_node_in_group("player") == null:
		return
	get_viewport().set_input_as_handled()
	open()


func open() -> void:
	_open = true
	var player: Node = get_tree().get_first_node_in_group("player")
	_was_enabled = player == null or bool(player.get("controls_enabled"))
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(false)
	get_tree().paused = true
	var near: bool = _enemy_near()
	_save_btn.disabled = near
	_note.text = "Tidak bisa menyimpan: ada musuh di dekatmu." if near else ""
	_root.visible = true
	_first.grab_focus()


func close() -> void:
	_open = false
	_root.visible = false
	get_tree().paused = false
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(_was_enabled)


func _enemy_near() -> bool:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return false
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en and en.is_inside_tree() and en.global_position.distance_to(player.global_position) < SAFE_DISTANCE:
			return true
	return false


func _on_trade() -> void:
	close()
	var tm: Node = get_tree().get_first_node_in_group("trade_menu")
	if tm and tm.has_method("open"):
		tm.open()


func _on_world_map() -> void:
	close()
	var wm: Node = get_tree().get_first_node_in_group("world_map_ui")
	if wm and wm.has_method("open"):
		wm.open()


func _on_save() -> void:
	if _enemy_near():
		return
	_note.text = "Game tersimpan." if SaveManager.save_game() else "Gagal menyimpan."
	AudioManager.play_sfx("heal_potion")


func _on_quit_to_menu() -> void:
	if not _enemy_near():
		SaveManager.save_game()
	close()
	SceneManager.change_scene(START_SCREEN)
