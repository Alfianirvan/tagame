extends CanvasLayer
## DialogBox: kotak dialog gaya Stardew (teks di bawah, potret + nama di kanan/tab), efek ketik,
## E untuk lanjut, dan pilihan jawaban. Hanya mendengarkan signal DialogManager.
## Data nama/potret karakter dibaca dari res://data/characters.json.

const CHARACTERS_PATH := "res://data/characters.json"
const PORTRAIT_DIR := "res://assets/portraits/"
const CHOICE_TEXTURE := preload("res://assets/ui/dialog/ChoiceBox.png")
const TYPE_SPEED := 45.0           # huruf per detik
const TYPE_SFX := false            # true = bunyi ketik tiap 3 huruf (dimatikan karena mengganggu)
const INPUT_GUARD_MSEC := 150      # abaikan input sesaat setelah dialog dibuka
const TEXT_WIDTH_PORTRAIT := 470.0
const TEXT_WIDTH_FULL := 560.0

@onready var root: Control = $Root
@onready var name_label: Label = $Root/NameLabel
@onready var text_label: RichTextLabel = $Root/Text
@onready var portrait_frame: TextureRect = $Root/PortraitFrame
@onready var portrait: TextureRect = $Root/Portrait
@onready var hint: Label = $Root/Hint
@onready var choice_box: VBoxContainer = $Root/Choices

var _characters: Dictionary = {}
var _tween: Tween
var _typing: bool = false
var _blip_next: int = 0   # jumlah huruf berikutnya yang memicu bunyi ketik
var _line: Dictionary = {}
var _choice_buttons: Array[Button] = []
var _selected: int = 0
var _opened_msec: int = 0


func _ready() -> void:
	layer = 50
	root.visible = false
	var data: Variant = GameManager.load_json(CHARACTERS_PATH)
	if data is Dictionary:
		_characters = data
	DialogManager.dialog_started.connect(_on_dialog_started)
	DialogManager.line_shown.connect(_on_line_shown)
	DialogManager.dialog_ended.connect(_on_dialog_ended)


func _on_dialog_started(_dialog_id: String) -> void:
	_opened_msec = Time.get_ticks_msec()
	root.visible = true


func _on_dialog_ended(_dialog_id: String) -> void:
	if _tween:
		_tween.kill()
	_clear_choices()
	root.visible = false


func _on_line_shown(line: Dictionary) -> void:
	_line = line
	_clear_choices()
	hint.visible = false
	_apply_speaker(String(line.get("speaker", "narator")))
	text_label.text = String(line.get("text", ""))
	text_label.visible_ratio = 0.0
	_typing = true
	if _tween:
		_tween.kill()
	var duration: float = maxf(0.05, text_label.text.length() / TYPE_SPEED)
	_blip_next = 0
	_tween = create_tween()
	_tween.tween_method(_type_step, 0.0, 1.0, duration)
	_tween.finished.connect(_on_typing_done)


## Langkah efek ketik: menampilkan huruf + bunyi ketik (dialog_suara1-3) tiap 3 huruf.
func _type_step(ratio: float) -> void:
	text_label.visible_ratio = ratio
	var shown: int = int(ratio * text_label.text.length())
	if shown >= _blip_next and shown < text_label.text.length():
		_blip_next = shown + 3
		if TYPE_SFX:
			AudioManager.play_sfx("dialog_suara%d" % randi_range(1, 3), 0.08)


## Mengisi nama dan potret sesuai pembicara; tanpa potret = teks dilebarkan.
func _apply_speaker(speaker: String) -> void:
	var info: Dictionary = _characters.get(speaker, {})
	var display: String = String(_line.get("name", info.get("name", "")))
	name_label.text = display
	name_label.visible = display != ""
	var portrait_name: String = String(info.get("portrait", ""))
	var path: String = PORTRAIT_DIR + portrait_name + ".png"
	var has_portrait: bool = portrait_name != "" and ResourceLoader.exists(path)
	portrait.texture = load(path) if has_portrait else null
	portrait.visible = has_portrait
	portrait_frame.visible = has_portrait
	text_label.size.x = TEXT_WIDTH_PORTRAIT if has_portrait else TEXT_WIDTH_FULL


func _on_typing_done() -> void:
	_typing = false
	var choices: Array = _line.get("choices", [])
	if choices.is_empty():
		hint.visible = true
	else:
		_show_choices(choices)


func _finish_typing() -> void:
	if _tween:
		_tween.kill()
	text_label.visible_ratio = 1.0
	_on_typing_done()


# ---------------------------------------------------------------- Pilihan jawaban

func _show_choices(choices: Array) -> void:
	for i in choices.size():
		var button: Button = Button.new()
		button.text = String(choices[i].get("text", ""))
		button.custom_minimum_size = Vector2(240, 28)
		button.focus_mode = Control.FOCUS_NONE
		button.add_theme_font_size_override("font_size", 14)
		button.add_theme_color_override("font_color", Color(0.2, 0.12, 0.1))
		button.add_theme_color_override("font_hover_color", Color(0.2, 0.12, 0.1))
		button.add_theme_color_override("font_pressed_color", Color(0.2, 0.12, 0.1))
		var style: StyleBoxTexture = StyleBoxTexture.new()
		style.texture = CHOICE_TEXTURE
		style.texture_margin_left = 6
		style.texture_margin_right = 6
		style.texture_margin_top = 6
		style.texture_margin_bottom = 6
		for state in ["normal", "hover", "pressed"]:
			button.add_theme_stylebox_override(state, style)
		button.pressed.connect(_confirm_choice.bind(i))
		button.mouse_entered.connect(_highlight.bind(i))
		choice_box.add_child(button)
		_choice_buttons.append(button)
	_highlight(0)


func _highlight(index: int) -> void:
	_selected = index
	for i in _choice_buttons.size():
		_choice_buttons[i].modulate = Color(1, 1, 1) if i == index else Color(0.75, 0.75, 0.75)


func _confirm_choice(index: int) -> void:
	_clear_choices()
	DialogManager.select_choice(index)


func _clear_choices() -> void:
	for button in _choice_buttons:
		button.queue_free()
	_choice_buttons.clear()


# ---------------------------------------------------------------- Input

func _unhandled_input(event: InputEvent) -> void:
	if not root.visible or Time.get_ticks_msec() - _opened_msec < INPUT_GUARD_MSEC:
		return
	if not _choice_buttons.is_empty():
		if event.is_action_pressed("move_up"):
			_highlight(posmod(_selected - 1, _choice_buttons.size()))
		elif event.is_action_pressed("move_down"):
			_highlight(posmod(_selected + 1, _choice_buttons.size()))
		elif event.is_action_pressed("interact"):
			_confirm_choice(_selected)
		else:
			return
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("interact"):
		if _typing:
			_finish_typing()
		else:
			DialogManager.advance()
		get_viewport().set_input_as_handled()
