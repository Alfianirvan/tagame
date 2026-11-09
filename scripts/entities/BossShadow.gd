class_name BossShadow
extends CharacterBody2D
## Bayangan King Subiyan: simpul pohon biner (tree). Tiap bayangan non-daun memanggil 2 bayangan anak.
## Selama masih punya anak (atau belum memanggilnya), bayangan terlindung tameng dan kebal.
## Hanya DAUN (leaf = tanpa anak) yang bisa dilukai, jadi pohon dikalahkan dari daun ke akar.

signal died(shadow: BossShadow)

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const COLLECTIBLE_SCENE := preload("res://scenes/entities/Collectible.tscn")
const BODY_CENTER := Vector2(0, -14)

var depth: int = 1
var max_depth: int = 2
var hp: int = 25
var cfg: Dictionary = {}
var frames: SpriteFrames
var children_nodes: Array[BossShadow] = []

var _pending_children: bool = false     # masih akan memanggil anak (tameng sudah aktif)
var _dead: bool = false
var _shoot_left: float = 1.5
var _player: Node2D
var _sprite: AnimatedSprite2D
var _flash_tween: Tween


static func create(sprite_frames: SpriteFrames, shadow_cfg: Dictionary, node_depth: int, depth_max: int) -> BossShadow:
	var s: BossShadow = BossShadow.new()
	s.frames = sprite_frames
	s.cfg = shadow_cfg
	s.depth = node_depth
	s.max_depth = depth_max
	s.hp = int(shadow_cfg.get("hp", 25))
	return s


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING  # top-down
	add_to_group("boss_shadow")
	collision_layer = 4     # enemy: dikenali hitbox player
	collision_mask = 1      # hanya dinding (tidak mendorong player)
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 8.0
	shape.shape = circle
	shape.position = BODY_CENTER
	add_child(shape)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = frames
	var offsets: Dictionary = frames.get_meta("offsets", {})
	_sprite.offset = offsets.get("idle", Vector2.ZERO)
	_sprite.scale = Vector2.ONE * float(cfg.get("scale", 0.75))
	_sprite.self_modulate = Color(0.55, 0.35, 0.9, 0.85)
	add_child(_sprite)
	_sprite.play("idle")
	# Muncul perlahan
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.4)
	_shoot_left = float(cfg.get("shoot_interval", 2.4)) * 0.6
	if depth < max_depth:
		_pending_children = true
		get_tree().create_timer(float(cfg.get("summon_delay", 1.4))).timeout.connect(_spawn_children)


func is_shielded() -> bool:
	return _pending_children or not children_nodes.is_empty()


func is_leaf() -> bool:
	return not is_shielded()


# ---------------------------------------------------------------- Memanggil anak (2 per bayangan)

func _spawn_children() -> void:
	if _dead or not is_inside_tree():
		return
	_pending_children = false
	for i in 2:
		var child: BossShadow = BossShadow.create(frames, cfg, depth + 1, max_depth)
		get_parent().add_child(child)
		child.global_position = global_position + Vector2(-30.0 if i == 0 else 30.0, 22.0)
		child.died.connect(_on_child_died)
		children_nodes.append(child)
	AudioManager.play_sfx("sihir", 0.1)
	queue_redraw()


func _on_child_died(child: BossShadow) -> void:
	children_nodes.erase(child)
	queue_redraw()


# ---------------------------------------------------------------- Perilaku

func _physics_process(delta: float) -> void:
	if _dead:
		return
	queue_redraw()   # garis ke anak mengikuti gerak
	if not is_leaf():
		velocity = Vector2.ZERO
		return
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	if _player == null:
		return
	var to_player: Vector2 = _player.global_position - global_position
	var speed: float = float(cfg.get("speed", 28))
	# Daun menjaga jarak menengah lalu menembak.
	if to_player.length() > 100.0:
		velocity = to_player.normalized() * speed
	elif to_player.length() < 60.0:
		velocity = -to_player.normalized() * speed
	else:
		velocity = Vector2.ZERO
	_sprite.flip_h = to_player.x < 0.0
	move_and_slide()
	_shoot_left -= delta
	if _shoot_left <= 0.0:
		_shoot_left = float(cfg.get("shoot_interval", 2.4))
		Projectile.launch(get_parent(), global_position + BODY_CENTER, to_player + Vector2(0, -14), int(cfg.get("shot_damage", 7)),
			false, float(cfg.get("shot_speed", 95)), Color(0.7, 0.4, 1.0), 3.0)


# ---------------------------------------------------------------- Terkena serangan

func take_hit(damage: int, _from_pos: Vector2) -> void:
	if _dead:
		return
	if is_shielded():
		DamagePopup.spawn(get_parent(), global_position + Vector2(0, -38), 0, Color(0.7, 0.7, 0.7))
		AudioManager.play_sfx("kuis_salah", 0.05)
		return
	hp = maxi(0, hp - damage)
	DamagePopup.spawn(get_parent(), global_position + Vector2(0, -38), damage)
	AudioManager.play_sfx("kena_hit2", 0.1)
	if _flash_tween:
		_flash_tween.kill()
	_sprite.modulate = Color(1.0, 0.4, 0.4)
	_flash_tween = create_tween()
	_flash_tween.tween_property(_sprite, "modulate", Color.WHITE, 0.15)
	if hp <= 0:
		_die()


func _die() -> void:
	_dead = true
	set_deferred("collision_layer", 0)
	var amount: int = randi_range(int(cfg.get("gold_min", 6)), int(cfg.get("gold_max", 12)))
	Collectible.spawn(get_parent(), COLLECTIBLE_SCENE, "gold", amount, global_position + Vector2(0, 4))
	AudioManager.play_sfx("ledakan", 0.15)
	died.emit(self)
	var tw: Tween = create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.25)
	tw.tween_callback(queue_free)


# ---------------------------------------------------------------- Gambar: tameng, label, garis ke anak

func _draw() -> void:
	if _dead:
		return
	for child in children_nodes:
		if is_instance_valid(child):
			draw_line(BODY_CENTER, child.global_position - global_position + BODY_CENTER, Color(0.7, 0.5, 1.0, 0.8), 2.0)
	var leaf: bool = is_leaf()
	if not leaf:
		draw_arc(BODY_CENTER, 15.0, 0.0, TAU, 24, Color(0.5, 0.9, 1.0, 0.8), 2.0, false)
	var label: String = "DAUN" if leaf else "NODE"
	var color: Color = Color(1, 0.9, 0.2) if leaf else Color(0.6, 0.9, 1.0)
	draw_string(FONT, Vector2(-9, -42), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 7, color)
