extends Node2D
## Bar HP kecil di atas musuh. Baru terlihat setelah musuh terkena serangan.

const WIDTH := 20.0
const HEIGHT := 3.0

var ratio: float = 1.0


## Dipanggil Enemy saat HP berubah.
func set_ratio(value: float) -> void:
	ratio = clampf(value, 0.0, 1.0)
	visible = ratio < 1.0 and ratio > 0.0
	queue_redraw()


func _draw() -> void:
	var origin: Vector2 = Vector2(-WIDTH / 2.0, 0)
	draw_rect(Rect2(origin - Vector2(1, 1), Vector2(WIDTH + 2, HEIGHT + 2)), Color(0, 0, 0, 0.8))
	draw_rect(Rect2(origin, Vector2(WIDTH * ratio, HEIGHT)), Color(0.85, 0.2, 0.2))
