class_name BossSprites
extends RefCounted
## Membangun SpriteFrames boss dari data/bosses.json (kunci "sprites") + offset "titik kaki".
##
## Tiap animasi punya ukuran frame berbeda, jadi offset dihitung dari titik kaki (x, y dalam frame)
## agar titik itu selalu tepat di origin node: offset = (lebar/2 - kaki.x, tinggi/2 - kaki.y).
## Offset per animasi disimpan di meta "offsets" (Dictionary anim -> Vector2) pada SpriteFrames.

const DIR := "res://assets/bosses/"


static func build(sprites: Dictionary) -> SpriteFrames:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.remove_animation("default")
	var offsets: Dictionary = {}
	for anim: String in sprites:
		var info: Dictionary = sprites[anim]
		var texture: Texture2D = load(DIR + String(info["file"])) as Texture2D
		if texture == null:
			push_warning("Sprite boss tidak ditemukan: %s" % info["file"])
			continue
		var count: int = int(info["frames"])
		var frame_w: int = texture.get_width() / count
		var frame_h: int = texture.get_height()
		frames.add_animation(anim)
		frames.set_animation_speed(anim, float(info.get("fps", 8.0)))
		frames.set_animation_loop(anim, bool(info.get("loop", false)))
		for i in count:
			var atlas: AtlasTexture = AtlasTexture.new()
			atlas.atlas = texture
			atlas.region = Rect2(i * frame_w, 0, frame_w, frame_h)
			frames.add_frame(anim, atlas)
		var foot: Array = info["foot"]
		offsets[anim] = Vector2(frame_w / 2.0 - float(foot[0]), frame_h / 2.0 - float(foot[1]))
	frames.set_meta("offsets", offsets)
	return frames
