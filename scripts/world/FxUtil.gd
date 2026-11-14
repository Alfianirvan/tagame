class_name FxUtil
extends RefCounted
## Pembantu kecil untuk efek visual dari strip horizontal (FX Ninja Adventure): membuat AnimatedSprite2D siap main.


## AnimatedSprite2D dari strip `strip` (frame fw x fh). `foot` = origin di bawah-tengah frame (untuk objek di tanah).
static func anim(strip: Texture2D, fw: int, fh: int, fps: float, loop: bool = true, foot: bool = false) -> AnimatedSprite2D:
	var sf: SpriteFrames = SpriteFrames.new()
	sf.remove_animation("default")
	sf.add_animation("a")
	sf.set_animation_loop("a", loop)
	sf.set_animation_speed("a", fps)
	@warning_ignore("integer_division")
	for i in maxi(1, strip.get_width() / fw):
		var at: AtlasTexture = AtlasTexture.new()
		at.atlas = strip
		at.region = Rect2(i * fw, 0, fw, fh)
		sf.add_frame("a", at)
	var s: AnimatedSprite2D = AnimatedSprite2D.new()
	s.sprite_frames = sf
	if foot:
		s.offset = Vector2(0, -fh / 2.0)
	s.play("a")
	return s


## Efek sekali main di `parent` pada posisi `pos`, lalu hilang sendiri.
static func burst(parent: Node, pos: Vector2, strip: Texture2D, fw: int, fh: int, fps: float = 14.0, tint: Color = Color.WHITE, z: int = 8) -> void:
	var s: AnimatedSprite2D = anim(strip, fw, fh, fps, false)
	s.position = pos
	s.modulate = tint
	s.z_index = z
	parent.add_child(s)
	s.animation_finished.connect(s.queue_free)


## Label kecil bergaris tepi hitam (dipakai papan indeks obor, petunjuk, dsb).
static func small_label(text: String, size: int = 8, color: Color = Color(1, 0.95, 0.7)) -> Label:
	var l: Label = Label.new()
	l.text = text
	l.add_theme_font_override("font", preload("res://assets/fonts/Square-Black.ttf"))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 3)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l
