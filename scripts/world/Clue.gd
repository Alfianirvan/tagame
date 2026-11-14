class_name Clue
extends Area2D
## Petunjuk berkilau di pinggiran desa (Quest Awal: "cari petunjuk"). Tekan E di dekatnya -> dialog petunjuk
## diputar -> flag cerita disetel (QuestManager menghitung progres langkah). Baru tampak setelah langkah
## quest `required_step` terbuka, dan hilang setelah diperiksa.

const SPARK := preload("res://assets/ninja/fx/Magic/Spark/SpriteSheet.png")

@export var flag: String = ""
@export var dialog_id: String = ""
## "quest_id:step_id" yang harus sudah terbuka agar petunjuk tampak (kosong = selalu).
@export var required_step: String = ""
## Wujud petunjuk: jejak (jejak kaki), catatan (kertas sobek), barang (kantong benih tercecer).
@export_enum("jejak", "catatan", "barang") var clue_kind: String = "jejak"

var _player_in_range: bool = false
var _hint: Label
var _t: float = 0.0


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2   # player
	var shape: CollisionShape2D = CollisionShape2D.new()
	var c: CircleShape2D = CircleShape2D.new()
	c.radius = 26.0
	shape.shape = c
	add_child(shape)
	_hint = FxUtil.small_label("E: Periksa")
	_hint.size = Vector2(80, 12)
	_hint.position = Vector2(-40, -34)
	_hint.visible = false
	add_child(_hint)
	body_entered.connect(func(b: Node2D) -> void:
		if b.is_in_group("player"):
			_player_in_range = true
			_update_hint())
	body_exited.connect(func(b: Node2D) -> void:
		if b.is_in_group("player"):
			_player_in_range = false
			_update_hint())
	DialogManager.dialog_ended.connect(_on_dialog_ended)
	QuestManager.quests_changed.connect(_refresh)
	_refresh()


func _is_shown() -> bool:
	if GameManager.has_story_flag(flag):
		return false
	if required_step == "":
		return true
	return QuestManager.is_step_unlocked(required_step.get_slice(":", 0), required_step.get_slice(":", 1))


func _refresh() -> void:
	var shown: bool = _is_shown()
	visible = shown
	monitoring = shown
	set_process(shown)
	if not shown:
		_player_in_range = false
	_update_hint()


func _update_hint() -> void:
	_hint.visible = _player_in_range and visible and not DialogManager.is_active


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or not visible or DialogManager.is_active or not event.is_action_pressed("interact"):
		return
	if DialogManager.start_dialog(dialog_id):
		get_viewport().set_input_as_handled()
		_update_hint()


func _on_dialog_ended(finished_id: String) -> void:
	if finished_id != dialog_id or not visible:
		_update_hint()
		return
	FxUtil.burst(get_parent(), global_position + Vector2(0, -8), SPARK, 30, 35, 16.0, Color(1, 0.95, 0.6))
	AudioManager.play_sfx("ambil_item")
	GameManager.set_story_flag(flag)   # -> quests_changed -> _refresh menyembunyikan petunjuk


func _draw() -> void:
	match clue_kind:
		"jejak":   # jejak kaki goblin (tiga pasang)
			for i in 3:
				var o: Vector2 = Vector2(-10 + i * 9, 2 - i * 5)
				draw_circle(o, 2.6, Color(0.25, 0.17, 0.1, 0.85))
				draw_circle(o + Vector2(4, -2), 2.6, Color(0.25, 0.17, 0.1, 0.85))
		"catatan":   # kertas sobek
			draw_colored_polygon(PackedVector2Array([Vector2(-7, -6), Vector2(6, -7), Vector2(8, 3), Vector2(2, 2), Vector2(-6, 5)]), Color(0.95, 0.92, 0.8))
			draw_line(Vector2(-4, -3), Vector2(4, -4), Color(0.4, 0.3, 0.25), 1.0)
			draw_line(Vector2(-4, 0), Vector2(3, -1), Color(0.4, 0.3, 0.25), 1.0)
		_:   # kantong benih tercecer
			draw_circle(Vector2(0, -3), 5.0, Color(0.7, 0.52, 0.3))
			draw_rect(Rect2(-2, -10, 4, 3), Color(0.55, 0.38, 0.2))
			for k in 4:
				draw_circle(Vector2(6 + k * 2.5, 1 - (k % 2) * 2), 1.0, Color(0.9, 0.8, 0.35))
	# kilau berdenyut di atas petunjuk
	var a: float = 0.55 + 0.45 * sin(_t * 5.0)
	var p: Vector2 = Vector2(2, -16 - 2.0 * sin(_t * 2.5))
	var r: float = 3.0 + a * 2.0
	draw_colored_polygon(PackedVector2Array([p + Vector2(0, -r), p + Vector2(r * 0.35, 0), p + Vector2(0, r), p + Vector2(-r * 0.35, 0)]), Color(1, 0.95, 0.5, a))
	draw_colored_polygon(PackedVector2Array([p + Vector2(-r, 0), p + Vector2(0, r * 0.35), p + Vector2(r, 0), p + Vector2(0, -r * 0.35)]), Color(1, 0.95, 0.5, a))
