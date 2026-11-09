class_name QuestArrow
extends Control
## Panah penunjuk di tepi layar yang mengarah ke target quest aktif (NPC, stasiun puzzle, boss, Kristal,
## gerbang, atau jalan keluar ke wilayah yang dituju) saat target berada di luar layar.
## Target dicari ulang hanya saat status quest/scene berubah (signal); _process hanya menggeser panah
## mengikuti kamera karena posisi layar target memang berubah tiap frame.

const MARGIN := 22.0          # jarak panah dari tepi layar
const ON_SCREEN_PAD := 14.0   # target dianggap terlihat bila lebih dari ini di dalam layar

var _target: Node2D = null
var _arrow_pos: Vector2 = Vector2.ZERO
var _arrow_dir: Vector2 = Vector2.RIGHT
var _pulse: float = 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	QuestManager.quests_changed.connect(refresh_target)
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: refresh_target())
	GameManager.crystal_collected.connect(func(_c: int) -> void: refresh_target())
	GameManager.chapter_changed.connect(func(_c: int) -> void: refresh_target.call_deferred())
	set_process(false)
	refresh_target.call_deferred()   # tunggu isi scene (boss, NPC) selesai dibuat


## Mencari node target untuk quest yang sedang dilacak.
func refresh_target() -> void:
	_target = _find_target()
	set_process(_target != null)
	if _target == null:
		queue_redraw()


func _find_target() -> Node2D:
	var id: String = QuestManager.get_tracked_quest_id()
	if id == "":
		return null
	var q: Dictionary = QuestManager.get_quest(id)
	var chapter: int = int(q.get("chapter", 0))
	var tree: SceneTree = get_tree()
	if q.get("type", "") == "puzzle":
		for s: Node in tree.get_nodes_in_group("puzzle_station"):
			if s is PuzzleStation and (s as PuzzleStation).chapter == chapter:
				return s as Node2D
		return _exit_toward(chapter)
	# Quest kuis: bila belum siap (Kristal belum diambil) arahkan ke boss / Kristal / gerbang
	if not QuestManager.is_ready(id):
		var boss: Node2D = tree.get_first_node_in_group("boss") as Node2D
		if boss != null:
			return boss
		var crystal: Node2D = tree.get_first_node_in_group("crystal") as Node2D
		if crystal != null:
			return crystal
		for g: Node in tree.get_nodes_in_group("region_gate"):
			if g is RegionGate and not (g as RegionGate).is_open:
				return g as Node2D
		return _exit_toward(chapter)
	for n: Node in tree.get_nodes_in_group("npc"):
		if String(n.get("npc_id")) == String(q.get("npc", "")):
			return n as Node2D
	return _exit_toward(chapter)


## Papan jalan menuju wilayah tujuan: satu langkah ke depan/belakang di rute lurus.
func _exit_toward(chapter: int) -> Node2D:
	var here: int = GameManager.current_chapter
	if chapter == here:
		return null
	var dest: int = here + 1 if chapter > here else here - 1
	for e: Node in get_tree().get_nodes_in_group("region_exit"):
		if e is RegionExit and (e as RegionExit).to_chapter == dest:
			return e as Node2D
	return null


func _process(delta: float) -> void:
	if _target == null or not is_instance_valid(_target):
		refresh_target()
		return
	_pulse += delta * 6.0
	var screen: Vector2 = get_viewport().get_visible_rect().size
	var pos: Vector2 = get_viewport().get_canvas_transform() * (_target.global_position + Vector2(0, -16))
	var inner: Rect2 = Rect2(Vector2.ZERO, screen).grow(-ON_SCREEN_PAD)
	if inner.has_point(pos):
		if visible:
			visible = false
		return
	visible = true
	var center: Vector2 = screen * 0.5
	var dir: Vector2 = (pos - center).normalized()
	# Titik potong garis dari tengah ke target dengan kotak layar (dikurangi margin)
	var half: Vector2 = screen * 0.5 - Vector2(MARGIN, MARGIN)
	var scale_x: float = half.x / maxf(absf(dir.x), 0.0001)
	var scale_y: float = half.y / maxf(absf(dir.y), 0.0001)
	_arrow_pos = center + dir * minf(scale_x, scale_y)
	_arrow_dir = dir
	queue_redraw()


func _draw() -> void:
	if _target == null or not visible:
		return
	var s: float = 1.0 + sin(_pulse) * 0.12
	var side: Vector2 = _arrow_dir.orthogonal()
	var tip: Vector2 = _arrow_pos + _arrow_dir * 9.0 * s
	var base_l: Vector2 = _arrow_pos - _arrow_dir * 7.0 * s + side * 8.0 * s
	var base_r: Vector2 = _arrow_pos - _arrow_dir * 7.0 * s - side * 8.0 * s
	var notch: Vector2 = _arrow_pos - _arrow_dir * 3.0 * s
	draw_colored_polygon(PackedVector2Array([tip + _arrow_dir * 1.5, base_l - side * 1.0, base_r + side * 1.0]), Color(0, 0, 0, 0.7))
	draw_colored_polygon(PackedVector2Array([tip, base_l, notch, base_r]), Color(1.0, 0.85, 0.25))
