class_name Shockwave
extends Node2D
## Gelombang kejut cincin yang merambat dari titik hantaman. Mengenai player satu kali bila
## player berada di pita cincin (dodge dengan i-frame bisa menembusnya).

var damage: int = 10
var max_radius: float = 90.0
var speed: float = 130.0
var width: float = 12.0

var _radius: float = 0.0
var _hit: bool = false


static func spawn(parent: Node, pos: Vector2, dmg: int, radius_max: float, wave_speed: float, wave_width: float) -> Shockwave:
	var s: Shockwave = Shockwave.new()
	s.damage = dmg
	s.max_radius = radius_max
	s.speed = wave_speed
	s.width = wave_width
	parent.add_child(s)
	s.global_position = pos
	return s


func _ready() -> void:
	z_index = -1   # di bawah sprite, di atas lantai


func _physics_process(delta: float) -> void:
	_radius += speed * delta
	if not _hit:
		var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
		if player != null and player.has_method("take_hit"):
			var d: float = global_position.distance_to(player.global_position)
			if absf(d - _radius) <= width * 0.5 + 4.0:
				_hit = true
				player.take_hit(damage, global_position)
	queue_redraw()
	if _radius >= max_radius:
		queue_free()


func _draw() -> void:
	var fade: float = 1.0 - _radius / max_radius
	draw_arc(Vector2.ZERO, _radius, 0.0, TAU, 48, Color(0.85, 0.75, 0.55, 0.3 + 0.6 * fade), width, false)
	draw_arc(Vector2.ZERO, _radius, 0.0, TAU, 48, Color(1, 1, 1, 0.5 * fade), 2.0, false)
