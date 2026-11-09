extends CanvasLayer
## QuestLog: catatan misi (tombol Q). Menampilkan quest aktif (tujuan + progres) dan quest selesai.
## Isi diperbarui lewat signal QuestManager.quests_changed / quest_progress, bukan polling.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const INK := Color(0.2, 0.12, 0.1)

var _root: Control
var _text: RichTextLabel
var _was_enabled: bool = true


func _ready() -> void:
	layer = 55
	add_to_group("ui_overlay")
	_build_ui()
	_root.visible = false
	QuestManager.quests_changed.connect(_refresh)
	QuestManager.quest_progress.connect(func(_id: String, _p: int, _g: int) -> void: _refresh())


func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)

	var dim: ColorRect = ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.5)
	_root.add_child(dim)

	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(80, 20)
	panel.custom_minimum_size = Vector2(480, 320)
	panel.size = Vector2(480, 320)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.96, 0.9, 0.76)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(4)
	style.set_corner_radius_all(4)
	style.set_content_margin_all(14)
	panel.add_theme_stylebox_override("panel", style)
	_root.add_child(panel)

	_text = RichTextLabel.new()
	_text.bbcode_enabled = true
	_text.add_theme_font_override("normal_font", FONT)
	_text.add_theme_font_override("bold_font", FONT)
	_text.add_theme_font_size_override("normal_font_size", 13)
	_text.add_theme_font_size_override("bold_font_size", 14)
	_text.add_theme_color_override("default_color", INK)
	panel.add_child(_text)


func _refresh() -> void:
	if not _root.visible:
		return
	var out: String = "[b][color=#8c5433]Catatan Misi[/color][/b]   [color=#7a5c4c](Q: tutup)[/color]\n\n"
	out += "[b]Misi Aktif[/b]\n"
	var any_active: bool = false
	for id in QuestManager.get_all_ids():
		if not QuestManager.is_available(id):
			continue
		any_active = true
		var q: Dictionary = QuestManager.get_quest(id)
		out += "[b]%s[/b]  [color=#7a5c4c](%s)[/color]\n" % [q.get("title", id), _stage_name(int(q.get("stage", 1)))]
		out += "  %s\n" % q.get("objective", "")
		if QuestManager.quest_progress_data.has(id) and QuestManager.quiz_db.has(id):
			var total: int = QuestManager.quiz_db[id].get("questions", []).size()
			out += "  Progres kuis: %d/%d\n" % [QuestManager.quest_progress_data[id], total]
		elif bool(q.get("requires_crystal", false)) and not GameManager.has_crystal(int(q.get("chapter", 0))):
			out += "  [color=#7a5c4c]Kristal belum didapat.[/color]\n"
		out += "\n"
	if not any_active:
		out += "  Tidak ada misi aktif.\n\n"
	out += "[b]Selesai[/b]\n"
	var any_done: bool = false
	for id in QuestManager.get_all_ids():
		if QuestManager.is_done(id):
			any_done = true
			out += "  [color=#2f7a3a][lb]x[rb][/color] %s\n" % QuestManager.get_quest(id).get("title", id)
	if not any_done:
		out += "  Belum ada.\n"
	_text.text = out


func _stage_name(stage: int) -> String:
	match stage:
		1: return "Quest Awal"
		2: return "Quest Tengah"
		_: return "Quest Akhir"


func _toggle() -> void:
	if _root.visible:
		_root.visible = false
		_set_player_controls(_was_enabled)
		return
	if DialogManager.is_active or QuestManager.quiz_active:
		return
	var player: Node = get_tree().get_first_node_in_group("player")
	_was_enabled = player == null or bool(player.get("controls_enabled"))
	_root.visible = true
	_set_player_controls(false)
	_refresh()


func _set_player_controls(enabled: bool) -> void:
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(enabled)


func is_open() -> bool:
	return _root.visible


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("quest_log") or (_root.visible and event.is_action_pressed("pause")):
		_toggle()
		get_viewport().set_input_as_handled()
