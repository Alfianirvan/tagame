extends Node
## Render wilayah ke PNG (butuh jendela/GPU, bukan --headless).
## godot --path . --rendering-driver d3d12 res://tools/render_map.tscn -- <scene> <x> <y> <w> <h> <zoom> <out.png>
## Contoh seluruh map: res://scenes/world/Ch1_HutanIndeks.tscn 0 0 3248 2304 0.4 docs/layout/x.png


func _ready() -> void:
	var a: PackedStringArray = OS.get_cmdline_user_args()
	var scene_path: String = a[0]
	var rect := Rect2(float(a[1]), float(a[2]), float(a[3]), float(a[4]))
	var zoom: float = float(a[5])
	var out: String = a[6]
	GameManager.mark_met("opening_ch1")
	var vp := SubViewport.new()
	vp.size = Vector2i(int(rect.size.x * zoom), int(rect.size.y * zoom))
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var scn: Node = (load(scene_path) as PackedScene).instantiate()
	vp.add_child(scn)
	var cam := Camera2D.new()
	cam.zoom = Vector2(zoom, zoom)
	cam.position = rect.get_center()
	cam.limit_left = -100000
	cam.limit_top = -100000
	cam.limit_right = 100000
	cam.limit_bottom = 100000
	vp.add_child(cam)
	cam.make_current()
	for i in 12:
		await get_tree().process_frame
		cam.position = rect.get_center()
		cam.make_current()
	var img: Image = vp.get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path("res://" + out))
	print("simpan ", out, " ", img.get_size())
	get_tree().quit()
