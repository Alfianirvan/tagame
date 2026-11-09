class_name BossKing
extends Boss
## King Subiyan (Chapter 5 – Tree), boss terakhir.
##
## Serangan: bola sihir menyebar (kipas), dengan garis merah bidik sebelum dilepas.
## Mekanik materi: saat HP turun melewati ambang (70%, 35%) dia memanggil 2 bayangan, dan tiap bayangan
## memanggil 2 bayangan lagi (pohon biner, akar = King). Boss terlindung selama masih ada bayangan.
## Bayangan hanya bisa dilukai dari DAUN ke atas (leaf dulu, lalu induknya, sampai akar terbuka).

enum Phase { WINDUP, CAST, SUMMON }

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const BODY_CENTER := Vector2(0, -34)

var _phase: Phase = Phase.WINDUP
var _phase_left: float = 0.0
var _dir: Vector2 = Vector2.RIGHT
var _magic: Dictionary = {}
var _tree: Dictionary = {}
var _orb_frames: SpriteFrames
var _shadow_frames: SpriteFrames
var _roots: Array[BossShadow] = []
var _threshold_idx: int = 0
var _released: bool = false


func _setup(config: Dictionary) -> void:
	_magic = config.get("magic", {})
	_tree = config.get("tree", {})
	_orb_frames = BossSprites.build(config["orb_sprite"])
	# Bayangan memakai animasi idle King (hanya animasi idle yang dibangun).
	_shadow_frames = BossSprites.build({"idle": config["sprites"]["idle"]})


func _physics_process(delta: float) -> void:
	if not _roots.is_empty():
		queue_redraw()   # garis ke bayangan mengikuti gerak
	super(delta)


func is_shielded() -> bool:
	return not _roots.is_empty()


# ---------------------------------------------------------------- Gerak: menjaga jarak

func _chase_velocity(to_player: Vector2) -> Vector2:
	var dist: float = to_player.length()
	var speed: float = float(cfg.get("speed", 32))
	if dist < float(_magic.get("retreat_range", 70)):
		return -to_player.normalized() * speed
	if dist > float(_magic.get("trigger_range", 170)):
		return to_player.normalized() * speed
	return Vector2.ZERO


# ---------------------------------------------------------------- Memilih serangan

func _try_attack(to_player: Vector2) -> bool:
	if _should_summon():
		state = State.ATTACK
		_phase = Phase.SUMMON
		_released = false
		sprite.play("attack")
		_apply_offset()
		queue_redraw()
		return true
	if to_player.length() > float(_magic.get("trigger_range", 170)):
		return false
	state = State.ATTACK
	_phase = Phase.WINDUP
	_phase_left = float(_magic.get("windup", 0.5))
	_dir = to_player.normalized()
	_released = false
	_play("idle")
	_flash(Color(1.0, 0.45, 0.45), _phase_left)
	queue_redraw()
	return true


func _should_summon() -> bool:
	var thresholds: Array = _tree.get("thresholds", [])
	if not _roots.is_empty() or _threshold_idx >= thresholds.size():
		return false
	return float(hp) <= float(thresholds[_threshold_idx]) * float(max_hp)


func _attack_process(delta: float) -> void:
	if _phase != Phase.WINDUP:
		return
	_phase_left -= delta
	if _phase_left <= 0.0:
		_phase = Phase.CAST
		sprite.play("attack")
		_apply_offset()
		queue_redraw()


func _on_attack_frame(frame: int) -> void:
	if _released:
		return
	if _phase == Phase.CAST and frame == int(_magic.get("cast_frame", 4)):
		_released = true
		_fire_fan()
	elif _phase == Phase.SUMMON and frame == int(_tree.get("summon_frame", 4)):
		_released = true
		_spawn_tree()


func _on_attack_finished() -> void:
	if _phase == Phase.SUMMON:
		_enter_recover(float(_tree.get("summon_recover", 1.0)))
	else:
		_enter_recover(float(_magic.get("recover", 1.3)))


# ---------------------------------------------------------------- Bola sihir (kipas)

func _fire_fan() -> void:
	var count: int = int(_magic.get("fan", 3))
	var spread: float = deg_to_rad(float(_magic.get("spread_deg", 18)))
	for i in count:
		var angle: float = (float(i) - float(count - 1) / 2.0) * spread
		var orb: BossOrb = BossOrb.create(_orb_frames, 0)
		get_parent().add_child(orb)
		orb.global_position = global_position + BODY_CENTER
		orb.launch(_dir.rotated(angle), 0.05, float(_magic.get("orb_speed", 110)), int(_magic.get("orb_damage", 10)))


# ---------------------------------------------------------------- Pohon bayangan

## Memanggil 2 bayangan tingkat 1; masing-masing nanti memanggil 2 anak sendiri (hingga max_depth).
func _spawn_tree() -> void:
	_threshold_idx += 1
	for i in 2:
		var shadow: BossShadow = BossShadow.create(_shadow_frames, _tree.get("shadow", {}), 1, int(_tree.get("max_depth", 2)))
		get_parent().add_child(shadow)
		shadow.global_position = global_position + Vector2(-55.0 if i == 0 else 55.0, 25.0)
		shadow.died.connect(_on_root_died)
		_roots.append(shadow)
	AudioManager.play_sfx("peringatan_boss", 0.05)
	queue_redraw()


func _on_root_died(shadow: BossShadow) -> void:
	_roots.erase(shadow)
	if _roots.is_empty() and state != State.DEAD:
		AudioManager.play_sfx("power_up", 0.05)
		DamagePopup.spawn(get_parent(), global_position + Vector2(0, -80), 0, Color(1, 0.9, 0.2))
	queue_redraw()


## Selama masih ada bayangan, King kebal (akar baru bisa dilukai setelah semua daun dan cabang tumbang).
func _filter_damage(damage: int, _from_pos: Vector2) -> int:
	if is_shielded():
		DamagePopup.spawn(get_parent(), global_position + Vector2(0, -70), 0, Color(0.7, 0.7, 0.7))
		return 0
	return damage


func _on_death_started() -> void:
	for s in get_tree().get_nodes_in_group("boss_shadow"):
		s.queue_free()
	_roots.clear()
	queue_redraw()


# ---------------------------------------------------------------- Gambar

func _draw() -> void:
	if state == State.DEAD:
		return
	if state == State.ATTACK and _phase == Phase.WINDUP:
		var count: int = int(_magic.get("fan", 3))
		var spread: float = deg_to_rad(float(_magic.get("spread_deg", 18)))
		for i in count:
			var angle: float = (float(i) - float(count - 1) / 2.0) * spread
			draw_line(BODY_CENTER, BODY_CENTER + _dir.rotated(angle) * 200.0, Color(1, 0.1, 0.1, 0.35), 4.0)
	if is_shielded():
		for s in _roots:
			if is_instance_valid(s):
				draw_line(BODY_CENTER, s.global_position - global_position + Vector2(0, -14), Color(0.7, 0.5, 1.0, 0.8), 2.0)
		draw_arc(BODY_CENTER, 22.0, 0.0, TAU, 28, Color(0.5, 0.9, 1.0, 0.8), 2.0, false)
		draw_string(FONT, Vector2(-14, -80), "ROOT", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.6, 0.9, 1.0))
