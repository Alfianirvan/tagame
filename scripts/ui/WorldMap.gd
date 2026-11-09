class_name WorldMap
extends CanvasLayer
## Peta Dunia (tombol M, atau dibuka sebagai scene sendiri). Satu gambar besar yang bisa digeser (seret mouse / panah / WASD)
## dan di-zoom (roda mouse). Klik wilayah terbuka = fast travel. Wilayah terkunci ditutup awan + gembok;
## awan menghilang dengan animasi saat wilayah baru terbuka. Wilayah tujuan berikutnya berkedip.
## Gambar sudah memuat nomor + nama wilayah; skrip ini menambah area klik, garis jalan yang sudah dilewati, awan, dan gembok.

signal closed

const MAP_TEX := preload("res://assets/worldmap/peta_dunia_preview.png")
const MAP_SIZE := Vector2(810, 1440)
## Pusat penanda di gambar 810x1440: S(Desa), 1..4, F(Pohon Dunia)
const MARKERS: Array[Vector2] = [Vector2(324, 1281), Vector2(378, 1020), Vector2(243, 762), Vector2(501, 576), Vector2(324, 360), Vector2(420, 144)]
const HIT_RADIUS := 36.0
const ZOOM_MIN := 0.6
const ZOOM_MAX := 1.8
const START_SCREEN := "res://scenes/ui/StartScreen.tscn"
const CLOUD_PUFFS: Array[Vector3] = [Vector3(-30, 8, 24), Vector3(0, -10, 30), Vector3(30, 6, 24), Vector3(-12, 22, 22), Vector3(16, 22, 22), Vector3(-44, -4, 16), Vector3(46, -2, 16)]

## Wilayah yang sudah pernah "dilihat terbuka" (agar animasi awan hanya sekali). Kunci: nomor chapter.
static var seen_open: Dictionary = {}

var standalone: bool = false
var _root: Control
var _view: Control
var _map: Control
var _over: Control
var _info_name: Label
var _info_state: Label
var _zoom: float = 0.9
var _dragging: bool = false
var _drag_dist: float = 0.0
var _hover: int = -1
var _cloud_alpha: Dictionary = {}   # chapter -> 0..1
var _pulse: float = 0.0
var _chapters: Dictionary = {}
var _paused_by_me: bool = false
var _was_enabled: bool = true
var _is_open: bool = false
var _pulse_tween: Tween


func _ready() -> void:
	layer = 60
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("world_map_ui")
	add_to_group("ui_overlay")
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "chapters.json")
	if data is Dictionary:
		_chapters = data
	_build_ui()
	GameManager.chapter_unlocked.connect(_on_chapter_unlocked)
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _over.queue_redraw())
	standalone = get_tree().current_scene == self
	if standalone:
		AudioManager.play_music("peta_dunia")
		open()
	else:
		_root.visible = false


# ---------------------------------------------------------------- UI

func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var bg: ColorRect = ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.08, 0.2, 0.42)
	_root.add_child(bg)

	_view = Control.new()
	_view.set_anchors_preset(Control.PRESET_FULL_RECT)
	_view.clip_contents = true
	_view.gui_input.connect(_on_view_input)
	_root.add_child(_view)

	_map = Control.new()
	_map.size = MAP_SIZE
	_map.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_view.add_child(_map)
	var tex: TextureRect = TextureRect.new()
	tex.texture = MAP_TEX
	tex.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tex.size = MAP_SIZE
	tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_map.add_child(tex)
	_over = Control.new()
	_over.size = MAP_SIZE
	_over.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_over.draw.connect(_draw_overlay)
	_map.add_child(_over)

	# Kartu info di bawah
	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(10, 292)
	panel.size = Vector2(620, 58)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel", UIKit.box(Color(0.96, 0.9, 0.76, 0.94), UIKit.BORDER, 3, 6))
	_root.add_child(panel)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(v)
	_info_name = UIKit.label("", 13, UIKit.TITLE)
	_info_state = UIKit.label("", 10, UIKit.INK)
	v.add_child(_info_name)
	v.add_child(_info_state)
	v.add_child(UIKit.label("Klik wilayah = pergi · seret / panah = geser · roda mouse = zoom · M / Esc = tutup", 9, Color(0.5, 0.36, 0.25)))

	var close_btn: Button = UIKit.button("Kembali", Vector2(70, 22))
	close_btn.position = Vector2(562, 8)
	close_btn.pressed.connect(_on_close_pressed)
	_root.add_child(close_btn)


# ---------------------------------------------------------------- Buka / tutup

func open() -> void:
	if _is_open:
		return
	if not standalone and (DialogManager.is_active or QuestManager.quiz_active):
		return
	_is_open = true
	_root.visible = true
	if not standalone:
		var player: Node = get_tree().get_first_node_in_group("player")
		_was_enabled = player == null or bool(player.get("controls_enabled"))
		if player and player.has_method("set_controls_enabled"):
			player.set_controls_enabled(false)
		_paused_by_me = not get_tree().paused
		get_tree().paused = true
	_cloud_alpha.clear()
	var first_time: bool = seen_open.is_empty()
	var fresh: Array[int] = []
	for c in range(0, GameManager.MAX_CHAPTER + 1):
		var open_now: bool = _is_region_open(c)
		_cloud_alpha[c] = 0.0 if open_now else 1.0
		if open_now and not seen_open.has(c) and not first_time:
			fresh.append(c)
		if open_now:
			seen_open[c] = true
	_center_on(_next_target() if standalone else GameManager.current_chapter)
	_start_pulse()
	_update_info(-1)
	_over.queue_redraw()
	for c in fresh:      # wilayah yang baru terbuka sejak peta terakhir dilihat: awan menghilang
		_cloud_alpha[c] = 1.0
		_reveal(c)


func close() -> void:
	if not _is_open:
		return
	_is_open = false
	_root.visible = false
	if _pulse_tween:
		_pulse_tween.kill()
	if not standalone:
		if _paused_by_me:
			get_tree().paused = false
		var player: Node = get_tree().get_first_node_in_group("player")
		if player and player.has_method("set_controls_enabled"):
			player.set_controls_enabled(_was_enabled)
	closed.emit()


func is_open() -> bool:
	return _is_open


func _on_close_pressed() -> void:
	AudioManager.play_sfx("menu_batal")
	if standalone:
		SceneManager.change_scene(START_SCREEN)
	else:
		close()


func _on_chapter_unlocked(chapter: int) -> void:
	if _is_open:
		_reveal(chapter)


# ---------------------------------------------------------------- Status wilayah

## Wilayah terbuka di peta: Desa selalu; Hutan Indeks setelah prolog Joko; lainnya sesuai unlocked_chapter.
func _is_region_open(ch: int) -> bool:
	if ch == 0:
		return true
	if ch == 1 and GameManager.get_quest_stage(0) < 1:
		return false
	return GameManager.is_chapter_unlocked(ch)


## Wilayah tujuan berikutnya: yang pertama terbuka tetapi belum tuntas (Quest Akhir).
func _next_target() -> int:
	if GameManager.get_quest_stage(0) < 1:
		return 0
	for c in range(1, GameManager.MAX_CHAPTER + 1):
		if _is_region_open(c) and GameManager.get_quest_stage(c) < 3:
			return c
	return GameManager.MAX_CHAPTER


func _region_name(ch: int) -> String:
	return String(_chapters.get(str(ch), {}).get("name", "Wilayah %d" % ch))


func _update_info(ch: int) -> void:
	var c: int = ch
	if c < 0:
		c = _next_target() if standalone else GameManager.current_chapter
	_info_name.text = "%s — %s" % [_region_name(c), String(_chapters.get(str(c), {}).get("topic", ""))]
	if not _is_region_open(c):
		_info_state.text = "Terkunci. " + _lock_hint(c)
	elif c == GameManager.current_chapter and not standalone:
		_info_state.text = "Kamu berada di sini."
	elif c > 0 and GameManager.get_quest_stage(c) >= 3:
		_info_state.text = "Selesai. Klik untuk berkunjung lagi."
	else:
		_info_state.text = "Terbuka. Klik untuk pergi." + ("  (Tujuan berikutnya)" if c == _next_target() else "")


func _lock_hint(ch: int) -> String:
	if ch == 1:
		return "Bicaralah dengan Joko di Desa Algoria dulu."
	return "Tuntaskan %s (Quest Akhir) untuk membukanya." % _region_name(ch - 1)


# ---------------------------------------------------------------- Animasi

func _start_pulse() -> void:
	if _pulse_tween:
		_pulse_tween.kill()
	_pulse_tween = create_tween().set_loops()
	_pulse_tween.tween_method(_set_pulse, 0.0, 1.0, 1.0)


func _set_pulse(v: float) -> void:
	_pulse = v
	_over.queue_redraw()


func _reveal(ch: int) -> void:
	AudioManager.play_sfx("menu_pindah")
	seen_open[ch] = true
	var tw: Tween = create_tween()
	tw.tween_interval(0.4)
	tw.tween_method(_set_cloud_alpha.bind(ch), 1.0, 0.0, 1.6)


func _set_cloud_alpha(a: float, ch: int) -> void:
	_cloud_alpha[ch] = a
	_over.queue_redraw()


func _draw_overlay() -> void:
	# Jalan yang sudah dilewati: titik kuning antar-penanda
	for i in range(GameManager.MAX_CHAPTER):
		if i == 0 and GameManager.get_quest_stage(0) < 1:
			continue
		if _is_region_open(i + 1) and (i == 0 or GameManager.get_quest_stage(i) >= 3):
			_dashed(MARKERS[i], MARKERS[i + 1], Color(1, 0.92, 0.45, 0.95))
	# Penanda tujuan berikutnya berkedip
	var tgt: int = _next_target()
	if _is_region_open(tgt) and GameManager.get_quest_stage(tgt) < (1 if tgt == 0 else 3):
		_over.draw_arc(MARKERS[tgt], 26.0 + 10.0 * _pulse, 0, TAU, 40, Color(1, 0.95, 0.4, 1.0 - _pulse), 3.0)
	# Hover
	if _hover >= 0 and _is_region_open(_hover):
		_over.draw_arc(MARKERS[_hover], 28, 0, TAU, 40, Color(1, 1, 1, 0.9), 3.0)
	# Posisi Raka sekarang
	if not standalone:
		var p: Vector2 = MARKERS[clampi(GameManager.current_chapter, 0, GameManager.MAX_CHAPTER)] + Vector2(0, -44)
		var tri: PackedVector2Array = PackedVector2Array([p, p + Vector2(-8, -14), p + Vector2(8, -14)])
		_over.draw_colored_polygon(tri, Color(0.9, 0.2, 0.2))
		tri.append(p)
		_over.draw_polyline(tri, Color(0.3, 0.05, 0.05), 1.5)
	# Awan + gembok di wilayah terkunci
	for c in range(0, GameManager.MAX_CHAPTER + 1):
		var a: float = float(_cloud_alpha.get(c, 0.0))
		if a > 0.01:
			_draw_cloud(MARKERS[c], a)


func _dashed(a: Vector2, b: Vector2, col: Color) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(length, 1.0)
	var t: float = 0.0
	while t < length:
		_over.draw_circle(a + dir * t, 2.5, col)
		t += 12.0


func _draw_cloud(center: Vector2, alpha: float) -> void:
	for puff: Vector3 in CLOUD_PUFFS:
		_over.draw_circle(center + Vector2(puff.x, puff.y), puff.z, Color(0.88, 0.91, 0.98, 0.97 * alpha))
	for puff: Vector3 in CLOUD_PUFFS:
		_over.draw_circle(center + Vector2(puff.x, puff.y - 4), puff.z * 0.7, Color(1, 1, 1, 0.92 * alpha))
	# Gembok
	var k: Vector2 = center + Vector2(0, 4)
	_over.draw_arc(k + Vector2(0, -2), 7, PI, TAU, 14, Color(0.35, 0.35, 0.4, alpha), 3.0)
	_over.draw_rect(Rect2(k + Vector2(-9, -2), Vector2(18, 14)), Color(0.45, 0.45, 0.52, alpha))
	_over.draw_rect(Rect2(k + Vector2(-9, -2), Vector2(18, 14)), Color(0.2, 0.2, 0.25, alpha), false, 1.5)
	_over.draw_circle(k + Vector2(0, 5), 2.2, Color(0.15, 0.15, 0.2, alpha))


# ---------------------------------------------------------------- Pan & zoom

func _center_on(ch: int) -> void:
	_apply_zoom(_zoom)
	_map.position = Vector2(320, 150) - MARKERS[clampi(ch, 0, GameManager.MAX_CHAPTER)] * _zoom
	_clamp_pan()


func _apply_zoom(z: float) -> void:
	_zoom = clampf(z, ZOOM_MIN, ZOOM_MAX)
	_map.scale = Vector2(_zoom, _zoom)


func _clamp_pan() -> void:
	var sz: Vector2 = MAP_SIZE * _zoom
	var view: Vector2 = Vector2(640, 360)
	if sz.x > view.x:
		_map.position.x = clampf(_map.position.x, view.x - sz.x, 0.0)
	else:
		_map.position.x = (view.x - sz.x) / 2.0
	if sz.y > view.y:
		_map.position.y = clampf(_map.position.y, view.y - sz.y, 0.0)
	else:
		_map.position.y = (view.y - sz.y) / 2.0


func _to_map(screen_pos: Vector2) -> Vector2:
	return (screen_pos - _map.position) / _zoom


func _marker_at(map_pos: Vector2) -> int:
	for c in range(MARKERS.size()):
		if map_pos.distance_to(MARKERS[c]) <= HIT_RADIUS:
			return c
	return -1


func _on_view_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_dragging = true
				_drag_dist = 0.0
			else:
				_dragging = false
				if _drag_dist < 6.0:
					_try_travel(_marker_at(_to_map(mb.position)))
		elif mb.pressed and (mb.button_index == MOUSE_BUTTON_WHEEL_UP or mb.button_index == MOUSE_BUTTON_WHEEL_DOWN):
			var before: Vector2 = _to_map(mb.position)
			_apply_zoom(_zoom * (1.12 if mb.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.12))
			_map.position = mb.position - before * _zoom
			_clamp_pan()
	elif event is InputEventMouseMotion:
		var mm: InputEventMouseMotion = event
		if _dragging:
			_drag_dist += mm.relative.length()
			_map.position += mm.relative
			_clamp_pan()
		var h: int = _marker_at(_to_map(mm.position))
		if h != _hover:
			_hover = h
			_update_info(h)
			_over.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _is_open:
		if not standalone and event.is_action_pressed("world_map"):
			get_viewport().set_input_as_handled()
			open()
		return
	if (event.is_action_pressed("world_map") and not standalone) or event.is_action_pressed("pause"):
		get_viewport().set_input_as_handled()
		_on_close_pressed()
		return
	var step: Vector2 = Vector2.ZERO
	if event.is_action_pressed("move_left"):
		step.x = 48
	elif event.is_action_pressed("move_right"):
		step.x = -48
	elif event.is_action_pressed("move_up"):
		step.y = 48
	elif event.is_action_pressed("move_down"):
		step.y = -48
	if step != Vector2.ZERO:
		_map.position += step
		_clamp_pan()
		get_viewport().set_input_as_handled()


# ---------------------------------------------------------------- Fast travel

func _try_travel(ch: int) -> void:
	if ch < 0:
		return
	if not _is_region_open(ch):
		AudioManager.play_sfx("menu_batal")
		_info_state.text = "Terkunci. " + _lock_hint(ch)
		return
	var path: String = String(_chapters.get(str(ch), {}).get("scene", ""))
	if path == "" or not ResourceLoader.exists(path):
		AudioManager.play_sfx("menu_batal")
		return
	if not standalone and ch == GameManager.current_chapter:
		close()
		return
	AudioManager.play_sfx("menu_pilih")
	# Titik hidup tetap bila sudah ada di wilayah tujuan; selain itu mulai dari pintu masuk wilayah.
	if GameManager.checkpoint_scene != path:
		GameManager.set_checkpoint(path, Vector2.ZERO)
	close()
	SceneManager.change_scene(path)
