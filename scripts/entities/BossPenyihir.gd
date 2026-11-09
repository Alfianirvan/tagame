class_name BossPenyihir
extends Boss
## Penyihir Menara (Chapter 2 – Stack, LIFO).
##
## Serangan: PUSH 3 kali (animasi cast; tiap cast menaruh satu bola di tumpukan, bernomor 1,2,3),
## lalu POP: bola yang terakhir ditaruh (nomor 3, label TOP) dilempar duluan, kemudian 2, lalu 1.
## Garis merah bidik muncul sebelum tiap lemparan. Pemain bisa membaca urutan lemparan dari nomor bola.

enum Phase { PUSH, POP }

const STACK_BASE := Vector2(34, -14)   # posisi bola nomor 1 relatif ke kaki boss
const STACK_STEP := Vector2(0, -14)    # tiap bola berikutnya di atasnya

var _cfg_stack: Dictionary = {}
var _orb_frames: SpriteFrames
var _stack: Array[BossOrb] = []
var _phase: Phase = Phase.PUSH


func _setup(config: Dictionary) -> void:
	_cfg_stack = config.get("stack", {})
	_orb_frames = BossSprites.build(config["orb_sprite"])


# ---------------------------------------------------------------- Gerak: jaga jarak (penyihir)

func _chase_velocity(to_player: Vector2) -> Vector2:
	var dist: float = to_player.length()
	var speed: float = float(cfg.get("speed", 34))
	if dist < float(_cfg_stack.get("retreat_range", 60)):
		return -to_player.normalized() * speed
	if dist > float(_cfg_stack.get("cast_range", 150)):
		return to_player.normalized() * speed
	return Vector2.ZERO


# ---------------------------------------------------------------- Serangan: push x3 lalu pop

func _try_attack(to_player: Vector2) -> bool:
	if to_player.length() > float(_cfg_stack.get("cast_range", 150)):
		return false
	state = State.ATTACK
	_phase = Phase.PUSH
	_cast_again()
	return true


## Memulai satu animasi cast (menaruh satu bola). Ganti animasi dulu agar frame kembali ke 0.
func _cast_again() -> void:
	sprite.play("idle")
	sprite.play("attack")
	_apply_offset()


## Di frame cast: push satu bola ke puncak tumpukan.
func _on_attack_frame(frame: int) -> void:
	if _phase != Phase.PUSH or frame != int(_cfg_stack.get("cast_frame", 5)):
		return
	_push_orb()


func _push_orb() -> void:
	var orb: BossOrb = BossOrb.create(_orb_frames, _stack.size() + 1)
	add_child(orb)
	orb.position = STACK_BASE + STACK_STEP * float(_stack.size())
	_stack.append(orb)
	for o in _stack:
		o.is_top = o == orb
	AudioManager.play_sfx("sihir", 0.1)


## Animasi cast selesai: tumpukan belum penuh → push lagi; sudah penuh → mulai pop.
func _on_attack_finished() -> void:
	if _stack.size() < int(_cfg_stack.get("orbs", 3)):
		_cast_again()
		return
	_phase = Phase.POP
	_play("idle")
	get_tree().create_timer(0.4).timeout.connect(_pop_next)


## Mengeluarkan bola paling atas (LIFO). Diulang dengan jeda sampai tumpukan kosong.
func _pop_next() -> void:
	if state != State.ATTACK or not is_inside_tree():
		return
	if _stack.is_empty():
		_enter_recover(float(_cfg_stack.get("recover", 1.8)))
		return
	var orb: BossOrb = _stack.pop_back()
	if not _stack.is_empty():
		_stack.back().is_top = true
	# Lepas dari boss agar tidak ikut bergerak, lalu bidik player (arah dikunci saat ini).
	var pos: Vector2 = orb.global_position
	remove_child(orb)
	get_parent().add_child(orb)
	orb.global_position = pos
	var dir: Vector2 = Vector2.RIGHT
	if _target_valid():
		dir = (_player.global_position + Vector2(0, -14) - pos).normalized()
	orb.launch(dir, float(_cfg_stack.get("aim_time", 0.4)), float(_cfg_stack.get("orb_speed", 120)),
		int(_cfg_stack.get("orb_damage", 10)))
	get_tree().create_timer(float(_cfg_stack.get("pop_interval", 0.55))).timeout.connect(_pop_next)


func _on_death_started() -> void:
	for orb in _stack:
		if is_instance_valid(orb):
			orb.queue_free()
	_stack.clear()
