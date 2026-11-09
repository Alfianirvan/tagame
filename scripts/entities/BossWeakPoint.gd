class_name BossWeakPoint
extends Area2D
## Titik lemah boss (Golem Batu). Berada di layer 4 agar terkena hitbox player; take_hit diteruskan
## ke boss lewat signal. Label menampilkan indeks (mulai 0); titik giliran berikutnya menyala.

signal hit(index: int, damage: int)

const RADIUS := 7.0

var index: int = 0
var is_next: bool = false:
	set(value):
		is_next = value
		queue_redraw()

var _t: float = 0.0


func _ready() -> void:
	collision_layer = 4    # layer enemy: dikenali hitbox player
	collision_mask = 0
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = RADIUS
	shape.shape = circle
	add_child(shape)
	z_index = 5


func _process(delta: float) -> void:
	if is_next:
		_t += delta
		queue_redraw()


## Dipanggil hitbox player (lihat Player._on_hitbox_target).
func take_hit(damage: int, _from_pos: Vector2) -> void:
	hit.emit(index, damage)


func _draw() -> void:
	var font: Font = ThemeDB.fallback_font
	if is_next:
		var pulse: float = 0.5 + 0.5 * sin(_t * 8.0)
		draw_circle(Vector2.ZERO, RADIUS + 2.0 + pulse * 2.0, Color(1.0, 0.9, 0.2, 0.35))
		draw_circle(Vector2.ZERO, RADIUS, Color(1.0, 0.85, 0.15))
	else:
		draw_circle(Vector2.ZERO, RADIUS, Color(0.35, 0.3, 0.3, 0.9))
	draw_arc(Vector2.ZERO, RADIUS, 0.0, TAU, 16, Color.BLACK, 1.0)
	draw_string(font, Vector2(-3, 4), str(index), HORIZONTAL_ALIGNMENT_CENTER, -1, 10, Color.BLACK)
