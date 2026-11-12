class_name Interior
extends Node2D
## Scene interior kecil (rumah/kedai): musik, kamera mengikuti Raka dalam batas ruangan, Raka muncul di PlayerStart.
## Pintu keluar = node InteriorDoor (is_exit). Posisi kembali ke wilayah disimpan GameManager saat masuk.

@export var chapter: int = 1
@export var music_name: String = "desa_algoria"
@export var room_size: Vector2i = Vector2i(288, 192)

@onready var player: CharacterBody2D = $Objects/Player
@onready var player_start: Marker2D = $PlayerStart


func _ready() -> void:
	GameManager.set_current_chapter(chapter)
	AudioManager.play_music(music_name)
	# Ruangan lebih kecil dari layar: batas kamera dibuat seukuran layar dan dipusatkan pada ruangan (sisanya latar hitam).
	var view: Vector2i = Vector2i(640, 360)
	player.set_camera_limits(Rect2i(room_size / 2 - view / 2, view))
	player.global_position = player_start.global_position
	player.death_finished.connect(_on_player_death_finished)


func _on_player_death_finished() -> void:
	var end_screen: Node = get_tree().get_first_node_in_group("end_screen")
	if end_screen and end_screen.has_method("show_lose"):
		end_screen.show_lose()
	else:
		GameManager.restore_full()
		SceneManager.reload_current()
