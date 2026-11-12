extends Node2D
## Hewan ternak desa (Ninja Adventure, sheet 32x16 = 2 frame 16x16, tampil scale 2).
## Berjalan acak pelan di sekitar titik asalnya, lalu diam sebentar. Tidak punya collision (hanya hiasan hidup).

@export var sheet: Texture2D
@export var wander_radius: float = 70.0
@export var speed: float = 14.0

var _sprite: AnimatedSprite2D
var _home: Vector2
var _target: Vector2
var _wait: float = 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	_home = position
	_target = position
	_sprite = AnimatedSprite2D.new()
	_sprite.scale = Vector2(2, 2)
	_sprite.offset = Vector2(0, -7)
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	for anim: String in ["diam", "jalan"]:
		sf.add_animation(anim)
		sf.set_animation_loop(anim, true)
		sf.set_animation_speed(anim, 2.0 if anim == "diam" else 5.0)
		for i in (1 if anim == "diam" else 2):
			var at := AtlasTexture.new()
			at.atlas = sheet
			at.region = Rect2(i * 16, 0, 16, 16)
			sf.add_frame(anim, at)
	_sprite.sprite_frames = sf
	add_child(_sprite)
	_sprite.play("diam")
	_wait = _rng.randf_range(0.5, 4.0)


func _process(delta: float) -> void:
	if _wait > 0.0:
		_wait -= delta
		if _wait <= 0.0:
			var a: float = _rng.randf() * TAU
			_target = _home + Vector2(cos(a), sin(a) * 0.6) * _rng.randf_range(10.0, wander_radius)
			_sprite.play("jalan")
		return
	var d: Vector2 = _target - position
	if d.length() < 2.0:
		_wait = _rng.randf_range(2.0, 6.0)
		_sprite.play("diam")
		return
	position += d.normalized() * speed * delta
	if absf(d.x) > 1.0:
		_sprite.flip_h = d.x < 0.0
