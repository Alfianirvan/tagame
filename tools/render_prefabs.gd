extends Node
## Render tiap prefab di scenes/prefabs/ sendirian ke docs/prefabs/<nama>.png (butuh jendela/GPU, bukan --headless).
## Overlay: silang kuning = ORIGIN (titik kaki), kotak merah = tabrakan. Jalankan:
##   godot --path . --rendering-driver d3d12 res://tools/render_prefabs.tscn


class Overlay extends Node2D:
	var cw: float
	var ch: float
	var cdx: float = 0.0
	func _draw() -> void:
		draw_rect(Rect2(cdx - cw / 2.0, -ch, cw, ch), Color(1, 0.1, 0.1, 0.9), false, 1.0)
		draw_line(Vector2(-4, 0), Vector2(4, 0), Color(1, 1, 0), 1.0)
		draw_line(Vector2(0, -4), Vector2(0, 4), Color(1, 1, 0), 1.0)


func _ready() -> void:
	var f: FileAccess = FileAccess.open("res://scenes/prefabs/_prefabs.json", FileAccess.READ)
	var list: Array = JSON.parse_string(f.get_as_text())
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://docs/prefabs"))
	for e: Dictionary in list:
		var w: int = int(e["w"]) + 48
		var h: int = int(e["h"]) + 48
		var vp := SubViewport.new()
		vp.size = Vector2i(w, h)
		vp.transparent_bg = false
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		add_child(vp)
		var bg := ColorRect.new()
		bg.color = Color(0.34, 0.51, 0.24)
		bg.size = Vector2(w, h)
		vp.add_child(bg)
		var root := Node2D.new()
		root.position = Vector2(w / 2.0, h - 24.0)
		vp.add_child(root)
		var inst: Node = (load("res://scenes/prefabs/%s.tscn" % e["name"]) as PackedScene).instantiate()
		root.add_child(inst)
		var ov := Overlay.new()
		ov.cw = float(e["cw"])
		ov.ch = float(e["ch"])
		ov.cdx = float(e.get("cdx", 0))
		root.add_child(ov)
		for i in 3:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		vp.get_texture().get_image().save_png("res://docs/prefabs/%s.png" % e["name"])
		vp.queue_free()
	print("selesai ", list.size())
	get_tree().quit()
