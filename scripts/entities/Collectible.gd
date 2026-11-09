class_name Collectible
extends Area2D
## Collectible (base): diambil otomatis saat Raka menyentuh.
## item_id "gold" = tambah Gold; id lain masuk inventory. Turunan hanya mengganti export di scene.

signal collected(item_id: String, amount: int)

const COLLECTED_SHEET := preload("res://assets/items/Collected.png")
const COLLECTED_FRAMES := 6
const COLLECTED_SIZE := 32

@export var item_id: String = "gold"
@export var amount: int = 1
@export var sfx: String = "ambil_item"
## Gambar khusus (mis. Apple untuk Herb). Kosong = ikon dari ItemIcons.
@export var custom_texture: Texture2D

@onready var sprite: Sprite2D = $Sprite2D

var _taken: bool = false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # layer player
	body_entered.connect(_on_body_entered)
	sprite.texture = custom_texture if custom_texture else ItemIcons.get_icon(item_id)
	sprite.position = Vector2(0, -8)
	# Melayang pelan agar mudah terlihat
	var tw: Tween = create_tween().set_loops()
	tw.tween_property(sprite, "position:y", -10.0, 0.6).set_trans(Tween.TRANS_SINE)
	tw.tween_property(sprite, "position:y", -6.0, 0.6).set_trans(Tween.TRANS_SINE)


## Memunculkan item di posisi tertentu (dipakai Chest & musuh).
static func spawn(parent: Node, scene: PackedScene, id: String, count: int, pos: Vector2) -> Node:
	var c: Node = scene.instantiate()
	c.set("item_id", id)
	c.set("amount", count)
	if id == "gold":
		c.set("sfx", "ambil_gold")
	# Deferred: spawn sering dipanggil dari callback fisika (hitbox kena -> musuh mati -> loot),
	# saat itu Area2D baru tidak boleh ditambahkan langsung ("flushing queries").
	var p: Vector2 = pos
	parent.add_child.call_deferred(c)
	c.set_deferred("global_position", p)
	return c


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	if item_id == "gold":
		GameManager.add_gold(amount)
	else:
		GameManager.add_item(item_id, amount)
	AudioManager.play_sfx(sfx, 0.05)
	collected.emit(item_id, amount)
	_play_effect()


func _play_effect() -> void:
	set_deferred("monitoring", false)
	var fx: Sprite2D = Sprite2D.new()
	fx.texture = COLLECTED_SHEET
	fx.hframes = COLLECTED_FRAMES
	fx.position = Vector2(0, -8)
	add_child(fx)
	sprite.visible = false
	var tw: Tween = create_tween()
	tw.tween_method(func(f: float) -> void: fx.frame = clampi(int(f), 0, COLLECTED_FRAMES - 1),
		0.0, float(COLLECTED_FRAMES), 0.3)
	tw.tween_callback(queue_free)
