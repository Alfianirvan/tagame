extends Node
## Uji main otomatis Chapter 3 (headless): masuk Kota Pelabuhan Antre -> tanya 3 warga -> 3 petunjuk Queue -> kuis Dadang
## -> kabut laut gerbang kota terbuka -> puzzle antrean warung -> barikade bajak laut hilang -> (Kristal) perahu karam jalan pintas hilang.
## Aksi pemain disimulasikan lewat API yang sama dengan node game.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch3_flow.tscn

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
	GameManager.set_quest_stage(1, 3)
	GameManager.set_quest_stage(2, 3)          # Chapter 1 & 2 tamat
	GameManager.unlocked_chapter = 3
	QuestManager.refresh_active()
	region = (load("res://scenes/world/Ch3_PelabuhanAntre.tscn") as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== 0 Mulai: ", tracked())
	check(QuestManager.get_tracked_quest_id() == "ch3_awal", "quest aktif ch3_awal")
	check(not cloud_open("AwanGerbangKota") and not cloud_open("AwanPerbatasan"), "kabut gerbang kota & perbatasan menutup")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk belum tampak sebelum tanya warga")
	check(QuestManager.get_dialog_for("dadang") == "dadang_ch3_tanya_warga", "Dadang: suruh tanya warga")
	for n in ["Dadang", "Wulan", "Bahar", "Nina"]:
		var spr: AnimatedSprite2D = node(n).get_node("AnimatedSprite2D") as AnimatedSprite2D
		check(spr.sprite_frames != null and spr.sprite_frames.get_animation_names().size() > 0, "sprite %s termuat" % n)
	check(node("PintuKedai") != null and ResourceLoader.exists("res://scenes/world/Interior_KedaiDadang.tscn"), "pintu & interior Kedai Dadang ada")
	var interior: Node = (load("res://scenes/world/Interior_KedaiDadang.tscn") as PackedScene).instantiate()
	check(interior != null, "interior Kedai Dadang bisa dimuat")
	interior.free()

	for v in ["wulan", "bahar", "nina"]:
		QuestManager.mark_villager(3, v)
	await frames(3)
	print("== 1 Warga: ", tracked())
	check((node("Petunjuk1") as CanvasItem).visible, "petunjuk tampak setelah tanya warga")

	for k in range(1, 4):
		await end_dialog("ch3_petunjuk_%d" % k)
	print("== 2 Petunjuk: ", tracked())
	check(QuestManager.is_ready("ch3_awal"), "Quest Awal Ch3 siap (kuis Dadang)")
	check(QuestManager.get_dialog_for("dadang") == "dadang_ch3_awal", "Dadang: dialog kuis")

	var lines: Array[String] = QuestManager.finish_quiz("ch3_awal", true)
	await frames(200)
	print("== 3 Kuis Dadang: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(3) == 1, "quest_stage Ch3 = 1")
	check(cloud_open("AwanGerbangKota") and not cloud_open("AwanPerbatasan"), "kabut gerbang kota terbuka, perbatasan masih")
	check(int(GameManager.inventory.get("zirah_kulit", 0)) >= 1 or GameManager.equipment.values().has("zirah_kulit"), "hadiah awal: Zirah Kulit")
	var st: PuzzleStation = node("StasiunAntrean") as PuzzleStation
	check(st != null and st._block_reason() == "", "stasiun antrean bisa dibuka")

	# Tahap 2: musuh perjalanan, barikade bajak laut (Quest Tengah), perahu karam (jalan pintas setelah Kristal)
	var mobs: int = 0
	for c in region.get_node("Objects").get_children():
		if c is Enemy:
			mobs += 1
	check(mobs >= 20, "musuh perjalanan terpasang (%d)" % mobs)
	var bar: StageBlocker = node("BarikadeBajakLaut") as StageBlocker
	var wreck: StageBlocker = node("PerahuKaram") as StageBlocker
	check(not bar.is_open and not wreck.is_open, "barikade & perahu karam masih menutup")
	st._open()
	await frames(2)
	st._puzzle.complete_puzzle()
	st._puzzle.close_puzzle()
	await frames(200)
	print("== 4 Antrean warung: ", tracked())
	check(GameManager.get_quest_stage(3) == 2, "quest_stage Ch3 = 2")
	check(bar.is_open and not (bar.get_node("Block") as TileMapLayer).collision_enabled, "barikade bajak laut hilang (tabrakan mati)")
	check(not wreck.is_open, "perahu karam masih menutup sebelum Kristal")
	check(int(GameManager.inventory.get("zirah_rantai", 0)) >= 1 or GameManager.equipment.values().has("zirah_rantai"), "hadiah tengah: Zirah Rantai")
	check(QuestManager.get_tracked_quest_id() == "ch3_akhir", "quest aktif ch3_akhir")
	GameManager.add_crystal(3)
	await frames(120)
	check(wreck.is_open and not (wreck.get_node("Block") as TileMapLayer).collision_enabled, "perahu karam tersingkir setelah Kristal Queue")
	check(not cloud_open("AwanPerbatasan"), "awan perbatasan masih ada sebelum kuis akhir")

	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch3_petunjuk_3") and GameManager.get_quest_stage(3) == 2 and GameManager.has_crystal(3), "flag, tahap quest & Kristal ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
