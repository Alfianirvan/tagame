extends CanvasLayer
## SceneManager: pindah scene dengan transisi fade (ColorRect hitam + Tween).

signal scene_change_started(path: String)
signal scene_changed(path: String)

var current_path: String = ""
var is_changing: bool = false

var _fade: ColorRect


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	_fade = ColorRect.new()
	_fade.color = Color.BLACK
	_fade.modulate.a = 0.0
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_fade)
	var scene: Node = get_tree().current_scene
	if scene:
		current_path = scene.scene_file_path


## Pindah ke scene lain: fade out → ganti scene → fade in.
func change_scene(path: String, duration: float = 0.4) -> void:
	if is_changing:
		return
	if not ResourceLoader.exists(path):
		push_error("Scene tidak ditemukan: %s" % path)
		return
	is_changing = true
	scene_change_started.emit(path)
	_fade.mouse_filter = Control.MOUSE_FILTER_STOP  # blokir klik selama transisi
	await _fade_to(1.0, duration)
	get_tree().paused = false
	var err: Error = get_tree().change_scene_to_file(path)
	if err != OK:
		push_error("Gagal pindah scene: %s" % error_string(err))
	else:
		current_path = path
		await get_tree().process_frame
		await get_tree().process_frame
	await _fade_to(0.0, duration)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	is_changing = false
	if err == OK:
		scene_changed.emit(path)


func reload_current(duration: float = 0.4) -> void:
	change_scene(current_path, duration)


func _fade_to(alpha: float, duration: float) -> void:
	var tween: Tween = create_tween()
	tween.tween_property(_fade, "modulate:a", alpha, duration)
	await tween.finished
