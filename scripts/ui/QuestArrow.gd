class_name QuestArrow
extends Control
## Panah penunjuk di tepi layar yang mengarah ke target quest aktif (NPC, stasiun puzzle, boss, Kristal,
## gerbang, atau jalan keluar ke wilayah yang dituju) saat target berada di luar layar.
## Target dicari ulang hanya saat status quest/scene berubah (signal); _process hanya menggeser panah
## mengikuti kamera karena posisi layar target memang berubah tiap frame.

const MARGIN := 22.0          # jarak panah dari tepi layar
const ON_SCREEN_PAD := 14.0   # target dianggap terlihat bila lebih dari ini di dalam layar
const DIRECT_RANGE := 520.0   # target lebih dekat dari ini (px, ~32 tile): panah menunjuk lurus, tidak mengikuti jalur

var _target: Node2D = null
var _arrow_pos: Vector2 = Vector2.ZERO
var _arrow_dir: Vector2 = Vector2.RIGHT
var _pulse: float = 0.0
var _on_route: bool = false   # sedang menuntun lewat jalur (histeresis supaya panah tidak bolak-balik di batas jarak)


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	QuestManager.quests_changed.connect(refresh_target)
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: refresh_target())
	GameManager.crystal_collected.connect(func(_c: int) -> void: refresh_target())
	GameManager.chapter_changed.connect(func(_c: int) -> void: refresh_target.call_deferred())
	GameManager.story_flag_set.connect(func(_f: String) -> void: refresh_target.call_deferred())
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
	# quest berlangkah: tuntun ke target langkah aktif, lalu ke final_target setelah semua langkah beres
	var step: Dictionary = QuestManager.get_current_step(id)
	if not step.is_empty():
		var st: Node2D = _step_target(step, chapter)
		if st != null:
			return st
	elif not QuestManager.get_steps(id).is_empty() and q.has("final_target"):
		var ft: Node2D = _nearest_named([q["final_target"]] if q["final_target"] is String else q["final_target"], [])
		if ft != null:
			return ft
	if q.get("type", "") == "puzzle":
		for s: Node in tree.get_nodes_in_group("puzzle_station"):
			if s is PuzzleStation and (s as PuzzleStation).chapter == chapter:
				return s as Node2D
		return _exit_toward(chapter)
	# Quest kuis dengan syarat warga: tuntun ke warga terdekat yang belum diajak bicara
	if int(q.get("requires_villagers", 0)) > 0 and QuestManager.is_available(id) and not QuestManager.is_ready(id):
		var player: Node2D = tree.get_first_node_in_group("player") as Node2D
		var cands0: Array[Node2D] = []
		for n: Node in tree.get_nodes_in_group("npc"):
			if int(n.get("villager_chapter")) == chapter and not QuestManager.has_talked_to_villager(chapter, String(n.get("npc_id"))):
				cands0.append(n as Node2D)
		var best: Node2D = _pick(cands0, player)
		if best != null:
			return best
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


## Target sebuah langkah quest: warga yang belum diajak bicara, anggota grup, atau node bernama (yang flag-nya belum beres).
func _step_target(step: Dictionary, chapter: int) -> Node2D:
	var tree: SceneTree = get_tree()
	var player: Node2D = tree.get_first_node_in_group("player") as Node2D
	if step.has("villagers"):
		var vc: int = int(step.get("villager_chapter", chapter))
		var cands: Array[Node2D] = []
		for n: Node in tree.get_nodes_in_group("npc"):
			if int(n.get("villager_chapter")) == vc and not QuestManager.has_talked_to_villager(vc, String(n.get("npc_id"))):
				cands.append(n as Node2D)
		return _pick(cands, player)
	if step.has("target_group"):
		var cands2: Array[Node2D] = []
		for n: Node in tree.get_nodes_in_group(String(step["target_group"])):
			if n is Node2D and n.is_inside_tree():
				cands2.append(n as Node2D)
		var g: Node2D = _pick(cands2, player)
		if g != null:
			return g
	if step.has("target"):
		var names: Array = [step["target"]] if step["target"] is String else step["target"]
		return _nearest_named(names, step.get("flags_all", []))
	return null


## Node bernama terdekat di scene wilayah; nama ke-i dilewati bila flags[i] sudah disetel.
func _nearest_named(names: Array, flags: Array) -> Node2D:
	var scene: Node = get_tree().get_first_node_in_group("region")
	if scene == null:
		return null
	var cands: Array[Node2D] = []
	for i in names.size():
		if i < flags.size() and GameManager.has_story_flag(String(flags[i])):
			continue
		var n: Node = scene.find_child(String(names[i]), true, false)
		if n is Node2D and not n.is_queued_for_deletion():
			cands.append(n as Node2D)
	return _pick(cands, get_tree().get_first_node_in_group("player") as Node2D)


## Pilih target dari beberapa kandidat (warga, petunjuk): tetap pada target sekarang selama masih jadi kandidat
## (belum selesai), supaya panah fokus ke SATU tujuan dan tidak berpindah-pindah saat Raka bergerak. Baru memilih
## kandidat terdekat bila target sekarang sudah selesai / bukan kandidat lagi.
func _pick(cands: Array[Node2D], player: Node2D) -> Node2D:
	if _target != null and is_instance_valid(_target) and _target in cands:
		return _target
	return _nearest(cands, player)


static func _nearest(cands: Array[Node2D], player: Node2D) -> Node2D:
	var best: Node2D = null
	for c in cands:
		if best == null or (player != null and c.global_position.distance_to(player.global_position) < best.global_position.distance_to(player.global_position)):
			best = c
	return best


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
	var aim: Vector2 = _guide_point(pos)
	var dir: Vector2 = (aim - center).normalized()
	# Titik potong garis dari tengah ke target dengan kotak layar (dikurangi margin)
	var half: Vector2 = screen * 0.5 - Vector2(MARGIN, MARGIN)
	var scale_x: float = half.x / maxf(absf(dir.x), 0.0001)
	var scale_y: float = half.y / maxf(absf(dir.y), 0.0001)
	_arrow_pos = center + dir * minf(scale_x, scale_y)
	_arrow_dir = dir
	queue_redraw()


## Titik yang dibidik panah. Bila wilayah punya jalur utama (Region.guide_route) dan target ada di dekat jalur itu,
## panah menuntun ke titik jalur berikutnya (~260 px di depan Raka) sehingga mengikuti jalan, bukan garis lurus menembus hutan/awan.
## Mengembalikan posisi layar yang dibidik; bila tak ada jalur, kembali ke posisi layar target.
func _guide_point(target_screen: Vector2) -> Vector2:
	var scene: Node = get_tree().get_first_node_in_group("region")
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if scene == null or player == null or not ("guide_route" in scene):
		return target_screen
	var route: PackedVector2Array = scene.guide_route
	# setelah Kristal didapat: pakai jalur pintas (bila ada) supaya Raka dituntun pulang lewat jalan pintas
	if "shortcut_route" in scene and (scene.shortcut_route as PackedVector2Array).size() >= 4 and GameManager.has_crystal(int(scene.chapter)):
		route = scene.shortcut_route
	if route.size() < 4:
		return target_screen
	# target sudah dekat: tunjuk lurus (jalur utama justru bisa memutar menjauh, mis. target di jalan cabang desa samping)
	var direct: float = player.global_position.distance_to(_target.global_position)
	if direct < DIRECT_RANGE:
		_on_route = false
		return target_screen
	var ip: int = _nearest_index(route, player.global_position)
	var it: int = _nearest_index(route, _target.global_position)
	# target jauh dari jalur utama (mis. di dalam desa samping): jalur tidak relevan. Batas masuk/keluar mode jalur dibuat
	# berbeda (histeresis) supaya panah tidak bolak-balik antara arah jalur dan arah lurus ketika Raka berdiri di dekat batas.
	var lim_t: float = 480.0 if _on_route else 420.0
	var lim_p: float = 360.0 if _on_route else 300.0
	_on_route = route[it].distance_to(_target.global_position) <= lim_t and route[ip].distance_to(player.global_position) <= lim_p
	if not _on_route:
		return target_screen
	if ip == it:
		return target_screen
	var step: int = 1 if it > ip else -1
	var i: int = ip
	while i != it and route[i].distance_to(player.global_position) < 260.0:
		i += step
	# hanya ikuti jalur bila titik yang dibidik memang mendekatkan ke target; bila tidak, tunjuk lurus
	if route[i].distance_to(_target.global_position) >= direct - 16.0:
		return target_screen
	return get_viewport().get_canvas_transform() * (route[i] + Vector2(0, -16))


static func _nearest_index(route: PackedVector2Array, p: Vector2) -> int:
	var best: int = 0
	var best_d: float = INF
	for k in route.size():
		var d: float = route[k].distance_squared_to(p)
		if d < best_d:
			best_d = d
			best = k
	return best


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
