extends StaticBody2D
## Chest: peti berisi item acak. Tekan E di dekatnya untuk membuka. Isi dari data/chest_loot.json.
## Bisa juga isi tetap lewat export fixed_loot (mis. {"potion": 2, "gold": 50}).

signal opened

const COLLECTIBLE_SCENE := preload("res://scenes/entities/Collectible.tscn")

@export var fixed_loot: Dictionary = {}
@export var roll_count: int = 2
## Id unik agar peti yang sudah dibuka tidak terisi lagi (kosong = selalu bisa dibuka sekali per scene).
@export var chest_id: String = ""

@onready var closed_sprite: Sprite2D = $Closed
@onready var open_sprite: Sprite2D = $Open
@onready var interact_area: Area2D = $InteractArea
@onready var hint: Label = $Hint

var is_open: bool = false
var _player_in_range: bool = false
var _table: Array = []


func _ready() -> void:
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "chest_loot.json")
	if data is Dictionary:
		_table = data.get("tabel", [])
	interact_area.body_entered.connect(func(b: Node2D) -> void: _set_range(b, true))
	interact_area.body_exited.connect(func(b: Node2D) -> void: _set_range(b, false))
	hint.visible = false
	_set_visual(false)


func _set_range(body: Node2D, inside: bool) -> void:
	if body.is_in_group("player"):
		_player_in_range = inside
		hint.visible = inside and not is_open


func _set_visual(opened: bool) -> void:
	closed_sprite.visible = not opened
	open_sprite.visible = opened


func _unhandled_input(event: InputEvent) -> void:
	if is_open or not _player_in_range or DialogManager.is_active:
		return
	if event.is_action_pressed("interact"):
		open()
		get_viewport().set_input_as_handled()


func open() -> void:
	if is_open:
		return
	is_open = true
	hint.visible = false
	_set_visual(true)
	AudioManager.play_sfx("ambil_item")
	var loot: Dictionary = (fixed_loot if not fixed_loot.is_empty() else _roll_loot()).duplicate()
	# Setiap peti juga menjatuhkan kertas catatan materi chapter yang sedang dijalani.
	var note_id: String = "catatan_%d" % GameManager.current_chapter
	if GameManager.get_item(note_id).size() > 0:
		loot[note_id] = 1
	var i: int = 0
	for id: String in loot:
		# Item muncul menyebar di depan peti
		var pos: Vector2 = global_position + Vector2((i - (loot.size() - 1) / 2.0) * 18.0, 14.0)
		Collectible.spawn(get_parent(), COLLECTIBLE_SCENE, id, int(loot[id]), pos)
		i += 1
	opened.emit()


## Mengundi isi peti dari tabel berbobot.
func _roll_loot() -> Dictionary:
	var loot: Dictionary = {}
	var total: int = 0
	for e: Dictionary in _table:
		total += int(e.get("bobot", 1))
	for _n in roll_count:
		var r: int = randi_range(1, maxi(total, 1))
		for e: Dictionary in _table:
			r -= int(e.get("bobot", 1))
			if r <= 0:
				var amt: int = randi_range(int(e.get("min", 1)), int(e.get("max", 1)))
				loot[e["item"]] = int(loot.get(e["item"], 0)) + amt
				break
	return loot
