extends SceneTree
## Skrip sekali jalan: menyimpan SpriteFrames Raka (hasil PlayerSprites.build()) ke file .tres.
## Jalankan ulang bila sprite Raka berubah:
##   godot --headless --path . --script res://tools/save_player_frames.gd

const PlayerSprites := preload("res://scripts/entities/PlayerSprites.gd")
const OUTPUT := "res://scenes/entities/player_frames.tres"


func _init() -> void:
	var frames: SpriteFrames = PlayerSprites.build()
	var err: Error = ResourceSaver.save(frames, OUTPUT)
	if err == OK:
		print("Tersimpan: %s (%d animasi)" % [OUTPUT, frames.get_animation_names().size()])
	else:
		push_error("Gagal menyimpan: %s" % error_string(err))
	quit(0 if err == OK else 1)
