class_name Region
extends Node2D
## Pengatur umum scene wilayah (Hutan Indeks, Tambang Tumpuk, dst): musik, kamera, posisi awal Raka
## (dari checkpoint bila ada), boss, dan hidup ulang saat Raka mati.
## Isi wilayah (tile, pohon, musuh, stasiun) dibuat oleh tools/gen_region.py dan boleh dirapikan di editor.
## Marker yang dibutuhkan: PlayerStart, BossSpawn (opsional), node Objects/Player.

@export var chapter: int = 1
@export var music_name: String = "ch1_hutan_indeks"
@export var boss_music_name: String = "boss"
@export var map_size: Vector2i = Vector2i(4000, 1024)
@export var boss_scene: PackedScene
## Kristal chapter sudah diambil = boss dianggap sudah kalah, tidak muncul lagi.
@export var respawn_boss_until_crystal: bool = true

@onready var player: CharacterBody2D = $Objects/Player
@onready var player_start: Marker2D = $PlayerStart

var boss: Boss


func _ready() -> void:
	GameManager.set_current_chapter(chapter)
	AudioManager.play_music(music_name)
	player.set_camera_limits(Rect2i(Vector2i.ZERO, map_size))
	player.death_finished.connect(_on_player_death_finished)
	var spawn: Vector2 = GameManager.get_checkpoint_spawn(self)
	if spawn != Vector2.ZERO:
		player.global_position = spawn
	else:
		player.global_position = player_start.global_position
	_spawn_boss()
	# Kristal sudah diambil (mis. muat save): NPC langsung berdiri di posisi akhir.
	if GameManager.has_crystal(chapter):
		_move_npcs_to_final()


## Pindahkan NPC ke marker FinalNPCs/<Nama> (metadata npc_id) agar Raka tidak perlu kembali ke awal wilayah.
func _move_npcs_to_final() -> void:
	var markers: Node = get_node_or_null("FinalNPCs")
	if markers == null:
		return
	for m in markers.get_children():
		var id: String = str(m.get_meta("npc_id", ""))
		for n in $Objects.get_children():
			if n is Node2D and "npc_id" in n and n.npc_id == id:
				n.global_position = (m as Node2D).global_position


func _spawn_boss() -> void:
	var spawn: Marker2D = get_node_or_null("BossSpawn") as Marker2D
	if boss_scene == null or spawn == null:
		return
	if respawn_boss_until_crystal and GameManager.has_crystal(chapter):
		return
	boss = boss_scene.instantiate() as Boss
	$Objects.add_child(boss)
	boss.global_position = spawn.global_position
	boss.fight_started.connect(func(_id: String) -> void: AudioManager.play_music(boss_music_name))
	boss.boss_defeated.connect(func(_id: String) -> void:
		AudioManager.play_music(music_name, 2.0)
		_move_npcs_to_final())


## Raka mati: tampilkan layar Kalah (Coba Lagi dari checkpoint / Menu Utama).
func _on_player_death_finished() -> void:
	var end_screen: Node = get_tree().get_first_node_in_group("end_screen")
	if end_screen and end_screen.has_method("show_lose"):
		end_screen.show_lose()
	else:
		GameManager.restore_full()
		SceneManager.reload_current()
