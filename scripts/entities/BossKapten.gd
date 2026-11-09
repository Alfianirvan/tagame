class_name BossKapten
extends Boss
## Kapten Bajak Laut (Chapter 3 – Queue, FIFO).
##
## Serangan 1: terjang jauh + tebas (tanda merah di lantai, lalu menerjang lurus dengan hitbox aktif).
## Serangan 2: memanggil anak buah ke ANTREAN bernomor 1,2,3. Yang masuk antrean lebih dulu keluar
## lebih dulu (FIFO): anak buah berikutnya baru turun ke arena saat yang sebelumnya kalah.

enum Phase { WINDUP, LUNGE, SUMMON }

const ENEMY_SCENE := preload("res://scenes/entities/Enemy.tscn")
const FONT := preload("res://assets/fonts/Square-Black.ttf")
const BODY_CENTER := Vector2(0, -14)

var _phase: Phase = Phase.WINDUP
var _phase_left: float = 0.0
var _dir: Vector2 = Vector2.RIGHT
var _lunge: Dictionary = {}
var _summon: Dictionary = {}
var _hitbox: Area2D
var _hitbox_shape: CollisionShape2D
var _queue: Array[Dictionary] = []     # antrean menunggu: {"n": nomor, "id": jenis musuh}
var _minions: Array[Enemy] = []        # anak buah yang sedang di arena
var _summon_cd: float = 0.0


func _setup(config: Dictionary) -> void:
	_lunge = config.get("lunge", {})
	_summon = config.get("summon", {})
	_summon_cd = float(_summon.get("first_delay", 3.0))
	# Hitbox tebasan: layer 5 (serangan musuh), damage dibaca Hurtbox player lewat meta.
	_hitbox = Area2D.new()
	_hitbox.collision_layer = 16
	_hitbox.collision_mask = 0
	_hitbox.monitoring = false
	_hitbox.monitorable = false
	_hitbox.set_meta("damage", int(_lunge.get("damage", 14)))
	_hitbox_shape = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 16.0
	_hitbox_shape.shape = circle
	_hitbox.add_child(_hitbox_shape)
	add_child(_hitbox)


func _on_fight_started() -> void:
	_summon_cd = float(_summon.get("first_delay", 3.0))


# ---------------------------------------------------------------- Memilih serangan

func _physics_process(delta: float) -> void:
	# Hitung mundur panggilan jalan terus selama bertarung (antrean kosong dan tidak ada anak buah),
	# supaya tidak tertahan oleh terjangan beruntun.
	if state != State.WAITING and state != State.DEAD and _queue.is_empty() and _minions.is_empty():
		_summon_cd -= delta
	super(delta)


func _try_attack(to_player: Vector2) -> bool:
	if _queue.is_empty() and _minions.is_empty() and _summon_cd <= 0.0:
		_start_summon()
		return true
	if to_player.length() <= float(_lunge.get("trigger_range", 150)):
		_start_windup(to_player)
		return true
	return false


# ---------------------------------------------------------------- Terjang + tebas

func _start_windup(to_player: Vector2) -> void:
	state = State.ATTACK
	_phase = Phase.WINDUP
	_phase_left = float(_lunge.get("windup", 0.7))
	_dir = to_player.normalized()
	_face(_dir)
	_play("idle")
	_flash(Color(1.0, 0.45, 0.45), _phase_left)
	queue_redraw()


func _begin_lunge() -> void:
	_phase = Phase.LUNGE
	_phase_left = float(_lunge.get("time", 0.3))
	_hitbox_shape.position = BODY_CENTER + _dir * 14.0
	_hitbox.set_deferred("monitorable", true)
	sprite.play("attack")
	_apply_offset()
	AudioManager.play_sfx("serang_tebas2", 0.1)
	queue_redraw()


func _end_lunge() -> void:
	_hitbox.set_deferred("monitorable", false)
	_enter_recover(float(_lunge.get("recover", 1.0)))


func _attack_process(delta: float) -> void:
	match _phase:
		Phase.WINDUP:
			_phase_left -= delta
			if _phase_left <= 0.0:
				_begin_lunge()
		Phase.LUNGE:
			velocity = _dir * (float(_lunge.get("distance", 130)) / float(_lunge.get("time", 0.3)))
			_phase_left -= delta
			if _phase_left <= 0.0:
				_end_lunge()
		Phase.SUMMON:
			pass


# ---------------------------------------------------------------- Memanggil anak buah (antrean FIFO)

func _start_summon() -> void:
	state = State.ATTACK
	_phase = Phase.SUMMON
	sprite.play("attack")
	_apply_offset()


## Di frame panggil: antrean 1..n terbentuk, nomor 1 langsung keluar.
func _on_attack_frame(frame: int) -> void:
	if _phase != Phase.SUMMON or frame != int(_summon.get("frame", 2)):
		return
	var ids: Array = _summon.get("minion_ids", ["orc_rogue"])
	for i in int(_summon.get("count", 3)):
		_queue.append({"n": i + 1, "id": String(ids[i % ids.size()])})
	AudioManager.play_sfx("peringatan_boss", 0.05)
	_release_next()


func _on_attack_finished() -> void:
	if _phase == Phase.SUMMON:
		_enter_recover(float(_summon.get("recover", 0.8)))


## Mengeluarkan anak buah paling depan dari antrean (FIFO: pop_front).
func _release_next() -> void:
	if state == State.DEAD or _queue.is_empty() or not is_inside_tree():
		return
	var entry: Dictionary = _queue.pop_front()
	var enemy: Enemy = ENEMY_SCENE.instantiate() as Enemy
	enemy.enemy_id = String(entry["id"])
	get_parent().add_child(enemy)
	enemy.global_position = global_position + Vector2(randf_range(-40.0, 40.0), 36.0)
	enemy.state = Enemy.State.CHASE   # langsung menyerbu, tanpa menunggu terdeteksi
	enemy.died.connect(_on_minion_died)
	var label: Label = Label.new()
	label.text = str(entry["n"])
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", 8)
	label.add_theme_constant_override("outline_size", 3)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.position = Vector2(-3, -52)
	enemy.add_child(label)
	_minions.append(enemy)
	queue_redraw()


func _on_minion_died(enemy: Enemy) -> void:
	_minions.erase(enemy)
	if state == State.DEAD:
		return
	if not _queue.is_empty():
		get_tree().create_timer(float(_summon.get("release_delay", 0.6))).timeout.connect(_release_next)
	elif _minions.is_empty():
		_summon_cd = float(_summon.get("cooldown", 8.0))
	queue_redraw()


func _on_death_started() -> void:
	_hitbox.set_deferred("monitorable", false)
	_queue.clear()
	for m in _minions:
		if is_instance_valid(m):
			m.queue_free()
	_minions.clear()
	queue_redraw()


# ---------------------------------------------------------------- Gambar: tanda merah + antrean

func _draw() -> void:
	if state == State.ATTACK and _phase == Phase.WINDUP:
		var red: Color = Color(1, 0.1, 0.1, 0.35)
		var target: Vector2 = BODY_CENTER + _dir * float(_lunge.get("distance", 130))
		draw_line(BODY_CENTER, target, red, 14.0)
		draw_circle(target, 16.0, red)
	# Antrean menunggu: kotak bernomor di atas kepala, yang paling depan (keluar duluan) bertanda kuning.
	for i in _queue.size():
		var origin: Vector2 = Vector2(-28.0 + i * 18.0, -82.0)
		var front: bool = i == 0
		draw_rect(Rect2(origin, Vector2(14, 14)), Color(0, 0, 0, 0.75))
		draw_rect(Rect2(origin, Vector2(14, 14)), Color(1, 0.9, 0.2) if front else Color(0.7, 0.7, 0.7), false, 1.0)
		draw_string(FONT, origin + Vector2(4, 11), str(_queue[i]["n"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color.WHITE)
	if not _queue.is_empty():
		draw_string(FONT, Vector2(-28.0, -86.0), "ANTRE >", HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(1, 0.9, 0.2))
