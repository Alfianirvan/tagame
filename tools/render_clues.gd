extends Node
## Render area sekitar petunjuk saat langkah "cari petunjuk" aktif (butuh GPU).
## godot --path . --rendering-driver d3d12 res://tools/render_clues.tscn -- <scene> <chapter> <out_prefix> [stage] [Node1 Node2 ...]
func _ready() -> void:
	var a: PackedStringArray = OS.get_cmdline_user_args()
	var ch: int = int(a[1])
	GameManager.reset_state(); QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)
	for c in range(1, ch):
		GameManager.set_quest_stage(c, 3); GameManager.add_crystal(c)
	GameManager.unlocked_chapter = ch
	for c in range(1, 6): GameManager.mark_met("opening_ch%d" % c)
	if ch == 1: GameManager.set_story_flag("ch1_goblin_usir")
	if a.size() > 3: GameManager.set_quest_stage(ch, int(a[3]))
	QuestManager.refresh_active()
	var vils: Dictionary = {1: ["penjaga", "penebang", "sari"], 2: ["mandor", "mirah", "udin"], 3: ["wulan", "bahar", "nina"], 4: ["gilang", "laras", "bayu"], 5: ["wira", "sekar", "dimas"]}
	for v in vils.get(ch, []): QuestManager.mark_villager(ch, v)
	var vp := SubViewport.new()
	vp.size = Vector2i(960, 560)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var scn: Node = (load(a[0]) as PackedScene).instantiate()
	vp.add_child(scn)
	var cam := Camera2D.new()
	cam.zoom = Vector2(2, 2)
	vp.add_child(cam)
	cam.make_current()
	var targets: Array = Array(a.slice(4)) if a.size() > 4 else ["Petunjuk1", "Petunjuk2", "Petunjuk3"]
	for k in range(1, targets.size() + 1):
		var c: Node2D = scn.find_child(targets[k - 1], true, false)
		cam.position = c.global_position
		for i in 12: await get_tree().process_frame
		await RenderingServer.frame_post_draw
		vp.get_texture().get_image().save_png("%s%d.png" % [a[2], k])
		print("simpan ", k, " visible=", c.visible)
	get_tree().quit()
