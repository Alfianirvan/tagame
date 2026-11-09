class_name Boss
extends CharacterBody2D
## Base class boss. Mengurus: state (menunggu → kejar → serang → pulih → mati), animasi dengan offset
## titik kaki, bar HP boss, kedip saat kena, drop, animasi mati lalu Kristal Struktur + autosave.
## Pola serangan khusus tiap boss ada di subclass (override _try_attack, _on_attack_frame, _filter_damage).
## Konvensi tabrakan sama dengan Enemy: badan layer 3 (enemy), serangan layer 5 membawa meta "damage".

signal damaged(hp: int, max_hp: int)
signal boss_defeated(boss_id: String)
signal fight_started(boss_id: String)   # pemain terdeteksi: wilayah memutar musik boss

enum State { WAITING, CHASE, ATTACK, RECOVER, DEAD }

const DB_PATH := "res://data/bosses.json"
const COLLECTIBLE_SCENE := preload("res://scenes/entities/Collectible.tscn")

## Kunci di data/bosses.json.
@export var boss_id: String = "golem_batu"

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var body_shape: CollisionShape2D = $CollisionShape2D

static var _db: Dictionary = {}

var cfg: Dictionary = {}
var hp: int = 1
var max_hp: int = 1
var state: State = State.WAITING

var _player: Node2D
var _state_left: float = 0.0
var _offsets: Dictionary = {}
var _flash_tween: Tween
var _bar: BossHealthBar


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING  # top-down
	add_to_group("enemy")
	add_to_group("boss")
	cfg = _get_config(boss_id)
	if cfg.is_empty():
		push_warning("Boss tidak dikenal: %s" % boss_id)
		queue_free()
		return
	max_hp = int(cfg.get("hp", 100))
	hp = max_hp
	var frames: SpriteFrames = BossSprites.build(cfg["sprites"])
	_offsets = frames.get_meta("offsets", {})
	sprite.sprite_frames = frames
	sprite.animation_changed.connect(_apply_offset)
	sprite.animation_changed.connect(_on_animation_changed_pose)
	sprite.animation_finished.connect(_on_animation_finished)
	sprite.frame_changed.connect(_on_frame_changed)
	(body_shape.shape as CircleShape2D).radius = float(cfg.get("body_radius", 14))
	body_shape.position = Vector2(0, -float(cfg.get("body_radius", 14)))
	_play("idle")
	_setup(cfg)


var _pose_tween: Tween   # gerak badan saat menyerang (lihat _pose_for_frame)


static func _get_config(id: String) -> Dictionary:
	if _db.is_empty():
		var data: Variant = GameManager.load_json(DB_PATH)
		if data is Dictionary:
			_db = data
	return _db.get(id, {})


# ---------------------------------------------------------------- Hook untuk subclass

## Dipanggil sekali di akhir _ready (pasang titik lemah, dsb).
func _setup(_config: Dictionary) -> void:
	pass


## Coba mulai serangan. Kembalikan true bila serangan dimulai (subclass harus set state ATTACK).
func _try_attack(_to_player: Vector2) -> bool:
	return false


## Dipanggil tiap physics frame selama state ATTACK (untuk fase berbasis waktu dan gerakan serang).
func _attack_process(_delta: float) -> void:
	pass


## Kecepatan gerak saat fase kejar. Default: mendekati player (boss jarak jauh meng-override).
func _chase_velocity(to_player: Vector2) -> Vector2:
	return to_player.normalized() * float(cfg.get("speed", 30))


## Frame animasi serang berganti (untuk hitbox/efek yang mengikuti frame).
func _on_attack_frame(_frame: int) -> void:
	pass


## Serangan selesai (animasi serang habis). Default: masuk RECOVER.
func _on_attack_finished() -> void:
	_enter_recover(float(cfg.get("recover", 1.5)))


## Saring damage yang diterima badan boss (mis. Golem hanya kena di titik lemah). Kembalikan damage akhir.
func _filter_damage(damage: int, _from_pos: Vector2) -> int:
	return damage


## Dipanggil sekali saat pertarungan dimulai (player terdeteksi).
func _on_fight_started() -> void:
	pass


# ---------------------------------------------------------------- Loop utama

func _physics_process(_delta: float) -> void:
	match state:
		State.WAITING:
			velocity = Vector2.ZERO
			if _player_in_range(float(cfg.get("detect_range", 150))):
				_start_fight()
		State.CHASE:
			_process_chase()
		State.ATTACK:
			velocity = Vector2.ZERO
			_attack_process(_delta)   # subclass boleh mengisi velocity (mis. terjangan)
		State.RECOVER:
			velocity = Vector2.ZERO
			_state_left -= _delta
			if _state_left <= 0.0:
				state = State.CHASE
		State.DEAD:
			velocity = Vector2.ZERO
	move_and_slide()


func _start_fight() -> void:
	state = State.CHASE
	_ensure_bar()
	AudioManager.play_sfx("peringatan_boss")
	fight_started.emit(boss_id)
	_on_fight_started()


func _process_chase() -> void:
	if not _target_valid():
		velocity = Vector2.ZERO
		return
	var to_player: Vector2 = _player.global_position - global_position
	_face(to_player)
	if _try_attack(to_player):
		return
	# Berhenti di jarak tertentu supaya boss tidak menempel/menumpuk di badan player.
	var v: Vector2 = _chase_velocity(to_player)
	# Hanya menahan gerak mendekat; gerak mundur boss jarak jauh tetap jalan.
	if to_player.length() <= float(cfg.get("stop_distance", 34)) and v.dot(to_player) > 0.0:
		v = Vector2.ZERO
	velocity = v
	_play("idle")


func _enter_recover(duration: float) -> void:
	state = State.RECOVER
	_state_left = duration
	_play("idle")
	queue_redraw()


func _face(dir: Vector2) -> void:
	if absf(dir.x) > 1.0:
		sprite.flip_h = dir.x < 0.0
		_apply_offset()


# ---------------------------------------------------------------- Animasi

func _play(anim: String) -> void:
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)
	_apply_offset()


## Menyamakan titik kaki antar-animasi (offset dicerminkan bila sprite menghadap kiri).
func _apply_offset() -> void:
	var off: Vector2 = _offsets.get(String(sprite.animation), Vector2.ZERO)
	if sprite.flip_h:
		off.x = -off.x
	sprite.offset = off


func _on_frame_changed() -> void:
	if state == State.ATTACK and sprite.animation == "attack":
		_pose_for_frame(sprite.frame)
		_on_attack_frame(sprite.frame)


# ---------------------------------------------------------------- Gerak badan saat menyerang (data-driven)

## Sheet serang boss hanya menggambar efek di sekitar badan (bola, garis, busur), badannya hampir diam.
## Kunci gerak badan ada di bosses.json "body_anim": per frame serang -> skala, geser, putar (titik putar = kaki),
## lama transisi t (detik), dan opsional shake (getaran kamera). X geser/putar dicerminkan bila boss menghadap kiri.
func _pose_for_frame(frame: int) -> void:
	for key: Dictionary in cfg.get("body_anim", []):
		if int(key.get("frame", -1)) != frame:
			continue
		if _pose_tween:
			_pose_tween.kill()
		var side: float = -1.0 if sprite.flip_h else 1.0
		var scl: Array = key.get("scale", [1.0, 1.0])
		var pos: Array = key.get("pos", [0.0, 0.0])
		var dur: float = maxf(0.02, float(key.get("t", 0.15)))
		_pose_tween = create_tween().set_parallel(true)
		_pose_tween.tween_property(sprite, "scale", Vector2(float(scl[0]), float(scl[1])), dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		_pose_tween.tween_property(sprite, "position", Vector2(float(pos[0]) * side, float(pos[1])), dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		_pose_tween.tween_property(sprite, "rotation", deg_to_rad(float(key.get("rot", 0.0))) * side, dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		if float(key.get("shake", 0.0)) > 0.0:
			var player: Node = get_tree().get_first_node_in_group("player")
			if player and player.has_method("shake_camera"):
				player.shake_camera(float(key["shake"]), 0.2)
		return


func _reset_pose() -> void:
	if _pose_tween:
		_pose_tween.kill()
	sprite.scale = Vector2.ONE
	sprite.position = Vector2.ZERO
	sprite.rotation = 0.0


func _on_animation_changed_pose() -> void:
	if sprite.animation != "attack" and cfg.has("body_anim"):
		_reset_pose()


func _on_animation_finished() -> void:
	if state == State.DEAD:
		_after_death_animation()
	elif state == State.ATTACK:
		_on_attack_finished()


# ---------------------------------------------------------------- Terkena serangan

## Dipanggil hitbox/proyektil player.
func take_hit(damage: int, from_pos: Vector2) -> void:
	if state == State.DEAD:
		return
	if state == State.WAITING:
		_start_fight()
	var final_damage: int = _filter_damage(damage, from_pos)
	if final_damage <= 0:
		return
	apply_damage(final_damage)


## Mengurangi HP langsung (dipakai subclass, mis. dari titik lemah).
func apply_damage(amount: int) -> void:
	if state == State.DEAD:
		return
	hp = maxi(0, hp - amount)
	damaged.emit(hp, max_hp)
	DamagePopup.spawn(get_parent(), global_position + Vector2(0, -60), amount)
	AudioManager.play_sfx("kena_hit2", 0.1)
	_flash(Color(1.0, 0.4, 0.4), 0.15)
	if hp <= 0:
		_die()


func _flash(color: Color, duration: float) -> void:
	if _flash_tween:
		_flash_tween.kill()
	sprite.modulate = color
	_flash_tween = create_tween()
	_flash_tween.tween_property(sprite, "modulate", Color.WHITE, duration)


# ---------------------------------------------------------------- Mati

func _die() -> void:
	state = State.DEAD
	set_deferred("collision_layer", 0)
	set_deferred("collision_mask", 0)
	queue_redraw()
	_on_death_started()
	_drop_loot()
	GameManager.add_xp(int(cfg.get("xp", 0)))
	GameManager.enemy_killed.emit(boss_id)
	AudioManager.play_sfx("ledakan", 0.1)
	_play("death")


## Hook: bersihkan efek (titik lemah, anak buah) saat boss mulai mati.
func _on_death_started() -> void:
	pass


func _drop_loot() -> void:
	var parent: Node = get_parent()
	for entry: Dictionary in cfg.get("drops", []):
		if randf() > float(entry.get("chance", 1.0)):
			continue
		var amount: int = randi_range(int(entry.get("min", 1)), int(entry.get("max", 1)))
		var offset: Vector2 = Vector2(randf_range(-30, 30), randf_range(4, 24))
		Collectible.spawn(parent, COLLECTIBLE_SCENE, String(entry["item"]), amount, global_position + offset)


## Animasi mati selesai: Kristal Struktur muncul, sprite memudar, boss dinyatakan kalah, autosave.
func _after_death_animation() -> void:
	Crystal.spawn(get_parent(), global_position + Vector2(0, -6), int(cfg.get("chapter", 1)))
	if is_instance_valid(_bar):
		_bar.queue_free()
	SaveManager.save_game()
	boss_defeated.emit(boss_id)
	var tw: Tween = create_tween()
	tw.tween_property(sprite, "modulate:a", 0.0, 0.8)
	tw.tween_callback(queue_free)


# ---------------------------------------------------------------- Bantuan

func _ensure_bar() -> void:
	if _bar != null:
		return
	_bar = BossHealthBar.new()
	add_child(_bar)
	_bar.setup(String(cfg.get("name", "Boss")))
	_bar.set_hp(hp, max_hp)
	damaged.connect(_bar.set_hp)


func _target_valid() -> bool:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
	return _player != null and GameManager.hp > 0


func _player_in_range(radius: float) -> bool:
	return _target_valid() and global_position.distance_to(_player.global_position) <= radius
