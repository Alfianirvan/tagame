extends Node2D
## TestArena: arena uji sementara untuk Player (lantai rumput + dinding tak terlihat).
## Tombol debug: F1-F5 beri+pasang senjata (pedang/tombak/palu/busur/tongkat); 1-6 ganti senjata milik player; klik kanan atau K = serangan alternatif pedang/tongkat, R = munculkan musuh acak,
## B = Golem Batu, N = Penyihir Menara, V = Kapten Bajak Laut, C = Ksatria Rantai, X = King Subiyan, H = kena hit uji, Backspace = bunuh player.

const TILE := 16
const ARENA := Vector2i(40, 24)            # ukuran dalam tile
const GRASS_ATLAS_COORDS: Array[Vector2i] = [Vector2i(1, 10), Vector2i(2, 10), Vector2i(3, 10), Vector2i(1, 11), Vector2i(2, 11), Vector2i(3, 11)]
const FLOOR_TEXTURE := "res://assets/tilesets/Floors_Tiles.png"
const DEBUG_BOSSES := {
	KEY_B: "res://scenes/entities/BossGolem.tscn",
	KEY_N: "res://scenes/entities/BossPenyihir.tscn",
	KEY_V: "res://scenes/entities/BossKapten.tscn",
	KEY_C: "res://scenes/entities/BossKsatria.tscn",
	KEY_X: "res://scenes/entities/BossKing.tscn",
}
const DEBUG_WEAPONS := {KEY_F1: "pedang_kayu", KEY_F2: "tombak_kayu", KEY_F3: "palu_kayu", KEY_F4: "busur_kayu", KEY_F5: "tongkat_sihir"}

@onready var floor_layer: TileMapLayer = $Floor
@onready var player: CharacterBody2D = $Player


func _ready() -> void:
	_build_floor()
	_build_walls()
	player.position = Vector2(ARENA * TILE) / 2.0
	player.set_camera_limits(Rect2i(Vector2i.ZERO, ARENA * TILE))
	player.death_finished.connect(_on_player_death_finished)
	if GameManager.equipment.get("weapon", "") == "":
		_give_and_equip("pedang_kayu")
	_spawn_test_items()
	_spawn_enemy("orc", Vector2(-140, -50))
	_spawn_enemy("skeleton", Vector2(140, -50))
	_spawn_enemy("orc_shaman", Vector2(-150, 70))
	_spawn_enemy("skeleton_rogue", Vector2(150, 70))


## Memunculkan musuh di posisi relatif terhadap tengah arena (Tahap 7).
func _spawn_enemy(enemy_id: String, offset: Vector2) -> CharacterBody2D:
	var enemy: CharacterBody2D = (load("res://scenes/entities/Enemy.tscn") as PackedScene).instantiate()
	enemy.set("enemy_id", enemy_id)
	add_child(enemy)
	enemy.global_position = Vector2(ARENA * TILE) / 2.0 + offset
	return enemy


## Membuat TileSet dari atlas Floors_Tiles (tile rumput penuh) lalu mengisi lantai.
func _build_floor() -> void:
	var source: TileSetAtlasSource = TileSetAtlasSource.new()
	source.texture = load(FLOOR_TEXTURE)
	source.texture_region_size = Vector2i(TILE, TILE)
	for coords in GRASS_ATLAS_COORDS:
		source.create_tile(coords)
	var tile_set: TileSet = TileSet.new()
	tile_set.tile_size = Vector2i(TILE, TILE)
	tile_set.add_source(source, 0)
	floor_layer.tile_set = tile_set
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 7
	for x in ARENA.x:
		for y in ARENA.y:
			# 85% tile polos, sisanya variasi (baris pertama saja agar warna seragam)
			var coords: Vector2i = GRASS_ATLAS_COORDS[1] if rng.randf() < 0.85 else GRASS_ATLAS_COORDS[rng.randi() % 3]
			floor_layer.set_cell(Vector2i(x, y), 0, coords)


## Empat dinding tak terlihat di tepi arena (layer 1 = world).
func _build_walls() -> void:
	var body: StaticBody2D = StaticBody2D.new()
	body.collision_layer = 1
	add_child(body)
	var size: Vector2 = Vector2(ARENA * TILE)
	var t: float = 32.0
	var rects: Array[Rect2] = [
		Rect2(-t, -t, size.x + t * 2, t),
		Rect2(-t, size.y, size.x + t * 2, t),
		Rect2(-t, 0, t, size.y),
		Rect2(size.x, 0, t, size.y),
	]
	for r in rects:
		var shape: CollisionShape2D = CollisionShape2D.new()
		var rect: RectangleShape2D = RectangleShape2D.new()
		rect.size = r.size
		shape.shape = rect
		shape.position = r.position + r.size / 2.0
		body.add_child(shape)


## Uji Tahap 6: collectible turunan + 2 peti di sekitar pemain.
func _spawn_test_items() -> void:
	var center: Vector2 = Vector2(ARENA * TILE) / 2.0
	var scenes: Array[String] = ["GoldCoin", "Ore", "Herb", "DataFragment", "Potion"]
	for i in scenes.size():
		var c: Node2D = (load("res://scenes/entities/%s.tscn" % scenes[i]) as PackedScene).instantiate()
		add_child(c)
		c.global_position = center + Vector2(-80 + i * 24, 50)
	for i in 2:
		var chest: Node2D = (load("res://scenes/entities/Chest.tscn") as PackedScene).instantiate()
		add_child(chest)
		chest.global_position = center + Vector2(-60 + i * 120, -60)


func _give_and_equip(weapon_id: String) -> void:
	if GameManager.count_item(weapon_id) == 0 and not GameManager.equipment.values().has(weapon_id):
		GameManager.add_item(weapon_id)
	GameManager.equip(weapon_id)


func _unhandled_key_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if DEBUG_WEAPONS.has(key.keycode):
		_give_and_equip(DEBUG_WEAPONS[key.keycode])
	elif key.keycode == KEY_R:
		# Debug: munculkan 1 musuh acak di dekat player
		var ids: Array = ["orc", "orc_rogue", "orc_warrior", "orc_shaman", "skeleton", "skeleton_rogue", "skeleton_warrior", "skeleton_mage"]
		var pos: Vector2 = player.global_position - Vector2(ARENA * TILE) / 2.0 + Vector2.from_angle(randf() * TAU) * 110.0
		_spawn_enemy(ids.pick_random(), pos)
	elif DEBUG_BOSSES.has(key.keycode):
		# Debug Tahap 8: munculkan boss pilihan (satu boss pada satu waktu)
		if get_tree().get_nodes_in_group("boss").is_empty():
			var scene_path: String = DEBUG_BOSSES[key.keycode]
			var boss: Node2D = (load(scene_path) as PackedScene).instantiate()
			add_child(boss)
			boss.global_position = player.global_position + Vector2(0, -110)
	elif key.keycode == KEY_H:
		player.take_hit(10, player.global_position + Vector2(20, 0))
	elif key.keycode == KEY_BACKSPACE:
		GameManager.take_damage(9999, true)


func _on_player_death_finished() -> void:
	# Layar Kalah dibuat di Tahap 11; sementara pulihkan dan muat ulang arena.
	GameManager.restore_full()
	SceneManager.reload_current()
