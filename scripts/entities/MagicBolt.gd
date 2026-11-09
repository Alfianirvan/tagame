class_name MagicBolt
extends Area2D
## Bola sihir tongkat (Staff Cast): terbang lurus dengan animasi Magic_Bolt (16x16 x4).
## Saat kena musuh: beri damage, mainkan Magic_Hit (32x32 x5), dan SFX sihir.
## Layer: milik player = layer 4 (kena musuh lewat take_hit), mask dinding + musuh.

const BOLT_SHEET := preload("res://assets/characters/player/Magic_Bolt-Sheet.png")
const HIT_SHEET := preload("res://assets/characters/player/Magic_Hit-Sheet.png")
const BOLT_FRAMES := 4
const HIT_FRAMES := 5

var direction: Vector2 = Vector2.RIGHT
var speed: float = 200.0
var damage: int = 5
var lifetime: float = 1.2

var _sprite: AnimatedSprite2D
var _done: bool = false


## Membuat dan melepaskan bola sihir dari posisi pos ke arah dir.
static func launch(parent: Node, pos: Vector2, dir: Vector2, dmg: int) -> MagicBolt:
	var b: MagicBolt = MagicBolt.new()
	b.direction = dir.normalized()
	b.damage = dmg
	parent.add_child(b)
	b.global_position = pos
	return b


func _ready() -> void:
	collision_layer = 8        # layer 4: serangan player
	collision_mask = 1 | 4     # dinding + musuh
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 6.0
	shape.shape = circle
	add_child(shape)

	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = _build_frames()
	_sprite.play("bolt")
	_sprite.rotation = direction.angle()   # sheet menghadap kanan
	add_child(_sprite)

	body_entered.connect(_on_target)
	area_entered.connect(_on_target)


func _physics_process(delta: float) -> void:
	if _done:
		return
	position += direction * speed * delta
	lifetime -= delta
	if lifetime <= 0.0:
		queue_free()


func _on_target(target: Node) -> void:
	if _done:
		return
	var victim: Node = target
	if not victim.has_method("take_hit") and victim.get_parent() and victim.get_parent().has_method("take_hit"):
		victim = victim.get_parent()
	if victim.has_method("take_hit"):
		victim.take_hit(damage, global_position)
	_impact()


## Berhenti terbang lalu mainkan animasi Magic_Hit di titik tumbukan.
func _impact() -> void:
	_done = true
	set_deferred("monitoring", false)
	AudioManager.play_sfx("sihir", 0.1)
	_sprite.rotation = 0.0
	_sprite.play("hit")
	_sprite.animation_finished.connect(queue_free)


func _build_frames() -> SpriteFrames:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.remove_animation("default")
	_add_strip(frames, "bolt", BOLT_SHEET, BOLT_FRAMES, 14.0, true)
	_add_strip(frames, "hit", HIT_SHEET, HIT_FRAMES, 16.0, false)
	return frames


func _add_strip(frames: SpriteFrames, anim: String, sheet: Texture2D, count: int, fps: float, loop: bool) -> void:
	frames.add_animation(anim)
	frames.set_animation_speed(anim, fps)
	frames.set_animation_loop(anim, loop)
	@warning_ignore("integer_division")
	var w: int = sheet.get_width() / count
	for i in count:
		var atlas: AtlasTexture = AtlasTexture.new()
		atlas.atlas = sheet
		atlas.region = Rect2(i * w, 0, w, sheet.get_height())
		frames.add_frame(anim, atlas)
