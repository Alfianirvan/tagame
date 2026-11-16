extends Node
## Uji main otomatis Chapter 5 (headless): masuk Desa Akar -> tanya 3 warga -> 3 petunjuk Tree -> kuis Tedy
## -> kabut ajaib di celah akar terbuka -> labirin bercabang -> segel cabang memudar -> King Subiyan -> Kristal -> akar tumbang menyusut -> kuis akhir Tedy -> TAMAT. Aksi pemain disimulasikan lewat API yang sama dengan node game.
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
		GameManager.set_quest_stage(ch, 3)     # Chapter 1-4 tamat (Kristalnya sudah didapat)
		GameManager.add_crystal(ch)
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

	var st: PuzzleStation = node("StasiunLabirin") as PuzzleStation
	check(st != null and st._block_reason() != "", "stasiun labirin terkunci sebelum misi Dusun Ranting")

	# Dusun Ranting: temui Pak Banyu -> nyalakan lentera ranting (pre-order) -> baru labirin bercabang
	var lt: PuzzleStation = node("StasiunLentera") as PuzzleStation
	check(node("Banyu") != null and lt != null, "Dusun Ranting: Pak Banyu & lentera ranting terpasang")
	check(QuestManager.get_current_step("ch5_tengah").get("id", "") == "dusun", "langkah aktif: temui Pak Banyu")
	check(QuestManager.get_dialog_for("banyu") == "banyu_ch5_minta", "Banyu: dialog minta tolong")
	check(lt._block_reason() != "", "lentera belum bisa dinyalakan sebelum bicara dengan Banyu")
	await end_dialog("banyu_ch5_minta")
	check(lt._block_reason() == "", "lentera ranting bisa dinyalakan")
	lt._open()
	await frames(2)
	var tt: TreeTraversal = lt._puzzle as TreeTraversal
	tt._on_lantern(2)                       # salah: bukan akar -> semua padam
	check(tt.lit.is_empty(), "salah urutan memadamkan semua lentera")
	for i in TreeTraversal.PREORDER:
		tt._on_lantern(i)
	check(tt.is_solved, "lentera menyala sesuai pre-order")
	tt.close_puzzle()
	await frames(60)
	print("== 3b Dusun Ranting: ", tracked())
	check(GameManager.has_story_flag("ch5_lentera_ranting") and GameManager.get_quest_stage(5) == 1, "langkah lentera selesai, quest tengah belum")
	check(QuestManager.get_dialog_for("banyu") == "banyu", "Banyu: dialog terima kasih")
	check(st._block_reason() == "", "stasiun labirin bercabang bisa dibuka")

	# Tahap 2: musuh perjalanan, segel cabang di kaki tangga akar (Quest Tengah), akar tumbang (jalan pintas setelah Kristal)
	var mobs: int = 0
	for c in region.get_node("Objects").get_children():
		if c is Enemy:
			mobs += 1
	check(mobs >= 20, "musuh perjalanan terpasang (%d)" % mobs)
	var bar: StageBlocker = node("SegelCabang") as StageBlocker
	var sc: StageBlocker = node("AkarTumbang") as StageBlocker
	check(not bar.is_open and not sc.is_open, "segel cabang & akar tumbang masih menutup")
	st._open()
	await frames(2)
	st._puzzle.complete_puzzle()
	st._puzzle.close_puzzle()
	await frames(200)
	print("== 4 Labirin: ", tracked())
	check(GameManager.get_quest_stage(5) == 2, "quest_stage Ch5 = 2")
	check(bar.is_open and not (bar.get_node("Block") as TileMapLayer).collision_enabled, "segel cabang memudar (tabrakan mati)")
	check(not sc.is_open, "akar tumbang masih menutup sebelum Kristal")
	check(int(GameManager.inventory.get("perisai_legendaris", 0)) >= 1 or GameManager.equipment.values().has("perisai_legendaris"), "hadiah tengah: Perisai Legendaris")
	check(QuestManager.get_tracked_quest_id() == "ch5_akhir", "quest aktif ch5_akhir (langkah boss)")
	check(QuestManager.get_dialog_for("tedy") == "tedy_ch5_tunggu_boss", "Tedy: arahkan ke King Subiyan")
	check(region.shortcut_route.size() > 4, "jalur pintas panah (akar tumbang) terpasang")

	# Tahap 3: King Subiyan kalah -> Kristal -> akar tumbang menyusut -> kembali ke Tedy -> kuis -> TAMAT
	var boss: Boss = region.boss
	check(boss != null and boss is BossKing, "King Subiyan ada di tajuk Pohon Dunia")
	if boss:
		boss.apply_damage(99999)
	await frames(420)
	var cr: Node = get_tree().get_first_node_in_group("crystal")
	if cr != null and cr.has_method("_on_body_entered"):
		cr._on_body_entered(region.player)
	else:
		GameManager.add_crystal(5)
	await frames(120)
	print("== 5 King Subiyan: ", tracked())
	check(GameManager.has_crystal(5), "Kristal Tree didapat")
	check(sc.is_open, "akar tumbang menyusut setelah Kristal Tree")
	check(QuestManager.is_ready("ch5_akhir") and QuestManager.get_dialog_for("tedy") == "tedy_ch5_akhir", "Tedy: dialog kuis akhir")
	check(QuestManager.get_objective_text("ch5_akhir").contains("Tedy"), "pelacak: bawa Kristal ke Tedy")

	lines = QuestManager.finish_quiz("ch5_akhir", true)
	await frames(200)
	print("== 6 TAMAT: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(5) == 3, "Chapter 5 selesai (game tamat)")
	var all_crystals: bool = true
	for ch in range(1, 6):
		all_crystals = all_crystals and GameManager.has_crystal(ch)
	check(all_crystals, "kelima Kristal Struktur terkumpul")
	check(int(GameManager.inventory.get("data_fragment", 0)) >= 1, "Data Fragment didapat")
	check(QuestManager.get_dialog_for("tedy") == "tedy_ch5_akhir_sukses", "Tedy: dialog penutup")

	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch5_petunjuk_3") and GameManager.get_quest_stage(5) == 3 and GameManager.has_crystal(5), "flag, tahap quest & Kristal ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
