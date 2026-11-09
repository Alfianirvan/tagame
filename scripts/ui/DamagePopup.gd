class_name DamagePopup
extends Label
## Angka damage yang melayang naik lalu hilang. Dibuat lewat DamagePopup.spawn().


## Memunculkan angka di posisi dunia tertentu sebagai anak dari parent.
static func spawn(parent: Node, pos: Vector2, amount: int, color: Color = Color(1, 0.9, 0.3)) -> void:
	var label: DamagePopup = DamagePopup.new()
	label.text = str(amount)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 3)
	label.add_theme_font_size_override("font_size", 10)
	label.z_index = 100
	parent.add_child(label)
	label.global_position = pos + Vector2(-8, -6)


func _ready() -> void:
	var tw: Tween = create_tween().set_parallel(true)
	tw.tween_property(self, "position:y", position.y - 18.0, 0.6)
	tw.tween_property(self, "modulate:a", 0.0, 0.6).set_delay(0.25)
	tw.chain().tween_callback(queue_free)
