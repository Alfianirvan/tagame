class_name RegionGate
extends StaticBody2D
## Gerbang kayu penghalang ke arena boss. Terkunci sampai Quest Tengah chapter-nya selesai
## (GameManager.quest_stage >= required_stage), lalu terbuka dengan animasi memudar.

signal opened

const FONT := preload("res://assets/fonts/Square-Black.ttf")

@export var chapter: int = 1
@export var required_stage: int = 2
@export var gate_height: float = 160.0        # panjang gerbang (vertikal)
@export var locked_text: String = "Gerbang terkunci.\nSelesaikan Quest Tengah."

var is_open: bool = false

var _shape: CollisionShape2D
var _hint_area: Area2D


func _ready() -> void:
	add_to_group("region_gate")
	collision_layer = 1
	collision_mask = 0
	_shape = CollisionShape2D.new()
	var rect: RectangleShape2D = RectangleShape2D.new()
	rect.size = Vector2(14, gate_height)
	_shape.shape = rect
	add_child(_shape)
	_hint_area = Area2D.new()
	_hint_area.collision_layer = 0
	_hint_area.collision_mask = 2
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = gate_height * 0.5 + 24.0
	shape.shape = circle
	_hint_area.add_child(shape)
	add_child(_hint_area)
	_hint_area.body_entered.connect(_on_body_entered)
	z_index = 2
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _refresh(true))
	_refresh(false)


func _refresh(animate: bool) -> void:
	if is_open or GameManager.get_quest_stage(chapter) < required_stage:
		queue_redraw()
		return
	is_open = true
	_shape.set_deferred("disabled", true)
	if animate:
		AudioManager.play_sfx("jingle_wilayah_terbuka")
		FloatingText.spawn(get_parent(), global_position + Vector2(0, -gate_height * 0.5 - 8), "Gerbang terbuka!", Color(0.6, 1.0, 0.6), 2.2)
		var tw: Tween = create_tween()
		tw.tween_property(self, "modulate:a", 0.0, 0.8)
		tw.tween_callback(func() -> void: visible = false)
	else:
		visible = false
	opened.emit()


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player") and not is_open:
		FloatingText.spawn(get_parent(), global_position + Vector2(-60, -gate_height * 0.5 - 8), locked_text, Color(1, 0.6, 0.5), 2.4)


## Pagar kayu tegak lurus sepanjang gerbang.
func _draw() -> void:
	var top: float = -gate_height / 2.0
	var y: float = top
	while y < gate_height / 2.0:
		draw_rect(Rect2(-7, y, 14, 18), Color(0.5, 0.33, 0.18))
		draw_rect(Rect2(-7, y, 14, 18), Color(0.25, 0.15, 0.08), false, 1.0)
		draw_rect(Rect2(-7, y, 14, 3), Color(0.65, 0.45, 0.25))
		y += 20.0
	draw_rect(Rect2(-9, top - 4, 18, 6), Color(0.3, 0.2, 0.1))
	draw_rect(Rect2(-9, gate_height / 2.0 - 2, 18, 6), Color(0.3, 0.2, 0.1))
