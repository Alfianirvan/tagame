extends Node2D
## Village (Desa Algoria): hub game. Mengatur musik, kamera, dan posisi awal Raka.
## Isi desa (tile, rumah, pohon, stasiun, marker NPC) dibuat oleh tools/gen_village.py dan boleh
## dirapikan manual di editor. Marker: NPCSpawns/<Nama> (metadata npc_id), PlayerStart.

## Ukuran peta desa (px), diisi generator (tools/gen_algoria.py).
@export var map_size: Vector2i = Vector2i(800, 640)

@onready var player: CharacterBody2D = $Objects/Player
@onready var player_start: Marker2D = $PlayerStart


func _ready() -> void:
	GameManager.set_current_chapter(0)
	AudioManager.play_music("desa_algoria")
	# Prolog Joko memakai musik cerita; setelah dialog selesai kembali ke musik desa
	DialogManager.dialog_started.connect(_on_dialog_started)
	DialogManager.dialog_ended.connect(_on_dialog_ended)
	player.set_camera_limits(Rect2i(Vector2i.ZERO, map_size))
	# Pulang dari Hutan Indeks lewat papan jalan: muncul di gerbang hutan (marker FromNext).
	# Selain itu muat dari checkpoint desa bila ada, terakhir di PlayerStart (depan rumah Raka).
	var back_from: int = GameManager.return_from_chapter
	GameManager.return_from_chapter = -1
	var spawn: Vector2 = Vector2.ZERO
	var from_next: Marker2D = get_node_or_null("FromNext") as Marker2D
	if back_from > 0 and from_next != null:
		spawn = from_next.global_position
	if spawn == Vector2.ZERO:
		spawn = GameManager.get_checkpoint_spawn(self)
	if spawn != Vector2.ZERO:
		player.global_position = spawn
	else:
		player.global_position = player_start.global_position


func _on_dialog_started(dialog_id: String) -> void:
	if dialog_id == "joko":
		AudioManager.play_music("cerita_prolog", 1.5)


func _on_dialog_ended(_dialog_id: String) -> void:
	AudioManager.play_music("desa_algoria", 1.5)
