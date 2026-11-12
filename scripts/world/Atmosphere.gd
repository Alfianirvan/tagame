extends Node2D
## Suasana hutan: daun jatuh (Leaf.png) + berkas cahaya (Raylight.png, blend add, alpha rendah) di sekitar kamera.
## Dipasang sebagai anak scene wilayah; mengikuti Raka supaya hemat (tidak ada ribuan partikel di seluruh peta).

const LEAF := preload("res://assets/ninja/fx/Particle/Leaf.png")
const RAY := preload("res://assets/ninja/fx/Environment/Raylight.png")

@export var leaves: bool = true
@export var rays: bool = true
@export var ray_count: int = 5
@export var ray_alpha: float = 0.16

var _leaf_fx: CPUParticles2D
var _ray_nodes: Array[Sprite2D] = []


func _ready() -> void:
	z_index = 20
	if leaves:
		_leaf_fx = CPUParticles2D.new()
		# daun = 6 frame 12x7 pada strip; pakai atlas frame pertama
		var at := AtlasTexture.new()
		at.atlas = LEAF
		at.region = Rect2(0, 0, 12, 7)
		_leaf_fx.texture = at
		_leaf_fx.amount = 14
		_leaf_fx.lifetime = 9.0
		_leaf_fx.preprocess = 9.0
		_leaf_fx.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		_leaf_fx.emission_rect_extents = Vector2(380, 6)
		_leaf_fx.direction = Vector2(0.35, 1)
		_leaf_fx.spread = 18.0
		_leaf_fx.gravity = Vector2(6, 10)
		_leaf_fx.initial_velocity_min = 10.0
		_leaf_fx.initial_velocity_max = 22.0
		_leaf_fx.angular_velocity_min = -80.0
		_leaf_fx.angular_velocity_max = 80.0
		_leaf_fx.scale_amount_min = 0.9
		_leaf_fx.scale_amount_max = 1.5
		add_child(_leaf_fx)
	if rays:
		var rng := RandomNumberGenerator.new()
		rng.seed = 11
		for i in ray_count:
			var s := Sprite2D.new()
			s.texture = RAY
			s.region_enabled = true
			s.region_rect = Rect2(72 * (i % 3), 0, 72, 102)
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			s.material = mat
			s.modulate = Color(1, 0.95, 0.7, ray_alpha)
			s.scale = Vector2.ONE * rng.randf_range(1.6, 2.4)
			s.set_meta("ox", rng.randf_range(-300, 300))
			s.set_meta("oy", rng.randf_range(-170, 40))
			add_child(s)
			_ray_nodes.append(s)
			var tw := create_tween().set_loops()
			tw.tween_property(s, "modulate:a", ray_alpha * 0.4, rng.randf_range(3.0, 5.0)).set_trans(Tween.TRANS_SINE)
			tw.tween_property(s, "modulate:a", ray_alpha, rng.randf_range(3.0, 5.0)).set_trans(Tween.TRANS_SINE)


func _process(_delta: float) -> void:
	var cam: Camera2D = get_viewport().get_camera_2d()
	if cam == null:
		return
	var c: Vector2 = cam.get_screen_center_position()
	if _leaf_fx:
		_leaf_fx.global_position = c + Vector2(0, -200)
	for s in _ray_nodes:
		s.global_position = c + Vector2(float(s.get_meta("ox")), float(s.get_meta("oy")))
