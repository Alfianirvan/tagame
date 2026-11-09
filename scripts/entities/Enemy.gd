class_name Enemy
extends CharacterBody2D
## Musuh biasa (Orc/Skeleton). Satu script untuk 8 jenis; perbedaan stat ada di data/enemies.json.
##
## Alur AI: IDLE -> (player terdeteksi) CHASE -> WINDUP (tanda merah di lantai) -> ATTACK
## (menerjang / menembak) -> RECOVER -> CHASE. Terkena serangan = HIT sesaat (knockback).
## Konvensi tabrakan: badan di layer 3 (enemy); area serangan di layer 5 membawa meta "damage".
## Player memanggil take_hit(damage, from_pos) lewat hitbox/proyektilnya.

signal died(enemy: Enemy)
signal damaged(hp: int, max_hp: int)

enum State { IDLE, CHASE, WINDUP, ATTACK, RECOVER, HIT, DEAD }

const DB_PATH := "res://data/enemies.json"
const COLLECTIBLE_SCENE := preload("res://scenes/entities/Collectible.tscn")
const BODY_CENTER := Vector2(0, -14)

## Jenis musuh: kunci di data/enemies.json (orc, orc_rogue, skeleton_mage, dst).
@export var enemy_id: String = "orc"
## Pengali damage serangan musuh ini (1.0 = sesuai enemies.json). Dipakai untuk menyetel kesulitan per wilayah.
@export var damage_scale: float = 1.0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var attack_area: Area2D = $AttackArea
@onready var attack_shape: CollisionShape2D = $AttackArea/CollisionShape2D
@onready var health_bar: Node2D = $HealthBar

static var _db: Dictionary = {}

var cfg: Dictionary = {}
var hp: int = 1
var max_hp: int = 1
var state: State = State.IDLE

var _player: Node2D
var _melee_hit_done: bool = false   # serangan jarak dekat ini sudah mengenai Raka
var _state_left: float = 0.0           # sisa waktu state sementara (windup/attack/recover/hit)
var _attack_dir: Vector2 = Vector2.RIGHT
var _knock_vec: Vector2 = Vector2.ZERO
var _flash_tween: Tween
var _persist_key: String = ""   # kunci untuk mencatat musuh ini sudah mati


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING  # top-down
	# Musuh yang sudah dibunuh sebelumnya (tersimpan di save) tidak muncul lagi.
	_persist_key = GameManager.enemy_key(self)
	if GameManager.is_enemy_killed(_persist_key):
		queue_free()
		return
	add_to_group("enemy")
	cfg = _get_config(enemy_id)
	if cfg.is_empty():
		push_warning("Jenis musuh tidak dikenal: %s" % enemy_id)
		queue_free()
		return
	if not is_equal_approx(damage_scale, 1.0):
		cfg = cfg.duplicate()   # jangan ubah data bersama milik musuh lain
		cfg["damage"] = maxi(1, roundi(float(cfg.get("damage", 5)) * damage_scale))
	max_hp = int(cfg.get("hp", 20))
	hp = max_hp
	sprite.sprite_frames = EnemySprites.build(cfg["sprite"], int(cfg.get("death_frames", 6)))
	sprite.offset = BODY_CENTER
	sprite.animation_finished.connect(_on_animation_finished)
	attack_area.collision_layer = 16   # layer 5
	attack_area.collision_mask = 0
	attack_area.set_meta("damage", int(cfg.get("damage", 5)))
	_set_attack_active(false)
	health_bar.position = Vector2(0, -36)
	health_bar.set_ratio(1.0)
	sprite.play("idle")


static func _get_config(id: String) -> Dictionary:
	if _db.is_empty():
		var data: Variant = GameManager.load_json(DB_PATH)
		if data is Dictionary:
			_db = data
	return _db.get(id, {})


func is_ranged() -> bool:
	return bool(cfg.get("ranged", false))


# ---------------------------------------------------------------- Loop utama

func _physics_process(delta: float) -> void:
	match state:
		State.IDLE:
			velocity = Vector2.ZERO
			if _player_in_range(float(cfg["detect_range"])):
				_set_state(State.CHASE)
		State.CHASE:
			_process_chase()
		State.WINDUP:
			velocity = Vector2.ZERO
			_state_left -= delta
			if _state_left <= 0.0:
				_begin_attack()
		State.ATTACK:
			_state_left -= delta
			_check_melee_hit()
			if _state_left <= 0.0:
				_end_attack()
		State.RECOVER:
			velocity = Vector2.ZERO
			_state_left -= delta
			if _state_left <= 0.0:
				_set_state(State.CHASE)
		State.HIT:
			_state_left -= delta
			velocity = _knock_vec * 120.0 * float(cfg.get("knockback", 1.0)) if _state_left > 0.0 else Vector2.ZERO
			if _state_left <= 0.0:
				_set_state(State.CHASE)
		State.DEAD:
			velocity = Vector2.ZERO
	move_and_slide()


func _process_chase() -> void:
	if not _target_valid():
		_set_state(State.IDLE)
		return
	var to_player: Vector2 = _player.global_position - global_position
	var dist: float = to_player.length()
	if dist > float(cfg["detect_range"]) * 1.8:
		_set_state(State.IDLE)
		return
	_face(to_player)
	var reach: float = float(cfg["attack_range"])
	var speed: float = float(cfg["speed"])
	if is_ranged():
		# Jaga jarak: mendekat bila jauh, mundur bila terlalu dekat, tembak saat dalam jangkauan.
		if dist <= reach:
			if dist < reach * 0.45:
				velocity = -to_player.normalized() * speed
			else:
				velocity = Vector2.ZERO
			_play_move()
			_start_windup(to_player)
			return
	elif dist <= reach:
		_start_windup(to_player)
		return
	velocity = to_player.normalized() * speed
	_play_move()


## Memainkan animasi serang (windup/strike) selama duration detik. Tanpa sheet serang (musuh jarak jauh)
## dipakai animasi lama: idle saat bersiap, lari saat menerjang.
func _play_attack_anim(anim: String, duration: float) -> void:
	if sprite.sprite_frames.has_animation(anim):
		sprite.speed_scale = 1.0 / maxf(duration, 0.05)   # animasi 3 frame @ 3 fps = 1 detik
		sprite.play(anim)
	else:
		sprite.speed_scale = 1.0
		sprite.play("idle" if anim == "windup" else "run")


func _play_move() -> void:
	sprite.speed_scale = 1.0
	var anim: String = "run" if velocity != Vector2.ZERO else "idle"
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)


func _face(dir: Vector2) -> void:
	if absf(dir.x) > 1.0:
		sprite.flip_h = dir.x < 0.0


# ---------------------------------------------------------------- Serangan

## Mulai membidik: arah dikunci, tanda merah muncul di lantai.
func _start_windup(to_player: Vector2) -> void:
	_attack_dir = to_player.normalized()
	velocity = Vector2.ZERO
	_set_state(State.WINDUP)
	_state_left = float(cfg.get("windup", 0.5))
	_play_attack_anim("windup", _state_left)
	_flash(Color(1.0, 0.45, 0.45), _state_left)
	queue_redraw()


func _begin_attack() -> void:
	queue_redraw()
	if is_ranged():
		_play_attack_anim("strike", 0.3)   # tongkat dihentakkan ke depan saat sihir dilepas
		Projectile.launch(get_parent(), global_position + BODY_CENTER, _attack_dir, int(cfg["damage"]), false,
			float(cfg.get("projectile_speed", 110)), Color(String(cfg.get("projectile_color", "#ff8040"))), 3.0)
		AudioManager.play_sfx("sihir", 0.1)
		_set_state(State.RECOVER)
		_state_left = float(cfg.get("recover", 1.0))
		return
	# Melee: menerjang lurus sambil mengaktifkan area serangan.
	_melee_hit_done = false
	_set_state(State.ATTACK)
	_state_left = float(cfg["lunge_time"])
	velocity = _attack_dir * (float(cfg["lunge_distance"]) / float(cfg["lunge_time"]))
	attack_shape.position = BODY_CENTER + _attack_dir * 12.0
	_set_attack_active(true)
	AudioManager.play_sfx("serang_tebas2", 0.1)
	_play_attack_anim("strike", maxf(float(cfg["lunge_time"]), 0.25))


## Serangan jarak dekat memukul Raka bila area serang menjangkau badannya. Dicek langsung selama fase serang
## (satu kali per serangan) karena sinyal area_entered sering tidak terpicu saat Raka sudah menempel.
func _check_melee_hit() -> void:
	if _melee_hit_done or is_ranged() or not _target_valid():
		return
	var shape: CircleShape2D = attack_shape.shape as CircleShape2D
	var reach: float = (shape.radius if shape else 12.0) + 10.0
	var target: Vector2 = _player.global_position + Vector2(0, -17)
	if attack_shape.global_position.distance_to(target) <= reach and _player.has_method("take_hit"):
		_melee_hit_done = true
		_player.take_hit(int(cfg["damage"]), global_position)


func _end_attack() -> void:
	sprite.speed_scale = 1.0
	_set_attack_active(false)
	velocity = Vector2.ZERO
	_set_state(State.RECOVER)
	_state_left = float(cfg.get("recover", 0.7))
	sprite.play("idle")


func _set_attack_active(active: bool) -> void:
	attack_area.set_deferred("monitorable", active)


## Tanda merah peringatan di lantai (melee: lingkaran di depan; jarak jauh: garis bidik).
func _draw() -> void:
	if state != State.WINDUP:
		return
	var red: Color = Color(1, 0.1, 0.1, 0.35)
	if is_ranged():
		draw_line(BODY_CENTER, BODY_CENTER + _attack_dir * float(cfg["attack_range"]) * 1.2, red, 2.0)
	else:
		var target: Vector2 = BODY_CENTER + _attack_dir * float(cfg["lunge_distance"]) * 0.7
		draw_circle(target, 14.0, red)
		draw_line(BODY_CENTER, target, red, 3.0)


# ---------------------------------------------------------------- Terkena serangan

## Dipanggil hitbox/proyektil player.
func take_hit(damage: int, from_pos: Vector2) -> void:
	if state == State.DEAD:
		return
	hp = maxi(0, hp - damage)
	damaged.emit(hp, max_hp)
	health_bar.set_ratio(float(hp) / float(max_hp))
	DamagePopup.spawn(get_parent(), global_position + Vector2(0, -34), damage)
	AudioManager.play_sfx("kena_hit2", 0.1)
	if hp <= 0:
		_die()
		return
	if state == State.ATTACK:
		return  # sedang menerjang: tidak terganggu
	_set_attack_active(false)
	_knock_vec = (global_position - from_pos).normalized()
	_set_state(State.HIT)
	_state_left = 0.22
	_flash(Color(1.0, 0.35, 0.35), 0.15)
	queue_redraw()
	sprite.speed_scale = 1.0   # keluar dari animasi bersiap yang diperlambat
	sprite.play("idle")


func _flash(color: Color, duration: float) -> void:
	if _flash_tween:
		_flash_tween.kill()
	sprite.modulate = color
	_flash_tween = create_tween()
	_flash_tween.tween_property(sprite, "modulate", Color.WHITE, duration)


# ---------------------------------------------------------------- Mati

func _die() -> void:
	_set_state(State.DEAD)
	_set_attack_active(false)
	set_deferred("collision_layer", 0)
	set_deferred("collision_mask", 0)
	health_bar.visible = false
	queue_redraw()
	_drop_loot()
	GameManager.add_xp(int(cfg.get("xp", 0)))
	GameManager.mark_enemy_killed(_persist_key)
	GameManager.enemy_killed.emit(enemy_id)
	AudioManager.play_sfx("ledakan", 0.15)
	sprite.speed_scale = 1.0
	sprite.play("death")
	died.emit(self)


## Mengundi drop dari data (setiap entri punya peluang sendiri).
func _drop_loot() -> void:
	var drops: Array = cfg.get("drops", [])
	var parent: Node = get_parent()
	var i: int = 0
	for entry: Dictionary in drops:
		if randf() > float(entry.get("chance", 1.0)):
			continue
		var amount: int = randi_range(int(entry.get("min", 1)), int(entry.get("max", 1)))
		var offset: Vector2 = Vector2(randf_range(-12, 12), randf_range(-4, 10))
		Collectible.spawn(parent, COLLECTIBLE_SCENE, String(entry["item"]), amount, global_position + offset)
		i += 1


func _on_animation_finished() -> void:
	if state != State.DEAD:
		return
	var tw: Tween = create_tween()
	tw.tween_property(sprite, "modulate:a", 0.0, 0.5).set_delay(0.4)
	tw.tween_callback(queue_free)


# ---------------------------------------------------------------- Bantuan

func _set_state(new_state: State) -> void:
	state = new_state


func _target_valid() -> bool:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	return _player != null and GameManager.hp > 0


func _player_in_range(radius: float) -> bool:
	return _target_valid() and global_position.distance_to(_player.global_position) <= radius
