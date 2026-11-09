extends CanvasLayer
## Pengaturan: slider volume musik & SFX (disimpan oleh AudioManager). Dipakai StartScreen dan PauseMenu.

signal closed

var _root: Control


func _ready() -> void:
	layer = 80
	process_mode = Node.PROCESS_MODE_ALWAYS
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_root.add_child(UIKit.dim(0.6))
	var v: VBoxContainer = UIKit.centered_panel(_root, Vector2(320, 190))
	v.add_child(UIKit.label("Pengaturan", 14, UIKit.TITLE, true))
	v.add_child(_slider_row("Musik", AudioManager.music_volume, AudioManager.set_music_volume))
	v.add_child(_slider_row("Efek suara (SFX)", AudioManager.sfx_volume, func(x: float) -> void:
		AudioManager.set_sfx_volume(x)
		AudioManager.play_sfx("menu_pindah")))
	var back: Button = UIKit.button("Kembali")
	back.pressed.connect(close)
	v.add_child(back)
	back.grab_focus.call_deferred()


func _slider_row(title: String, value: float, on_change: Callable) -> VBoxContainer:
	var row: VBoxContainer = VBoxContainer.new()
	var head: Label = UIKit.label("%s: %d%%" % [title, roundi(value * 100)], 11)
	row.add_child(head)
	var s: HSlider = HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.05
	s.value = value
	s.custom_minimum_size = Vector2(260, 18)
	s.value_changed.connect(func(x: float) -> void:
		head.text = "%s: %d%%" % [title, roundi(x * 100)]
		on_change.call(x))
	row.add_child(s)
	return row


func close() -> void:
	closed.emit()
	queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		close()
