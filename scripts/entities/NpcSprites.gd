extends RefCounted
## Membangun SpriteFrames NPC buatan kelompok dari res://assets/characters/npc/.
## File: <Nama>_<Idle|Walk>_<Down|Side|Up>-Sheet.png, atau <Nama>_<Idle|Walk>-Sheet.png (tanpa arah =
## menghadap samping, seperti Lilbah). Frame persegi: ukuran frame = tinggi gambar.
## Nama animasi: "idle_down", "walk_side", dst. Side menghadap kanan; kiri = flip_h.

const DIR := "res://assets/characters/npc/"
const ACTIONS := {"idle": {"file": "Idle", "fps": 6.0}, "walk": {"file": "Walk", "fps": 10.0}}
const DIRECTIONS := {"down": "Down", "side": "Side", "up": "Up"}


static func build(npc_name: String) -> SpriteFrames:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.remove_animation("default")
	for action: String in ACTIONS:
		var info: Dictionary = ACTIONS[action]
		for dir: String in DIRECTIONS:
			var path: String = "%s%s_%s_%s-Sheet.png" % [DIR, npc_name, info["file"], DIRECTIONS[dir]]
			if not ResourceLoader.exists(path) and dir == "side":
				path = "%s%s_%s-Sheet.png" % [DIR, npc_name, info["file"]]  # tanpa arah
			if not ResourceLoader.exists(path):
				continue
			_add_animation(frames, "%s_%s" % [action, dir], load(path) as Texture2D, info["fps"])
	return frames


static func _add_animation(frames: SpriteFrames, anim: String, texture: Texture2D, fps: float) -> void:
	var size: int = texture.get_height()
	frames.add_animation(anim)
	frames.set_animation_speed(anim, fps)
	frames.set_animation_loop(anim, true)
	@warning_ignore("integer_division")
	for i in texture.get_width() / size:
		var atlas: AtlasTexture = AtlasTexture.new()
		atlas.atlas = texture
		atlas.region = Rect2(i * size, 0, size, size)
		frames.add_frame(anim, atlas)
