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
signal step_completed(quest_id: String, step_id: String)     # satu langkah quest selesai

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
	GameManager.story_flag_set.connect(_on_story_flag_set)
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


## Warga yang sudah diajak bicara di sebuah chapter (disimpan di GameManager.met_npcs, jadi ikut tersimpan di save).
func villagers_talked(chapter: int) -> int:
	var prefix: String = "warga_ch%d_" % chapter
	var n: int = 0
	for m: String in GameManager.met_npcs:
		if m.begins_with(prefix):
			n += 1
	return n


func has_talked_to_villager(chapter: int, npc_id: String) -> bool:
	return GameManager.has_met("warga_ch%d_%s" % [chapter, npc_id])


func mark_villager(chapter: int, npc_id: String) -> void:
	GameManager.mark_met("warga_ch%d_%s" % [chapter, npc_id])
	quests_changed.emit()    # ikon NPC, pelacak tujuan, dan panah ikut diperbarui


## Teks tujuan untuk HUD / Catatan Misi; quest dengan syarat warga menampilkan hitungannya.
func get_objective_text(quest_id: String) -> String:
	var q: Dictionary = get_quest(quest_id)
	var step: Dictionary = get_current_step(quest_id)
	if not step.is_empty():
		var text: String = String(step.get("text", ""))
		if "%d" in text:
			var pr: Vector2i = step_progress(quest_id, step)
			text = text % [pr.x, pr.y]
		return text
	var need: int = int(q.get("requires_villagers", 0))
	if need > 0 and is_available(quest_id):
		var have: int = villagers_talked(int(q.get("chapter", 0)))
		if have < need:
			return "Tanya warga tentang masalah desa (%d/%d)" % [have, need]
	return String(q.get("objective", q.get("title", "")))


## Siap dikerjakan: tersedia, cukup warga sudah diajak bicara, dan (untuk quest akhir) Kristal sudah diambil.
func is_ready(quest_id: String) -> bool:
	if not is_available(quest_id):
		return false
	var q: Dictionary = get_quest(quest_id)
	if villagers_talked(int(q.get("chapter", 0))) < int(q.get("requires_villagers", 0)):
		return false
	if not get_current_step(quest_id).is_empty():
		return false
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


# ---------------------------------------------------------------- Langkah quest (steps)
## Quest boleh punya "steps": langkah berurutan SEBELUM tujuan akhirnya (kuis NPC / puzzle). Tiap langkah:
##   id, text ("%d/%d" diganti progres), dan salah satu syarat selesai:
##     flag | flags_all (+targets sejajar) | villagers (+villager_chapter) | crystal: true
##   opsional: target (nama node / daftar nama) atau target_group untuk panah penunjuk,
##             talk {npc, dialog}: bicara dengan NPC itu memutar dialog lalu menyetel flag langkah,
##             npc_dialogs {npc: dialog}: dialog NPC lain selama langkah ini aktif, reward (seperti reward quest).
## Quest boleh juga punya final_target / final_npc_dialogs untuk tujuan akhir setelah semua langkah beres.

func get_steps(quest_id: String) -> Array:
	return get_quest(quest_id).get("steps", [])


## Progres langkah sebagai (sudah, butuh).
func step_progress(quest_id: String, step: Dictionary) -> Vector2i:
	var chapter: int = int(get_quest(quest_id).get("chapter", 0))
	if step.has("villagers"):
		var need: int = int(step["villagers"])
		return Vector2i(mini(villagers_talked(int(step.get("villager_chapter", chapter))), need), need)
	if step.has("flags_all"):
		var flags: Array = step["flags_all"]
		var n: int = 0
		for f in flags:
			if GameManager.has_story_flag(String(f)):
				n += 1
		return Vector2i(n, flags.size())
	if bool(step.get("crystal", false)):
		return Vector2i(1 if GameManager.has_crystal(chapter) else 0, 1)
	return Vector2i(1 if GameManager.has_story_flag(String(step.get("flag", ""))) else 0, 1)


func is_step_done(quest_id: String, step: Dictionary) -> bool:
	if is_done(quest_id):
		return true
	var pr: Vector2i = step_progress(quest_id, step)
	return pr.x >= pr.y


## Langkah pertama yang belum selesai dari quest yang sedang tersedia ({} bila tidak ada / quest belum tersedia).
func get_current_step(quest_id: String) -> Dictionary:
	if not is_available(quest_id):
		return {}
	for step: Dictionary in get_steps(quest_id):
		if not is_step_done(quest_id, step):
			return step
	return {}


## Langkah `step_id` sudah boleh dikerjakan (atau sudah lewat): quest selesai, atau quest tersedia dan semua langkah sebelumnya beres.
func is_step_unlocked(quest_id: String, step_id: String) -> bool:
	if is_done(quest_id):
		return true
	if not is_available(quest_id):
		return false
	for step: Dictionary in get_steps(quest_id):
		if String(step.get("id", "")) == step_id:
			return true
		if not is_step_done(quest_id, step):
			return false
	return false


## Flag cerita baru: beri hadiah langkah yang selesai karenanya (sekali saja, karena flag hanya bisa disetel sekali).
func _on_story_flag_set(flag: String) -> void:
	for id in _sorted_ids:
		for step: Dictionary in get_steps(id):
			var by_flag: bool = String(step.get("flag", "")) == flag
			var by_all: bool = step.has("flags_all") and flag in step["flags_all"] and is_step_done(id, step)
			if by_flag or by_all:
				var lines: Array[String] = _grant_rewards(step, false)
				if not lines.is_empty():
					_show_reward_text(lines)
				step_completed.emit(id, String(step.get("id", "")))
	refresh_active()
	SaveManager.save_game()   # langkah penting ikut tersimpan


func _show_reward_text(lines: Array[String]) -> void:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player != null and player.get_parent() != null:
		FloatingText.spawn(player.get_parent(), player.global_position + Vector2(0, -52), ", ".join(lines), Color(1, 0.9, 0.4), 2.6)


# ---------------------------------------------------------------- NPC

## NPC ini punya quest (kuis) di data?
func npc_has_quests(npc_id: String) -> bool:
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id:
			return true
	return false


## Ikon "!" muncul bila ada quest kuis milik NPC yang siap dikerjakan.
func npc_has_ready_quest(npc_id: String) -> bool:
	if npc_has_step_talk(npc_id):
		return true
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id and is_ready(id):
			return true
	return false


## Tahap (1/2/3) quest milik NPC yang siap dikerjakan sekarang; 0 bila tidak ada.
## Dipakai ikon NPC: tahap 3 (serahkan Kristal) = "?", selain itu = "!".
func get_ready_stage(npc_id: String) -> int:
	if npc_has_step_talk(npc_id):
		return Stage.AKHIR   # lapor = ikon "?"
	for id in _sorted_ids:
		if quest_db[id].get("npc", "") == npc_id and is_ready(id):
			return int(quest_db[id].get("stage", 1))
	return 0


## Langkah aktif suatu quest meminta Raka bicara dengan NPC ini (lapor).
func npc_has_step_talk(npc_id: String) -> bool:
	for id in active_quests:
		if String(get_current_step(id).get("talk", {}).get("npc", "")) == npc_id:
			return true
	return false


## Quest yang sedang dilacak HUD: quest aktif paling awal (urutan chapter lalu tahap). Kosong bila tidak ada.
func get_tracked_quest_id() -> String:
	for id in _sorted_ids:
		if id in active_quests:
			return id
	return ""


## Memilih dialog NPC sesuai progres quest. String kosong bila tidak ada yang cocok.
func get_dialog_for(npc_id: String) -> String:
	# langkah quest aktif boleh mengganti dialog NPC (lapor / menunggu)
	for id in active_quests:
		var step: Dictionary = get_current_step(id)
		var pick: String = ""
		if step.is_empty():
			if not get_steps(id).is_empty():
				pick = String(get_quest(id).get("final_npc_dialogs", {}).get(npc_id, ""))
		elif String(step.get("talk", {}).get("npc", "")) == npc_id:
			pick = String(step["talk"].get("dialog", ""))
		else:
			pick = String(step.get("npc_dialogs", {}).get(npc_id, ""))
		if _existing_dialog(pick) != "":
			return pick
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
	# dialog "lapor" sebuah langkah selesai -> flag langkah disetel
	for id in active_quests.duplicate():
		var step: Dictionary = get_current_step(id)
		if not step.is_empty() and String(step.get("talk", {}).get("dialog", "")) == finished_id:
			GameManager.set_story_flag(String(step.get("flag", "")))
			return
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
