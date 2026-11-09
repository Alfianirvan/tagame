extends SceneTree
## Skrip sekali jalan: menyimpan SpriteFrames tiap NPC (hasil NpcSprites.build()) ke
## res://scenes/entities/npc_frames/<nama>.tres untuk pratinjau di editor.
##   godot --headless --path . --script res://tools/save_npc_frames.gd

const NpcSprites := preload("res://scripts/entities/NpcSprites.gd")
const OUTPUT_DIR := "res://scenes/entities/npc_frames/"
const NPC_NAMES: Array[String] = ["Joko", "Arman", "Lilbah", "Dadang", "Megas", "Tedy"]


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	for npc_name in NPC_NAMES:
		var frames: SpriteFrames = NpcSprites.build(npc_name)
		if frames.get_animation_names().is_empty():
			print("Dilewati (sprite tidak ada): %s" % npc_name)
			continue
		var path: String = "%s%s.tres" % [OUTPUT_DIR, npc_name.to_lower()]
		var err: Error = ResourceSaver.save(frames, path)
		print("%s -> %s (%d animasi)" % [path, error_string(err), frames.get_animation_names().size()])
	quit()
