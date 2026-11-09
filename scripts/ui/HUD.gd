extends CanvasLayer
## HUD: bar HP, bar Stamina, Gold, Level/XP, dan chapter aktif.
## Semua nilai diperbarui lewat signal GameManager (tanpa polling di _process).

const FONT := preload("res://assets/fonts/Square-Black.ttf")
const BAR_W := 110.0
const BAR_H := 9.0

var _hp_fill: ColorRect
var _sta_fill: ColorRect
var _hp_label: Label
var _gold_label: Label
var _level_label: Label
var _xp_fill: ColorRect
var _hp_pct: Label               # teks persen di kanan bar
var _sta_pct: Label
var _xp_pct: Label
var _chapter_label: Label
var _chapters: Dictionary = {}
var _heal_btn: Button            # tombol heal cepat (pakai potion)
var _tracker_label: Label        # pelacak tujuan quest aktif (kiri atas, di bawah panel atribut)


func _ready() -> void:
	layer = 10
	add_to_group("hud")
	var data: Variant = GameManager.load_json(GameManager.DATA_DIR + "chapters.json")
	if data is Dictionary:
		_chapters = data
	_build_ui()
	_build_tracker()
	add_child(QuestArrow.new())   # panah penunjuk target quest
	QuestManager.quests_changed.connect(_refresh_tracker)
	_refresh_tracker()
	GameManager.hp_changed.connect(_on_hp)
	GameManager.stamina_changed.connect(_on_stamina)
	GameManager.gold_changed.connect(func(g: int) -> void: _gold_label.text = "Gold: %d" % g)
	GameManager.xp_changed.connect(_on_xp)
	GameManager.chapter_changed.connect(_on_chapter)
	# Nilai awal
	_on_hp(GameManager.hp, GameManager.max_hp)
	_on_stamina(GameManager.stamina, GameManager.max_stamina)
	_gold_label.text = "Gold: %d" % GameManager.gold
	_on_xp(GameManager.xp, GameManager.xp_needed(GameManager.level), GameManager.level)
	_on_chapter(GameManager.current_chapter)


func _build_ui() -> void:
	var panel: Panel = Panel.new()
	panel.position = Vector2(6, 6)
	panel.size = Vector2(184, 74)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.1, 0.07, 0.05, 0.7)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(2)
	style.set_corner_radius_all(3)
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)

	_hp_fill = _make_bar(Vector2(32, 8), Color(0.85, 0.2, 0.2), panel)
	_hp_pct = _make_pct_label(Vector2(146, 5), panel)
	_hp_label = _make_label(Vector2(8, 5), 9, panel)
	_hp_label.text = "HP"
	_sta_fill = _make_bar(Vector2(32, 21), Color(0.25, 0.75, 0.35), panel)
	_sta_pct = _make_pct_label(Vector2(146, 18), panel)
	_make_label(Vector2(8, 18), 9, panel).text = "ST"
	_xp_fill = _make_bar(Vector2(32, 34), Color(0.35, 0.6, 0.95), panel)
	_xp_pct = _make_pct_label(Vector2(146, 31), panel)
	_make_label(Vector2(8, 31), 9, panel).text = "XP"
	_level_label = _make_label(Vector2(8, 46), 10, panel)
	_gold_label = _make_label(Vector2(70, 46), 10, panel)
	_gold_label.add_theme_color_override("font_color", Color(1, 0.85, 0.3))
	_chapter_label = _make_label(Vector2(8, 59), 9, panel)
	_chapter_label.add_theme_color_override("font_color", Color(0.8, 0.9, 0.7))
	_build_heal_button(panel)


## Tombol Heal: pakai potion dari inventory (juga tombol H). Tidak mengambil fokus keyboard.
func _build_heal_button(parent: Control) -> void:
	_heal_btn = Button.new()
	_heal_btn.position = Vector2(138, 44)
	_heal_btn.size = Vector2(40, 16)
	_heal_btn.focus_mode = Control.FOCUS_NONE
	_heal_btn.add_theme_font_override("font", FONT)
	_heal_btn.add_theme_font_size_override("font_size", 8)
	_heal_btn.tooltip_text = "Pulihkan HP dengan potion (H)"
	_heal_btn.pressed.connect(_on_heal_pressed)
	parent.add_child(_heal_btn)
	GameManager.inventory_changed.connect(_refresh_heal_button)
	_refresh_heal_button()


func _potion_count() -> int:
	return GameManager.count_item("potion") + GameManager.count_item("potion_besar")


func _refresh_heal_button() -> void:
	_heal_btn.text = "Heal %d" % _potion_count()
	_heal_btn.disabled = _potion_count() == 0


func _on_heal_pressed() -> void:
	if GameManager.quick_heal():
		AudioManager.play_sfx("heal_potion")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("heal"):
		_on_heal_pressed()


## Kotak tujuan: teks objective quest yang sedang dilacak.
func _build_tracker() -> void:
	var box: PanelContainer = PanelContainer.new()
	box.position = Vector2(6, 84)
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = Color(0.1, 0.07, 0.05, 0.7)
	style.border_color = Color(0.45, 0.28, 0.16)
	style.set_border_width_all(2)
	style.set_corner_radius_all(3)
	style.set_content_margin_all(5)
	box.add_theme_stylebox_override("panel", style)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tracker_label = Label.new()
	_tracker_label.custom_minimum_size = Vector2(170, 0)
	_tracker_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_tracker_label.add_theme_font_override("font", FONT)
	_tracker_label.add_theme_font_size_override("font_size", 8)
	_tracker_label.add_theme_color_override("font_color", Color(1.0, 0.92, 0.6))
	_tracker_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_tracker_label.add_theme_constant_override("outline_size", 2)
	box.add_child(_tracker_label)
	add_child(box)


func _refresh_tracker() -> void:
	var id: String = QuestManager.get_tracked_quest_id()
	var box: Control = _tracker_label.get_parent() as Control
	if id == "":
		box.visible = false
		return
	var q: Dictionary = QuestManager.get_quest(id)
	_tracker_label.text = "Tujuan: %s" % String(q.get("objective", q.get("title", "")))
	box.visible = true
	box.reset_size()


func _make_bar(pos: Vector2, color: Color, parent: Control) -> ColorRect:
	var back: ColorRect = ColorRect.new()
	back.color = Color(0, 0, 0, 0.6)
	back.position = pos
	back.size = Vector2(BAR_W, BAR_H)
	parent.add_child(back)
	var fill: ColorRect = ColorRect.new()
	fill.color = color
	fill.position = Vector2(1, 1)
	fill.size = Vector2(BAR_W - 2, BAR_H - 2)
	back.add_child(fill)
	return fill


## Teks persen di sebelah kanan bar.
func _make_pct_label(pos: Vector2, parent: Control) -> Label:
	var l: Label = _make_label(pos, 9, parent)
	l.add_theme_color_override("font_color", Color(1, 0.95, 0.8))
	return l


func _make_label(pos: Vector2, font_size: int, parent: Control) -> Label:
	var l: Label = Label.new()
	l.position = pos
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 2)
	parent.add_child(l)
	return l


func _set_fill(fill: ColorRect, ratio: float) -> void:
	fill.size.x = maxf(0.0, (BAR_W - 2.0) * clampf(ratio, 0.0, 1.0))


func _on_hp(hp: int, max_hp: int) -> void:
	_set_fill(_hp_fill, float(hp) / float(maxi(max_hp, 1)))
	_hp_label.text = "HP"
	_hp_pct.text = "%d%%" % roundi(100.0 * hp / maxi(max_hp, 1))
	_hp_fill.get_parent().tooltip_text = "%d / %d" % [hp, max_hp]


func _on_stamina(stamina: float, max_stamina: float) -> void:
	_set_fill(_sta_fill, stamina / maxf(max_stamina, 1.0))
	_sta_pct.text = "%d%%" % roundi(100.0 * stamina / maxf(max_stamina, 1.0))


func _on_xp(xp: int, needed: int, level: int) -> void:
	_set_fill(_xp_fill, float(xp) / float(maxi(needed, 1)))
	_xp_pct.text = "%d%%" % roundi(100.0 * xp / maxi(needed, 1))
	_level_label.text = "Lv %d" % level


func _on_chapter(chapter: int) -> void:
	var info: Dictionary = _chapters.get(str(chapter), {})
	_chapter_label.text = "%s" % info.get("name", "Chapter %d" % chapter)
