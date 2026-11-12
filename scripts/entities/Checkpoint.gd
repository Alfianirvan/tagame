class_name Checkpoint
extends Area2D
## Checkpoint = BENDERA. Belum aktif: bendera abu-abu diam. Disentuh Raka: berkibar (loop), berubah warna,
## SFX + teks "Progres tersimpan", autosave, dan jadi titik hidup ulang. Status aktif ikut tersimpan
## (GameManager.active_flags). Tidak memulihkan HP (itu tugas Bonfire).

signal activated

const FLAG_DIR := "res://assets/craftpix/fields/animated/1 Flag/"
const FRAME_W := 32
const FRAME_H := 64

var is_active: bool = false
var _sprite: AnimatedSprite2D


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
	_sprite = AnimatedSprite2D.new()
	_sprite.position = Vector2(0, 0)
	_sprite.offset = Vector2(0, -FRAME_H / 2.0)      # tiang menapak di titik kaki
	_sprite.sprite_frames = _make_frames()
	add_child(_sprite)
	# Sudah aktif dari sesi sebelumnya (status bendera ikut tersimpan) atau titik hidup ulang saat ini?
	is_active = GameManager.is_flag_active(_flag_key()) \
		or (GameManager.checkpoint_scene == _scene_path() and GameManager.checkpoint_node == _node_path())
	_refresh()


## Bendera biru berkibar (1.png, 6 frame 32x64) saat aktif; belum aktif = bendera terlipat (5.png, frame pertama, diam, kelabu).
func _make_frames() -> SpriteFrames:
	var sf: SpriteFrames = SpriteFrames.new()
	sf.remove_animation("default")
	for anim: String in ["mati", "aktif"]:
		sf.add_animation(anim)
		var tex: Texture2D = load(FLAG_DIR + ("5.png" if anim == "mati" else "1.png"))
		var count: int = 1 if anim == "mati" else 6
		for i in count:
			var at: AtlasTexture = AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(i * FRAME_W, 0, FRAME_W, FRAME_H)
			sf.add_frame(anim, at)
		sf.set_animation_loop(anim, true)
		sf.set_animation_speed(anim, 7.0)
	return sf


func _refresh() -> void:
	_sprite.modulate = Color.WHITE if is_active else Color(0.72, 0.72, 0.72)
	_sprite.play("aktif" if is_active else "mati")


func _scene_path() -> String:
	return get_tree().current_scene.scene_file_path


## Path node ini dari root scene (dipakai menyimpan checkpoint tanpa bergantung pada koordinat).
func _node_path() -> String:
	return str(get_tree().current_scene.get_path_to(self))


func _flag_key() -> String:
	return _scene_path() + ":" + _node_path()


## Titik muncul Raka: sedikit di depan bendera.
func _spawn_point() -> Vector2:
	return global_position + Vector2(0, 14)


func get_respawn_point() -> Vector2:
	return _spawn_point()


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	# Bendera yang sudah aktif tetap boleh jadi titik hidup ulang terbaru saat disentuh lagi (tanpa teks).
	var first_time: bool = not is_active
	is_active = true
	GameManager.mark_flag_active(_flag_key())
	GameManager.set_checkpoint(_scene_path(), _spawn_point(), _node_path())
	if not first_time:
		return
	SaveManager.save_game()
	AudioManager.play_sfx("menu_pilih")
	FloatingText.spawn(get_parent(), global_position + Vector2(0, -44), "Progres tersimpan", Color(0.6, 1.0, 0.6))
	activated.emit()
	_refresh()
