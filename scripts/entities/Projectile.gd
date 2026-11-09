class_name Projectile
extends Area2D
## Proyektil lurus: dipakai musuh jarak jauh (Shaman/Mage) dan senjata jarak jauh player.
##
## Layer: milik player = layer 4 (kena musuh lewat take_hit), milik musuh = layer 5
## (kena player lewat meta "damage" di Hurtbox). Hilang saat menabrak dinding/target/habis waktu.

const SCENE := preload("res://scenes/entities/Projectile.tscn")

var direction: Vector2 = Vector2.RIGHT
var speed: float = 120.0
var damage: int = 5
var from_player: bool = false
var color: Color = Color(1, 0.5, 0.2)
var lifetime: float = 2.0


## Membuat dan melepaskan proyektil. Mengembalikan node-nya.
static func launch(parent: Node, pos: Vector2, dir: Vector2, dmg: int, by_player: bool,
		spd: float = 120.0, col: Color = Color(1, 0.5, 0.2), life: float = 2.0) -> Projectile:
	var p: Projectile = SCENE.instantiate() as Projectile
	p.direction = dir.normalized()
	p.damage = dmg
	p.from_player = by_player
	p.speed = spd
	p.color = col
	p.lifetime = life
	parent.add_child(p)
	p.global_position = pos
	return p


func _ready() -> void:
	if from_player:
		collision_layer = 8      # layer 4: serangan player
		collision_mask = 1 | 4   # dinding + musuh
	else:
		collision_layer = 16     # layer 5: serangan musuh
		collision_mask = 1 | 2   # dinding + player
		set_meta("damage", damage)
	body_entered.connect(_on_body_entered)
	rotation = direction.angle()


func _physics_process(delta: float) -> void:
	position += direction * speed * delta
	lifetime -= delta
	if lifetime <= 0.0:
		queue_free()


func _on_body_entered(body: Node2D) -> void:
	if from_player and body.has_method("take_hit"):
		body.take_hit(damage, global_position)
	# Proyektil musuh: damage ke player ditangani Hurtbox player lewat meta "damage".
	set_deferred("monitoring", false)
	set_deferred("monitorable", false)
	queue_free()


func _draw() -> void:
	draw_circle(Vector2.ZERO, 4.0, color)
	draw_circle(Vector2.ZERO, 2.0, color.lightened(0.7))
