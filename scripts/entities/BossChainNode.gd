class_name BossChainNode
extends Area2D
## Node kristal rantai milik Ksatria Rantai (mewakili node linked list). Berada di layer 4 agar
## terkena hitbox player; pukulan diteruskan ke boss lewat signal. Node ujung (tail) bertanda kuning.

signal hit(index: int)

const RADIUS := 7.0

var index: int = 0                 # urutan dari kepala (0 = dekat boss)
var alive: bool = true
var is_tail: bool = false:
	set(value):
		is_tail = value
		queue_redraw()

var _t: float = 0.0


func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = RADIUS
	shape.shape = circle
	add_child(shape)
	z_index = 5


func _process(delta: float) -> void:
	if alive and is_tail:
		_t += delta
		queue_redraw()


## Dipanggil hitbox player (lihat Player._on_hitbox_target).
func take_hit(_damage: int, _from_pos: Vector2) -> void:
	if alive:
		hit.emit(index)


## Memutus node: hilang dari arena.
func cut() -> void:
	alive = false
	visible = false
	set_deferred("monitorable", false)


## Memulihkan node (rantai tumbuh lagi).
func restore() -> void:
	alive = true
	visible = true
	set_deferred("monitorable", true)
	queue_redraw()


func _draw() -> void:
	var font: Font = ThemeDB.fallback_font
	var body: Color = Color(0.45, 0.5, 0.95)
	if is_tail:
		var pulse: float = 0.5 + 0.5 * sin(_t * 8.0)
		draw_circle(Vector2.ZERO, RADIUS + 2.0 + pulse * 2.0, Color(1.0, 0.9, 0.2, 0.35))
		body = Color(1.0, 0.85, 0.2)
	var pts: PackedVector2Array = [Vector2(0, -RADIUS - 2), Vector2(RADIUS, 0), Vector2(0, RADIUS + 2), Vector2(-RADIUS, 0)]
	draw_colored_polygon(pts, body)
	draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]]), Color.BLACK, 1.0)
	draw_string(font, Vector2(-3, 4), str(index), HORIZONTAL_ALIGNMENT_CENTER, -1, 9, Color.BLACK)
	if is_tail:
		draw_string(font, Vector2(-10, -12), "UJUNG", HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(1, 0.9, 0.2))
