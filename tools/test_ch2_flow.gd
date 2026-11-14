extends Node
## Uji main otomatis Chapter 2 (headless), Tahap 1: masuk Kampung Tumpuk -> tanya 3 warga -> 3 petunjuk -> kuis Lilbah
## -> kabut debu gerbang desa terbuka. Aksi pemain disimulasikan lewat API yang sama dengan node game.
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
	check(not cloud_open("AwanGerbangDesa") and not cloud_open("AwanGerbangArena") and not cloud_open("AwanPerbatasan"), "kabut gerbang/arena/perbatasan menutup")
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
	check(cloud_open("AwanGerbangDesa") and not cloud_open("AwanGerbangArena"), "kabut debu gerbang desa terbuka, arena masih")
	var st: PuzzleStation = node("StasiunPeti") as PuzzleStation
	check(st._block_reason() == "", "stasiun tumpukan peti bisa dibuka")

	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
