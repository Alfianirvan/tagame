extends CanvasLayer
## QuizPanel: kuis pilihan ganda. Salah -> petunjuk, jawab ulang (tanpa game over).
## Semua soal benar -> hadiah; benar semua di percobaan pertama -> bonus (dihitung QuestManager).
## Hanya berkomunikasi lewat signal/fungsi QuestManager. UI dibangun lewat kode.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const CHOICE_TEXTURE := preload("res://assets/ui/dialog/ChoiceBox.png")
const INPUT_GUARD_MSEC := 200
const INK := Color(0.2, 0.12, 0.1)

enum Mode { ASKING, CORRECT, RESULT }

var _root: Control
var _title: Label
var _counter: Label
var _question: Label
var _choice_box: VBoxContainer
var _feedback: Label
var _footer: Label

var _quest_id: String = ""
var _questions: Array = []
var _index: int = 0
var _wrong_count: int = 0
var _mode: Mode = Mode.ASKING
var _buttons: Array[Button] = []
var _selected: int = 0
var _opened_msec: int = 0


func _ready() -> void:
	layer = 60
	_build_ui()
	_root.visible = false
	QuestManager.quiz_started.connect(_on_quiz_started)


func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)

	var dim: ColorRect = ColorRect.new()  # menggelapkan latar dan menahan klik ke game
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.55)
	_root.add_child(dim)

	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(60, 10)
	panel.custom_minimum_size = Vector2(520, 340)
	panel.size = Vector2(520, 340)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.96, 0.9, 0.76)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(4)
	style.set_corner_radius_all(4)
	style.set_content_margin_all(14)
	panel.add_theme_stylebox_override("panel", style)
	_root.add_child(panel)

	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	panel.add_child(box)

	_title = _make_label(16, Color(0.55, 0.33, 0.2))
	box.add_child(_title)
	_counter = _make_label(12, Color(0.45, 0.35, 0.3))
	box.add_child(_counter)
	_question = _make_label(15, INK)
	_question.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_question.custom_minimum_size = Vector2(490, 44)
	box.add_child(_question)
	_choice_box = VBoxContainer.new()
	_choice_box.add_theme_constant_override("separation", 4)
	box.add_child(_choice_box)
	_feedback = _make_label(13, Color(0.7, 0.15, 0.1))
	_feedback.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_feedback.custom_minimum_size = Vector2(490, 36)
	box.add_child(_feedback)
	_footer = _make_label(11, Color(0.45, 0.35, 0.3))
	_footer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_footer.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	box.add_child(_footer)


func _make_label(size: int, color: Color) -> Label:
	var label: Label = Label.new()
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	return label


# ---------------------------------------------------------------- Alur kuis

func _on_quiz_started(quest_id: String, questions: Array) -> void:
	_quest_id = quest_id
	_questions = questions
	_index = 0
	_wrong_count = 0
	_opened_msec = Time.get_ticks_msec()
	_title.text = "Kuis: %s" % String(QuestManager.get_quest(quest_id).get("title", ""))
	_set_player_controls(false)
	_root.visible = true
	_show_question()


func _show_question() -> void:
	var q: Dictionary = _questions[_index]
	_mode = Mode.ASKING
	_counter.text = "Soal %d dari %d" % [_index + 1, _questions.size()]
	_question.text = String(q.get("q", ""))
	_feedback.text = ""
	_footer.text = "W/S: pilih   E / klik: jawab"
	_clear_buttons()
	var choices: Array = q.get("choices", [])
	for i in choices.size():
		var button: Button = _make_choice_button(String(choices[i]))
		button.pressed.connect(_answer.bind(i))
		button.mouse_entered.connect(_highlight.bind(i))
		_choice_box.add_child(button)
		_buttons.append(button)
	_highlight(0)


func _make_choice_button(text: String) -> Button:
	var button: Button = Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(490, 28)
	button.focus_mode = Control.FOCUS_NONE
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.add_theme_font_override("font", FONT)
	button.add_theme_font_size_override("font_size", 13)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_disabled_color"]:
		button.add_theme_color_override(key, INK)
	var style: StyleBoxTexture = StyleBoxTexture.new()
	style.texture = CHOICE_TEXTURE
	style.set_texture_margin_all(6)
	for state in ["normal", "hover", "pressed", "disabled"]:
		button.add_theme_stylebox_override(state, style)
	return button


func _highlight(index: int) -> void:
	if _mode != Mode.ASKING:
		return
	_selected = index
	for i in _buttons.size():
		var chosen: bool = i == index
		_buttons[i].modulate = Color(1, 1, 1) if chosen else Color(0.78, 0.78, 0.78)
		if _buttons[i].disabled:
			_buttons[i].modulate = Color(0.55, 0.45, 0.45)


func _answer(index: int) -> void:
	if _mode != Mode.ASKING or _buttons[index].disabled:
		return
	var q: Dictionary = _questions[_index]
	if index == int(q.get("answer", -1)):
		_mode = Mode.CORRECT
		_feedback.add_theme_color_override("font_color", Color(0.15, 0.5, 0.2))
		_feedback.text = "Benar!"
		AudioManager.play_sfx("kuis_benar")
		_footer.text = "E: lanjut"
		QuestManager.set_progress(_quest_id, _index + 1, _questions.size())
	else:
		_wrong_count += 1
		AudioManager.play_sfx("kuis_salah")
		_buttons[index].disabled = true
		_feedback.add_theme_color_override("font_color", Color(0.7, 0.15, 0.1))
		_feedback.text = "Belum tepat. Petunjuk: %s" % String(q.get("hint", ""))
		_highlight(_selected)


func _next_step() -> void:
	_index += 1
	if _index < _questions.size():
		_show_question()
	else:
		_show_result()


func _show_result() -> void:
	_mode = Mode.RESULT
	var first_try: bool = _wrong_count == 0
	var lines: Array[String] = QuestManager.finish_quiz(_quest_id, first_try)
	_clear_buttons()
	_counter.text = ""
	_question.text = "Semua jawaban benar! Kamu lulus."
	_feedback.add_theme_color_override("font_color", Color(0.15, 0.5, 0.2))
	_feedback.text = "Hadiah:\n" + "\n".join(lines) if not lines.is_empty() else ""
	_feedback.custom_minimum_size.y = 20.0 + 16.0 * lines.size()
	_footer.text = "E: tutup"


func _close() -> void:
	_root.visible = false
	_feedback.custom_minimum_size.y = 36.0
	QuestManager.close_quiz(_quest_id)  # bisa memulai dialog penutup
	if not DialogManager.is_active:
		_set_player_controls(true)


func _clear_buttons() -> void:
	for button in _buttons:
		button.queue_free()
	_buttons.clear()


func _set_player_controls(enabled: bool) -> void:
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(enabled)


# ---------------------------------------------------------------- Input

func _unhandled_input(event: InputEvent) -> void:
	if not _root.visible or Time.get_ticks_msec() - _opened_msec < INPUT_GUARD_MSEC:
		return
	if _mode == Mode.ASKING:
		if event.is_action_pressed("move_up"):
			_highlight(posmod(_selected - 1, _buttons.size()))
		elif event.is_action_pressed("move_down"):
			_highlight(posmod(_selected + 1, _buttons.size()))
		elif event.is_action_pressed("interact"):
			_answer(_selected)
		else:
			return
	elif event.is_action_pressed("interact"):
		if _mode == Mode.CORRECT:
			_next_step()
		else:
			_close()
	else:
		return
	get_viewport().set_input_as_handled()
