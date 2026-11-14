class_name Altar
extends Area2D
## Altar segel di tengah Desa 4 (Ch1). Setelah Golem kalah dan Kristal Array diambil, Raka menekan E di sini:
## dialog `dialog_id` diputar, lalu flag `flag` disetel -> kubah segel & tanah terkutuk memudar (SealDome),
## Tetua Desa 4 muncul (NPC.hidden_until_flag) dan Quest Akhir bisa diserahkan kepadanya.

@export var chapter: int = 1
@export var flag: String = "ch1_segel_pudar"
@export var dialog_id: String = "ch1_altar"

var _player_in_range: bool = false
var _hint: Label
var _t: float = 0.0


func _ready() -> void:
	add_to_group("altar")
	collision_layer = 0
	collision_mask = 2
	var shape: CollisionShape2D = CollisionShape2D.new()
	var c: CircleShape2D = CircleShape2D.new()
	c.radius = 28.0
	shape.shape = c
	shape.position = Vector2(0, 6)
	add_child(shape)
	_hint = FxUtil.small_label("")
	_hint.size = Vector2(160, 12)
	_hint.position = Vector2(-80, -52)
	_hint.visible = false
	add_child(_hint)
	z_index = 1
	body_entered.connect(func(b: Node2D) -> void:
		if b.is_in_group("player"):
			_player_in_range = true
			_update_hint())
	body_exited.connect(func(b: Node2D) -> void:
		if b.is_in_group("player"):
			_player_in_range = false
			_update_hint())
	DialogManager.dialog_ended.connect(_on_dialog_ended)
	GameManager.story_flag_set.connect(func(_f: String) -> void: queue_redraw())


func _process(delta: float) -> void:
	_t += delta
	if GameManager.has_story_flag(flag):
		queue_redraw()


func _update_hint() -> void:
	if not _player_in_range or GameManager.has_story_flag(flag) or DialogManager.is_active:
		_hint.visible = false
		return
	_hint.text = "E: Letakkan Kristal Array" if GameManager.has_crystal(chapter) else "Altar segel. Butuh Kristal Array."
	_hint.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or not event.is_action_pressed("interact"):
		return
	if GameManager.has_story_flag(flag) or not GameManager.has_crystal(chapter):
		return
	if DialogManager.start_dialog(dialog_id):
		get_viewport().set_input_as_handled()
		_update_hint()


func _on_dialog_ended(finished_id: String) -> void:
	if finished_id == dialog_id and GameManager.has_crystal(chapter) and not GameManager.has_story_flag(flag):
		AudioManager.play_sfx("power_up")
		GameManager.set_story_flag(flag)
	_update_hint()


## Kristal Array melayang di atas altar setelah diletakkan.
func _draw() -> void:
	if not GameManager.has_story_flag(flag):
		return
	var y: float = -34.0 + sin(_t * 2.0) * 2.0
	var pts: PackedVector2Array = PackedVector2Array([Vector2(0, y - 8), Vector2(5, y), Vector2(0, y + 8), Vector2(-5, y)])
	draw_circle(Vector2(0, y), 9.0, Color(0.5, 0.8, 1, 0.25 + 0.1 * sin(_t * 4.0)))
	draw_colored_polygon(pts, Color(0.55, 0.85, 1))
	draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.9, 1, 1), 1.0)
