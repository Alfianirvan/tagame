extends Node
## Uji main otomatis Chapter 4 (headless): masuk Desa Simpul -> tanya 3 warga -> 3 petunjuk Linked List -> kuis Megas
## -> badai salju gerbang desa terbuka. Aksi pemain disimulasikan lewat API yang sama dengan node game.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch4_flow.tscn

var region: Node
var fails: int = 0


func check(cond: bool, what: String) -> void:
	if cond:
		print("  OK   ", what)
	else:
		fails += 1
		print("  GAGAL ", what)


func tracked() -> String:
	var id: String = QuestManager.get_tracked_quest_id()
	return "%s | %s" % [id, QuestManager.get_objective_text(id)]


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func node(n: String) -> Node:
	return region.find_child(n, true, false)


func cloud_open(n: String) -> bool:
	return (node(n) as CloudBarrier).is_open


func end_dialog(id: String) -> void:
	DialogManager.dialog_ended.emit(id)
	await frames(3)


func _ready() -> void:
	GameManager.reset_state()
	QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)
	for ch in [1, 2, 3]:
		GameManager.set_quest_stage(ch, 3)     # Chapter 1-3 tamat
	GameManager.unlocked_chapter = 4
	QuestManager.refresh_active()
	region = (load("res://scenes/world/Ch4_GuaRantai.tscn") as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== 0 Mulai: ", tracked())
	check(QuestManager.get_tracked_quest_id() == "ch4_awal", "quest aktif ch4_awal")
	check(not cloud_open("AwanGerbangDesa") and not cloud_open("AwanPerbatasan"), "badai salju gerbang & perbatasan menutup")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk belum tampak sebelum tanya warga")
	check(QuestManager.get_dialog_for("megas") == "megas_ch4_tanya_warga", "Megas: suruh tanya warga")
	for n in ["Megas", "Gilang", "Laras", "Bayu"]:
		var spr: AnimatedSprite2D = node(n).get_node("AnimatedSprite2D") as AnimatedSprite2D
		check(spr.sprite_frames != null and spr.sprite_frames.get_animation_names().size() > 0, "sprite %s termuat" % n)
	check(node("PintuMegas") != null and ResourceLoader.exists("res://scenes/world/Interior_RumahMegas.tscn"), "pintu & interior rumah Megas ada")
	var interior: Node = (load("res://scenes/world/Interior_RumahMegas.tscn") as PackedScene).instantiate()
	check(interior != null, "interior rumah Megas bisa dimuat")
	interior.free()

	for v in ["gilang", "laras", "bayu"]:
		QuestManager.mark_villager(4, v)
	await frames(3)
	print("== 1 Warga: ", tracked())
	check((node("Petunjuk1") as CanvasItem).visible, "petunjuk tampak setelah tanya warga")

	for k in range(1, 4):
		await end_dialog("ch4_petunjuk_%d" % k)
	print("== 2 Petunjuk: ", tracked())
	check(QuestManager.is_ready("ch4_awal"), "Quest Awal Ch4 siap (kuis Megas)")
	check(QuestManager.get_dialog_for("megas") == "megas_ch4_awal", "Megas: dialog kuis")

	var lines: Array[String] = QuestManager.finish_quiz("ch4_awal", true)
	await frames(200)
	print("== 3 Kuis Megas: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(4) == 1, "quest_stage Ch4 = 1")
	check(cloud_open("AwanGerbangDesa") and not cloud_open("AwanPerbatasan"), "badai salju gerbang terbuka, perbatasan masih")
	check(int(GameManager.inventory.get("tongkat_sihir", 0)) >= 1 or GameManager.equipment.values().has("tongkat_sihir"), "hadiah awal: Tongkat Sihir")

	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch4_petunjuk_3") and GameManager.get_quest_stage(4) == 1, "flag & tahap quest ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
