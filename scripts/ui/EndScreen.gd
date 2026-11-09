extends CanvasLayer
## EndScreen: layar akhir sesi.
##  - Menang: muncul setelah Quest Akhir chapter selesai (rangkuman materi + hadiah). Chapter 5 = tamat.
##  - Kalah : dipanggil Region saat Raka mati (Coba Lagi dari checkpoint / Menu Utama).
## Dipasang sekali per scene permainan oleh Player._ensure_ui.

const START_SCREEN := "res://scenes/ui/StartScreen.tscn"

var _root: Control
var _panel_box: VBoxContainer
var _showing: bool = false
var _chapters: Dictionary = {}


func _ready() -> void:
	layer = 75
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("end_screen")
	add_to_group("ui_overlay")
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "chapters.json")
	if data is Dictionary:
		_chapters = data
	QuestManager.quest_completed.connect(_on_quest_completed)


func is_open() -> bool:
	return _showing


# ---------------------------------------------------------------- Menang

func _on_quest_completed(quest_id: String) -> void:
	if not quest_id.ends_with("_akhir"):
		return
	var q: Dictionary = QuestManager.get_quest(quest_id)
	var chapter: int = int(q.get("chapter", 0))
	# Tunggu dialog penutup & panel kuis selesai agar tidak menimpa
	while DialogManager.is_active or QuestManager.quiz_active or _showing:
		await get_tree().create_timer(0.4).timeout
	await get_tree().create_timer(0.6).timeout
	show_win(chapter, q)


func show_win(chapter: int, quest: Dictionary) -> void:
	var final: bool = chapter >= GameManager.MAX_CHAPTER or bool(quest.get("ends_game", false))
	var info: Dictionary = _chapters.get(str(chapter), {})
	_open_panel(Vector2(420, 290))
	AudioManager.play_music("menang_tamat" if final else "peta_dunia", 0.5)
	AudioManager.play_sfx("jingle_quest_selesai")
	_panel_box.add_child(UIKit.label("TAMAT — Algoria Pulih!" if final else "%s Selesai!" % String(info.get("name", "Chapter")), 16, UIKit.TITLE, true))
	_panel_box.add_child(UIKit.label("Materi: %s" % String(info.get("topic", "")), 11, UIKit.INK, true))
	_panel_box.add_child(UIKit.label("Rangkuman", 11, UIKit.TITLE))
	_panel_box.add_child(UIKit.label(String(info.get("summary", "")), 10, UIKit.INK))
	_panel_box.add_child(UIKit.label("Hadiah: " + _reward_text(quest), 10, Color(0.5, 0.3, 0.05)))
	if final:
		_panel_box.add_child(UIKit.label("Terima kasih sudah bermain! Kamu menguasai Array, Stack, Queue, Linked List, dan Tree.", 10, UIKit.INK, true))
	var row: HBoxContainer = HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	_panel_box.add_child(row)
	var first: Button
	if final:
		first = _row_button(row, "Menu Utama", _go_menu)
	else:
		first = _row_button(row, "Lanjut Bermain", _close_win)
		_row_button(row, "Peta Dunia", _open_map)
		_row_button(row, "Menu Utama", _go_menu)
	first.grab_focus.call_deferred()


func _reward_text(q: Dictionary) -> String:
	var reward: Dictionary = q.get("reward", {})
	var parts: Array[String] = []
	if int(reward.get("gold", 0)) > 0:
		parts.append("%d Gold" % int(reward["gold"]))
	if int(reward.get("xp", 0)) > 0:
		parts.append("%d XP" % int(reward["xp"]))
	var items: Dictionary = reward.get("items", {})
	for id: String in items:
		parts.append("%s x%d" % [GameManager.get_item_name(id), int(items[id])])
	return ", ".join(parts) if not parts.is_empty() else "-"


func _close_win() -> void:
	_close_panel()


func _open_map() -> void:
	_close_panel()
	var wm: Node = get_tree().get_first_node_in_group("world_map_ui")
	if wm and wm.has_method("open"):
		wm.open()


# ---------------------------------------------------------------- Kalah

func show_lose() -> void:
	if _showing:
		return
	_open_panel(Vector2(300, 150))
	AudioManager.play_music("kalah", 0.3)
	AudioManager.play_sfx("jingle_game_over")
	_panel_box.add_child(UIKit.label("Kamu Kalah", 16, Color(0.6, 0.15, 0.1), true))
	_panel_box.add_child(UIKit.label("Jangan menyerah! Pelajari pola musuh lalu coba lagi.", 10, UIKit.INK, true))
	var row: HBoxContainer = HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	_panel_box.add_child(row)
	var retry: Button = _row_button(row, "Coba Lagi", _retry)
	_row_button(row, "Menu Utama", _go_menu)
	retry.grab_focus.call_deferred()


func _retry() -> void:
	_close_panel()
	GameManager.restore_full()
	SceneManager.reload_current()     # hidup lagi di checkpoint terakhir


# ---------------------------------------------------------------- Umum

func _open_panel(size: Vector2) -> void:
	_showing = true
	if _root:
		_root.queue_free()
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_root.add_child(UIKit.dim(0.7))
	_panel_box = UIKit.centered_panel(_root, size)
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(false)
	get_tree().paused = true


func _close_panel() -> void:
	_showing = false
	if _root:
		_root.queue_free()
		_root = null
	get_tree().paused = false
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(true)


func _row_button(row: HBoxContainer, text: String, action: Callable) -> Button:
	var b: Button = UIKit.button(text, Vector2(110, 24))
	b.pressed.connect(action)
	row.add_child(b)
	return b


func _go_menu() -> void:
	_close_panel()
	SaveManager.save_game()
	SceneManager.change_scene(START_SCREEN)
