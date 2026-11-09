extends StaticBody2D
## NPC: berdiri idle, menghadap Raka saat diajak bicara, ikon "!" bila punya quest baru.
## Tekan E saat Raka berada di area interaksi -> DialogManager memulai dialog.
## Dialog dibaca dari res://data/dialogs/<dialog_id>.json (default = npc_id).

signal interacted(npc_id: String)
signal dialog_finished(npc_id: String)

const NpcSprites := preload("res://scripts/entities/NpcSprites.gd")
const ICON_Y := -80.0   # di atas kepala, di atas label [E]

@export var npc_id: String = ""
@export var dialog_id: String = ""                 # kosong = pakai npc_id
@export_enum("down", "side", "up") var default_facing: String = "down"
@export var has_new_quest: bool = false: set = set_has_new_quest
## NPC pedagang: setelah dialog selesai, Kantong Pedagang (tab Toko) langsung terbuka.
@export var opens_shop: bool = false

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var interact_area: Area2D = $InteractArea
@onready var hint: Label = $Hint

var _player_in_range: bool = false
var _icon_tween: Tween
var quest_icon: Label        # tanda "!" (quest baru) atau "?" (siap diserahkan), dibuat di kode


func _ready() -> void:
	add_to_group("npc")
	sprite.sprite_frames = NpcSprites.build(npc_id.capitalize())
	sprite.offset = Vector2(0, -16)  # kaki di y=48 dari frame 64x64
	_face(default_facing, false)
	interact_area.body_entered.connect(_on_body_entered)
	interact_area.body_exited.connect(_on_body_exited)
	DialogManager.dialog_started.connect(func(_id: String) -> void: _update_hint())
	DialogManager.dialog_ended.connect(_on_dialog_ended)
	hint.visible = false
	_build_quest_icon()
	set_has_new_quest(has_new_quest)
	# Ikon "!" mengikuti status quest bila NPC ini punya quest di quests.json
	QuestManager.quests_changed.connect(_refresh_quest_icon)
	_refresh_quest_icon()


func _build_quest_icon() -> void:
	quest_icon = Label.new()
	quest_icon.add_theme_font_override("font", hint.get_theme_font("font"))
	quest_icon.add_theme_font_size_override("font_size", 16)
	quest_icon.add_theme_color_override("font_color", Color(1.0, 0.85, 0.2))
	quest_icon.add_theme_color_override("font_outline_color", Color.BLACK)
	quest_icon.add_theme_constant_override("outline_size", 5)
	quest_icon.size = Vector2(24, 20)
	quest_icon.position = Vector2(-12, ICON_Y)
	quest_icon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	quest_icon.text = "!"
	quest_icon.visible = false
	add_child(quest_icon)


## "!" = quest baru, "?" = quest akhir siap diserahkan (Kristal sudah di tangan).
func _refresh_quest_icon() -> void:
	if QuestManager.npc_has_quests(npc_id):
		var stage: int = QuestManager.get_ready_stage(npc_id)
		quest_icon.text = "?" if stage == QuestManager.Stage.AKHIR else "!"
		set_has_new_quest(stage > 0)


func set_has_new_quest(value: bool) -> void:
	has_new_quest = value
	if not is_node_ready():
		return
	quest_icon.visible = value
	if _icon_tween:
		_icon_tween.kill()
	quest_icon.position.y = ICON_Y
	if value:  # ikon naik-turun pelan
		_icon_tween = create_tween().set_loops()
		_icon_tween.tween_property(quest_icon, "position:y", ICON_Y - 3.0, 0.5)
		_icon_tween.tween_property(quest_icon, "position:y", ICON_Y, 0.5)


## Dialog yang diputar: dialog tetap bila diisi, selain itu mengikuti progres quest, terakhir default = npc_id.
func get_dialog_id() -> String:
	if dialog_id != "":
		return dialog_id
	var from_quest: String = QuestManager.get_dialog_for(npc_id)
	return from_quest if from_quest != "" else npc_id


# ---------------------------------------------------------------- Interaksi

func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = true
		_update_hint()


func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_in_range = false
		_update_hint()


func _update_hint() -> void:
	hint.visible = _player_in_range and not DialogManager.is_active


func _unhandled_input(event: InputEvent) -> void:
	if not _player_in_range or DialogManager.is_active or not event.is_action_pressed("interact"):
		return
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player:
		_face_toward(player.global_position)
	if opens_shop and GameManager.has_met(npc_id):
		# Pedagang yang sudah pernah bicara: langsung ke pembelian tanpa mengulang percakapan.
		get_viewport().set_input_as_handled()
		_open_shop()
		return
	if DialogManager.start_dialog(get_dialog_id()):
		interacted.emit(npc_id)
		get_viewport().set_input_as_handled()  # E yang membuka dialog tidak ikut melanjutkan dialog


func _on_dialog_ended(finished_id: String) -> void:
	_update_hint()
	if finished_id == get_dialog_id():
		dialog_finished.emit(npc_id)
		if opens_shop:
			GameManager.mark_met(npc_id)   # percakapan cukup sekali; berikutnya langsung buka toko
			_open_shop.call_deferred()


## Membuka Kantong Pedagang di tab Toko (tab Jual, Tempa, Racik, Skill ada di dalamnya).
func _open_shop() -> void:
	var menu: Node = get_tree().get_first_node_in_group("trade_menu")
	if menu and menu.has_method("open_shop"):
		menu.open_shop(0)


# ---------------------------------------------------------------- Arah hadap

func _face_toward(target: Vector2) -> void:
	var delta: Vector2 = target - global_position
	if absf(delta.x) >= absf(delta.y):
		_face("side", delta.x < 0.0)
	else:
		_face("up" if delta.y < 0.0 else "down", false)


func _face(direction: String, flip: bool) -> void:
	var anim: String = "idle_%s" % direction
	if not sprite.sprite_frames.has_animation(anim):
		anim = "idle_side"  # NPC tanpa arah lengkap (mis. Lilbah)
	if not sprite.sprite_frames.has_animation(anim):
		return
	sprite.flip_h = flip
	sprite.play(anim)
