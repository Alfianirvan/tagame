extends Node
## Alat (headless): cari titik pengganti untuk petunjuk/peti yang tertutup pohon, rumah, NPC, atau awan.
## Syarat titik: TIDAK tertutup sprite yang tergambar di atasnya (Objects ber-y-sort / awan), tidak menabrak dinding,
## >= 260 px dari blok awan mana pun, >= 40 px dari NPC, dan TERJANGKAU jalan kaki dari PlayerStart saat semua awan menutup.
## Pemakaian:
##   godot --headless --path . res://tools/fix_clue_spots.tscn -- <scene.tscn> <NamaNode> [<NamaNode> ...]
## Mode cek tutupan saja (untuk peti): tambahkan --tutup sebelum nama node; hanya melaporkan "TERTUTUP <nama> oleh <node>".
## Opsi: --dari=<Node> (titik awal flood, default PlayerStart), --tahap=<N> (quest_stage chapter + Kristal bila >= 3),
##       --awan=<px> (jarak minimal ke blok awan, default 260).
## Keluaran: baris "SPOT <NamaNode> <x> <y> (geser <d> px)" atau "OK <NamaNode>" bila posisi lama sudah aman.

const GRID := 8.0
var CLOUD_MIN := 260.0
const NPC_MIN := 40.0
const SEARCH := 260.0

var region: Node
var space: PhysicsDirectSpaceState2D
var occluders: Array = []     # [Rect2 global, y dasar]
var cloud_pts: Array[Vector2] = []
var npc_pts: Array[Vector2] = []
var reach: Dictionary = {}    # Vector2i sel grid -> true
var exclude: Array[RID] = []


func _ready() -> void:
	var raw: PackedStringArray = OS.get_cmdline_user_args()
	var args: PackedStringArray = []
	var from_node: String = "PlayerStart"
	var stage: int = 0
	for x in raw:
		if x.begins_with("--dari="): from_node = x.substr(7)
		elif x.begins_with("--tahap="): stage = int(x.substr(8))
		elif x.begins_with("--awan="): CLOUD_MIN = float(x.substr(7))
		else: args.append(x)
	GameManager.reset_state()
	QuestManager.reset_state()
	GameManager.set_quest_stage(0, 1)
	var chn: int = int(args[0].get_file().substr(2, 1)) if args[0].get_file().begins_with("Ch") else 0
	for c in range(1, chn):
		GameManager.set_quest_stage(c, 3)
		GameManager.add_crystal(c)
	if stage > 0 and chn > 0:
		GameManager.set_quest_stage(chn, mini(stage, 2))
		if stage >= 3:
			GameManager.add_crystal(chn)
	QuestManager.refresh_active()
	for ch in range(1, 6):
		GameManager.mark_met("opening_ch%d" % ch)
	region = (load(args[0]) as PackedScene).instantiate()
	add_child(region)
	for i in 6:
		await get_tree().physics_frame
	space = (region as Node2D).get_world_2d().direct_space_state
	var names: Array = Array(args.slice(1))
	var only_cover: bool = names.has("--tutup")
	names.erase("--tutup")
	_collect(names)
	if only_cover:
		for nm: String in names:
			var p0: Vector2 = (region.find_child(nm, true, false) as Node2D).global_position
			for o: Array in occluders:
				if (o[0] as Rect2).grow(-20).has_point(p0 + Vector2(0, -6)) and float(o[1]) >= p0.y - 6.0:
					print("TERTUTUP ", nm, " ", p0, " ", o[2])
		get_tree().quit()
		return
	for i in 30:
		await get_tree().physics_frame   # awan yang terbuka memudar & mematikan collision
	_flood((region.find_child(from_node, true, false) as Node2D).global_position + Vector2(0, 24))
	for nm: String in names:
		var n: Node2D = region.find_child(nm, true, false) as Node2D
		var p: Vector2 = n.global_position
		if _good(p):
			print("OK ", nm)
			continue
		var best: Vector2 = Vector2.INF
		var r: float = GRID
		while r <= SEARCH and best == Vector2.INF:
			var steps: int = int(TAU * r / GRID)
			for s in steps:
				var q: Vector2 = (p + Vector2.from_angle(TAU * s / steps) * r).round()
				if _good(q):
					best = q
					break
			r += GRID
		if best == Vector2.INF:
			print("GAGAL ", nm, " tidak ada titik aman dalam ", SEARCH, " px")
		else:
			print("SPOT %s %d %d (geser %d px)" % [nm, best.x, best.y, p.distance_to(best)])
	get_tree().quit()


func _collect(names: Array) -> void:
	for n: Node in region.find_children("*", "", true, false):
		if n is CollisionObject2D and n.name in names:
			continue
		var in_cloud: bool = false
		var a: Node = n.get_parent()
		while a != null and a != region:
			if a.get_script() and String(a.get_script().resource_path).ends_with("CloudBarrier.gd"):
				in_cloud = true
			a = a.get_parent()
		if n.name == "Block" and n is TileMapLayer and n.get_parent().get_script() \
				and String(n.get_parent().get_script().resource_path).ends_with("CloudBarrier.gd"):
			var blk: TileMapLayer = n as TileMapLayer
			for cell in blk.get_used_cells():
				cloud_pts.append(blk.to_global(blk.map_to_local(cell)))
		if n.is_in_group("npc") and n is Node2D:
			npc_pts.append((n as Node2D).global_position)
		if n is CollisionObject2D and (n.is_in_group("player") or n is Area2D):
			exclude.append((n as CollisionObject2D).get_rid())
		if not (n is Sprite2D or n is AnimatedSprite2D):
			continue
		var owner_obj: Node = n
		var under_objects: bool = false
		var b: Node = n
		while b != null and b != region:
			if b.name == "Objects":
				under_objects = true
			if b.name in names:
				under_objects = false
				break
			b = b.get_parent()
		if not (under_objects or in_cloud):
			continue
		var s: Node2D = n as Node2D
		var rect: Rect2
		if n is Sprite2D:
			rect = (n as Sprite2D).get_rect()
		else:
			var asp: AnimatedSprite2D = n as AnimatedSprite2D
			if asp.sprite_frames == null or not asp.sprite_frames.has_animation(asp.animation):
				continue
			var tex: Texture2D = asp.sprite_frames.get_frame_texture(asp.animation, 0)
			if tex == null:
				continue
			rect = Rect2(-tex.get_size() / 2.0 + asp.offset, tex.get_size())
		var gr: Rect2 = Rect2(s.global_transform * rect.position, rect.size * s.global_scale.abs())
		if gr.size.x < 20 or gr.size.x > 700:
			continue
		# dasar y untuk y-sort = posisi node induk teratas di bawah Objects (pohon/rumah/NPC)
		var base_y: float = s.global_position.y
		var top: Node = owner_obj
		while top.get_parent() != null and top.get_parent().name != "Objects" and top.get_parent() != region:
			top = top.get_parent()
		if top is Node2D:
			base_y = (top as Node2D).global_position.y
		occluders.append([gr.grow(24), 1e9 if in_cloud else base_y, top.name])


func _blocked(p: Vector2, radius: float) -> bool:
	var q: PhysicsShapeQueryParameters2D = PhysicsShapeQueryParameters2D.new()
	var c: CircleShape2D = CircleShape2D.new()
	c.radius = radius
	q.shape = c
	q.transform = Transform2D(0.0, p)
	q.collision_mask = 1
	q.exclude = exclude
	return not space.intersect_shape(q, 1).is_empty()


func _flood(start: Vector2) -> void:
	var s: Vector2i = Vector2i((start / GRID).round())
	var todo: Array[Vector2i] = [s]
	reach[s] = true
	var size: Vector2 = Vector2(region.get("map_size")) if region.get("map_size") != null else Vector2(6000, 6000)
	while not todo.is_empty():
		var c: Vector2i = todo.pop_back()
		for d: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nc: Vector2i = c + d
			if reach.has(nc) or nc.x < 0 or nc.y < 0 or nc.x * GRID > size.x or nc.y * GRID > size.y:
				continue
			if _blocked(Vector2(nc) * GRID, 6.0):
				reach[nc] = false
				continue
			reach[nc] = true
			todo.append(nc)


func _good(p: Vector2) -> bool:
	if not reach.get(Vector2i((p / GRID).round()), false) or _blocked(p, 9.0):
		return false
	for o: Array in occluders:
		if (o[0] as Rect2).has_point(p + Vector2(0, -6)) and float(o[1]) >= p.y - 6.0:
			return false
	for c: Vector2 in cloud_pts:
		if c.distance_to(p) < CLOUD_MIN:
			return false
	for c: Vector2 in npc_pts:
		if c.distance_to(p) < NPC_MIN:
			return false
	return true
