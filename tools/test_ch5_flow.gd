extends Node
## Uji main otomatis Chapter 5 (headless): masuk Desa Akar -> tanya 3 warga -> 3 petunjuk Tree -> kuis Tedy
## -> kabut ajaib di celah akar terbuka. Aksi pemain disimulasikan lewat API yang sama dengan node game.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch5_flow.tscn

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
	for ch in [1, 2, 3, 4]:
		GameManager.set_quest_stage(ch, 3)     # Chapter 1-4 tamat
	GameManager.unlocked_chapter = 5
	QuestManager.refresh_active()
	region = (load("res://scenes/world/Ch5_PohonDunia.tscn") as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== 0 Mulai: ", tracked())
	check(QuestManager.get_tracked_quest_id() == "ch5_awal", "quest aktif ch5_awal")
	check(not cloud_open("AwanGerbangDesa"), "kabut ajaib gerbang menutup")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk belum tampak sebelum tanya warga")
	check(QuestManager.get_dialog_for("tedy") == "tedy_ch5_tanya_warga", "Tedy: suruh tanya warga")
	for n in ["Tedy", "Wira", "Sekar", "Dimas"]:
		var spr: AnimatedSprite2D = node(n).get_node("AnimatedSprite2D") as AnimatedSprite2D
		check(spr.sprite_frames != null and spr.sprite_frames.get_animation_names().size() > 0, "sprite %s termuat" % n)
	check(node("PintuTedy") != null and ResourceLoader.exists("res://scenes/world/Interior_PosTedy.tscn"), "pintu & interior pos Tedy ada")
	var interior: Node = (load("res://scenes/world/Interior_PosTedy.tscn") as PackedScene).instantiate()
	check(interior != null, "interior pos Tedy bisa dimuat")
	interior.free()

	for v in ["wira", "sekar", "dimas"]:
		QuestManager.mark_villager(5, v)
	await frames(3)
	print("== 1 Warga: ", tracked())
	check((node("Petunjuk1") as CanvasItem).visible, "petunjuk tampak setelah tanya warga")

	for k in range(1, 4):
		await end_dialog("ch5_petunjuk_%d" % k)
	print("== 2 Petunjuk: ", tracked())
	check(QuestManager.is_ready("ch5_awal"), "Quest Awal Ch5 siap (kuis Tedy)")
	check(QuestManager.get_dialog_for("tedy") == "tedy_ch5_awal", "Tedy: dialog kuis")

	var lines: Array[String] = QuestManager.finish_quiz("ch5_awal", true)
	await frames(200)
	print("== 3 Kuis Tedy: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(5) == 1, "quest_stage Ch5 = 1")
	check(cloud_open("AwanGerbangDesa"), "kabut ajaib gerbang terbuka")
	check(int(GameManager.inventory.get("armor_besi", 0)) >= 1 or GameManager.equipment.values().has("armor_besi"), "hadiah awal: Armor Besi")

	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch5_petunjuk_3") and GameManager.get_quest_stage(5) == 1, "flag & tahap quest ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
