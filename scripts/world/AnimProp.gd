extends Node2D
## Prop beranimasi dari strip horizontal (bunga, tanaman). Frame berukuran frame_w x frame_h, bermain berulang.

@export var strip: Texture2D
@export var frame_w: int = 16
@export var frame_h: int = 16
@export var fps: float = 4.0
@export var random_phase: bool = true


func _ready() -> void:
	var count: int = maxi(1, int(strip.get_width() / frame_w))
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	sf.add_animation("a")
	sf.set_animation_loop("a", true)
	sf.set_animation_speed("a", fps)
	for i in count:
		var at := AtlasTexture.new()
		at.atlas = strip
		at.region = Rect2(i * frame_w, 0, frame_w, frame_h)
		sf.add_frame("a", at)
	var s := AnimatedSprite2D.new()
	s.sprite_frames = sf
	s.offset = Vector2(0, -frame_h / 2.0)
	add_child(s)
	s.play("a")
	if random_phase:
		s.frame = randi() % count
