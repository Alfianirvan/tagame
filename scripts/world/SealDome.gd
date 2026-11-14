class_name SealDome
extends Node2D
## Kubah segel ungu Desa 4 (Ch1). Tiga keadaan:
##  1) TERSEGEL (Golem belum kalah): kubah pekat + tabrakan, Raka tidak bisa masuk.
##  2) MELEMAH (Kristal Array sudah diambil): kubah berkedip tipis, tabrakan mati, Raka bisa ke altar.
##  3) PUDAR (flag `open_flag`, Kristal diletakkan di altar): kubah, tanah terkutuk, dan dekorasi kutukan memudar.
## Visual: isi elips ungu tembus pandang + garis tepi + perisai FX Ninja (Shield, di-modulate ungu) sepanjang tepi
## + lingkaran sihir (Circle) di tengah. Node yang memudar bersama kutukan: anak Objects/Decor berawalan `fade_prefix`.

const SHIELD := preload("res://assets/ninja/fx/Magic/Shield/SpriteSheetBlue.png")
const CIRCLE := preload("res://assets/ninja/fx/Magic/Circle/SpriteSheetWhite.png")
const SPARK := preload("res://assets/ninja/fx/Magic/Spark/SpriteSheet.png")
const PURPLE := Color(0.72, 0.42, 1.0)

@export var chapter: int = 1
@export var radius_x: float = 150.0
@export var radius_y: float = 112.0
@export var open_flag: String = "ch1_segel_pudar"
@export var fade_prefix: String = "D4Kutuk"
@export var locked_text: String = "Segel ungu menolakmu.\nKalahkan Golem Batu dulu."

var _visual: Node2D
var _fill: Polygon2D
var _rim: Line2D
var _body: StaticBody2D
var _state: int = -1
var _pulse: Tween


func _ready() -> void:
	add_to_group("seal_dome")
	z_index = 4
	_build()
	GameManager.crystal_collected.connect(func(_c: int) -> void: _refresh(true))
	GameManager.story_flag_set.connect(func(_f: String) -> void: _refresh(true))
	_refresh(false)


func _ellipse(rx: float, ry: float, n: int = 48) -> PackedVector2Array:
	var pts: PackedVector2Array = PackedVector2Array()
	for k in n:
		var a: float = TAU * k / n
		pts.append(Vector2(cos(a) * rx, sin(a) * ry))
	return pts


func _build() -> void:
	_visual = Node2D.new()
	add_child(_visual)
	_fill = Polygon2D.new()
	_fill.polygon = _ellipse(radius_x, radius_y)
	_fill.color = Color(PURPLE.r, PURPLE.g, PURPLE.b, 0.2)
	_visual.add_child(_fill)
	_rim = Line2D.new()
	var rim_pts: PackedVector2Array = _ellipse(radius_x, radius_y)
	rim_pts.append(rim_pts[0])
	_rim.points = rim_pts
	_rim.width = 2.0
	_rim.default_color = Color(0.85, 0.6, 1.0, 0.85)
	_visual.add_child(_rim)
	# perisai FX di sepanjang tepi (frame 24x26)
	var n: int = int(TAU * (radius_x + radius_y) * 0.5 / 34.0)
	for k in n:
		var a: float = TAU * k / n
		var s: AnimatedSprite2D = FxUtil.anim(SHIELD, 24, 26, 8.0)
		s.position = Vector2(cos(a) * radius_x, sin(a) * radius_y)
		s.modulate = Color(PURPLE.r, PURPLE.g, PURPLE.b, 0.8)
		s.frame = k % 6
		_visual.add_child(s)
	var c: AnimatedSprite2D = FxUtil.anim(CIRCLE, 32, 32, 6.0)
	c.modulate = Color(0.85, 0.55, 1.0, 0.9)
	c.position = Vector2(0, -26)
	_visual.add_child(c)
	# tabrakan: elips padat (Raka di luar tidak bisa masuk)
	_body = StaticBody2D.new()
	_body.collision_layer = 1
	_body.collision_mask = 0
	var poly: CollisionPolygon2D = CollisionPolygon2D.new()
	poly.polygon = _ellipse(radius_x - 6.0, radius_y - 6.0, 32)
	_body.add_child(poly)
	add_child(_body)
	# teks peringatan saat mendekat selama masih tersegel
	var a2: Area2D = Area2D.new()
	a2.collision_layer = 0
	a2.collision_mask = 2
	var cp: CollisionPolygon2D = CollisionPolygon2D.new()
	cp.polygon = _ellipse(radius_x + 26.0, radius_y + 26.0, 32)
	a2.add_child(cp)
	add_child(a2)
	var last: Array[float] = [-100.0]
	a2.body_entered.connect(func(b: Node2D) -> void:
		if _state != 0 or not b.is_in_group("player"):
			return
		var now: float = Time.get_ticks_msec() / 1000.0
		if now - last[0] < 4.0:
			return
		last[0] = now
		FloatingText.spawn(get_parent(), b.global_position + Vector2(0, -44), locked_text, Color(0.9, 0.7, 1), 2.6))


## 0 = tersegel, 1 = melemah, 2 = pudar.
func _target_state() -> int:
	if GameManager.has_story_flag(open_flag):
		return 2
	if GameManager.has_crystal(chapter):
		return 1
	return 0


func _refresh(animate: bool) -> void:
	var st: int = _target_state()
	if st == _state:
		return
	_state = st
	if _pulse:
		_pulse.kill()
	_body.process_mode = Node.PROCESS_MODE_INHERIT if st == 0 else Node.PROCESS_MODE_DISABLED
	_body.collision_layer = 1 if st == 0 else 0
	match st:
		0:
			_visual.modulate.a = 1.0
		1:
			_visual.modulate.a = 0.6
			_pulse = create_tween().set_loops()
			_pulse.tween_property(_visual, "modulate:a", 0.25, 0.9)
			_pulse.tween_property(_visual, "modulate:a", 0.6, 0.9)
		2:
			_fade_curse(animate)


func _fade_curse(animate: bool) -> void:
	var targets: Array[CanvasItem] = [_visual]
	for parent_name: String in ["Objects", "Decor"]:
		var p: Node = get_parent().get_node_or_null(parent_name)
		if p == null:
			continue
		for n in p.get_children():
			if n is CanvasItem and String(n.name).begins_with(fade_prefix):
				targets.append(n as CanvasItem)
	if not animate:
		for t in targets:
			_disable(t)
		return
	for k in 6:
		var a: float = TAU * k / 6.0
		FxUtil.burst(get_parent(), global_position + Vector2(cos(a) * radius_x * 0.6, sin(a) * radius_y * 0.6 - 20), SPARK, 30, 35, 12.0, Color(0.9, 0.7, 1), 6)
	var tw: Tween = create_tween().set_parallel(true)
	for t in targets:
		tw.tween_property(t, "modulate:a", 0.0, 2.5)
	tw.chain().tween_callback(func() -> void:
		for t in targets:
			_disable(t))


func _disable(t: CanvasItem) -> void:
	t.visible = false
	if t is CollisionObject2D:
		(t as CollisionObject2D).collision_layer = 0
