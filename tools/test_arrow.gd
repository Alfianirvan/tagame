extends Node
## Uji regresi panah penunjuk (headless): dari beberapa titik di sekitar Dusun Ranting (Ch5), panah harus mengarah ke Pak Banyu
## yang berada di jalan cabang, bukan mengikuti jalur utama yang menjauh. Jalankan: godot --headless --path . res://tools/test_arrow.tscn

func _ready() -> void:
	GameManager.reset_state()
	QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)
	for ch in [1, 2, 3, 4]:
		GameManager.set_quest_stage(ch, 3)
	GameManager.set_quest_stage(5, 1)
	GameManager.unlocked_chapter = 5
	QuestManager.refresh_active()
	var region: Node = (load("res://scenes/world/Ch5_PohonDunia.tscn") as PackedScene).instantiate()
	add_child(region)
	var arrow := QuestArrow.new()
	add_child(arrow)
	for i in 10:
		await get_tree().process_frame
	var player: Node2D = region.player
	var banyu: Node2D = region.find_child("Banyu", true, false)
	var cam := Camera2D.new()
	player.add_child(cam)
	cam.make_current()
	var bad: int = 0
	for tile in [Vector2(150, 112), Vector2(150, 110), Vector2(150, 108), Vector2(152, 106), Vector2(140, 108), Vector2(120, 110), Vector2(100, 98)]:
		player.global_position = tile * 16 + Vector2(8, 8)
		arrow.refresh_target()
		for i in 4:
			await get_tree().process_frame
		var to_t: Vector2 = (banyu.global_position - player.global_position).normalized()
		var dot: float = arrow._arrow_dir.dot(to_t)
		var ok: bool = dot > -0.2 or not arrow.visible
		if not ok:
			bad += 1
		print("Raka ", tile, " target=", arrow._target.name if arrow._target else "-", " arah panah . arah target = %.2f" % dot, " terlihat=", arrow.visible, "  ", "OK" if ok else "SALAH")
	print("HASIL: ", "SEMUA OK" if bad == 0 else "%d SALAH" % bad)
	get_tree().quit()
