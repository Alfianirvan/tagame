extends Node
## Uji main otomatis Desa Algoria (headless): desa besar termuat -> Raka mulai di depan rumahnya -> warga & sprite termuat
## -> rumah Raka bisa dimasuki -> kuis Joko (Quest Awal ch0) -> hadiah -> papan jalan ke Hutan Indeks -> pulang dari Ch1 muncul di gerbang.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch0_flow.tscn

var fails: int = 0


func check(cond: bool, what: String) -> void:
	if cond:
		print("  OK   ", what)
	else:
		fails += 1
		print("  GAGAL ", what)


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _ready() -> void:
	GameManager.reset_state()
	QuestManager.reset_state()
	QuestManager.refresh_active()
	var village: Node = (load("res://scenes/world/Village.tscn") as PackedScene).instantiate()
	add_child(village)
	await frames(10)
	var player: Node2D = village.get_node("Objects/Player") as Node2D
	var start: Node2D = village.get_node("PlayerStart") as Node2D
	check(village.map_size.x >= 2000 and village.map_size.y >= 1500, "Desa Algoria besar (%s px)" % village.map_size)
	check(player.global_position.distance_to(start.global_position) < 2.0, "Raka mulai di depan rumahnya")
	check(QuestManager.get_tracked_quest_id() == "ch0_awal", "quest aktif ch0_awal")
	for n in ["Joko", "PedagangAlun", "Ani", "Rudi", "Sumi", "Bagas"]:
		var npc: Node = village.find_child(n, true, false)
		var spr: AnimatedSprite2D = npc.get_node("AnimatedSprite2D") as AnimatedSprite2D if npc else null
		check(spr != null and spr.sprite_frames != null and spr.sprite_frames.get_animation_names().size() > 0, "NPC & sprite %s termuat" % n)
	check(QuestManager.get_dialog_for("joko") == "joko", "Joko: dialog prolog + kuis")
	check(village.find_child("PintuRaka", true, false) != null, "pintu rumah Raka ada")
	var interior: Node = (load("res://scenes/world/Interior_RumahRaka.tscn") as PackedScene).instantiate()
	check(interior != null, "interior rumah Raka bisa dimuat")
	interior.free()
	var exit: RegionExit = village.find_child("GerbangHutan", true, false) as RegionExit
	check(exit != null and exit.to_chapter == 1, "papan jalan ke Hutan Indeks di gerbang utara")
	var lines: Array[String] = QuestManager.finish_quiz("ch0_awal", true)
	await frames(120)
	print("== Kuis Joko: hadiah ", lines)
	check(GameManager.get_quest_stage(0) >= 1, "Quest Awal desa selesai")
	check(int(GameManager.inventory.get("pedang_kayu", 0)) >= 1 or GameManager.equipment.values().has("pedang_kayu"), "hadiah: Pedang Kayu")
	village.queue_free()
	await frames(5)
	# pulang dari Hutan Indeks: muncul di gerbang hutan (marker FromNext), bukan di depan rumah
	GameManager.return_from_chapter = 1
	var v2_: Node = (load("res://scenes/world/Village.tscn") as PackedScene).instantiate()
	add_child(v2_)
	await frames(10)
	var p2: Node2D = v2_.get_node("Objects/Player") as Node2D
	var fn: Node2D = v2_.get_node("FromNext") as Node2D
	check(p2.global_position.distance_to(fn.global_position) < 2.0, "pulang dari Ch1 muncul di gerbang hutan")
	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
