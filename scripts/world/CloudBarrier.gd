class_name CloudBarrier
extends Node2D
## Awan tebal ber-collision (batas wilayah / gerbang quest). Awan = Clouds.png bertumpuk (skala 2-3, sedikit melayang);
## collision ada di anak "Block" (TileMapLayer, tile tak terlihat). Saat syarat terpenuhi awan memudar
## dan collision dimatikan (bersamaan dengan fog of war di Peta Dunia untuk batas chapter).

signal opened

const CLOUD := preload("res://assets/ninja/fx/Particle/Clouds.png")

## "chapter" = terbuka saat chapter berikutnya terbuka (Quest Akhir selesai); "stage" = quest_stage chapter >= required_stage;
## "flag" = flag cerita `required_flag` sudah disetel (mis. langkah quest "lapor ke Arman").
@export_enum("chapter", "stage", "flag") var mode: String = "chapter"
@export var chapter: int = 1
@export var required_stage: int = 1
@export var required_flag: String = ""
## Titik pusat awan (koordinat lokal). Diisi generator scene.
@export var cloud_points: PackedVector2Array = PackedVector2Array()
@export var seed_value: int = 7
@export var locked_text: String = ""
## Warna awan (putih = awan biasa; ungu/kelabu untuk kabut desa).
@export var tint: Color = Color.WHITE
@export var scale_min: float = 2.0
@export var scale_max: float = 3.0

var is_open: bool = false
var _visual: Node2D


func _ready() -> void:
	z_index = 3
	_visual = Node2D.new()
	add_child(_visual)
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = seed_value
	for i in cloud_points.size():
		var p: Vector2 = cloud_points[i]
		var c: Sprite2D = Sprite2D.new()
		c.texture = CLOUD
		c.position = p + Vector2(rng.randf_range(-10, 10), rng.randf_range(-8, 8))
		c.scale = Vector2.ONE * rng.randf_range(scale_min, scale_max)
		c.modulate = Color(tint.r, tint.g, tint.b, rng.randf_range(0.88, 1.0))
		_visual.add_child(c)
		# melayang pelan
		var tw: Tween = create_tween().set_loops()
		var dx: float = rng.randf_range(3.0, 7.0)
		tw.tween_property(c, "position:x", c.position.x + dx, rng.randf_range(2.5, 4.5)).set_trans(Tween.TRANS_SINE)
		tw.tween_property(c, "position:x", c.position.x - dx, rng.randf_range(2.5, 4.5)).set_trans(Tween.TRANS_SINE)
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _refresh(true))
	GameManager.chapter_unlocked.connect(func(_c: int) -> void: _refresh(true))
	GameManager.crystal_collected.connect(func(_c: int) -> void: _refresh(true))
	GameManager.story_flag_set.connect(func(_f: String) -> void: _refresh(true))
	_refresh(false)
	# area peringatan: teks singkat bila Raka mendekat dan masih tertutup
	if locked_text != "":
		_make_hint_area()


func _condition() -> bool:
	if mode == "stage":
		return GameManager.get_quest_stage(chapter) >= required_stage
	if mode == "flag":
		return GameManager.has_story_flag(required_flag) or GameManager.get_quest_stage(chapter) >= required_stage
	return GameManager.unlocked_chapter > chapter


func _refresh(animate: bool) -> void:
	if is_open or not _condition():
		return
	is_open = true
	var block: TileMapLayer = get_node_or_null("Block") as TileMapLayer
	if block:
		block.set_deferred("collision_enabled", false)
	if animate:
		var tw: Tween = create_tween()
		tw.tween_property(_visual, "modulate:a", 0.0, 2.0)
		tw.tween_callback(func() -> void: _visual.visible = false)
	else:
		_visual.visible = false
	opened.emit()


func _make_hint_area() -> void:
	var a: Area2D = Area2D.new()
	a.collision_layer = 0
	a.collision_mask = 2
	a.monitoring = true
	var rect: Rect2 = Rect2(cloud_points[0], Vector2.ZERO)
	for p in cloud_points:
		rect = rect.expand(p)
	rect = rect.grow(70.0)
	var shape: CollisionShape2D = CollisionShape2D.new()
	var rs: RectangleShape2D = RectangleShape2D.new()
	rs.size = rect.size
	shape.shape = rs
	shape.position = rect.get_center()
	a.add_child(shape)
	add_child(a)
	var last: float = -100.0
	a.body_entered.connect(func(b: Node2D) -> void:
		if is_open or not b.is_in_group("player"):
			return
		var now: float = Time.get_ticks_msec() / 1000.0
		if now - last < 4.0:
			return
		last = now
		FloatingText.spawn(get_parent(), b.global_position + Vector2(0, -40), locked_text, Color(1, 0.8, 0.6), 2.4))
