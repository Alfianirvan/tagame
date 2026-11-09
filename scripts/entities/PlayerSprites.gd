extends RefCounted
## Membangun SpriteFrames Raka dari file Raka_<Aksi>_<Arah>-Sheet.png (frame 64x64).
## Nama animasi: "<aksi>_<arah>", contoh "walk_down", "slice_side", "death_up".
## Arah kiri = arah "side" dengan flip_h (diatur oleh Player.gd).

const DIR := "res://assets/characters/player/"
const FRAME := 64

## aksi -> {file: nama di file, fps, loop}
const ACTIONS := {
	"idle": {"file": "Idle", "fps": 6.0, "loop": true},
	"walk": {"file": "Walk", "fps": 10.0, "loop": true},
	"run": {"file": "Run", "fps": 12.0, "loop": true},
	"slice": {"file": "Slice", "fps": 16.0, "loop": false},
	"pierce": {"file": "Pierce", "fps": 16.0, "loop": false},
	"crush": {"file": "Crush", "fps": 10.0, "loop": false},
	"hit": {"file": "Hit", "fps": 10.0, "loop": false},
	"death": {"file": "Death", "fps": 8.0, "loop": false},
	"collect": {"file": "Collect", "fps": 10.0, "loop": false},
}
const DIRECTIONS := {"down": "Down", "side": "Side", "up": "Up"}
## Animasi serang pedang & tongkat (8 frame 64x64, 14 fps, tidak loop): nama animasi -> awalan file.
const WEAPON_ANIMS := {
	"sword_slash": "Raka_Sword_Slash",
	"sword_pierce": "Raka_Sword_Pierce",
	"staff_cast": "Raka_Staff_Cast",
	"staff_slam": "Raka_Staff_Slam",
}
const WEAPON_FPS := 14.0


static func build() -> SpriteFrames:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.remove_animation("default")
	for action: String in ACTIONS:
		var info: Dictionary = ACTIONS[action]
		for dir: String in DIRECTIONS:
			var dir_name: String = DIRECTIONS[dir]
			if action == "pierce" and dir == "up":
				dir_name = "Top"  # file tusuk ke atas bernama "Top"
			var path: String = "%sRaka_%s_%s-Sheet.png" % [DIR, info["file"], dir_name]
			var texture: Texture2D = load(path) as Texture2D
			if texture == null:
				push_warning("Sprite Raka tidak ditemukan: %s" % path)
				continue
			var anim: String = "%s_%s" % [action, dir]
			frames.add_animation(anim)
			frames.set_animation_speed(anim, info["fps"])
			frames.set_animation_loop(anim, info["loop"])
			@warning_ignore("integer_division")
			for i in texture.get_width() / FRAME:
				var atlas: AtlasTexture = AtlasTexture.new()
				atlas.atlas = texture
				atlas.region = Rect2(i * FRAME, 0, FRAME, FRAME)
				frames.add_frame(anim, atlas)
	add_weapon_animations(frames)
	return frames


## Animasi serang tanpa senjata ("atk_<arah>", 8 frame) dari pose idle/lari Raka.
## Sprite serang lama menggambar kapak di tangan; senjata sekarang digambar terpisah oleh Player.gd
## sesuai item yang dipasang (atau kepalan bila tangan kosong). Aman dipanggil berulang.
static func add_attack_animations(frames: SpriteFrames) -> void:
	for dir: String in ["down", "side", "up"]:
		var anim: String = "atk_" + dir
		if frames.has_animation(anim):
			continue
		var idle: String = "idle_" + dir
		var run: String = "run_" + dir
		if not frames.has_animation(idle) or not frames.has_animation(run):
			continue
		frames.add_animation(anim)
		frames.set_animation_speed(anim, 16.0)
		frames.set_animation_loop(anim, false)
		# frame 0-1 bersiap, 2-5 (hitbox aktif) pose melangkah, 6-7 pulih
		for step: Array in [[idle, 0], [idle, 0], [run, 1], [run, 1], [run, 2], [run, 2], [idle, 0], [idle, 0]]:
			var n: int = frames.get_frame_count(step[0])
			frames.add_frame(anim, frames.get_frame_texture(step[0], mini(int(step[1]), n - 1)))


## Menambahkan animasi pedang/tongkat (sword_slash_*, sword_pierce_*, staff_cast_*, staff_slam_*).
## Aman dipanggil berulang: animasi yang sudah ada dilewati. Arah kiri = "side" di-flip oleh Player.gd.
static func add_weapon_animations(frames: SpriteFrames) -> void:
	for key: String in WEAPON_ANIMS:
		for dir: String in DIRECTIONS:
			var anim: String = "%s_%s" % [key, dir]
			if frames.has_animation(anim):
				continue
			var path: String = "%s%s_%s-Sheet.png" % [DIR, WEAPON_ANIMS[key], DIRECTIONS[dir]]
			var texture: Texture2D = load(path) as Texture2D
			if texture == null:
				push_warning("Sprite serang tidak ditemukan: %s" % path)
				continue
			frames.add_animation(anim)
			frames.set_animation_speed(anim, WEAPON_FPS)
			frames.set_animation_loop(anim, false)
			@warning_ignore("integer_division")
			for i in texture.get_width() / FRAME:
				var atlas: AtlasTexture = AtlasTexture.new()
				atlas.atlas = texture
				atlas.region = Rect2(i * FRAME, 0, FRAME, FRAME)
				frames.add_frame(anim, atlas)
