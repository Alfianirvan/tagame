extends Node2D
## Village (Desa Algoria): hub game. Mengatur musik, kamera, dan posisi awal Raka.
## Isi desa (tile, rumah, pohon, stasiun, marker NPC) dibuat oleh tools/gen_village.py dan boleh
## dirapikan manual di editor. Marker: NPCSpawns/<Nama> (metadata npc_id), PlayerStart.

const MAP_SIZE := Vector2i(800, 640)

@onready var player: CharacterBody2D = $Objects/Player
@onready var player_start: Marker2D = $PlayerStart


func _ready() -> void:
	GameManager.set_current_chapter(0)
	AudioManager.play_music("desa_algoria")
	# Prolog Joko memakai musik cerita; setelah dialog selesai kembali ke musik desa
	DialogManager.dialog_started.connect(_on_dialog_started)
	DialogManager.dialog_ended.connect(_on_dialog_ended)
	player.set_camera_limits(Rect2i(Vector2i.ZERO, MAP_SIZE))
	# Muat dari checkpoint desa bila ada, selain itu mulai di PlayerStart
	var spawn: Vector2 = GameManager.get_checkpoint_spawn(self)
	if spawn != Vector2.ZERO:
		player.global_position = spawn
	else:
		player.global_position = player_start.global_position


func _on_dialog_started(dialog_id: String) -> void:
	if dialog_id == "joko":
		AudioManager.play_music("cerita_prolog", 1.5)


func _on_dialog_ended(_dialog_id: String) -> void:
	AudioManager.play_music("desa_algoria", 1.5)
