extends Node
## Mengubah warna (modulate) sekumpulan node saat flag cerita disetel, misalnya Desa 2 yang tercemar ungu
## kembali normal setelah sumurnya dimurnikan. Node dicari di scene wilayah berdasarkan nama di `target_names`.

@export var flag: String = ""
@export var target_names: PackedStringArray = PackedStringArray()
@export var to_color: Color = Color.WHITE
@export var duration: float = 2.5


func _ready() -> void:
	GameManager.story_flag_set.connect(func(f: String) -> void:
		if f == flag:
			_apply(true))
	if GameManager.has_story_flag(flag):
		_apply.call_deferred(false)


func _apply(animate: bool) -> void:
	var scene: Node = get_parent()
	for nm in target_names:
		var n: Node = scene.find_child(nm, true, false)
		if not (n is CanvasItem):
			continue
		var ci: CanvasItem = n as CanvasItem
		if animate:
			create_tween().tween_property(ci, "modulate", to_color, duration)
		else:
			ci.modulate = to_color
