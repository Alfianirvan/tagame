extends Node
## DialogManager (kerangka Tahap 1): state dialog + signal. DialogBox (Tahap 4) hanya mendengarkan signal.
## Format file res://data/dialogs/<id>.json:
##   { "lines": [ { "speaker": "joko", "text": "...", "choices": [ {"text": "...", "next": 3} ] } ] }

signal dialog_started(dialog_id: String)
signal line_shown(line: Dictionary)
signal choice_selected(choice_index: int)
signal dialog_ended(dialog_id: String)

const DIALOG_BOX_SCENE := "res://scenes/ui/DialogBox.tscn"

var is_active: bool = false
var current_id: String = ""

var _lines: Array = []
var _index: int = -1


func _ready() -> void:
	# Kotak dialog dipasang sekali di sini agar tersedia di semua scene
	add_child((load(DIALOG_BOX_SCENE) as PackedScene).instantiate())


## Memulai dialog dari file JSON. Bisa juga memberi `lines` langsung (untuk dialog dinamis).
func start_dialog(dialog_id: String, lines: Array = []) -> bool:
	if is_active or QuestManager.quiz_active:
		return false
	if lines.is_empty():
		var data: Variant = GameManager.load_json("res://data/dialogs/%s.json" % dialog_id)
		if not (data is Dictionary) or not (data.get("lines") is Array):
			return false
		lines = data["lines"]
	_lines = lines
	_index = -1
	current_id = dialog_id
	is_active = true
	dialog_started.emit(dialog_id)
	advance()
	return true


## Lanjut ke baris berikutnya; dialog berakhir bila sudah habis.
func advance() -> void:
	if not is_active:
		return
	_index += 1
	if _index >= _lines.size():
		end_dialog()
		return
	line_shown.emit(_lines[_index])


## Dipanggil UI saat pemain memilih jawaban; `next` (opsional) = indeks baris tujuan.
func select_choice(choice_index: int) -> void:
	if not is_active or _index < 0 or _index >= _lines.size():
		return
	var choices: Array = _lines[_index].get("choices", [])
	choice_selected.emit(choice_index)
	if choice_index >= 0 and choice_index < choices.size() and choices[choice_index].has("next"):
		_index = int(choices[choice_index]["next"]) - 1
	advance()


func end_dialog() -> void:
	if not is_active:
		return
	var finished: String = current_id
	is_active = false
	current_id = ""
	_lines = []
	_index = -1
	dialog_ended.emit(finished)
