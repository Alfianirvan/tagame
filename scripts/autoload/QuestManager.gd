extends Node
## QuestManager: status quest per chapter. Tiap chapter punya 3 quest berurutan:
## awal (kuis) -> tengah (puzzle) -> akhir (setelah boss, kuis evaluasi).
## Data quest di res://data/quests.json, soal di res://data/quiz.json.
## Tahap selesai disimpan di GameManager.quest_stage; daftar quest aktif dihitung dari tahap tersebut.

signal quest_started(quest_id: String)
signal quest_completed(quest_id: String)
signal quest_progress(quest_id: String, progress: int, goal: int)
signal quests_changed                                        # status quest berubah (untuk ikon NPC & Quest Log)
signal quiz_started(quest_id: String, questions: Array)      # didengar QuizPanel

enum Stage { AWAL = 1, TENGAH = 2, AKHIR = 3 }

const QUIZ_PANEL_SCENE := "res://scenes/ui/QuizPanel.tscn"
const QUEST_LOG_SCENE := "res://scenes/ui/QuestLog.tscn"
const DIALOG_DIR := "res://data/dialogs/"

var active_quests: Array[String] = []     # id quest yang bisa dikerjakan sekarang (dihitung otomatis)
var quest_progress_data: Dictionary = {}  # id quest -> progres (angka)
var quest_db: Dictionary = {}             # dari quests.json
var quiz_db: Dictionary = {}              # dari quiz.json
var quiz_active: bool = false             # true selama kuis berlangsung

var _sorted_ids: Array[String] = []       # id quest terurut (chapter, tahap)


func _ready() -> void:
	var quests: Variant = GameManager.load_json(GameManager.DATA_DIR + "quests.json")
	if quests is Dictionary:
		quest_db = quests
	var quiz: Variant = GameManager.load_json(GameManager.DATA_DIR + "quiz.json")
	if quiz is Dictionary:
		quiz_db = quiz
	_sorted_ids.clear()
	for id: String in quest_db:
		_sorted_ids.append(id)
	_sorted_ids.sort_custom(func(a: String, b: String) -> bool: return _order_key(a) < _order_key(b))

	# Panel kuis & catatan misi dipasang sekali di sini agar tersedia di semua scene
	add_child((load(QUIZ_PANEL_SCENE) as PackedScene).instantiate())
	add_child((load(QUEST_LOG_SCENE) as PackedScene).instantiate())

	DialogManager.dialog_ended.connect(_on_dialog_ended)
	GameManager.crystal_collected.connect(func(_chapter: int) -> void: refresh_active())
	refresh_active()


func _order_key(id: String) -> int:
	var q: Dictionary = quest_db.get(id, {})
	return int(q.get("chapter", 0)) * 10 + int(q.get("stage", 0))


func reset_state() -> void:
	active_quests = []
	quest_progress_data = {}
	quiz_active = false
	refresh_active()


## ID quest standar: "ch1_awal", "ch1_tengah", "ch1_akhir"; chapter 0 = "ch0_awal" (prolog Joko).
static func make_id(chapter: int, stage: int) -> String:
	var names: Dictionary = {1: "awal", 2: "tengah", 3: "akhir"}
	return "ch%d_%s" % [chapter, names.get(stage, "awal")]


# ---------------------------------------------------------------- Status quest

func get_quest(quest_id: String) -> Dictionary:
	return quest_db.get(quest_id, {})


func get_all_ids() -> Array[String]:
	return _sorted_ids


func is_done(quest_id: String) -> bool:
	var q: Dictionary = get_quest(quest_id)
	return not q.is_empty() and GameManager.get_quest_stage(int(q["chapter"])) >= int(q["stage"])


## Tahap sebelumnya selesai dan chapter sebelumnya tuntas (quest akhir chapter itu).
func is_available(quest_id: String) -> bool:
	var q: Dictionary = get_quest(quest_id)
	if q.is_empty():
		return false
	var chapter: int = int(q["chapter"])
	var stage: int = int(q["stage"])
	if GameManager.get_quest_stage(chapter) != stage - 1:
		return false
	if stage == Stage.AWAL and chapter > 0:
		var prev: int = chapter - 1
		var needed: int = Stage.AWAL if prev == 0 else Stage.AKHIR
		return GameManager.get_quest_stage(prev) >= needed
	return true


## Siap dikerjakan: tersedia, dan (untuk quest akhir) Kristal sudah diambil.
func is_ready(quest_id: String) -> bool:
	if not is_available(quest_id):
		return false
	var q: Dictionary = get_quest(quest_id)
	return not bool(q.get("requires_crystal", false)) or GameManager.has_crystal(int(q["chapter"]))


func is_quest_active(quest_id: String) -> bool:
	return quest_id in active_quests


## Menghitung ulang daftar quest aktif dari progres GameManager.
func refresh_active() -> void:
	var fresh: Array[String] = []
	for id in _sorted_ids:
		if is_available(id):
			fresh.append(id)
	var added: Array[String] = []
	for id in fresh:
		if not (id in active_quests):
			added.append(id)
	active_quests = fresh
	for id in added:
		quest_started.emit(id)
	quests_changed.emit()


func set_progress(quest_id: String, progress: int, goal: int = 1) -> void:
	quest_progress_data[quest_id] = progress
	quest_progress.emit(quest_id, progress, goal)


# ---------------------------------------------------------------- NPC

## NPC ini punya quest (kuis) di data?
func npc_has_quests(npc_id: String) -> bool:
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id:
			return true
	return false


## Ikon "!" muncul bila ada quest kuis milik NPC yang siap dikerjakan.
func npc_has_ready_quest(npc_id: String) -> bool:
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id and is_ready(id):
			return true
	return false


## Tahap (1/2/3) quest milik NPC yang siap dikerjakan sekarang; 0 bila tidak ada.
## Dipakai ikon NPC: tahap 3 (serahkan Kristal) = "?", selain itu = "!".
func get_ready_stage(npc_id: String) -> int:
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id and is_ready(id):
			return int(quest_db[id].get("stage", 1))
	return 0


## Quest yang sedang dilacak HUD: quest aktif paling awal (urutan chapter lalu tahap). Kosong bila tidak ada.
func get_tracked_quest_id() -> String:
	for id in _sorted_ids:
		if id in active_quests:
			return id
	return ""


## Memilih dialog NPC sesuai progres quest. String kosong bila tidak ada yang cocok.
func get_dialog_for(npc_id: String) -> String:
	var last_done: Dictionary = {}
	for id in _sorted_ids:
		var q: Dictionary = quest_db[id]
		if q.get("npc", "") != npc_id:
			continue
		if is_done(id):
			last_done = q
		elif is_ready(id):
			return _existing_dialog(String(q.get("dialog", "")))
		elif is_available(id):  # tersedia tetapi belum siap (Kristal belum diambil)
			return _existing_dialog(String(q.get("dialog_waiting", "")))
		else:
			var locked: String = _existing_dialog(String(q.get("dialog_locked", "")))
			if locked != "":
				return locked
			break
	return _existing_dialog(String(last_done.get("dialog_done", "")))


func _existing_dialog(dialog_id: String) -> String:
	if dialog_id != "" and FileAccess.file_exists(DIALOG_DIR + dialog_id + ".json"):
		return dialog_id
	return ""


# ---------------------------------------------------------------- Kuis

## Dialog pembuka quest selesai -> kuis dimulai (ditunda satu frame agar kontrol Raka tidak bentrok).
func _on_dialog_ended(finished_id: String) -> void:
	for id in _sorted_ids:
		var q: Dictionary = quest_db[id]
		if q.get("type", "") == "quiz" and q.get("dialog", "") == finished_id and is_ready(id):
			start_quiz.call_deferred(id)
			return


func start_quiz(quest_id: String) -> void:
	if quiz_active or not quiz_db.has(quest_id):
		return
	var questions: Array = quiz_db[quest_id].get("questions", [])
	if questions.is_empty():
		return
	quiz_active = true
	set_progress(quest_id, 0, questions.size())
	quiz_started.emit(quest_id, questions)


## Dipanggil QuizPanel saat semua soal benar. Mengembalikan baris hadiah untuk ditampilkan.
func finish_quiz(quest_id: String, first_try: bool) -> Array[String]:
	var q: Dictionary = get_quest(quest_id)
	return complete_quest(int(q.get("chapter", 0)), int(q.get("stage", 1)), first_try)


## Dipanggil QuizPanel setelah hasil ditutup: putar dialog penutup bila ada.
func close_quiz(quest_id: String) -> void:
	quiz_active = false
	var after: String = _existing_dialog(String(get_quest(quest_id).get("dialog_success", "")))
	if after != "":
		DialogManager.start_dialog(after)


# ---------------------------------------------------------------- Penyelesaian & hadiah

## Menandai tahap quest selesai, memberi hadiah (sekali saja), autosave.
## Mengembalikan daftar teks hadiah. Dipakai juga oleh puzzle (quest tengah).
func complete_quest(chapter: int, stage: int, first_try: bool = false) -> Array[String]:
	var quest_id: String = make_id(chapter, stage)
	var lines: Array[String] = []
	if GameManager.get_quest_stage(chapter) >= stage:
		return lines  # sudah selesai, jangan beri hadiah dua kali
	GameManager.set_quest_stage(chapter, stage)
	active_quests.erase(quest_id)
	lines = _grant_rewards(get_quest(quest_id), first_try)
	quest_progress_data.erase(quest_id)
	quest_completed.emit(quest_id)
	refresh_active()
	SaveManager.save_game()  # autosave setelah quest selesai
	return lines


func _grant_rewards(q: Dictionary, first_try: bool) -> Array[String]:
	var lines: Array[String] = []
	var reward: Dictionary = q.get("reward", {})
	var gold: int = int(reward.get("gold", 0))
	var xp: int = int(reward.get("xp", 0))
	if first_try:
		var bonus: Dictionary = q.get("bonus", {})
		gold += int(bonus.get("gold", 0))
		xp += int(bonus.get("xp", 0))
	if gold > 0:
		GameManager.add_gold(gold)
		lines.append("+%d Gold" % gold)
	var items: Dictionary = reward.get("items", {})
	for item_id: String in items:
		var count: int = int(items[item_id])
		GameManager.add_item(item_id, count)
		lines.append("%s x%d" % [GameManager.get_item_name(item_id), count] if count > 1 else GameManager.get_item_name(item_id))
		# Perlengkapan baru langsung dipakai bila slotnya masih kosong
		var slot: String = GameManager.get_slot_for(item_id)
		if slot != "" and GameManager.equipment.get(slot, "") == "":
			GameManager.equip(item_id)
	var unlock: int = int(reward.get("unlock_chapter", 0))
	if unlock > 0:
		GameManager.unlock_chapter(unlock)
		lines.append("Wilayah baru terbuka!")
	if xp > 0:
		GameManager.add_xp(xp)  # terakhir: naik level mengisi ulang HP
		lines.append("+%d XP" % xp)
	if first_try:
		lines.append("Bonus: benar semua di percobaan pertama!")
	return lines


# ---------------------------------------------------------------- Save

func get_save_data() -> Dictionary:
	return {"active": active_quests, "progress": quest_progress_data}


func apply_save_data(d: Dictionary) -> void:
	reset_state()
	for id: String in d.get("progress", {}):
		quest_progress_data[id] = int(d["progress"][id])
	refresh_active()  # daftar aktif dihitung ulang dari tahap quest di GameManager
