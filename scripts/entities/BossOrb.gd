class_name BossOrb
extends Area2D
## Bola sihir Penyihir Menara. Tiga mode:
## STACKED  = melayang di tumpukan di samping boss (diberi nomor urutan push),
## AIMING   = di-pop dari puncak tumpukan, garis merah bidik tampil (arah terkunci, bisa dihindari),
## FLYING   = meluncur lurus; kena player lewat meta "damage" (Hurtbox player), hilang saat menabrak.

enum Mode { STACKED, AIMING, FLYING }

var mode: Mode = Mode.STACKED
var number: int = 1                 # urutan push (1 = pertama masuk)
var direction: Vector2 = Vector2.RIGHT
var speed: float = 120.0
var damage: int = 10
var is_top: bool = false:
	set(value):
		is_top = value
		queue_redraw()

var _sprite: AnimatedSprite2D
var _life: float = 3.5


## Membuat bola bersprite dari SpriteFrames (animasi "orb").
static func create(frames: SpriteFrames, order: int) -> BossOrb:
	var orb: BossOrb = BossOrb.new()
	orb.number = order
	orb._sprite = AnimatedSprite2D.new()
	orb._sprite.sprite_frames = frames
	orb.add_child(orb._sprite)
	return orb


func _ready() -> void:
	collision_layer = 0
	collision_mask = 0
	monitoring = false
	monitorable = false
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 5.0
	shape.shape = circle
	add_child(shape)
	body_entered.connect(_on_body_entered)
	z_index = 8
	_sprite.play("orb")


## Mulai membidik; setelah aim_time bola meluncur ke arah yang sudah dikunci.
func launch(dir: Vector2, aim_time: float, spd: float, dmg: int) -> void:
	direction = dir.normalized()
	speed = spd
	damage = dmg
	mode = Mode.AIMING
	is_top = false
	rotation = 0.0
	queue_redraw()
	get_tree().create_timer(aim_time).timeout.connect(_start_flying)


func _start_flying() -> void:
	if not is_inside_tree():
		return
	mode = Mode.FLYING
	set_meta("damage", damage)
	collision_layer = 16     # layer 5: serangan musuh
	collision_mask = 1 | 2   # dinding + player
	set_deferred("monitoring", true)
	set_deferred("monitorable", true)
	queue_redraw()
	AudioManager.play_sfx("bola_api", 0.1)


func _physics_process(delta: float) -> void:
	if mode != Mode.FLYING:
		return
	position += direction * speed * delta
	_life -= delta
	if _life <= 0.0:
		queue_free()


func _on_body_entered(_body: Node2D) -> void:
	# Damage ke player diurus Hurtbox player lewat meta "damage"; di sini cukup hilang.
	set_deferred("monitoring", false)
	set_deferred("monitorable", false)
	queue_free()


func _draw() -> void:
	var font: Font = ThemeDB.fallback_font
	match mode:
		Mode.STACKED:
			draw_string(font, Vector2(-3, -9), str(number), HORIZONTAL_ALIGNMENT_CENTER, -1, 8, Color.WHITE)
			if is_top:
				draw_arc(Vector2.ZERO, 8.0, 0.0, TAU, 20, Color(1, 0.9, 0.2), 1.0)
				draw_string(font, Vector2(10, 3), "TOP", HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(1, 0.9, 0.2))
		Mode.AIMING:
			# Garis bidik merah ke arah lemparan (koordinat dunia dikonversi ke lokal).
			draw_line(Vector2.ZERO, direction * 220.0, Color(1, 0.1, 0.1, 0.45), 2.0)
