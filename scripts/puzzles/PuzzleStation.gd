class_name PuzzleStation
extends Area2D
## Titik di dunia yang membuka puzzle Quest Tengah saat Raka menekan E di dekatnya (dipasang di wilayah, Tahap 10).
## Puzzle baru bisa dibuka setelah Quest Awal chapter itu selesai. Setelah puzzle beres, hadiahnya
## diberikan PuzzleBase lewat QuestManager; stasiun tetap bisa dibuka lagi untuk latihan (tanpa hadiah).

signal puzzle_solved

@export var puzzle_scene: PackedScene
@export var chapter: int = 1
@export var station_label: String = "Puzzle"

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const REOPEN_GUARD_MSEC := 300

var _puzzle: PuzzleBase
var _player_in_range: bool = false
var _hint: Label
var _closed_msec: int = -10000


func _ready() -> void:
	add_to_group("puzzle_station")
	collision_layer = 0
	collision_mask = 2   # player
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 30.0
	shape.shape = circle
	add_child(shape)
	_hint = Label.new()
	_hint.add_theme_font_override("font", FONT)
	_hint.add_theme_font_size_override("font_size", 8)
	_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_hint.add_theme_constant_override("outline_size", 3)
	_hint.position = Vector2(-40, -44)
	_hint.visible = false
	add_child(_hint)
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	z_index = 1


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = true
		_update_hint()


func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = false
		_hint.visible = false


func _update_hint() -> void:
	var reason: String = _block_reason()
	_hint.text = "E: %s" % station_label if reason == "" else reason
	_hint.visible = _player_in_range and not (_puzzle != null and _puzzle.is_open())


func _block_reason() -> String:
	if GameManager.get_quest_stage(chapter) < 1:
		return "Selesaikan Quest Awal dulu"
	return ""


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or not event.is_action_pressed("interact"):
		return
	if DialogManager.is_active or QuestManager.quiz_active or (_puzzle != null and _puzzle.is_open()):
		return
	if Time.get_ticks_msec() - _closed_msec < REOPEN_GUARD_MSEC:
		return
	if _block_reason() != "":
		_update_hint()
		return
	_open()
	get_viewport().set_input_as_handled()


func _open() -> void:
	if puzzle_scene == null:
		push_warning("PuzzleStation: puzzle_scene belum diisi")
		return
	if _puzzle == null:
		_puzzle = puzzle_scene.instantiate() as PuzzleBase
		_puzzle.chapter = chapter
		_puzzle.solved.connect(func() -> void: puzzle_solved.emit())
		_puzzle.closed.connect(_on_puzzle_closed)
		add_child(_puzzle)
	_hint.visible = false
	_puzzle.open_puzzle()


func _on_puzzle_closed() -> void:
	_closed_msec = Time.get_ticks_msec()
	_update_hint()


## Papan puzzle sederhana (dapat diganti sprite saat dipasang di wilayah).
func _draw() -> void:
	draw_rect(Rect2(-9, -22, 18, 14), Color(0.55, 0.38, 0.22))
	draw_rect(Rect2(-9, -22, 18, 14), Color(0.3, 0.18, 0.1), false, 1.0)
	draw_rect(Rect2(-2, -8, 4, 8), Color(0.4, 0.27, 0.15))
	draw_string(FONT, Vector2(-3, -11), "?", HORIZONTAL_ALIGNMENT_CENTER, 6, 9, Color(1, 0.95, 0.6))
