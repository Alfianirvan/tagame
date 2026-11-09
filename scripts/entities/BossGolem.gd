class_name BossGolem
extends Boss
## Golem Batu (Chapter 1 – Array).
##
## Serangan: hantam tanah (tanda merah di lantai → gelombang kejut cincin merambat; hindari dengan dodge).
## Mekanik materi: badan golem kebal. Ada 3 titik lemah berlabel indeks 0, 1, 2 (mulai dari 0 seperti array).
## Hanya titik yang menyala (giliran berikutnya) yang melukai, jadi player harus memukul sesuai urutan indeks.
## Setelah indeks terakhir, urutan kembali ke 0.

const WEAK_POINT_SCRIPT := preload("res://scripts/entities/BossWeakPoint.gd")

var _weak_points: Array[BossWeakPoint] = []
var _next_index: int = 0
var _slam: Dictionary = {}
var _slam_pos: Vector2 = Vector2.ZERO
var _warn_t: float = 0.0
var _body_tween: Tween


func _setup(config: Dictionary) -> void:
	_slam = config.get("slam", {})
	for entry: Dictionary in config.get("weak_points", []):
		var wp: BossWeakPoint = WEAK_POINT_SCRIPT.new()
		wp.index = int(entry["index"])
		var p: Array = entry["pos"]
		wp.position = Vector2(float(p[0]), float(p[1]))
		wp.hit.connect(_on_weak_point_hit)
		add_child(wp)
		_weak_points.append(wp)
	_update_glow()


# ---------------------------------------------------------------- Serangan: hantam tanah

func _try_attack(to_player: Vector2) -> bool:
	if to_player.length() > float(_slam.get("trigger_range", 70)):
		return false
	state = State.ATTACK
	_slam_pos = global_position
	_warn_t = 0.0
	sprite.play("attack")
	_apply_offset()
	queue_redraw()
	return true


## Animasi badan Golem selama serang: mengangkat badan (frame 1-3), menghantam turun (frame 4),
## squash saat gelombang kejut keluar (frame 5), lalu kembali tegak (frame 6+). Titik putar = kaki (origin).
func _animate_body(frame: int) -> void:
	var impact: int = int(_slam.get("impact_frame", 5))
	# Hanya frame kunci yang memulai gerakan baru; frame lain membiarkan gerakan sebelumnya selesai.
	if frame != 1 and frame != impact - 1 and frame != impact + 1:
		return
	if _body_tween:
		_body_tween.kill()
	_body_tween = create_tween()
	if frame == 1:
		_body_tween.set_parallel(true)
		_body_tween.tween_property(sprite, "scale", Vector2(0.94, 1.14), 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		_body_tween.tween_property(sprite, "position:y", -8.0, 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	elif frame == impact - 1:
		_body_tween.set_parallel(true)
		_body_tween.tween_property(sprite, "scale", Vector2(1.2, 0.8), 0.08).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		_body_tween.tween_property(sprite, "position:y", 0.0, 0.08).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	else:
		_body_tween.tween_property(sprite, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _reset_body() -> void:
	if _body_tween:
		_body_tween.kill()
	sprite.scale = Vector2.ONE
	sprite.position = Vector2.ZERO


## Debu terlempar dari titik hantaman.
func _dust_burst(pos: Vector2) -> void:
	var p: CPUParticles2D = CPUParticles2D.new()
	p.one_shot = true
	p.emitting = true
	p.amount = 18
	p.lifetime = 0.55
	p.explosiveness = 1.0
	p.direction = Vector2.UP
	p.spread = 160.0
	p.initial_velocity_min = 35.0
	p.initial_velocity_max = 85.0
	p.gravity = Vector2(0, 90)
	p.scale_amount_min = 2.0
	p.scale_amount_max = 4.0
	var fade: Gradient = Gradient.new()
	fade.colors = PackedColorArray([Color(0.78, 0.68, 0.52, 0.9), Color(0.7, 0.6, 0.45, 0.0)])
	p.color_ramp = fade
	get_parent().add_child(p)
	p.global_position = pos + Vector2(0, -2)
	get_tree().create_timer(1.0).timeout.connect(p.queue_free)


## Frame hantaman: gelombang kejut keluar dari kaki golem.
func _on_attack_frame(frame: int) -> void:
	_animate_body(frame)
	if frame != int(_slam.get("impact_frame", 5)):
		return
	_dust_burst(_slam_pos)
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("shake_camera"):
		player.shake_camera(3.0, 0.3)
	Shockwave.spawn(get_parent(), _slam_pos, int(_slam.get("damage", 12)), float(_slam.get("max_radius", 90)),
		float(_slam.get("wave_speed", 130)), float(_slam.get("wave_width", 12)))
	AudioManager.play_sfx("hantam_tanah", 0.05)
	queue_redraw()


func _on_attack_finished() -> void:
	_reset_body()
	_enter_recover(float(_slam.get("recover", 1.6)))


func _process(delta: float) -> void:
	# Hanya animasi tanda peringatan; tidak memengaruhi logika.
	if state == State.ATTACK and sprite.frame < int(_slam.get("impact_frame", 5)):
		_warn_t += delta
		queue_redraw()


## Tanda merah di lantai: area gelombang kejut + lingkaran isi yang membesar sampai frame hantaman.
func _draw() -> void:
	if state != State.ATTACK or sprite.frame >= int(_slam.get("impact_frame", 5)):
		return
	var max_r: float = float(_slam.get("max_radius", 90))
	var progress: float = clampf(float(sprite.frame) / float(_slam.get("impact_frame", 5)), 0.0, 1.0)
	draw_circle(Vector2.ZERO, max_r, Color(1, 0.1, 0.1, 0.12))
	draw_arc(Vector2.ZERO, max_r, 0.0, TAU, 48, Color(1, 0.15, 0.15, 0.7), 2.0, false)
	draw_circle(Vector2.ZERO, max_r * progress, Color(1, 0.1, 0.1, 0.18))


# ---------------------------------------------------------------- Titik lemah (urutan indeks)

## Badan golem kebal; beri umpan balik agar player tahu harus memukul titik lemah.
func _filter_damage(_damage: int, _from_pos: Vector2) -> int:
	DamagePopup.spawn(get_parent(), global_position + Vector2(0, -60), 0, Color(0.7, 0.7, 0.7))
	return 0


func _on_weak_point_hit(index: int, damage: int) -> void:
	if state == State.DEAD:
		return
	if index != _next_index:
		# Salah urutan: tidak ada damage, tanpa hukuman.
		DamagePopup.spawn(get_parent(), global_position + Vector2(0, -64), 0, Color(1, 0.4, 0.4))
		AudioManager.play_sfx("kuis_salah", 0.05)
		return
	apply_damage(damage)
	if state == State.DEAD:
		return
	_next_index = (_next_index + 1) % _weak_points.size()
	_update_glow()


func _update_glow() -> void:
	for wp in _weak_points:
		wp.is_next = wp.index == _next_index


func _on_death_started() -> void:
	_reset_body()
	for wp in _weak_points:
		wp.set_deferred("monitorable", false)   # dipanggil dari callback fisika (hitbox Raka): harus ditunda
		wp.visible = false
