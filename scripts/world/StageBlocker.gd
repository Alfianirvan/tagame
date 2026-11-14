class_name StageBlocker
extends Node2D
## Penghalang dari tumpukan objek (anak = instance prefab StaticBody2D, mis. peti/batu longsoran) yang hilang saat syarat
## terpenuhi: "stage" = quest_stage chapter >= required_stage, "crystal" = Kristal chapter sudah didapat.
## Saat terbuka: anak-anak memudar + debu, tabrakan dimatikan. Dipakai Ch2 (peti menutup terowongan tambang,
## longsoran batu = jalan pintas kembali ke desa setelah boss).

const DUST := preload("res://assets/ninja/fx/Smoke/Smoke/SpriteSheet.png")

@export_enum("stage", "crystal") var mode: String = "stage"
@export var chapter: int = 2
@export var required_stage: int = 2
@export var locked_text: String = ""
## Ukuran area peringatan (teks muncul saat Raka mendekat dan masih tertutup).
@export var hint_size: Vector2 = Vector2(140, 120)

var is_open: bool = false


func _ready() -> void:
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _refresh(true))
	GameManager.crystal_collected.connect(func(_c: int) -> void: _refresh(true))
	_refresh(false)
	if locked_text != "" and not is_open:
		_make_hint_area()


func _condition() -> bool:
	if mode == "crystal":
		return GameManager.has_crystal(chapter)
	return GameManager.get_quest_stage(chapter) >= required_stage


func _refresh(animate: bool) -> void:
	if is_open or not _condition():
		return
	is_open = true
	for c in get_children():
		if c is CollisionObject2D:
			(c as CollisionObject2D).set_deferred("collision_layer", 0)
		if c is TileMapLayer:   # tile penghalang tak terlihat
			(c as TileMapLayer).set_deferred("collision_enabled", false)
			continue
		if not (c is CanvasItem):
			continue
		if animate:
			FxUtil.burst(get_parent(), (c as Node2D).global_position + Vector2(0, -10), DUST, 32, 32, 12.0, Color(0.9, 0.8, 0.65))
			var tw: Tween = create_tween()
			tw.tween_property(c, "modulate:a", 0.0, 1.2)
			tw.tween_callback((c as CanvasItem).hide)
		else:
			(c as CanvasItem).hide()


func _make_hint_area() -> void:
	var a: Area2D = Area2D.new()
	a.collision_layer = 0
	a.collision_mask = 2
	var shape: CollisionShape2D = CollisionShape2D.new()
	var rs: RectangleShape2D = RectangleShape2D.new()
	rs.size = hint_size
	shape.shape = rs
	a.add_child(shape)
	add_child(a)
	var last: float = -100.0
	a.body_entered.connect(func(b: Node2D) -> void:
		if is_open or not b.is_in_group("player"):
			return
		var now: float = Time.get_ticks_msec() / 1000.0
		if now - last < 4.0:
			return
		last = now
		FloatingText.spawn(get_parent(), b.global_position + Vector2(0, -40), locked_text, Color(1, 0.8, 0.6), 2.4))
