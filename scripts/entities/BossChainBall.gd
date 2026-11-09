class_name BossChainBall
extends Area2D
## Bola berantai Ksatria Rantai: meluncur keluar sampai jarak maksimum, lalu ditarik kembali ke boss.
## Rantai digambar dari boss ke bola. Damage lewat meta "damage" (dibaca Hurtbox player, layer 5).

var owner_boss: Node2D
var direction: Vector2 = Vector2.RIGHT
var speed: float = 220.0
var max_range: float = 150.0
var damage: int = 12

var _origin: Vector2
var _returning: bool = false


static func launch(boss: Node2D, from_pos: Vector2, dir: Vector2, rng: float, spd: float, dmg: int) -> BossChainBall:
	var b: BossChainBall = BossChainBall.new()
	b.owner_boss = boss
	b.direction = dir.normalized()
	b.max_range = rng
	b.speed = spd
	b.damage = dmg
	boss.get_parent().add_child(b)
	b.global_position = from_pos
	b._origin = from_pos
	return b


func _ready() -> void:
	collision_layer = 16     # layer 5: serangan musuh
	collision_mask = 0
	monitoring = false
	set_meta("damage", damage)
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 7.0
	shape.shape = circle
	add_child(shape)
	z_index = 8
	AudioManager.play_sfx("serang_tebas", 0.1)


func _physics_process(delta: float) -> void:
	if not is_instance_valid(owner_boss):
		queue_free()
		return
	if not _returning:
		position += direction * speed * delta
		if global_position.distance_to(_origin) >= max_range:
			_returning = true
	else:
		var home: Vector2 = owner_boss.global_position + Vector2(0, -14)
		var to_home: Vector2 = home - global_position
		if to_home.length() <= speed * delta + 4.0:
			queue_free()
			return
		position += to_home.normalized() * speed * delta
	queue_redraw()


func _draw() -> void:
	if not is_instance_valid(owner_boss):
		return
	var home: Vector2 = owner_boss.global_position + Vector2(0, -14) - global_position
	draw_line(Vector2.ZERO, home, Color(0.6, 0.6, 0.65), 2.0)
	draw_circle(Vector2.ZERO, 7.0, Color(0.2, 0.2, 0.25))
	draw_arc(Vector2.ZERO, 7.0, 0.0, TAU, 16, Color(0.8, 0.8, 0.85), 1.0)
	for i in 6:
		var v: Vector2 = Vector2.from_angle(i * TAU / 6.0) * 7.0
		draw_line(v, v * 1.35, Color(0.8, 0.8, 0.85), 1.5)
