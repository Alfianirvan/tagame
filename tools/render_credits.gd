extends Node
## Tangkapan layar credit scene (butuh jendela/GPU): kartu judul & baris cerita opening_ch3, credit bergulir ending.
## godot --path . --rendering-driver d3d12 res://tools/render_credits.tscn
const OC := preload("res://scripts/ui/OpeningCredits.gd")   # dipakai lewat preload (tidak bergantung cache class_name editor)
const EC := preload("res://scripts/ui/EndCredits.gd")


func _snap(path: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("res://" + path))
	print("simpan ", path)


func _ready() -> void:
	var oc: OC = OC.new()
	oc.credits_key = "opening_ch3"
	add_child(oc)
	await get_tree().create_timer(1.6).timeout
	await _snap("docs/layout/Credit_judul_ch3.png")
	await get_tree().create_timer(4.6).timeout
	await _snap("docs/layout/Credit_cerita_ch3.png")
	oc._finish()
	await get_tree().create_timer(1.0).timeout
	var ec: EC = EC.new()
	add_child(ec)
	await get_tree().create_timer(5.2).timeout
	await _snap("docs/layout/Credit_epilog.png")
	for c in ec.get_children():
		if c is OC:
			c._finish()
	await get_tree().create_timer(9.0).timeout
	await _snap("docs/layout/Credit_bergulir.png")
	get_tree().quit()
