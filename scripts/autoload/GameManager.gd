extends Node
## GameManager: menyimpan state inti game (atribut, inventory, equipment, progres chapter).
## Semua perubahan dikabarkan lewat signal agar HUD/UI tidak perlu polling.

signal hp_changed(hp: int, max_hp: int)
signal stamina_changed(stamina: float, max_stamina: float)
signal gold_changed(gold: int)
signal xp_changed(xp: int, xp_needed: int, level: int)
signal level_up(new_level: int)
signal inventory_changed
signal equipment_changed(slot: String, item_id: String)
signal player_died
signal chapter_changed(chapter: int)
signal chapter_unlocked(chapter: int)
signal crystal_collected(chapter: int)
signal quest_stage_changed(chapter: int, stage: int)
signal item_forged(item_id: String, new_level: int)   # tempa berhasil
signal skill_unlocked(skill_id: String)
signal enemy_killed(enemy_id: String)   # dipancarkan Enemy saat mati (untuk quest/statistik)

const DATA_DIR := "res://data/"
const SLOTS: Array[String] = ["weapon", "helm", "armor", "shield", "accessory"]
const MAX_CHAPTER := 5

const BASE_HP := 100
const BASE_STAMINA := 100
const HP_PER_LEVEL := 10
const STAMINA_PER_LEVEL := 5
const STAMINA_REGEN := 15.0         # per detik
const STAMINA_REGEN_DELAY := 1.0    # jeda (detik) setelah memakai stamina
const START_SCENE := "res://scenes/world/Village.tscn"

# --- Atribut ---
var hp: int = BASE_HP
var max_hp: int = BASE_HP
var stamina: float = BASE_STAMINA
var max_stamina: float = BASE_STAMINA
var gold: int = 0
var xp: int = 0
var level: int = 1

# --- Inventory & equipment ---
var inventory: Dictionary = {}      # id item -> jumlah
var equipment: Dictionary = {}      # slot -> id item ("" bila kosong)
var item_upgrades: Dictionary = {}  # id item -> level tempa (0-3)

# --- Progres ---
var current_chapter: int = 0                # 0 = Desa / awal game
var unlocked_chapter: int = 1               # chapter tertinggi yang terbuka di Peta Dunia
var quest_stage: Dictionary = {}            # "chapter" -> tahap selesai (0 belum, 1 awal, 2 tengah, 3 akhir)
var crystals: Array[int] = []               # chapter yang kristalnya sudah diambil
var checkpoint_scene: String = START_SCENE
var checkpoint_position: Vector2 = Vector2.ZERO
var checkpoint_node: String = ""             # path node checkpoint/bonfire; posisi dicari dari node ini (tahan digeser di editor)
var met_npcs: Array[String] = []             # NPC pedagang yang dialog perkenalannya sudah selesai (langsung buka toko)
var killed_enemies: Array[String] = []      # kunci musuh yang sudah dibunuh ("scene:path-node"), tidak muncul lagi

# --- Database data (dari JSON) ---
var item_db: Dictionary = {}                # gabungan items + weapons + armors
var upgrade_data: Dictionary = {}
var shop_stock: Array = []                  # dari shop.json
var recipes: Array = []                     # dari recipes.json
var skill_db: Dictionary = {}               # dari skills.json
var unlocked_skills: Array[String] = []     # skill spesial yang sudah dibuka (Data Fragment)

var _regen_timer: Timer
var _regen_delay_left: float = 0.0


func _ready() -> void:
	_load_databases()
	_regen_timer = Timer.new()
	_regen_timer.wait_time = 0.1
	_regen_timer.one_shot = false
	_regen_timer.timeout.connect(_on_regen_tick)
	add_child(_regen_timer)
	reset_state()


# ---------------------------------------------------------------- Data

func _load_databases() -> void:
	item_db.clear()
	for file in ["items.json", "weapons.json", "armors.json"]:
		var data: Variant = load_json(DATA_DIR + file)
		if data is Dictionary:
			for id: String in data:
				var entry: Dictionary = data[id]
				entry["id"] = id
				item_db[id] = entry
	var upg: Variant = load_json(DATA_DIR + "upgrades.json")
	upgrade_data = upg if upg is Dictionary else {}
	var shop: Variant = load_json(DATA_DIR + "shop.json")
	shop_stock = shop.get("stok", []) if shop is Dictionary else []
	var rec: Variant = load_json(DATA_DIR + "recipes.json")
	recipes = rec.get("resep", []) if rec is Dictionary else []
	var sk: Variant = load_json(DATA_DIR + "skills.json")
	skill_db = sk.get("skill", {}) if sk is Dictionary else {}


## Membaca file JSON; mengembalikan null bila gagal.
func load_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		push_warning("File JSON tidak ditemukan: %s" % path)
		return null
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if parsed == null:
		push_warning("JSON tidak valid: %s" % path)
	return parsed


func get_item(id: String) -> Dictionary:
	return item_db.get(id, {})


func get_item_name(id: String) -> String:
	return get_item(id).get("name", id)


## Batas level tempa untuk sebuah chapter (CLAUDE.md Bagian 8).
func get_upgrade_cap(chapter: int) -> int:
	var caps: Dictionary = upgrade_data.get("chapter_cap", {})
	return int(caps.get(str(chapter), 3 if chapter > 3 else 0))


# ---------------------------------------------------------------- State

## Mengembalikan semua state ke kondisi game baru.
func reset_state() -> void:
	level = 1
	xp = 0
	gold = 0
	inventory = {}
	item_upgrades = {}
	equipment = {}
	for slot in SLOTS:
		equipment[slot] = ""
	current_chapter = 0
	unlocked_chapter = 1
	quest_stage = {}
	for c in range(0, MAX_CHAPTER + 1):
		quest_stage[str(c)] = 0
	crystals = []
	unlocked_skills = []
	checkpoint_scene = START_SCENE
	checkpoint_position = Vector2.ZERO
	checkpoint_node = ""
	met_npcs = []
	killed_enemies = []
	_recalc_stats(true)
	stamina = max_stamina
	_emit_all()


func _emit_all() -> void:
	hp_changed.emit(hp, max_hp)
	stamina_changed.emit(stamina, max_stamina)
	gold_changed.emit(gold)
	xp_changed.emit(xp, xp_needed(level), level)
	inventory_changed.emit()
	for slot in SLOTS:
		equipment_changed.emit(slot, equipment[slot])
	chapter_changed.emit(current_chapter)


func get_save_data() -> Dictionary:
	return {
		"hp": hp, "stamina": stamina, "gold": gold, "xp": xp, "level": level,
		"inventory": inventory, "equipment": equipment, "item_upgrades": item_upgrades,
		"current_chapter": current_chapter, "unlocked_chapter": unlocked_chapter,
		"quest_stage": quest_stage, "crystals": crystals, "unlocked_skills": unlocked_skills,
		"checkpoint_scene": checkpoint_scene,
		"checkpoint_position": [checkpoint_position.x, checkpoint_position.y],
		"checkpoint_node": checkpoint_node,
		"killed_enemies": killed_enemies,
		"met_npcs": met_npcs,
	}


## Memuat state dari hasil get_save_data (JSON mengubah int jadi float, jadi dikonversi ulang).
func apply_save_data(d: Dictionary) -> void:
	reset_state()
	level = int(d.get("level", 1))
	xp = int(d.get("xp", 0))
	gold = int(d.get("gold", 0))
	inventory = {}
	for id: String in d.get("inventory", {}):
		inventory[id] = int(d["inventory"][id])
	item_upgrades = {}
	for id: String in d.get("item_upgrades", {}):
		item_upgrades[id] = int(d["item_upgrades"][id])
	for slot in SLOTS:
		equipment[slot] = String(d.get("equipment", {}).get(slot, ""))
	current_chapter = int(d.get("current_chapter", 0))
	unlocked_chapter = int(d.get("unlocked_chapter", 1))
	for key: String in d.get("quest_stage", {}):
		quest_stage[key] = int(d["quest_stage"][key])
	unlocked_skills = []
	for sid in d.get("unlocked_skills", []):
		unlocked_skills.append(String(sid))
	crystals = []
	for c in d.get("crystals", []):
		crystals.append(int(c))
	checkpoint_scene = String(d.get("checkpoint_scene", START_SCENE))
	var pos: Array = d.get("checkpoint_position", [0, 0])
	checkpoint_position = Vector2(float(pos[0]), float(pos[1]))
	checkpoint_node = String(d.get("checkpoint_node", ""))
	met_npcs = []
	for m in d.get("met_npcs", []):
		met_npcs.append(String(m))
	killed_enemies = []
	for k in d.get("killed_enemies", []):
		killed_enemies.append(String(k))
	_recalc_stats(true)
	hp = clampi(int(d.get("hp", max_hp)), 1, max_hp)
	stamina = clampf(float(d.get("stamina", max_stamina)), 0.0, max_stamina)
	_emit_all()


# ---------------------------------------------------------------- Atribut

func xp_needed(for_level: int) -> int:
	return 50 + (for_level - 1) * 25


## Hitung ulang HP/Stamina maks dari level + bonus equipment.
func _recalc_stats(refill: bool = false) -> void:
	var bonus_hp: int = 0
	var bonus_stamina: int = 0
	for slot in SLOTS:
		var item: Dictionary = get_item(equipment.get(slot, ""))
		var mult: float = upgrade_multiplier(equipment.get(slot, ""))
		bonus_hp += roundi(float(item.get("max_hp", 0)) * mult)
		bonus_stamina += int(item.get("max_stamina", 0))
	max_hp = BASE_HP + (level - 1) * HP_PER_LEVEL + bonus_hp
	max_stamina = float(BASE_STAMINA + (level - 1) * STAMINA_PER_LEVEL + bonus_stamina)
	if refill:
		hp = max_hp
		stamina = max_stamina
	else:
		hp = mini(hp, max_hp)
		stamina = minf(stamina, max_stamina)
	hp_changed.emit(hp, max_hp)
	stamina_changed.emit(stamina, max_stamina)


func take_damage(amount: int, ignore_defense: bool = false) -> int:
	if hp <= 0:
		return 0
	var dmg: int = amount if ignore_defense else maxi(1, amount - get_defense())
	hp = maxi(0, hp - dmg)
	hp_changed.emit(hp, max_hp)
	if hp == 0:
		player_died.emit()
	return dmg


func heal(amount: int) -> void:
	if hp <= 0:
		return
	hp = mini(max_hp, hp + amount)
	hp_changed.emit(hp, max_hp)


func restore_full() -> void:
	hp = max_hp
	stamina = max_stamina
	hp_changed.emit(hp, max_hp)
	stamina_changed.emit(stamina, max_stamina)


## Memakai stamina; false bila tidak cukup.
func use_stamina(amount: float) -> bool:
	if stamina < amount:
		return false
	stamina -= amount
	_regen_delay_left = STAMINA_REGEN_DELAY
	stamina_changed.emit(stamina, max_stamina)
	_regen_timer.start()
	return true


func _on_regen_tick() -> void:
	if _regen_delay_left > 0.0:
		_regen_delay_left -= _regen_timer.wait_time
		return
	stamina = minf(max_stamina, stamina + STAMINA_REGEN * _regen_timer.wait_time)
	stamina_changed.emit(stamina, max_stamina)
	if stamina >= max_stamina:
		_regen_timer.stop()


func add_gold(amount: int) -> void:
	gold += amount
	gold_changed.emit(gold)


## Mengurangi gold; false bila tidak cukup.
func spend_gold(amount: int) -> bool:
	if gold < amount:
		return false
	gold -= amount
	gold_changed.emit(gold)
	return true


## Menambah XP; naik level otomatis (HP & Stamina maks ikut naik, terisi penuh).
func add_xp(amount: int) -> void:
	xp += amount
	var leveled: bool = false
	while xp >= xp_needed(level):
		xp -= xp_needed(level)
		level += 1
		leveled = true
	if leveled:
		_recalc_stats(true)
		level_up.emit(level)
	xp_changed.emit(xp, xp_needed(level), level)


# ---------------------------------------------------------------- Inventory

func add_item(id: String, count: int = 1) -> void:
	if count <= 0:
		return
	if not item_db.has(id):
		push_warning("Item tidak dikenal: %s" % id)
	inventory[id] = int(inventory.get(id, 0)) + count
	inventory_changed.emit()


## Mengurangi item; false bila jumlah tidak cukup.
func remove_item(id: String, count: int = 1) -> bool:
	var have: int = int(inventory.get(id, 0))
	if count <= 0 or have < count:
		return false
	if have == count:
		inventory.erase(id)
	else:
		inventory[id] = have - count
	inventory_changed.emit()
	return true


func count_item(id: String) -> int:
	return int(inventory.get(id, 0))


func has_item(id: String, count: int = 1) -> bool:
	return count_item(id) >= count


## Memakai item konsumsi (potion). false bila bukan konsumsi / tidak ada.
func use_item(id: String) -> bool:
	var item: Dictionary = get_item(id)
	if item.get("type", "") != "consumable" or not has_item(id):
		return false
	remove_item(id)
	heal(int(item.get("heal", 0)))
	return true


## Heal cepat (tombol HUD / tombol H): pakai potion terkecil yang tersedia. false bila HP penuh / tidak ada potion.
func quick_heal() -> bool:
	if hp <= 0 or hp >= max_hp:
		return false
	for id: String in ["potion", "potion_besar"]:
		if has_item(id):
			return use_item(id)
	return false


# ---------------------------------------------------------------- Equipment

## Slot tujuan sebuah item ("" bila tidak bisa dipakai).
func get_slot_for(id: String) -> String:
	var item: Dictionary = get_item(id)
	match item.get("type", ""):
		"weapon":
			return "weapon"
		"armor":
			return String(item.get("slot", ""))
	return ""


## Memakai item dari inventory; item lama dikembalikan ke inventory.
func equip(id: String) -> bool:
	var slot: String = get_slot_for(id)
	if slot == "" or not has_item(id):
		return false
	remove_item(id)
	var old: String = equipment[slot]
	if old != "":
		add_item(old)
	equipment[slot] = id
	_recalc_stats()
	equipment_changed.emit(slot, id)
	return true


func unequip(slot: String) -> bool:
	if not equipment.has(slot) or equipment[slot] == "":
		return false
	var old: String = equipment[slot]
	equipment[slot] = ""
	add_item(old)
	_recalc_stats()
	equipment_changed.emit(slot, "")
	return true


func get_item_upgrade(id: String) -> int:
	return int(item_upgrades.get(id, 0))


## Pengali stat dari level tempa (+20% / +40% / +70%).
func upgrade_multiplier(id: String) -> float:
	return multiplier_for_level(get_item_upgrade(id))


func multiplier_for_level(lv: int) -> float:
	if lv <= 0:
		return 1.0
	var levels: Dictionary = upgrade_data.get("levels", {})
	var percent: float = float(levels.get(str(lv), {}).get("bonus_percent", 0))
	return 1.0 + percent / 100.0


func get_attack_damage() -> int:
	var id: String = equipment.get("weapon", "")
	if id == "":
		return 3  # tangan kosong
	return roundi(float(get_item(id).get("damage", 0)) * upgrade_multiplier(id))


func get_defense() -> int:
	var total: float = 0.0
	for slot in SLOTS:
		var id: String = equipment.get(slot, "")
		if id != "":
			total += float(get_item(id).get("defense", 0)) * upgrade_multiplier(id)
	return roundi(total)


# ---------------------------------------------------------------- Progres chapter

func set_current_chapter(chapter: int) -> void:
	current_chapter = chapter
	chapter_changed.emit(chapter)


func unlock_chapter(chapter: int) -> void:
	if chapter > unlocked_chapter and chapter <= MAX_CHAPTER:
		unlocked_chapter = chapter
		chapter_unlocked.emit(chapter)


func is_chapter_unlocked(chapter: int) -> bool:
	return chapter <= unlocked_chapter


func get_quest_stage(chapter: int) -> int:
	return int(quest_stage.get(str(chapter), 0))


func set_quest_stage(chapter: int, stage: int) -> void:
	quest_stage[str(chapter)] = stage
	quest_stage_changed.emit(chapter, stage)


func add_crystal(chapter: int) -> void:
	if not crystals.has(chapter):
		crystals.append(chapter)
		crystal_collected.emit(chapter)


func has_crystal(chapter: int) -> bool:
	return crystals.has(chapter)


## Kunci unik musuh yang diletakkan di scene (musuh hasil spawn dinamis tidak punya kunci).
func enemy_key(enemy: Node) -> String:
	if enemy.owner == null:
		return ""
	return "%s:%s" % [enemy.owner.scene_file_path, enemy.owner.get_path_to(enemy)]


func has_met(npc_id: String) -> bool:
	return npc_id in met_npcs


func mark_met(npc_id: String) -> void:
	if not (npc_id in met_npcs):
		met_npcs.append(npc_id)


func is_enemy_killed(key: String) -> bool:
	return key != "" and key in killed_enemies


func mark_enemy_killed(key: String) -> void:
	if key != "" and not (key in killed_enemies):
		killed_enemies.append(key)


func set_checkpoint(scene_path: String, pos: Vector2, node_path: String = "") -> void:
	checkpoint_scene = scene_path
	checkpoint_position = pos
	checkpoint_node = node_path


## Posisi hidup ulang di scene aktif. Bila checkpoint tercatat lewat node, posisi diambil dari node itu
## (mengikuti kalau checkpoint digeser di editor); selain itu memakai posisi tersimpan. ZERO = tidak ada.
func get_checkpoint_spawn(scene_root: Node) -> Vector2:
	if checkpoint_scene != scene_root.scene_file_path:
		return Vector2.ZERO
	if checkpoint_node != "":
		var n: Node = scene_root.get_node_or_null(NodePath(checkpoint_node))
		if n != null and n.has_method("get_respawn_point"):
			return n.get_respawn_point()
	return checkpoint_position


# ---------------------------------------------------------------- Ekonomi: Toko, Tempa, Racik, Skill

## Barang Toko yang sudah tersedia (sesuai chapter terbuka).
func get_shop_items() -> Array[String]:
	var out: Array[String] = []
	for entry: Dictionary in shop_stock:
		if int(entry.get("chapter", 1)) <= unlocked_chapter and item_db.has(String(entry["item"])):
			out.append(String(entry["item"]))
	return out


func buy_item(id: String) -> bool:
	var price: int = int(get_item(id).get("price", 0))
	if price <= 0 or not spend_gold(price):
		return false
	add_item(id)
	return true


## Harga jual item (0 = tidak bisa dijual). Item yang sedang dipakai tidak muncul di daftar jual.
func get_sell_price(id: String) -> int:
	return int(get_item(id).get("sell", int(get_item(id).get("price", 0)) / 2))


func sell_item(id: String) -> bool:
	var price: int = get_sell_price(id)
	if price <= 0 or not remove_item(id):
		return false
	add_gold(price)
	return true


## Batas level tempa saat ini (naik tiap chapter terbuka: Ch1 +1, Ch2 +2, Ch3+ +3).
func get_current_upgrade_cap() -> int:
	return get_upgrade_cap(unlocked_chapter)


## Item yang bisa ditempa: senjata/armor, baik terpasang maupun di tas.
func is_forgeable(id: String) -> bool:
	return get_slot_for(id) != ""


## Biaya tempa ke level berikutnya: {"gold", "ore", "data_fragment"}; kosong bila sudah maksimum (+3).
func get_forge_cost(id: String) -> Dictionary:
	var next: int = get_item_upgrade(id) + 1
	var info: Dictionary = upgrade_data.get("levels", {}).get(str(next), {})
	if info.is_empty():
		return {}
	return {"gold": int(info.get("gold", 0)), "ore": int(info.get("ore", 0)), "data_fragment": int(info.get("data_fragment", 0))}


## String kosong bila boleh ditempa; selain itu berisi alasan penolakan.
func forge_block_reason(id: String) -> String:
	if not is_forgeable(id):
		return "Item ini tidak bisa ditempa."
	var cost: Dictionary = get_forge_cost(id)
	if cost.is_empty():
		return "Sudah level maksimum (+3)."
	if get_item_upgrade(id) + 1 > get_current_upgrade_cap():
		return "Batas tempa chapter ini +%d. Lanjutkan petualangan untuk membuka batas lebih tinggi." % get_current_upgrade_cap()
	if gold < int(cost["gold"]):
		return "Gold kurang."
	if count_item("ore") < int(cost["ore"]):
		return "Ore kurang."
	if count_item("data_fragment") < int(cost["data_fragment"]):
		return "Data Fragment kurang."
	return ""


func forge_item(id: String) -> bool:
	if forge_block_reason(id) != "":
		return false
	var cost: Dictionary = get_forge_cost(id)
	spend_gold(int(cost["gold"]))
	remove_item("ore", int(cost["ore"]))
	if int(cost["data_fragment"]) > 0:
		remove_item("data_fragment", int(cost["data_fragment"]))
	item_upgrades[id] = get_item_upgrade(id) + 1
	_recalc_stats()
	for slot in SLOTS:
		if equipment.get(slot, "") == id:
			equipment_changed.emit(slot, id)
	inventory_changed.emit()
	item_forged.emit(id, get_item_upgrade(id))
	return true


## Racik: bahan cukup?
func can_craft(recipe: Dictionary) -> bool:
	var mats: Dictionary = recipe.get("bahan", {})
	for id: String in mats:
		if count_item(id) < int(mats[id]):
			return false
	return true


func craft(recipe: Dictionary) -> bool:
	if not can_craft(recipe):
		return false
	var mats: Dictionary = recipe.get("bahan", {})
	for id: String in mats:
		remove_item(id, int(mats[id]))
	add_item(String(recipe.get("hasil", "")), int(recipe.get("jumlah", 1)))
	return true


func has_skill(skill_id: String) -> bool:
	return unlocked_skills.has(skill_id)


func unlock_skill(skill_id: String) -> bool:
	var info: Dictionary = skill_db.get(skill_id, {})
	if info.is_empty() or has_skill(skill_id):
		return false
	var cost: int = int(info.get("biaya_fragment", 1))
	if count_item("data_fragment") < cost:
		return false
	remove_item("data_fragment", cost)
	unlocked_skills.append(skill_id)
	skill_unlocked.emit(skill_id)
	return true
