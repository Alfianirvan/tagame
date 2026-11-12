class_name InteriorDoor
extends Area2D
## Pintu bangunan: tekan E di dekatnya untuk masuk ke scene interior (mode masuk), atau keluar kembali ke depan pintu
## bangunan di wilayah (mode keluar, is_exit = true). Posisi kembali disimpan di GameManager.interior_return_*.

const FONT := preload("res://assets/fonts/Square-Black.ttf")

@export_file("*.tscn") var interior_scene: String = ""   # tujuan saat masuk
@export var is_exit: bool = false                        # true = pintu keluar di dalam interior
@export var hint_text: String = "E: Masuk"
@export var front_offset: Vector2 = Vector2(0, 30)       # posisi Raka muncul saat keluar, relatif pintu masuk

var _player_in_range: bool = false
var _hint: Label


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2
	body_entered.connect(func(b: Node2D) -> void: _set_range(b, true))
	body_exited.connect(func(b: Node2D) -> void: _set_range(b, false))
	_hint = Label.new()
	_hint.text = "E: Keluar" if is_exit else hint_text
	_hint.add_theme_font_override("font", FONT)
	_hint.add_theme_font_size_override("font_size", 8)
	_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_hint.add_theme_constant_override("outline_size", 3)
	_hint.position = Vector2(-18, -44)
	_hint.visible = false
	add_child(_hint)


func _set_range(body: Node2D, inside: bool) -> void:
	if body.is_in_group("player"):
		_player_in_range = inside
		_hint.visible = inside


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or QuestManager.quiz_active or get_tree().paused:
		return
	if not event.is_action_pressed("interact") or SceneManager.is_changing:
		return
	get_viewport().set_input_as_handled()
	if is_exit:
		if GameManager.interior_return_scene == "":
			return
		GameManager.pending_spawn_scene = GameManager.interior_return_scene
		GameManager.pending_spawn_pos = GameManager.interior_return_pos
		SceneManager.change_scene(GameManager.interior_return_scene)
	elif interior_scene != "":
		GameManager.interior_return_scene = get_tree().current_scene.scene_file_path
		GameManager.interior_return_pos = global_position + front_offset
		SceneManager.change_scene(interior_scene)
