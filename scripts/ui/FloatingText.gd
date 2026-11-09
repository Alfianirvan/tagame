class_name FloatingText
extends Label
## Teks melayang singkat di dunia (pesan "Checkpoint tersimpan", "Gerbang terkunci", dsb). Hilang sendiri.

const FONT := preload("res://assets/fonts/Square-Black.ttf")


static func spawn(parent: Node, pos: Vector2, text: String, color: Color = Color(1, 1, 0.8), life: float = 1.6) -> void:
	var label: FloatingText = FloatingText.new()
	label.text = text
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", 8)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 3)
	label.z_index = 100
	parent.add_child(label)
	label.reset_size()
	label.global_position = pos - Vector2(label.size.x / 2.0, 0.0)
	var tw: Tween = label.create_tween().set_parallel(true)
	tw.tween_property(label, "global_position:y", label.global_position.y - 14.0, life)
	tw.tween_property(label, "modulate:a", 0.0, life * 0.5).set_delay(life * 0.5)
	tw.chain().tween_callback(label.queue_free)
