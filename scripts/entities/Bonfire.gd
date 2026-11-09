class_name Bonfire
extends StaticBody2D
## Bonfire: tekan E di dekatnya untuk beristirahat: HP & Stamina pulih penuh, titik hidup ulang disimpan,
## dan game tersimpan. E membuka pilihan: Istirahat / Simpan & Keluar (ke Menu Utama) / Batal.

signal rested

const BASE_SHEET := preload("res://assets/props/stations/Bonfire/Bonfire_01-Sheet.png")
const FIRE_SHEET := preload("res://assets/props/stations/Bonfire/Fire_01-Sheet.png")
const FONT := preload("res://assets/fonts/Square-Black.ttf")

var _player_in_range: bool = false
var _hint: Label
var _menu: CanvasLayer
var _was_enabled: bool = true


func _ready() -> void:
	collision_layer = 1
	collision_mask = 0
	_add_sprite(BASE_SHEET, 32, 32, Vector2(0, -16), 6.0)
	_add_sprite(FIRE_SHEET, 32, 48, Vector2(0, -26), 8.0)
	var body: CollisionShape2D = CollisionShape2D.new()
	var rect: RectangleShape2D = RectangleShape2D.new()
	rect.size = Vector2(22, 10)
	body.shape = rect
	body.position = Vector2(0, -5)
	add_child(body)
	var area: Area2D = Area2D.new()
	area.collision_layer = 0
	area.collision_mask = 2
	area.position = Vector2(0, -10)
	var shape: CollisionShape2D = CollisionShape2D.new()
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = 36.0
	shape.shape = circle
	area.add_child(shape)
	add_child(area)
	area.body_entered.connect(func(b: Node2D) -> void: _set_range(b, true))
	area.body_exited.connect(func(b: Node2D) -> void: _set_range(b, false))
	_hint = Label.new()
	_hint.text = "E: Istirahat"
	_hint.add_theme_font_override("font", FONT)
	_hint.add_theme_font_size_override("font_size", 8)
	_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_hint.add_theme_constant_override("outline_size", 3)
	_hint.position = Vector2(-26, -56)
	_hint.visible = false
	add_child(_hint)


func _add_sprite(sheet: Texture2D, fw: int, fh: int, pos: Vector2, fps: float) -> void:
	var frames: SpriteFrames = SpriteFrames.new()
	frames.set_animation_speed("default", fps)
	for i in sheet.get_width() / fw:
		var atlas: AtlasTexture = AtlasTexture.new()
		atlas.atlas = sheet
		atlas.region = Rect2(i * fw, 0, fw, fh)
		frames.add_frame("default", atlas)
	var sprite: AnimatedSprite2D = AnimatedSprite2D.new()
	sprite.sprite_frames = frames
	sprite.position = pos
	sprite.autoplay = "default"
	add_child(sprite)


func _set_range(body: Node2D, inside: bool) -> void:
	if body.is_in_group("player"):
		_player_in_range = inside
		_hint.visible = inside


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or QuestManager.quiz_active:
		return
	if event.is_action_pressed("interact") and _menu == null and not get_tree().paused:
		get_viewport().set_input_as_handled()
		_open_menu()


## Titik muncul Raka bila hidup ulang di bonfire ini.
func get_respawn_point() -> Vector2:
	return global_position + Vector2(0, 24)


## Memulihkan HP/Stamina, menyimpan checkpoint, lalu autosave.
func rest() -> void:
	GameManager.restore_full()
	GameManager.set_checkpoint(get_tree().current_scene.scene_file_path, get_respawn_point(), str(get_tree().current_scene.get_path_to(self)))
	SaveManager.save_game()
	AudioManager.play_sfx("heal_potion")
	FloatingText.spawn(get_parent(), global_position + Vector2(0, -60), "HP & Stamina pulih. Tersimpan.", Color(1.0, 0.9, 0.5))
	rested.emit()


## Pilihan saat berdiri di dekat api unggun.
func _open_menu() -> void:
	var player: Node = get_tree().get_first_node_in_group("player")
	_was_enabled = player == null or bool(player.get("controls_enabled"))
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(false)
	get_tree().paused = true
	_menu = CanvasLayer.new()
	_menu.layer = 72
	_menu.process_mode = Node.PROCESS_MODE_ALWAYS
	var root: Control = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_menu.add_child(root)
	root.add_child(UIKit.dim(0.45))
	var v: VBoxContainer = UIKit.centered_panel(root, Vector2(220, 150))
	v.add_child(UIKit.label("Api Unggun", 13, UIKit.TITLE, true))
	var rest_btn: Button = UIKit.button("Istirahat (pulih + simpan)", Vector2(190, 24))
	rest_btn.pressed.connect(func() -> void:
		_close_menu()
		rest())
	var quit_btn: Button = UIKit.button("Simpan & Keluar ke Menu", Vector2(190, 24))
	quit_btn.pressed.connect(func() -> void:
		_close_menu()
		rest()
		SceneManager.change_scene("res://scenes/ui/StartScreen.tscn"))
	var cancel_btn: Button = UIKit.button("Batal", Vector2(190, 24))
	cancel_btn.pressed.connect(_close_menu)
	for b: Button in [rest_btn, quit_btn, cancel_btn]:
		v.add_child(b)
	get_tree().current_scene.add_child(_menu)
	rest_btn.grab_focus.call_deferred()


func _close_menu() -> void:
	if _menu:
		_menu.queue_free()
		_menu = null
	get_tree().paused = false
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(_was_enabled)
