class_name Crystal
extends Area2D
## Kristal Struktur yang tertinggal setelah boss kalah. Diambil saat disentuh player:
## masuk GameManager.crystals lalu autosave (CLAUDE.md Bagian 8, "Save").

signal picked(chapter: int)

var chapter: int = 1
var _taken: bool = false
var _t: float = 0.0


## Membuat kristal di posisi dunia tertentu.
static func spawn(parent: Node, pos: Vector2, for_chapter: int) -> Crystal:
	var c: Crystal = Crystal.new()
	c.chapter = for_chapter
	parent.add_child(c)
	c.global_position = pos
	return c


func _ready() -> void:
	add_to_group("crystal")
	collision_layer = 0
	collision_mask = 2   # player
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 12.0
	shape.shape = circle
	add_child(shape)
	body_entered.connect(_on_body_entered)
	z_index = 10


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	GameManager.add_crystal(chapter)
	AudioManager.play_sfx("power_up")
	SaveManager.save_game()
	picked.emit(chapter)
	var tw: Tween = create_tween().set_parallel(true)
	tw.tween_property(self, "scale", Vector2(2, 2), 0.4)
	tw.tween_property(self, "modulate:a", 0.0, 0.4)
	tw.chain().tween_callback(queue_free)


## Berlian biru yang melayang naik-turun + kilau.
func _draw() -> void:
	var bob: float = sin(_t * 3.0) * 2.0
	var c: Vector2 = Vector2(0, -12 + bob)
	var pts: PackedVector2Array = [c + Vector2(0, -9), c + Vector2(6, 0), c + Vector2(0, 9), c + Vector2(-6, 0)]
	draw_circle(c, 11.0 + sin(_t * 4.0), Color(0.4, 0.8, 1.0, 0.18))
	draw_colored_polygon(pts, Color(0.35, 0.8, 1.0))
	draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]]), Color(0.9, 1.0, 1.0), 1.0)
	draw_line(c + Vector2(0, -9), c + Vector2(0, 9), Color(1, 1, 1, 0.5), 1.0)
	draw_circle(Vector2(0, 0), 4.0, Color(0, 0, 0, 0.25))
