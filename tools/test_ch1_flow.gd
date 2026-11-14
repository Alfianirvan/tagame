extends Node
## Uji main otomatis Chapter 1 (headless): opening -> Goblin -> warga -> petunjuk -> kuis Arman -> rak Desa 2 ->
## lapor -> penyintas Desa 3 -> Arman menyusun petunjuk -> obor segel -> Golem -> altar Desa 4 -> kuis Tetua -> tamat.
## Aksi pemain disimulasikan lewat API yang sama dengan yang dipakai node game (dialog_ended, mark_villager, dst.).
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_ch1_flow.tscn

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
	# sama seperti DialogBox saat dialog selesai
	DialogManager.dialog_ended.emit(id)
	await frames(3)


func press_interact(target: Node) -> void:
	var ev: InputEventAction = InputEventAction.new()
	ev.action = "interact"
	ev.pressed = true
	target._unhandled_input(ev)


func _ready() -> void:
	GameManager.reset_state()
	QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)          # prolog Joko selesai
	QuestManager.refresh_active()
	GameManager.mark_met("opening_ch1")        # opening sudah ditampilkan (diuji terpisah)
	region = (load("res://scenes/world/Ch1_HutanIndeks.tscn") as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== 0 Mulai: ", tracked())
	check(QuestManager.get_tracked_quest_id() == "ch1_awal", "quest aktif ch1_awal")
	check(not cloud_open("AwanDesa2") and not cloud_open("AwanDesa3") and not cloud_open("AwanGerbangDesa"), "kabut Desa 2/3/utara masih menutup")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk belum tampak sebelum tanya warga")

	# 1. usir Goblin
	for k in range(1, 5):
		var g: Enemy = node("GoblinEvent%d" % k) as Enemy
		if g:
			g.take_hit(9999, g.global_position + Vector2(10, 0))
	await frames(120)
	print("== 1 Goblin: ", tracked())
	check(GameManager.has_story_flag("ch1_goblin_usir"), "flag Goblin diusir")

	# 2. tanya 3 warga
	for v in ["penjaga", "penebang", "sari"]:
		QuestManager.mark_villager(1, v)
	await frames(3)
	print("== 2 Warga: ", tracked())
	check((node("Petunjuk1") as CanvasItem).visible, "petunjuk tampak setelah tanya warga")
	check(QuestManager.get_dialog_for("arman") == "arman_tanya_warga", "Arman: menunggu petunjuk")

	# 3. tiga petunjuk
	for k in range(1, 4):
		await end_dialog("ch1_petunjuk_%d" % k)
	print("== 3 Petunjuk: ", tracked())
	check(QuestManager.is_ready("ch1_awal"), "Quest Awal siap (kuis Arman)")
	check(QuestManager.get_dialog_for("arman") == "arman", "Arman: dialog kuis")
	check(not (node("Petunjuk1") as CanvasItem).visible, "petunjuk hilang setelah diperiksa")

	# 4. kuis Arman
	var lines: Array[String] = QuestManager.finish_quiz("ch1_awal", true)
	await frames(5)
	print("== 4 Kuis Arman: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(1) == 1, "quest_stage Ch1 = 1")
	check(cloud_open("AwanDesa2") and not cloud_open("AwanDesa3"), "kabut Desa 2 terbuka, Desa 3 masih")
	check(QuestManager.get_dialog_for("arman") == "arman_tunggu_desa2", "Arman: tunggu Desa 2")

	# 5. rak lumbung Desa 2
	var st: PuzzleStation = node("StasiunRak") as PuzzleStation
	check(st._block_reason() == "", "stasiun rak Desa 2 bisa dibuka")
	st._open()
	await frames(2)
	st._puzzle.complete_puzzle()
	st._puzzle.close_puzzle()
	await frames(200)
	print("== 5 Rak Desa 2: ", tracked())
	check(GameManager.has_story_flag("ch1_sumur_murni"), "flag sumur dimurnikan")
	check((node("AirUngu") as CanvasItem).modulate.is_equal_approx(Color.WHITE), "air ungu Desa 2 kembali normal")
	check(QuestManager.get_dialog_for("arman") == "arman_lapor_desa2", "Arman: dialog lapor Desa 2")
	check(QuestManager.npc_has_step_talk("arman"), "ikon ? di Arman")

	# 6. lapor Arman
	await end_dialog("arman_lapor_desa2")
	print("== 6 Lapor: ", tracked())
	check(cloud_open("AwanDesa3"), "kabut Desa 3 terbuka")

	# 7. tiga penyintas Desa 3
	for v in ["rani", "darso", "tami"]:
		QuestManager.mark_villager(101, v)
	await frames(3)
	print("== 7 Penyintas: ", tracked())
	check(QuestManager.get_dialog_for("arman") == "arman_susun_petunjuk", "Arman: menyusun petunjuk")

	# 8. Arman menyusun petunjuk
	await end_dialog("arman_susun_petunjuk")
	print("== 8 Petunjuk disusun: ", tracked())
	check(cloud_open("AwanGerbangDesa"), "kabut jalan utara terbuka")
	check(QuestManager.is_ready("ch1_tengah"), "obor segel siap")
	check(not cloud_open("AwanGerbangArena"), "cincin awan arena masih menutup")

	# 9. obor segel: satu kali salah, lalu urutan benar 0..4
	var ts: TorchSeal = node("OborSegel") as TorchSeal
	var pos_of: Dictionary = {}
	for i in ts.torch_indices.size():
		pos_of[ts.torch_indices[i]] = i
	ts._near = pos_of[2]
	press_interact(ts)
	check(not ts._lit.has(true), "salah urutan -> semua obor padam")
	for idx in range(5):
		ts._near = pos_of[idx]
		press_interact(ts)
	await frames(200)
	print("== 9 Obor: ", tracked())
	check(GameManager.get_quest_stage(1) == 2, "quest_stage Ch1 = 2")
	check(cloud_open("AwanGerbangArena"), "cincin awan arena terbuka")
	var dome: SealDome = node("KubahSegel") as SealDome
	check(dome._state == 0, "kubah Desa 4 masih tersegel sebelum Golem kalah")

	# 10. Golem kalah -> Kristal
	var boss: Boss = region.boss
	check(boss != null, "Golem ada di arena")
	if boss:
		boss.apply_damage(99999)
	await frames(420)
	var cr: Node = get_tree().get_first_node_in_group("crystal")
	if cr != null and cr.has_method("_on_body_entered"):
		cr._on_body_entered(region.player)
	else:
		GameManager.add_crystal(1)
	await frames(10)
	print("== 10 Golem: ", tracked())
	check(GameManager.has_crystal(1), "Kristal Array didapat")
	check(dome._state == 1, "kubah melemah (bisa dimasuki)")
	check(QuestManager.get_dialog_for("arman") == "arman_ke_desa4", "Arman (di desa): arahkan ke Desa 4")

	# 11. altar
	await end_dialog("ch1_altar")
	await frames(240)
	print("== 11 Altar: ", tracked())
	check(GameManager.has_story_flag("ch1_segel_pudar"), "flag segel pudar")
	check(dome._state == 2 and not (node("D4KutukTanah") as CanvasItem).visible, "kubah & tanah terkutuk Desa 4 memudar")
	var tetua: Node = node("Tetua")
	check((tetua as CanvasItem).visible, "Tetua muncul")
	check(QuestManager.get_dialog_for("tetua") == "tetua_akhir" and QuestManager.is_ready("ch1_akhir"), "Tetua: dialog kuis akhir")

	# 12. kuis Tetua -> Chapter 1 tamat
	lines = QuestManager.finish_quiz("ch1_akhir", true)
	await frames(200)
	print("== 12 Tamat: hadiah ", lines, " -> ", tracked())
	check(GameManager.get_quest_stage(1) == 3 and GameManager.unlocked_chapter >= 2, "Chapter 1 selesai, Chapter 2 terbuka")
	check(cloud_open("AwanPerbatasan"), "awan perbatasan ke Chapter 2 hilang")
	check(QuestManager.get_dialog_for("arman") == "arman_selesai", "Arman: dialog penutup")

	# 13. simpan & muat ulang menjaga flag
	var data: Dictionary = GameManager.get_save_data()
	GameManager.reset_state()
	GameManager.apply_save_data(data)
	check(GameManager.has_story_flag("ch1_segel_pudar") and GameManager.has_story_flag("ch1_goblin_usir"), "flag cerita ikut tersimpan")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
