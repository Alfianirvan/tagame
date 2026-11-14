class_name TorchSeal
extends Node2D
## Puzzle segel gerbang arena Golem (akhir Quest Tengah Ch1). Lima obor berdiri ACAK di depan gerbang, tiap obor
## punya papan indeks [0]..[4]. Petunjuk penyintas yang disusun Arman: array 5 obor berindeks 0..4, nyalakan
## berurutan dari indeks terkecil. Salah urutan -> semua padam lagi. Benar -> Quest Tengah selesai (quest_stage 2)
## sehingga cincin awan arena membuka. Baru bisa dipakai setelah semua langkah Quest Tengah beres.

const FLAME := preload("res://assets/ninja/fx/Flam/Flam.png")
const CIRCLE := preload("res://assets/ninja/fx/Magic/Circle/SpriteSheetWhite.png")
const SPARK := preload("res://assets/ninja/fx/Magic/Spark/SpriteSheet.png")

@export var chapter: int = 1
@export var quest_id: String = "ch1_tengah"
## Posisi lokal tiap obor dan indeks yang tertulis di papannya (urutan posisi sengaja diacak).
@export var torch_offsets: PackedVector2Array = PackedVector2Array([Vector2(-72, 6), Vector2(-36, -14), Vector2(0, 8), Vector2(36, -14), Vector2(72, 6)])
@export var torch_indices: PackedInt32Array = PackedInt32Array([3, 0, 4, 1, 2])

var _flames: Array[AnimatedSprite2D] = []
var _lit: Array[bool] = []
var _next: int = 0
var _near: int = -1
var _hint: Label


func _ready() -> void:
	add_to_group("torch_seal")
	for i in torch_offsets.size():
		_build_torch(i)
	_hint = FxUtil.small_label("")
	_hint.size = Vector2(200, 12)
	_hint.visible = false
	add_child(_hint)
	GameManager.quest_stage_changed.connect(func(_c: int, _s: int) -> void: _refresh_solved())
	_refresh_solved()


func _build_torch(i: int) -> void:
	var p: Vector2 = torch_offsets[i]
	# tiang batu (tabrakan kecil di kaki)
	var body: StaticBody2D = StaticBody2D.new()
	body.position = p
	body.collision_layer = 1
	body.collision_mask = 0
	var cs: CollisionShape2D = CollisionShape2D.new()
	var r: RectangleShape2D = RectangleShape2D.new()
	r.size = Vector2(10, 6)
	cs.shape = r
	cs.position = Vector2(0, -3)
	body.add_child(cs)
	add_child(body)
	var flame: AnimatedSprite2D = FxUtil.anim(FLAME, 20, 30, 10.0, true, true)
	flame.position = p + Vector2(0, -16)
	flame.visible = false
	add_child(flame)
	_flames.append(flame)
	_lit.append(false)
	var plate: Label = FxUtil.small_label("[%d]" % torch_indices[i], 8, Color(0.85, 0.95, 1))
	plate.size = Vector2(30, 12)
	plate.position = p + Vector2(-15, 2)
	add_child(plate)
	# area interaksi per obor
	var a: Area2D = Area2D.new()
	a.position = p
	a.collision_layer = 0
	a.collision_mask = 2
	var acs: CollisionShape2D = CollisionShape2D.new()
	var c: CircleShape2D = CircleShape2D.new()
	c.radius = 18.0
	acs.shape = c
	a.add_child(acs)
	add_child(a)
	a.body_entered.connect(func(b: Node2D) -> void:
		if b.is_in_group("player"):
			_near = i
			_update_hint())
	a.body_exited.connect(func(b: Node2D) -> void:
		if b.is_in_group("player") and _near == i:
			_near = -1
			_update_hint())


func _solved() -> bool:
	return GameManager.get_quest_stage(chapter) >= 2


func _refresh_solved() -> void:
	if _solved():
		for k in _flames.size():
			_set_lit(k, true)
	queue_redraw()
	_update_hint()


func _block_reason() -> String:
	if _solved():
		return ""
	if not QuestManager.is_ready(quest_id):
		return "Obor segel. Arman belum menyusun petunjuk."
	return ""


func _update_hint() -> void:
	if _near < 0 or _solved():
		_hint.visible = false
		return
	var reason: String = _block_reason()
	_hint.text = reason if reason != "" else ("E: Nyalakan obor [%d]" % torch_indices[_near])
	_hint.position = torch_offsets[_near] + Vector2(-100, -58)
	_hint.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if _near < 0 or _solved() or not event.is_action_pressed("interact") or DialogManager.is_active:
		return
	get_viewport().set_input_as_handled()
	if _block_reason() != "" or _lit[_near]:
		return
	var idx: int = torch_indices[_near]
	if idx == _next:
		_set_lit(_near, true)
		AudioManager.play_sfx("bola_api")
		_next += 1
		if _next >= torch_offsets.size():
			_finish()
	else:
		# salah urutan: semua padam, ulangi dari indeks 0
		AudioManager.play_sfx("kuis_salah")
		for k in _flames.size():
			_set_lit(k, false)
		_next = 0
		FloatingText.spawn(get_parent(), global_position + Vector2(0, -60),
			"Apinya padam! Mulai lagi dari indeks 0, berurutan.", Color(1, 0.6, 0.5), 2.6)
	_update_hint()


func _set_lit(k: int, on: bool) -> void:
	_lit[k] = on
	_flames[k].visible = on
	queue_redraw()


func _finish() -> void:
	FxUtil.burst(get_parent(), global_position + Vector2(0, -20), CIRCLE, 32, 32, 10.0, Color(0.7, 0.9, 1), 6)
	for k in _flames.size():
		FxUtil.burst(get_parent(), global_position + torch_offsets[k] + Vector2(0, -24), SPARK, 30, 35, 16.0, Color(1, 0.9, 0.6), 6)
	AudioManager.play_sfx("jingle_wilayah_terbuka")
	var lines: Array[String] = QuestManager.complete_quest(chapter, 2)
	var text: String = "Segel gerbang arena terbuka!"
	if not lines.is_empty():
		text += "\n" + ", ".join(lines)
	FloatingText.spawn(get_parent(), global_position + Vector2(0, -70), text, Color(0.7, 1, 0.7), 3.2)


func _draw() -> void:
	# tiang obor: batu kelabu + mangkuk besi
	for k in torch_offsets.size():
		var p: Vector2 = torch_offsets[k]
		draw_rect(Rect2(p + Vector2(-4, -14), Vector2(8, 14)), Color(0.45, 0.45, 0.5))
		draw_rect(Rect2(p + Vector2(-4, -14), Vector2(8, 14)), Color(0.2, 0.2, 0.24), false, 1.0)
		draw_rect(Rect2(p + Vector2(-6, -18), Vector2(12, 4)), Color(0.3, 0.27, 0.25))
		if not _lit.is_empty() and not _lit[k]:
			draw_rect(Rect2(p + Vector2(-3, -20), Vector2(6, 2)), Color(0.15, 0.12, 0.1))
