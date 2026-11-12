class_name Anvil
extends StaticBody2D
## Landasan tempa: tekan E di dekatnya untuk membuka Kantong Pedagang hanya dengan Tempa (upgrade senjata/armor), tanpa Toko/Jual/Racik/Skill.
## Sprite & tabrakan dibuat oleh scene (node Dekor_anvil_* dari tools/add_decor.py); script ini menambah area interaksi dan petunjuk.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
var _player_in_range: bool = false
var _hint: Label


func _ready() -> void:
	var area: Area2D = Area2D.new()
	area.collision_layer = 0
	area.collision_mask = 2
	area.position = Vector2(0, -22)
	var shape: CollisionShape2D = CollisionShape2D.new()
	var rect: RectangleShape2D = RectangleShape2D.new()
	rect.size = Vector2(150, 96)   # cukup lebar agar bisa dijangkau dari segala sisi (tabrakan menutupi badan)
	shape.shape = rect
	area.add_child(shape)
	add_child(area)
	area.body_entered.connect(func(b: Node2D) -> void: _set_range(b, true))
	area.body_exited.connect(func(b: Node2D) -> void: _set_range(b, false))
	_hint = Label.new()
	_hint.text = "E: Tempa Senjata"
	_hint.add_theme_font_override("font", FONT)
	_hint.add_theme_font_size_override("font_size", 8)
	_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_hint.add_theme_constant_override("outline_size", 3)
	_hint.position = Vector2(-32, -62)
	_hint.visible = false
	add_child(_hint)


func _set_range(body: Node2D, inside: bool) -> void:
	if body.is_in_group("player"):
		_player_in_range = inside
		_hint.visible = inside


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or QuestManager.quiz_active or get_tree().paused:
		return
	if event.is_action_pressed("interact"):
		var menu: Node = get_tree().get_first_node_in_group("trade_menu")
		if menu and menu.has_method("open_forge"):
			get_viewport().set_input_as_handled()
			menu.open_forge()
