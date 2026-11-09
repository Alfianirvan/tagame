extends CanvasLayer
## Inventory (tombol I): grid item + 5 slot equipment. Klik item untuk melihat detail,
## lalu "Pakai" (potion) atau "Pasang" (senjata/armor). Klik slot equipment untuk melepas.
## Diperbarui lewat signal GameManager.inventory_changed / equipment_changed.

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const INK := Color(0.2, 0.12, 0.1)
const SLOT_NAMES := {"weapon": "Senjata", "helm": "Helm", "armor": "Armor", "shield": "Perisai", "accessory": "Aksesori"}
const GRID_COLS := 6
const CELL := 40

var _root: Control
var _grid: GridContainer
var _slot_buttons: Dictionary = {}
var _stats: Label
var _detail: RichTextLabel
var _action: Button
var _selected: String = ""
var _was_enabled: bool = true


func _ready() -> void:
	layer = 54
	add_to_group("inventory_ui")
	add_to_group("ui_overlay")
	_build_ui()
	_root.visible = false
	GameManager.inventory_changed.connect(_refresh)
	GameManager.equipment_changed.connect(func(_s: String, _i: String) -> void: _refresh())
	GameManager.gold_changed.connect(func(_g: int) -> void: _refresh())


# ---------------------------------------------------------------- Bangun UI

func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var dim: ColorRect = ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.5)
	_root.add_child(dim)

	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(40, 20)
	panel.size = Vector2(560, 320)
	panel.add_theme_stylebox_override("panel", _box(Color(0.96, 0.9, 0.76), Color(0.45, 0.28, 0.16), 4, 10))
	_root.add_child(panel)

	var cols: HBoxContainer = HBoxContainer.new()
	cols.add_theme_constant_override("separation", 12)
	panel.add_child(cols)

	# --- Kolom kiri: equipment + stat
	var left: VBoxContainer = VBoxContainer.new()
	left.custom_minimum_size = Vector2(150, 0)
	left.add_theme_constant_override("separation", 4)
	cols.add_child(left)
	left.add_child(_label("Perlengkapan", 13, Color(0.55, 0.33, 0.2)))
	for slot in GameManager.SLOTS:
		var b: Button = Button.new()
		b.custom_minimum_size = Vector2(150, 32)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.expand_icon = true
		b.clip_text = true
		b.add_theme_font_override("font", FONT)
		b.add_theme_font_size_override("font_size", 10)
		b.pressed.connect(_on_slot_pressed.bind(slot))
		left.add_child(b)
		_slot_buttons[slot] = b
	_stats = _label("", 11, INK)
	left.add_child(_stats)

	# --- Kolom kanan: grid + detail
	var right: VBoxContainer = VBoxContainer.new()
	right.custom_minimum_size = Vector2(360, 0)
	right.add_theme_constant_override("separation", 6)
	cols.add_child(right)
	right.add_child(_label("Tas   (I / Esc: tutup)", 13, Color(0.55, 0.33, 0.2)))
	var scroll: ScrollContainer = ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(360, 130)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(scroll)
	_grid = GridContainer.new()
	_grid.columns = GRID_COLS
	_grid.add_theme_constant_override("h_separation", 4)
	_grid.add_theme_constant_override("v_separation", 4)
	scroll.add_child(_grid)

	_detail = RichTextLabel.new()
	_detail.bbcode_enabled = true
	_detail.custom_minimum_size = Vector2(360, 90)
	_detail.add_theme_font_override("normal_font", FONT)
	_detail.add_theme_font_override("bold_font", FONT)
	_detail.add_theme_font_size_override("normal_font_size", 11)
	_detail.add_theme_color_override("default_color", INK)
	right.add_child(_detail)

	_action = Button.new()
	_action.custom_minimum_size = Vector2(120, 26)
	_action.add_theme_font_override("font", FONT)
	_action.add_theme_font_size_override("font_size", 11)
	_action.pressed.connect(_on_action_pressed)
	right.add_child(_action)


func _label(text: String, size: int, color: Color) -> Label:
	var l: Label = Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


func _box(bg: Color, border: Color, border_w: int, margin: int) -> StyleBoxFlat:
	var s: StyleBoxFlat = StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(border_w)
	s.set_corner_radius_all(4)
	s.set_content_margin_all(margin)
	return s


# ---------------------------------------------------------------- Isi

func _refresh() -> void:
	if not _root.visible:
		return
	# Slot equipment
	for slot: String in _slot_buttons:
		var b: Button = _slot_buttons[slot]
		var id: String = GameManager.equipment.get(slot, "")
		b.icon = ItemIcons.get_icon(id) if id != "" else null
		b.text = " %s: %s" % [SLOT_NAMES[slot], _display_name(id) if id != "" else "-"]
	# Grid item (urut nama agar stabil)
	for c in _grid.get_children():
		c.queue_free()
	var ids: Array = GameManager.inventory.keys()
	ids.sort()
	if _selected != "" and not GameManager.has_item(_selected):
		_selected = ""
	for id: String in ids:
		var cell: Button = Button.new()
		cell.custom_minimum_size = Vector2(CELL, CELL)
		cell.icon = ItemIcons.get_icon(id)
		cell.expand_icon = true
		cell.text = "x%d" % GameManager.count_item(id)
		cell.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cell.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		cell.add_theme_font_override("font", FONT)
		cell.add_theme_font_size_override("font_size", 9)
		cell.tooltip_text = _display_name(id)
		cell.toggle_mode = true
		cell.button_pressed = (id == _selected)
		cell.pressed.connect(_on_item_pressed.bind(id))
		_grid.add_child(cell)
	_stats.text = "\nSerangan: %d\nPertahanan: %d\nHP maks: %d\nStamina maks: %d\nGold: %d" % [
		GameManager.get_attack_damage(), GameManager.get_defense(),
		GameManager.max_hp, int(GameManager.max_stamina), GameManager.gold]
	_show_detail()


func _display_name(id: String) -> String:
	var lv: int = GameManager.get_item_upgrade(id)
	return GameManager.get_item_name(id) + (" +%d" % lv if lv > 0 else "")


func _show_detail() -> void:
	if _selected == "":
		_detail.text = "Pilih item di tas untuk melihat detail."
		_action.visible = false
		return
	var item: Dictionary = GameManager.get_item(_selected)
	var t: String = "[b]%s[/b]\n%s\n" % [_display_name(_selected), item.get("description", "")]
	if item.has("damage"):
		t += "Damage: %d\n" % roundi(float(item["damage"]) * GameManager.upgrade_multiplier(_selected))
	if item.has("defense"):
		t += "Pertahanan: %d  HP maks: +%d\n" % [item.get("defense", 0), item.get("max_hp", 0)]
	if item.has("heal"):
		t += "Memulihkan %d HP\n" % int(item["heal"])
	_detail.text = t
	if item.get("type", "") == "consumable":
		_action.text = "Pakai"
		_action.visible = true
	elif item.get("type", "") == "note":
		_action.text = "Baca"
		_action.visible = true
	elif GameManager.get_slot_for(_selected) != "":
		_action.text = "Pasang"
		_action.visible = true
	else:
		_action.visible = false


# ---------------------------------------------------------------- Aksi

func _on_item_pressed(id: String) -> void:
	_selected = id
	AudioManager.play_sfx("menu_pilih")
	_refresh()


func _on_action_pressed() -> void:
	if _selected == "":
		return
	if GameManager.get_item(_selected).get("type", "") == "note":
		_read_note(_selected)
	elif GameManager.get_item(_selected).get("type", "") == "consumable":
		if GameManager.hp >= GameManager.max_hp:
			return  # HP sudah penuh, potion tidak terbuang
		if GameManager.use_item(_selected):
			AudioManager.play_sfx("heal_potion")
	elif GameManager.equip(_selected):
		AudioManager.play_sfx("menu_pilih")


## Membuka panel baca untuk kertas catatan materi.
func _read_note(id: String) -> void:
	var chapter: int = int(GameManager.get_item(id).get("chapter", 0))
	AudioManager.play_sfx("menu_pilih")
	add_child(NoteReader.create(chapter))


func _on_slot_pressed(slot: String) -> void:
	if GameManager.unequip(slot):
		AudioManager.play_sfx("menu_batal")


# ---------------------------------------------------------------- Buka / tutup

func _toggle() -> void:
	if _root.visible:
		_root.visible = false
		_set_player_controls(_was_enabled)
		return
	if DialogManager.is_active or QuestManager.quiz_active:
		return
	var player: Node = get_tree().get_first_node_in_group("player")
	_was_enabled = player == null or bool(player.get("controls_enabled"))
	_root.visible = true
	_set_player_controls(false)
	_refresh()


func is_open() -> bool:
	return _root.visible


func _set_player_controls(enabled: bool) -> void:
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(enabled)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("inventory") or (_root.visible and event.is_action_pressed("pause")):
		_toggle()
		get_viewport().set_input_as_handled()
