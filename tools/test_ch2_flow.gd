extends Node
## Uji main otomatis Chapter 2 (headless): masuk Kampung Tumpuk -> tanya 3 warga -> 3 petunjuk -> kuis Lilbah
## -> kabut debu gerbang desa terbuka -> puzzle tumpukan peti -> peti lorong tambang hilang -> (Kristal) longsoran jalan pintas terbuka. Aksi pemain disimulasikan lewat API yang sama dengan node game.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch2_flow.tscn

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
	GameManager.set_quest_stage(1, 3)          # Chapter 1 tamat
	GameManager.unlocked_chapter = 2
	QuestManager.refresh_active()
	region = (load("res://scenes/world/Ch2_TambangTumpuk.tscn") as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== 0 Mulai: ", tracked())
	check(QuestManager.get_tracked_quest_id() == "ch2_awal", "quest aktif ch2_awal")
	check(not cloud_open("AwanGerbangDesa") and not cloud_open("AwanPerbatasan"), "kabut gerbang desa & perbatasan menutup")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk belum tampak sebelum tanya warga")
	check(QuestManager.get_dialog_for("lilbah") == "lilbah_ch2_tanya_warga", "Lilbah: suruh tanya warga")
	for n in ["Lilbah", "Mandor", "Mirah", "Udin"]:
		var spr: AnimatedSprite2D = node(n).get_node("AnimatedSprite2D") as AnimatedSprite2D
		check(spr.sprite_frames != null and spr.sprite_frames.get_animation_names().size() > 0, "sprite %s termuat" % n)

	for v in ["mandor", "mirah", "udin"]:
		QuestManager.mark_villager(2, v)
	await frames(3)
	print("== 1 Warga: ", tracked())
	check((node("Petunjuk1") as CanvasItem).visible, "petunjuk tampak setelah tanya warga")

	for k in range(1, 4):
		await end_dialog("ch2_petunjuk_%d" % k)
	print("== 2 Petunjuk: ", tracked())
	check(QuestManager.is_ready("ch2_awal"), "Quest Awal Ch2 siap (kuis Lilbah)")
	check(QuestManager.get_dialog_for("lilbah") == "lilbah_ch2_awal", "Lilbah: dialog kuis")

	var lines: Array[String] = QuestManager.finish_quiz("ch2_awal", true)
	await frames(200)
	print("== 3 Kuis Lilbah: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(2) == 1, "quest_stage Ch2 = 1")
	check(cloud_open("AwanGerbangDesa") and not cloud_open("AwanPerbatasan"), "kabut debu gerbang desa terbuka, perbatasan masih")
	var st: PuzzleStation = node("StasiunPeti") as PuzzleStation
	check(st._block_reason() == "", "stasiun tumpukan peti bisa dibuka")

	# Tahap 2: musuh perjalanan, peti penutup lorong tambang, longsoran jalan pintas
	var mobs: int = 0
	for c in region.get_node("Objects").get_children():
		if c is Enemy:
			mobs += 1
	check(mobs >= 20, "musuh perjalanan terpasang (%d)" % mobs)
	var crates: StageBlocker = node("PetiTerowongan") as StageBlocker
	var rocks: StageBlocker = node("LongsoranPintas") as StageBlocker
	check(not crates.is_open and not rocks.is_open, "peti lorong & longsoran masih menutup")
	st._open()
	await frames(2)
	st._puzzle.complete_puzzle()
	st._puzzle.close_puzzle()
	await frames(200)
	print("== 4 Tumpukan peti: ", tracked())
	check(GameManager.get_quest_stage(2) == 2, "quest_stage Ch2 = 2")
	check(crates.is_open and not (crates.get_node("Block") as TileMapLayer).collision_enabled, "peti lorong tambang hilang (tabrakan mati)")
	check(not rocks.is_open, "longsoran jalan pintas masih menutup sebelum Kristal")
	check(int(GameManager.inventory.get("pedang_besi", 0)) >= 1 or GameManager.equipment.values().has("pedang_besi"), "hadiah tengah: Pedang Besi")
	check(QuestManager.get_tracked_quest_id() == "ch2_akhir", "quest aktif ch2_akhir (langkah boss)")
	check(QuestManager.get_dialog_for("lilbah") == "lilbah_ch2_tunggu_boss", "Lilbah: arahkan ke Penyihir Menara")

	# Tahap 3: Penyihir Menara kalah -> Kristal -> longsoran terbuka -> kembali ke Lilbah -> kuis -> tamat
	var boss: Boss = region.boss
	check(boss != null and boss is BossPenyihir, "Penyihir Menara ada di aula tambang")
	if boss:
		boss.apply_damage(99999)
	await frames(420)
	var cr: Node = get_tree().get_first_node_in_group("crystal")
	if cr != null and cr.has_method("_on_body_entered"):
		cr._on_body_entered(region.player)
	else:
		GameManager.add_crystal(2)
	await frames(120)
	print("== 5 Penyihir: ", tracked())
	check(GameManager.has_crystal(2), "Kristal Stack didapat")
	check(rocks.is_open and not (rocks.get_node("Block") as TileMapLayer).collision_enabled, "longsoran jalan pintas terbuka setelah Kristal Stack")
	check(QuestManager.is_ready("ch2_akhir") and QuestManager.get_dialog_for("lilbah") == "lilbah_ch2_akhir", "Lilbah: dialog kuis akhir")
	check(QuestManager.get_objective_text("ch2_akhir").contains("Lilbah"), "pelacak: bawa Kristal ke Lilbah")
	check(not cloud_open("AwanPerbatasan"), "awan perbatasan masih ada sebelum kuis akhir")

	lines = QuestManager.finish_quiz("ch2_akhir", true)
	await frames(200)
	print("== 6 Tamat: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(2) == 3 and GameManager.unlocked_chapter >= 3, "Chapter 2 selesai, Chapter 3 terbuka")
	check(cloud_open("AwanPerbatasan"), "awan perbatasan ke Pelabuhan Antre hilang")
	check(int(GameManager.inventory.get("data_fragment", 0)) >= 1, "Data Fragment didapat")
	check(QuestManager.get_dialog_for("lilbah") == "lilbah_ch2_akhir_sukses", "Lilbah: dialog penutup")

	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch2_petunjuk_3") and GameManager.has_crystal(2), "flag & Kristal ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
