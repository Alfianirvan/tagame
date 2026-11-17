extends Node
## Uji regresi PANAH PENUNJUK sepanjang alur quest Ch1-Ch5 (headless): di setiap langkah quest, panah harus menunjuk target
## langkah itu (warga, petunjuk, NPC lapor, stasiun puzzle, boss, NPC kuis) dan TIDAK melompat ke desa/puzzle/boss lain.
## Jalankan (save asli dicadangkan dulu oleh pemanggil):
##   godot --headless --fixed-fps 60 --path . res://tools/test_arrow_alur.tscn

var region: Node
var arrow: QuestArrow
var fails: int = 0


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


## names: nama node yang boleh jadi target; "@boss" = node di grup boss, "@altar" = grup altar.
func expect(label: String, names: Array) -> void:
	await frames(3)
	arrow.refresh_target()
	await frames(2)
	var t: Node2D = arrow._target
	var ok: bool = false
	if t != null:
		for n: String in names:
			if (n.begins_with("@") and t.is_in_group(n.substr(1))) or String(t.name) == n:
				ok = true
	var step: Dictionary = QuestManager.get_current_step(QuestManager.get_tracked_quest_id())
	if not ok:
		fails += 1
	print("  %s %s | %s:%s -> %s (harus: %s)" % ["OK   " if ok else "GAGAL", label, QuestManager.get_tracked_quest_id(),
		step.get("id", "-"), t.name if t else "(tidak ada)", ", ".join(names)])


func load_region(path: String, chapter: int) -> void:
	if region != null:
		region.queue_free()
		await frames(3)
	GameManager.reset_state()
	QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)
	for ch in range(1, chapter):
		GameManager.set_quest_stage(ch, 3)
		GameManager.add_crystal(ch)
	GameManager.unlocked_chapter = chapter
	for ch in range(1, 6):
		GameManager.mark_met("opening_ch%d" % ch)
	QuestManager.refresh_active()
	region = (load(path) as PackedScene).instantiate()
	add_child(region)
	await frames(10)
	print("== Chapter %d" % chapter)


func say(id: String) -> void:
	DialogManager.dialog_ended.emit(id)
	await frames(3)


func villagers(chapter: int, ids: Array, names: Array) -> void:
	await expect("tanya warga 0/3", names)
	QuestManager.mark_villager(chapter, ids[0])
	await expect("tanya warga 1/3 (bukan yang sudah ditanya)", names.slice(1))
	for v in ids.slice(1):
		QuestManager.mark_villager(chapter, v)


func clues(chapter: int) -> void:
	await expect("cari petunjuk 0/3", ["Petunjuk1", "Petunjuk2", "Petunjuk3"])
	await say("ch%d_petunjuk_1" % chapter)
	await expect("cari petunjuk 1/3 (bukan yang sudah)", ["Petunjuk2", "Petunjuk3"])
	await say("ch%d_petunjuk_2" % chapter)
	await say("ch%d_petunjuk_3" % chapter)


func boss_and_back(chapter: int, npc_name: String) -> void:
	QuestManager.complete_quest(chapter, 2)
	await expect("quest akhir: kalahkan boss", ["@boss"])
	GameManager.add_crystal(chapter)
	if region.boss != null:
		region.boss.queue_free()
	await frames(5)


func _ready() -> void:
	arrow = QuestArrow.new()
	add_child(arrow)
	# ---------------------------------------------------------------- Ch1
	await load_region("res://scenes/world/Ch1_HutanIndeks.tscn", 1)
	await expect("usir Goblin", ["GoblinEvent1", "GoblinEvent2", "GoblinEvent3", "GoblinEvent4"])
	GameManager.set_story_flag("ch1_goblin_usir")
	await villagers(1, ["penjaga", "penebang", "sari"], ["Penjaga", "Penebang", "Sari"])
	await clues(1)
	await expect("kuis Arman", ["Arman"])
	QuestManager.finish_quiz("ch1_awal", true)
	await expect("ke Desa 2: rak lumbung", ["StasiunRak"])
	GameManager.set_story_flag("ch1_sumur_murni")
	await expect("lapor ke Arman", ["Arman"])
	await say("arman_lapor_desa2")
	await expect("selamatkan penyintas Desa 3", ["Rani", "Darso", "Tami"])
	for v in ["rani", "darso", "tami"]:
		QuestManager.mark_villager(101, v)
	await expect("Arman menyusun petunjuk", ["Arman"])
	await say("arman_susun_petunjuk")
	await expect("obor segel", ["OborSegel"])
	await boss_and_back(1, "Arman")
	await expect("Kristal ke altar Desa 4", ["@altar"])
	GameManager.set_story_flag("ch1_segel_pudar")
	await expect("kuis Tetua", ["Tetua"])
	# ---------------------------------------------------------------- Ch2
	await load_region("res://scenes/world/Ch2_TambangTumpuk.tscn", 2)
	await villagers(2, ["mandor", "mirah", "udin"], ["Mandor", "Mirah", "Udin"])
	await clues(2)
	await expect("kuis Lilbah", ["Lilbah"])
	QuestManager.finish_quiz("ch2_awal", true)
	await expect("ke Dusun Cadas: temui Sesepuh", ["Sesepuh"])
	await say("sesepuh_ch2_minta")
	await expect("susun tugu batu", ["StasiunTugu"])
	GameManager.set_story_flag("ch2_tugu_cadas")
	await expect("tumpukan peti mulut tambang", ["StasiunPeti"])
	await boss_and_back(2, "Lilbah")
	await expect("Kristal ke Lilbah", ["Lilbah"])
	# ---------------------------------------------------------------- Ch3
	await load_region("res://scenes/world/Ch3_PelabuhanAntre.tscn", 3)
	await villagers(3, ["wulan", "bahar", "nina"], ["Wulan", "Bahar", "Nina"])
	await clues(3)
	await expect("kuis Dadang", ["Dadang"])
	QuestManager.finish_quiz("ch3_awal", true)
	await expect("antrean warung", ["StasiunAntrean"])
	await boss_and_back(3, "Dadang")
	await expect("Kristal ke Dadang", ["Dadang"])
	# ---------------------------------------------------------------- Ch4
	await load_region("res://scenes/world/Ch4_GuaRantai.tscn", 4)
	await villagers(4, ["gilang", "laras", "bayu"], ["Gilang", "Laras", "Bayu"])
	await clues(4)
	await expect("kuis Megas", ["Megas"])
	QuestManager.finish_quiz("ch4_awal", true)
	await expect("batu portal", ["StasiunPortal"])
	await boss_and_back(4, "Megas")
	await expect("Kristal ke Megas", ["Megas"])
	# ---------------------------------------------------------------- Ch5
	await load_region("res://scenes/world/Ch5_PohonDunia.tscn", 5)
	await villagers(5, ["wira", "sekar", "dimas"], ["Wira", "Sekar", "Dimas"])
	await clues(5)
	await expect("kuis Tedy", ["Tedy"])
	QuestManager.finish_quiz("ch5_awal", true)
	await expect("ke Dusun Ranting: temui Pak Banyu", ["Banyu"])
	await say("banyu_ch5_minta")
	await expect("nyalakan lentera ranting", ["StasiunLentera"])
	GameManager.set_story_flag("ch5_lentera_ranting")
	await expect("labirin bercabang", ["StasiunLabirin"])
	await boss_and_back(5, "Tedy")
	await expect("Kristal ke Tedy", ["Tedy"])
	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
