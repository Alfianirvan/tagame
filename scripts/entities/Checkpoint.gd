class_name Checkpoint
extends Area2D
## Checkpoint: bendera yang menyimpan titik hidup ulang. Menyentuhnya pertama kali mencatat posisi di
## GameManager dan autosave (CLAUDE.md Bagian 8, "Save"). Tidak memulihkan HP (itu tugas Bonfire).

signal activated

const FONT := preload("res://assets/fonts/Square-Black.ttf")

var is_active: bool = false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2   # player
	var shape: CollisionShape2D = CollisionShape2D.new()
	var rect: RectangleShape2D = RectangleShape2D.new()
	rect.size = Vector2(44, 44)
	shape.shape = rect
	shape.position = Vector2(0, -16)
	add_child(shape)
	body_entered.connect(_on_body_entered)
	# Sudah menjadi checkpoint aktif dari sesi sebelumnya?
	is_active = GameManager.checkpoint_scene == _scene_path() and GameManager.checkpoint_node == _node_path()
	queue_redraw()


func _scene_path() -> String:
	return get_tree().current_scene.scene_file_path


## Titik muncul Raka: sedikit di depan bendera.
func _spawn_point() -> Vector2:
	return global_position + Vector2(0, 14)


func get_respawn_point() -> Vector2:
	return _spawn_point()


## Path node ini dari root scene (dipakai menyimpan checkpoint tanpa bergantung pada koordinat).
func _node_path() -> String:
	return str(get_tree().current_scene.get_path_to(self))


func _on_body_entered(body: Node2D) -> void:
	if is_active or not body.is_in_group("player"):
		return
	is_active = true
	GameManager.set_checkpoint(_scene_path(), _spawn_point(), _node_path())
	SaveManager.save_game()
	AudioManager.play_sfx("menu_pilih")
	FloatingText.spawn(get_parent(), global_position + Vector2(0, -34), "Checkpoint tersimpan", Color(0.6, 1.0, 0.6))
	activated.emit()
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(-1, -30, 2, 30), Color(0.4, 0.27, 0.15))
	var flag: Color = Color(0.3, 0.85, 0.35) if is_active else Color(0.7, 0.7, 0.7)
	draw_colored_polygon(PackedVector2Array([Vector2(1, -30), Vector2(15, -25), Vector2(1, -19)]), flag)
	draw_rect(Rect2(-4, -2, 8, 3), Color(0.35, 0.3, 0.3))
