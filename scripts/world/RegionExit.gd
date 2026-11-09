class_name RegionExit
extends Area2D
## Papan jalan pulang: tekan E di dekatnya untuk pindah ke scene lain (mis. kembali ke Desa Algoria).

const FONT := preload("res://assets/fonts/Square-Black.ttf")

## Wilayah tujuan (0 = Desa, 1..5 = chapter). Scene dibaca dari data/chapters.json.
## Rute LURUS: maju ke chapter N hanya bila chapter N-1 tuntas (Desa -> prolog Joko, wilayah lain -> Quest Akhir).
## Mundur ke chapter sebelumnya selalu boleh.
@export var to_chapter: int = 0
## Isi bila ingin menimpa scene tujuan (kosong = pakai chapters.json).
@export_file("*.tscn") var target_scene: String = ""
@export var sign_text: String = "Kembali ke Desa"

var _player_in_range: bool = false
var _hint: Label
var _chapters: Dictionary = {}


func _ready() -> void:
	add_to_group("region_exit")
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "chapters.json")
	if data is Dictionary:
		_chapters = data
	collision_layer = 0
	collision_mask = 2
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 30.0
	shape.shape = circle
	add_child(shape)
	_hint = Label.new()
	_hint.add_theme_font_override("font", FONT)
	_hint.add_theme_font_size_override("font_size", 8)
	_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_hint.add_theme_constant_override("outline_size", 3)
	_hint.position = Vector2(-60, -52)
	_hint.size = Vector2(120, 20)
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.visible = false
	add_child(_hint)
	body_entered.connect(func(b: Node2D) -> void: _set_range(b, true))
	body_exited.connect(func(b: Node2D) -> void: _set_range(b, false))
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _refresh())
	GameManager.chapter_changed.connect(func(_c: int) -> void: _refresh())  # chapter aktif baru ditetapkan Region setelah node ini siap
	z_index = 1
	_refresh()


## Maju ke chapter berikutnya terkunci sampai chapter sebelumnya tuntas.
func is_locked() -> bool:
	if to_chapter <= GameManager.current_chapter:
		return false
	var prev: int = to_chapter - 1
	var needed: int = 1 if prev == 0 else 3
	return GameManager.get_quest_stage(prev) < needed


func get_target_scene() -> String:
	if target_scene != "":
		return target_scene
	return String(_chapters.get(str(to_chapter), {}).get("scene", ""))


func _lock_text() -> String:
	var prev: int = to_chapter - 1
	if prev == 0:
		return "Terkunci: bicaralah dengan Joko dulu."
	var prev_name: String = String(_chapters.get(str(prev), {}).get("name", "chapter ini"))
	return "Terkunci: tuntaskan %s (Quest Akhir)." % prev_name


func _refresh() -> void:
	modulate = Color(0.65, 0.65, 0.65) if is_locked() else Color.WHITE
	_hint.text = _lock_text() if is_locked() else "E: %s" % sign_text


func _set_range(body: Node2D, inside: bool) -> void:
	if body.is_in_group("player"):
		_player_in_range = inside
		_refresh()
		_hint.visible = inside


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or QuestManager.quiz_active:
		return
	if not event.is_action_pressed("interact"):
		return
	get_viewport().set_input_as_handled()
	if is_locked():
		AudioManager.play_sfx("menu_batal")
		return
	var path: String = get_target_scene()
	if path == "" or not ResourceLoader.exists(path):
		FloatingText.spawn(get_parent(), global_position + Vector2(-50, -60), "Wilayah ini belum tersedia.", Color(1, 0.8, 0.5), 2.2)
		return
	# Tabrakan tidak mengunci kontrol saat berpindah; fade SceneManager yang menahan klik.
	SceneManager.change_scene(path)


func _draw() -> void:
	draw_rect(Rect2(-1, -26, 2, 26), Color(0.4, 0.27, 0.15))
	draw_rect(Rect2(-10, -28, 20, 9), Color(0.6, 0.42, 0.24))
	draw_rect(Rect2(-10, -28, 20, 9), Color(0.3, 0.18, 0.1), false, 1.0)
	draw_colored_polygon(PackedVector2Array([Vector2(-7, -23.5), Vector2(-2, -26), Vector2(-2, -21)]), Color(0.2, 0.12, 0.1))
