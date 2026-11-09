class_name EnemySprites
extends RefCounted
## Membangun SpriteFrames musuh dari res://assets/enemies/<orc|skeleton>/<Nama>/<Idle|Run|Death>/<Aksi>-Sheet.png.
## Idle & Run: frame persegi (ukuran = tinggi gambar). Death: jumlah frame dari data (lebar ÷ jumlah).
## Nama animasi: "idle", "run", "death". Semua sprite menghadap kanan (kiri = flip_h).

const DIR := "res://assets/enemies/"
const ACTIONS := {
	"idle": {"file": "Idle", "fps": 6.0, "loop": true},
	"run": {"file": "Run", "fps": 10.0, "loop": true},
	"death": {"file": "Death", "fps": 9.0, "loop": false},
}


static func build(sprite_folder: String, death_frames: int) -> SpriteFrames:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.remove_animation("default")
	for anim: String in ACTIONS:
		var info: Dictionary = ACTIONS[anim]
		var path: String = "%s%s/%s/%s-Sheet.png" % [DIR, sprite_folder, info["file"], info["file"]]
		# Idle & Run memakai versi bersenjata (tools/make_enemy_armed.py) bila ada
		var armed: String = "%s%s/%s/%s-Armed-Sheet.png" % [DIR, sprite_folder, info["file"], info["file"]]
		if anim != "death" and ResourceLoader.exists(armed):
			path = armed
		var texture: Texture2D = load(path) as Texture2D
		if texture == null:
			push_warning("Sprite musuh tidak ditemukan: %s" % path)
			continue
		var count: int = death_frames if anim == "death" else texture.get_width() / texture.get_height()
		var frame_w: int = texture.get_width() / count
		frames.add_animation(anim)
		frames.set_animation_speed(anim, info["fps"])
		frames.set_animation_loop(anim, info["loop"])
		for i in count:
			var atlas: AtlasTexture = AtlasTexture.new()
			atlas.atlas = texture
			atlas.region = Rect2(i * frame_w, 0, frame_w, texture.get_height())
			frames.add_frame(anim, atlas)
	_add_attack(frames, sprite_folder)
	return frames


## Animasi serang jarak dekat dari Attack/Attack-Sheet.png (6 frame 64x64, dibuat tools/make_enemy_attack.py):
## "windup" = frame 0-2 (bersiap), "strike" = frame 3-5 (menebas). FPS 3 = 1 detik per animasi pada speed_scale 1;
## Enemy.gd mengatur speed_scale supaya pas dengan lama windup / terjangan. Musuh jarak jauh tidak punya sheet ini.
static func _add_attack(frames: SpriteFrames, sprite_folder: String) -> void:
	var texture: Texture2D = load("%s%s/Attack/Attack-Sheet.png" % [DIR, sprite_folder]) as Texture2D
	if texture == null:
		return
	var size: int = texture.get_height()
	var parts: Dictionary = {"windup": [0, 1, 2], "strike": [3, 4, 5]}
	for anim: String in parts:
		frames.add_animation(anim)
		frames.set_animation_speed(anim, 3.0)
		frames.set_animation_loop(anim, false)
		for i: int in parts[anim]:
			var atlas: AtlasTexture = AtlasTexture.new()
			atlas.atlas = texture
			atlas.region = Rect2(i * size, 0, size, size)
			frames.add_frame(anim, atlas)
