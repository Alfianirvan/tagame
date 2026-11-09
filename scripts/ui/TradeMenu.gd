extends CanvasLayer
## Kantong Pedagang (tombol Tab): tab Toko, Jual, Tempa, Racik, Skill.
## Lore: Raka murid pandai besi, jadi ia membawa palu & landasan kecil; Toko = kantong pedagang kiriman Dadang/Joko.
## Bisa dipakai di mana saja kecuali saat bertarung (ada musuh dekat). Data dari data/shop.json, upgrades.json,
## recipes.json, skills.json; logikanya ada di GameManager (buy_item, forge_item, craft, unlock_skill).

const TABS: Array[String] = ["Toko", "Jual", "Tempa", "Racik", "Skill"]
const SAFE_DISTANCE := 260.0
const SLOT_NAMES := {"weapon": "Senjata", "helm": "Helm", "armor": "Armor", "shield": "Perisai", "accessory": "Aksesori"}

var _root: Control
var _tab_buttons: Array[Button] = []
var _list: VBoxContainer
var _resources: Label
var _icon: TextureRect
var _title: Label
var _detail: Label
var _message: Label
var _action: Button
var _fx_layer: Control

var _tab: int = 0
var _entries: Array[Dictionary] = []
var _selected: int = 0
var _open: bool = false
var _was_enabled: bool = true
var _busy: bool = false


func _ready() -> void:
	layer = 56
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("ui_overlay")
	add_to_group("trade_menu")
	_build_ui()
	_root.visible = false
	GameManager.gold_changed.connect(func(_g: int) -> void: _on_state_changed())
	GameManager.inventory_changed.connect(_on_state_changed)
	GameManager.chapter_unlocked.connect(func(_c: int) -> void: _on_state_changed())


# ---------------------------------------------------------------- Bangun UI

func _build_ui() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_root.add_child(UIKit.dim(0.5))
	var panel: PanelContainer = PanelContainer.new()
	panel.position = Vector2(30, 14)
	panel.size = Vector2(580, 332)
	panel.add_theme_stylebox_override("panel", UIKit.box(UIKit.PAPER, UIKit.BORDER, 4, 8))
	_root.add_child(panel)
	var v: VBoxContainer = VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	panel.add_child(v)

	var head: HBoxContainer = HBoxContainer.new()
	v.add_child(head)
	var title: Label = UIKit.label("Kantong Pedagang  (Tab / Esc: tutup)", 13, UIKit.TITLE)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.autowrap_mode = TextServer.AUTOWRAP_OFF   # satu baris, jangan dipecah per huruf
	head.add_child(title)
	_resources = UIKit.label("", 10, Color(0.45, 0.28, 0.05))
	_resources.autowrap_mode = TextServer.AUTOWRAP_OFF   # tanpa ini teks Gold/Ore/Herb pecah per huruf & mendorong panel
	_resources.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(_resources)

	var tabs: HBoxContainer = HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	v.add_child(tabs)
	for i in range(TABS.size()):
		var b: Button = UIKit.button(TABS[i], Vector2(80, 22))
		b.pressed.connect(_set_tab.bind(i))
		tabs.add_child(b)
		_tab_buttons.append(b)

	var body: HBoxContainer = HBoxContainer.new()
	body.add_theme_constant_override("separation", 8)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(body)

	var scroll: ScrollContainer = ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(230, 250)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 2)
	_list.custom_minimum_size = Vector2(220, 0)
	scroll.add_child(_list)

	var right: VBoxContainer = VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 4)
	body.add_child(right)
	var top: HBoxContainer = HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	right.add_child(top)
	var frame: Control = Control.new()
	frame.custom_minimum_size = Vector2(48, 48)
	top.add_child(frame)
	_icon = TextureRect.new()
	_icon.custom_minimum_size = Vector2(40, 40)
	_icon.size = Vector2(40, 40)
	_icon.position = Vector2(4, 4)
	_icon.pivot_offset = Vector2(20, 20)
	_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	frame.add_child(_icon)
	_fx_layer = Control.new()
	_fx_layer.position = Vector2(24, 24)
	_fx_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_fx_layer)
	_title = UIKit.label("", 13, UIKit.INK)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_title)
	_detail = UIKit.label("", 10, UIKit.INK)
	_detail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(_detail)
	_message = UIKit.label("", 10, Color(0.65, 0.2, 0.12))
	right.add_child(_message)
	_action = UIKit.button("", Vector2(200, 26))
	_action.pressed.connect(_on_action)
	right.add_child(_action)


# ---------------------------------------------------------------- Buka / tutup

func is_open() -> bool:
	return _open


func _unhandled_input(event: InputEvent) -> void:
	if _open:
		if event.is_action_pressed("trade_menu") or event.is_action_pressed("pause"):
			get_viewport().set_input_as_handled()
			if not _busy:
				close()
		return
	if event.is_action_pressed("trade_menu"):
		get_viewport().set_input_as_handled()
		open()


## Membuka Kantong Pedagang langsung di tab tertentu (0 Toko, 1 Jual, 2 Tempa, 3 Racik); dipanggil NPC pedagang.
func open_shop(tab: int = 0) -> void:
	_tab = clampi(tab, 0, TABS.size() - 1)
	open()


## Dipanggil Tab atau tombol di menu Jeda. Menolak bila sedang bertarung / dialog / UI lain terbuka.
func open() -> void:
	if _open or DialogManager.is_active or QuestManager.quiz_active:
		return
	for n in get_tree().get_nodes_in_group("ui_overlay"):
		if n != self and n.has_method("is_open") and n.is_open():
			return
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return
	if enemy_near():
		FloatingText.spawn(player.get_parent(), player.global_position + Vector2(0, -50), "Tidak bisa saat bertarung!", Color(1, 0.6, 0.5), 1.8)
		AudioManager.play_sfx("menu_batal")
		return
	_open = true
	_was_enabled = bool(player.get("controls_enabled"))
	player.set_controls_enabled(false)
	_root.visible = true
	AudioManager.play_sfx("menu_pindah")
	_message.text = ""
	_set_tab(_tab)


func close() -> void:
	if not _open:
		return
	_open = false
	_root.visible = false
	var player: Node = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_controls_enabled"):
		player.set_controls_enabled(_was_enabled)


func enemy_near() -> bool:
	var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
	if player == null:
		return false
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en and en.is_inside_tree() and en.global_position.distance_to(player.global_position) < SAFE_DISTANCE:
			return true
	return false


# ---------------------------------------------------------------- Tab & daftar

func _set_tab(i: int) -> void:
	_tab = i
	_message.text = ""
	_selected = 0
	for n in range(_tab_buttons.size()):
		_tab_buttons[n].disabled = n == i
	_rebuild()


func _on_state_changed() -> void:
	if _open and not _busy:
		_rebuild()


func _rebuild() -> void:
	var keep: String = ""
	if _selected >= 0 and _selected < _entries.size():
		keep = String(_entries[_selected].get("id", ""))
	_entries = _make_entries()
	_selected = 0
	for i in range(_entries.size()):
		if String(_entries[i].get("id", "")) == keep and keep != "":
			_selected = i
	for c in _list.get_children():
		c.queue_free()
	for i in range(_entries.size()):
		var b: Button = UIKit.button(String(_entries[i]["label"]), Vector2(210, 22))
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(_select.bind(i))
		_list.add_child(b)
	_resources.text = "Gold %d   Ore %d   Herb %d   Fragment %d" % [GameManager.gold, GameManager.count_item("ore"),
		GameManager.count_item("herb"), GameManager.count_item("data_fragment")]
	_show_detail()


func _select(i: int) -> void:
	_selected = i
	_message.text = ""
	_show_detail()


func _make_entries() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	match _tab:
		0:  # Toko
			for id in GameManager.get_shop_items():
				out.append({"id": id, "label": "%s  —  %d G" % [GameManager.get_item_name(id), int(GameManager.get_item(id).get("price", 0))]})
		1:  # Jual: semua isi tas yang punya harga jual (perlengkapan terpasang tidak ada di tas)
			for id: String in GameManager.inventory:
				if GameManager.get_sell_price(id) > 0 and id != "data_fragment":
					out.append({"id": id, "label": "%s x%d  —  %d G" % [GameManager.get_item_name(id), GameManager.count_item(id), GameManager.get_sell_price(id)]})
		2:  # Tempa: perlengkapan terpasang + di tas
			var seen: Dictionary = {}
			for slot in GameManager.SLOTS:
				var eid: String = GameManager.equipment.get(slot, "")
				if eid != "" and not seen.has(eid):
					seen[eid] = true
					out.append({"id": eid, "label": "%s%s  [dipakai]" % [GameManager.get_item_name(eid), _plus(eid)]})
			for id: String in GameManager.inventory:
				if GameManager.is_forgeable(id) and not seen.has(id):
					seen[id] = true
					out.append({"id": id, "label": "%s%s" % [GameManager.get_item_name(id), _plus(id)]})
		3:  # Racik
			for r: Dictionary in GameManager.recipes:
				out.append({"id": String(r.get("id", "")), "label": String(r.get("nama", r.get("hasil", ""))), "recipe": r})
		4:  # Skill
			for sid: String in GameManager.skill_db:
				var info: Dictionary = GameManager.skill_db[sid]
				out.append({"id": sid, "label": "%s%s" % [String(info.get("nama", sid)), "  [terbuka]" if GameManager.has_skill(sid) else ""]})
	return out


func _plus(id: String) -> String:
	var lv: int = GameManager.get_item_upgrade(id)
	return " +%d" % lv if lv > 0 else ""


# ---------------------------------------------------------------- Detail & aksi

func _show_detail() -> void:
	_action.visible = true
	_action.disabled = true
	_icon.modulate = Color.WHITE
	if _entries.is_empty():
		_icon.texture = null
		_title.text = "—"
		_detail.text = _empty_text()
		_action.visible = false
		return
	_selected = clampi(_selected, 0, _entries.size() - 1)
	var e: Dictionary = _entries[_selected]
	var id: String = String(e["id"])
	match _tab:
		0:
			_show_item(id)
			var price: int = int(GameManager.get_item(id).get("price", 0))
			_detail.text += "\nHarga: %d Gold" % price
			_action.text = "Beli (%d G)" % price
			_action.disabled = GameManager.gold < price
			if _action.disabled:
				_message.text = "Gold tidak cukup."
		1:
			_show_item(id)
			_detail.text += "\nDimiliki: %d" % GameManager.count_item(id)
			_action.text = "Jual 1 (+%d G)" % GameManager.get_sell_price(id)
			_action.disabled = false
		2:
			_show_forge(id)
		3:
			_show_recipe(e["recipe"])
		4:
			_show_skill(id)


func _empty_text() -> String:
	match _tab:
		1:
			return "Tidak ada barang yang bisa dijual."
		2:
			return "Belum ada senjata atau armor."
		_:
			return "Kosong."


func _show_item(id: String) -> void:
	var item: Dictionary = GameManager.get_item(id)
	_icon.texture = ItemIcons.get_icon(id)
	_title.text = "%s%s" % [GameManager.get_item_name(id), _plus(id)]
	var desc: String = String(item.get("description", ""))
	var stats: String = _stat_text(id, GameManager.get_item_upgrade(id))
	# Hindari baris ganda bila deskripsi sudah menyebut hal yang sama dengan ringkasan stat.
	_detail.text = desc if (stats == "" or desc.trim_suffix(".") == stats) else "%s\n%s" % [desc, stats]


## Ringkasan stat item pada level tempa tertentu.
func _stat_text(id: String, level: int) -> String:
	var item: Dictionary = GameManager.get_item(id)
	var mult: float = GameManager.multiplier_for_level(level)
	var parts: Array[String] = []
	match String(item.get("type", "")):
		"weapon":
			parts.append("Damage %d" % roundi(float(item.get("damage", 0)) * mult))
			parts.append("Jangkauan %d" % int(item.get("range", 0)))
		"armor":
			parts.append("Pertahanan %d" % roundi(float(item.get("defense", 0)) * mult))
			if int(item.get("max_hp", 0)) > 0:
				parts.append("HP maks +%d" % roundi(float(item.get("max_hp", 0)) * mult))
			if int(item.get("max_stamina", 0)) > 0:
				parts.append("Stamina maks +%d" % int(item.get("max_stamina", 0)))
		"consumable":
			parts.append("Memulihkan %d HP" % int(item.get("heal", 0)))
	return " · ".join(parts)


func _show_forge(id: String) -> void:
	_show_item(id)
	var lv: int = GameManager.get_item_upgrade(id)
	var cost: Dictionary = GameManager.get_forge_cost(id)
	var lines: Array[String] = [String(GameManager.get_item(id).get("description", "")), "Level tempa: +%d  (batas chapter ini: +%d)" % [lv, GameManager.get_current_upgrade_cap()]]
	if cost.is_empty():
		lines.append("Sudah level maksimum.")
		_action.visible = false
	else:
		lines.append("Sebelum: %s" % _stat_text(id, lv))
		lines.append("Sesudah: %s   (+%d%%)" % [_stat_text(id, lv + 1), int(GameManager.upgrade_data.get("levels", {}).get(str(lv + 1), {}).get("bonus_percent", 0))])
		var need: String = "Biaya: %d Gold, %d Ore" % [int(cost["gold"]), int(cost["ore"])]
		if int(cost["data_fragment"]) > 0:
			need += ", %d Data Fragment" % int(cost["data_fragment"])
		lines.append(need)
		var reason: String = GameManager.forge_block_reason(id)
		_message.text = reason
		_action.text = "Tempa ke +%d" % (lv + 1)
		_action.disabled = reason != ""
	_detail.text = "\n".join(lines)


func _show_recipe(r: Dictionary) -> void:
	var result: String = String(r.get("hasil", ""))
	_icon.texture = ItemIcons.get_icon(result)
	_title.text = "%s x%d" % [GameManager.get_item_name(result), int(r.get("jumlah", 1))]
	var lines: Array[String] = [String(GameManager.get_item(result).get("description", "")), "Bahan:"]
	var mats: Dictionary = r.get("bahan", {})
	for mid: String in mats:
		lines.append("  %s  %d / %d" % [GameManager.get_item_name(mid), GameManager.count_item(mid), int(mats[mid])])
	_detail.text = "\n".join(lines)
	_action.text = "Racik"
	_action.disabled = not GameManager.can_craft(r)
	if _action.disabled:
		_message.text = "Bahan belum cukup."


func _show_skill(sid: String) -> void:
	var info: Dictionary = GameManager.skill_db.get(sid, {})
	_icon.texture = ItemIcons.get_icon("data_fragment")
	_title.text = String(info.get("nama", sid))
	var lines: Array[String] = [String(info.get("deskripsi", "")), "Tombol: %s   Stamina: %d   Jeda: %ds" % [String(info.get("tombol", "?")), int(info.get("stamina", 0)), int(info.get("cooldown", 0))]]
	var cost: int = int(info.get("biaya_fragment", 1))
	if GameManager.has_skill(sid):
		lines.append("Skill sudah terbuka.")
		_action.visible = false
	else:
		lines.append("Biaya: %d Data Fragment (dimiliki %d)" % [cost, GameManager.count_item("data_fragment")])
		_action.text = "Buka skill (%d Fragment)" % cost
		_action.disabled = GameManager.count_item("data_fragment") < cost
		if _action.disabled:
			_message.text = "Data Fragment kurang."
	_detail.text = "\n".join(lines)


func _on_action() -> void:
	if _entries.is_empty() or _busy:
		return
	var e: Dictionary = _entries[_selected]
	var id: String = String(e["id"])
	match _tab:
		0:
			if GameManager.buy_item(id):
				AudioManager.play_sfx("ambil_gold")
				_message.text = "Dibeli: %s" % GameManager.get_item_name(id)
				_after_trade()
		1:
			if GameManager.sell_item(id):
				AudioManager.play_sfx("ambil_koin")
				_message.text = "Terjual: %s" % GameManager.get_item_name(id)
				_after_trade()
		2:
			_forge(id)
		3:
			if GameManager.craft(e["recipe"]):
				AudioManager.play_sfx("heal_potion")
				_message.text = "Berhasil meracik %s." % GameManager.get_item_name(String(e["recipe"].get("hasil", "")))
				_after_trade()
		4:
			if GameManager.unlock_skill(id):
				AudioManager.play_sfx("jingle_naik_level")
				_message.text = "Skill terbuka! Tekan %s di dalam game." % String(GameManager.skill_db[id].get("tombol", ""))
				_after_trade()


## Tampilan ulang setelah transaksi, pesan sukses dipertahankan.
func _after_trade() -> void:
	var msg: String = _message.text
	_rebuild()
	_message.text = msg


# ---------------------------------------------------------------- Tempa (animasi + SFX)

func _forge(id: String) -> void:
	if GameManager.forge_block_reason(id) != "":
		AudioManager.play_sfx("menu_batal")
		return
	_busy = true
	_action.disabled = true
	_message.text = "Menempa..."
	for n in range(3):    # tiga ayunan palu: ikon berguncang + percikan + dentang landasan
		AudioManager.play_sfx("tempa_anvil", 0.08)
		var tw: Tween = create_tween()
		tw.tween_property(_icon, "scale", Vector2(0.8, 1.15), 0.08)
		tw.tween_property(_icon, "scale", Vector2(1.0, 1.0), 0.12)
		_icon.modulate = Color(1.0, 0.75, 0.45)
		_sparks()
		await get_tree().create_timer(0.3).timeout
	GameManager.forge_item(id)
	_icon.modulate = Color(1.6, 1.5, 1.1)
	AudioManager.play_sfx("power_up")
	_busy = false
	var nm: String = GameManager.get_item_name(id)
	_after_trade_with("%s ditempa menjadi +%d!" % [nm, GameManager.get_item_upgrade(id)])


func _after_trade_with(msg: String) -> void:
	_rebuild()
	_message.text = msg
	_message.add_theme_color_override("font_color", Color(0.2, 0.5, 0.15))
	var tw: Tween = create_tween()
	tw.tween_interval(2.0)
	tw.tween_callback(func() -> void: _message.add_theme_color_override("font_color", Color(0.65, 0.2, 0.12)))


func _sparks() -> void:
	for i in range(8):
		var s: ColorRect = ColorRect.new()
		s.size = Vector2(3, 3)
		s.color = Color(1.0, 0.85, 0.3)
		_fx_layer.add_child(s)
		var target: Vector2 = Vector2.from_angle(randf() * TAU) * randf_range(14.0, 30.0)
		var tw: Tween = create_tween().set_parallel(true)
		tw.tween_property(s, "position", target, 0.3)
		tw.tween_property(s, "modulate:a", 0.0, 0.3)
		tw.chain().tween_callback(s.queue_free)
