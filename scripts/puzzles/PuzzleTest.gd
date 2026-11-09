extends Node
## Scene tes puzzle: membuka satu puzzle dalam mode uji (tidak mengubah quest/save).
## Tombol: R = buka/ulang puzzle. Puzzle dikendalikan dengan mouse (dan A/D untuk labirin Tree).

@export var puzzle_scene: PackedScene

var _puzzle: PuzzleBase
var _status: Label


func _ready() -> void:
	var bg: ColorRect = ColorRect.new()
	bg.color = Color(0.25, 0.4, 0.25)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var hint_layer: CanvasLayer = CanvasLayer.new()
	hint_layer.layer = 5
	add_child(hint_layer)
	_status = PuzzleBase.make_label("", 12, Color.WHITE)
	_status.position = Vector2(8, 336)
	hint_layer.add_child(_status)
	_puzzle = puzzle_scene.instantiate() as PuzzleBase
	_puzzle.test_mode = true
	_puzzle.solved.connect(func() -> void: _status.text = "SELESAI (mode uji, quest tidak diubah). R: ulang")
	_puzzle.closed.connect(func() -> void: _status.text = "Ditutup. R: buka lagi")
	add_child(_puzzle)
	_open()


func _open() -> void:
	_status.text = "Mode uji. Esc: tutup   R: ulang"
	_puzzle.open_puzzle()


func _unhandled_key_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_R:
		_open()
