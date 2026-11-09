class_name BossKsatria
extends Boss
## Ksatria Rantai (Chapter 4 – Linked List).
##
## Serangan: ayun bola berantai jarak jauh (garis merah bidik, lalu bola keluar dan ditarik kembali).
## Mekanik materi: boss terhubung ke rantai node HEAD → 0 → 1 → 2 → NULL dan kebal selama rantai utuh.
## Node harus diputus dari UJUNG (tail) dulu; memukul node tengah/depan tidak berefek.
## Setelah semua node putus, boss "TERBUKA" beberapa detik (menerima damage penuh), lalu rantai tumbuh lagi.

enum Phase { WINDUP, SWING }

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const NODE_SCRIPT := preload("res://scripts/entities/BossChainNode.gd")
const BODY_CENTER := Vector2(0, -14)

var _phase: Phase = Phase.WINDUP
var _phase_left: float = 0.0
var _dir: Vector2 = Vector2.RIGHT
var _ball_cfg: Dictionary = {}
var _chain_cfg: Dictionary = {}
var _nodes: Array[BossChainNode] = []
var _vulnerable: bool = false
var _vuln_left: float = 0.0
var _ball_released: bool = false


func _setup(config: Dictionary) -> void:
	_ball_cfg = config.get("ball", {})
	_chain_cfg = config.get("chain", {})
	var i: int = 0
	for entry: Dictionary in _chain_cfg.get("nodes", []):
		var n: BossChainNode = NODE_SCRIPT.new()
		n.index = i
		var p: Array = entry["pos"]
		n.position = Vector2(float(p[0]), float(p[1]))
		n.hit.connect(_on_node_hit)
		add_child(n)
		_nodes.append(n)
		i += 1
	_update_tail()


# ---------------------------------------------------------------- Gerak & waktu terbuka

func _physics_process(delta: float) -> void:
	if _vulnerable and state != State.DEAD:
		_vuln_left -= delta
		if _vuln_left <= 0.0:
			_regrow_chain()
	super(delta)


func _chase_velocity(to_player: Vector2) -> Vector2:
	if _vulnerable:
		return Vector2.ZERO
	if to_player.length() > float(_ball_cfg.get("keep_distance", 100)):
		return to_player.normalized() * float(cfg.get("speed", 36))
	return Vector2.ZERO


# ---------------------------------------------------------------- Serangan: bola berantai

func _try_attack(to_player: Vector2) -> bool:
	if _vulnerable or to_player.length() > float(_ball_cfg.get("trigger_range", 150)):
		return false
	state = State.ATTACK
	_phase = Phase.WINDUP
	_phase_left = float(_ball_cfg.get("windup", 0.6))
	_dir = to_player.normalized()
	_ball_released = false
	_play("idle")
	_flash(Color(1.0, 0.45, 0.45), _phase_left)
	queue_redraw()
	return true


func _attack_process(delta: float) -> void:
	if _phase != Phase.WINDUP:
		return
	_phase_left -= delta
	if _phase_left <= 0.0:
		_phase = Phase.SWING
		sprite.play("attack")
		_apply_offset()
		queue_redraw()


## Di frame lepas: bola berantai keluar ke arah yang sudah dikunci.
func _on_attack_frame(frame: int) -> void:
	if _phase != Phase.SWING or _ball_released or frame != int(_ball_cfg.get("release_frame", 3)):
		return
	_ball_released = true
	BossChainBall.launch(self, global_position + BODY_CENTER, _dir, float(_ball_cfg.get("range", 150)),
		float(_ball_cfg.get("speed", 220)), int(_ball_cfg.get("damage", 12)))


func _on_attack_finished() -> void:
	_enter_recover(float(_ball_cfg.get("recover", 1.2)))


# ---------------------------------------------------------------- Rantai node (putus dari ujung)

## Node yang sedang menjadi ujung = node hidup dengan indeks terbesar.
func _tail_index() -> int:
	for i in range(_nodes.size() - 1, -1, -1):
		if _nodes[i].alive:
			return i
	return -1


func _update_tail() -> void:
	var tail: int = _tail_index()
	for n in _nodes:
		n.is_tail = n.index == tail
	queue_redraw()


func _on_node_hit(index: int) -> void:
	if state == State.DEAD or _vulnerable:
		return
	if index != _tail_index():
		DamagePopup.spawn(get_parent(), _nodes[index].global_position + Vector2(0, -12), 0, Color(1, 0.4, 0.4))
		AudioManager.play_sfx("kuis_salah", 0.05)
		return
	_nodes[index].cut()
	AudioManager.play_sfx("ledakan", 0.1)
	_update_tail()
	if _tail_index() == -1:
		_open_up()


func _open_up() -> void:
	_vulnerable = true
	_vuln_left = float(_chain_cfg.get("vulnerable_time", 6.0))
	sprite.self_modulate = Color(1.0, 1.0, 0.6)
	AudioManager.play_sfx("power_up", 0.05)
	queue_redraw()


func _regrow_chain() -> void:
	_vulnerable = false
	sprite.self_modulate = Color.WHITE
	for n in _nodes:
		n.restore()
	_update_tail()


## Rantai utuh = kebal. Terbuka = damage penuh.
func _filter_damage(damage: int, _from_pos: Vector2) -> int:
	if _vulnerable:
		return damage
	DamagePopup.spawn(get_parent(), global_position + Vector2(0, -50), 0, Color(0.7, 0.7, 0.7))
	return 0


func _on_death_started() -> void:
	for n in _nodes:
		n.cut()
	_vulnerable = false
	sprite.self_modulate = Color.WHITE
	queue_redraw()


# ---------------------------------------------------------------- Gambar rantai + tanda bidik

func _draw() -> void:
	if state == State.ATTACK and _phase == Phase.WINDUP:
		var red: Color = Color(1, 0.1, 0.1, 0.35)
		draw_line(BODY_CENTER, BODY_CENTER + _dir * float(_ball_cfg.get("range", 150)), red, 10.0)
	if state == State.DEAD:
		return
	# Rantai linked list: HEAD → node hidup berurutan → NULL.
	var prev: Vector2 = BODY_CENTER
	var last_alive: Vector2 = BODY_CENTER
	for n in _nodes:
		if not n.alive:
			break   # rantai putus dari ujung, sisa di belakang tidak ada
		draw_line(prev, n.position, Color(0.6, 0.6, 0.7), 2.0)
		prev = n.position
		last_alive = n.position
	if not _nodes.is_empty() and _nodes[0].alive:
		draw_string(FONT, BODY_CENTER + Vector2(8, -18), "HEAD", HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(0.7, 0.9, 1.0))
	var tail: int = _tail_index()
	if tail >= 0:
		draw_string(FONT, _nodes[tail].position + Vector2(10, 4), "NULL", HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(0.7, 0.9, 1.0))
	if _vulnerable:
		draw_string(FONT, Vector2(-26, -72), "TERBUKA!", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(1, 0.9, 0.2))
