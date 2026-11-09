extends CanvasLayer
## About: nama + foto 3 anggota dan dosen (placeholder dulu), plus credit aset.
## Ganti nama/foto di MEMBERS; letakkan foto di assets/ui/about/ lalu isi "photo".

signal closed

const MEMBERS: Array[Dictionary] = [
	{"name": "(Nama anggota 1)", "role": "Combat, musuh, boss", "photo": ""},
	{"name": "(Nama anggota 2)", "role": "NPC, dialog, quest, shop", "photo": ""},
	{"name": "(Nama anggota 3)", "role": "Map, UI, audio, dokumen", "photo": ""},
]
const LECTURER := {"name": "(Nama dosen pengampu)", "role": "Dosen pengampu", "photo": ""}
const CREDITS := "Aset utama: Pixel Crawler Free Pack 2.11 oleh Anokolisa. " 	+ "Musik, efek suara, dan UI: Ninja Adventure Asset Pack oleh pixel-boy & AAA (lisensi CC0). " 	+ "Sprite Raka, NPC, dan boss dibuat kelompok dari basis Pixel Crawler. Potret dialog dibuat dengan AI. Detail: CREDITS.md."

var _root: Control
var _prev_music: String = ""


func _ready() -> void:
	layer = 80
	process_mode = Node.PROCESS_MODE_ALWAYS
	_prev_music = AudioManager.current_music
	AudioManager.play_music("kredit_about", 1.0)
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_root.add_child(UIKit.dim(0.65))
	var v: VBoxContainer = UIKit.centered_panel(_root, Vector2(560, 310))
	v.add_child(UIKit.label("About — Kelompok 10", 14, UIKit.TITLE, true))
	v.add_child(UIKit.label("Struktura: Legenda Dunia Data · Workshop PPLG (GameProg)", 10, UIKit.INK, true))
	var row: HBoxContainer = HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 10)
	v.add_child(row)
	for m: Dictionary in MEMBERS + [LECTURER]:
		row.add_child(_card(m))
	v.add_child(UIKit.label(CREDITS, 9, UIKit.INK))
	var back: Button = UIKit.button("Kembali")
	back.pressed.connect(close)
	v.add_child(back)
	back.grab_focus.call_deferred()


func _card(m: Dictionary) -> VBoxContainer:
	var c: VBoxContainer = VBoxContainer.new()
	c.custom_minimum_size = Vector2(120, 0)
	var frame: Panel = Panel.new()
	frame.custom_minimum_size = Vector2(96, 96)
	frame.add_theme_stylebox_override("panel", UIKit.box(Color(0.82, 0.72, 0.55), UIKit.BORDER, 2, 2))
	c.add_child(frame)
	var photo_path: String = String(m.get("photo", ""))
	if photo_path != "" and ResourceLoader.exists(photo_path):
		var tr: TextureRect = TextureRect.new()
		tr.texture = load(photo_path)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.set_anchors_preset(Control.PRESET_FULL_RECT)
		frame.add_child(tr)
	else:
		var ph: Label = UIKit.label("Foto", 10, Color(0.5, 0.4, 0.3), true)
		ph.set_anchors_preset(Control.PRESET_FULL_RECT)
		ph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		frame.add_child(ph)
	c.add_child(UIKit.label(String(m["name"]), 10, UIKit.INK, true))
	c.add_child(UIKit.label(String(m["role"]), 9, UIKit.TITLE, true))
	return c


func close() -> void:
	if _prev_music != "":
		AudioManager.play_music(_prev_music, 1.0)
	closed.emit()
	queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		close()
