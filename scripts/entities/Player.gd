extends CharacterBody2D
## Player (Raka): gerak 4 arah (8 arah input), lari, dodge, serang sesuai senjata, terkena hit, mati.
##
## Konvensi tabrakan (layer): 1 world, 2 player, 3 enemy, 4 serangan player, 5 serangan musuh.
## - Musuh/boss (layer 3) harus punya method take_hit(damage: int, from_pos: Vector2).
## - Area serangan musuh (layer 5) menyimpan damage lewat meta "damage" (set_meta("damage", 8)).

signal died                  # HP habis, animasi mati mulai
signal death_finished        # animasi mati selesai -> game menampilkan layar Kalah
signal attacked(style: String)

const PlayerSprites := preload("res://scripts/entities/PlayerSprites.gd")

enum State { NORMAL, ATTACK, DODGE, HIT, DEAD }

@export var walk_speed: float = 80.0
@export var run_speed: float = 120.0
@export var dodge_speed: float = 220.0
@export var dodge_time: float = 0.25
@export var dodge_cooldown: float = 0.5
@export var dodge_stamina: float = 20.0
@export var hit_invulnerable_time: float = 0.8
@export var knockback_speed: float = 140.0
@export var knockback_time: float = 0.15

## Frame animasi serang saat hitbox aktif (dari 8 frame).
const ATTACK_ACTIVE_FRAMES := Vector2i(2, 5)
## Pedang (sheet Pierce): pedang baru menusuk di frame 3-5, frame 0-2 masih bersiap.
const SWORD_ACTIVE_FRAMES := Vector2i(4, 5)
## Tongkat: Cast melepas Magic_Bolt di frame 4; Slam menghantam di frame 5.
const STAFF_CAST_FRAME := 4
const STAFF_SLAM_FRAME := 5
const WEAPON_SLOT_COUNT := 6           # tombol 1-6 untuk ganti senjata
const STAFF_TIP_DIST := 26.0           # jarak ujung tongkat dari badan Raka (searah hadap)
## Tangan kosong (sheet Hit, 4 frame): lengan terangkat memukul di frame 1-2.
const UNARMED_ACTIVE_FRAMES := Vector2i(1, 2)
const BODY_CENTER := Vector2(0, -17)   # titik tengah badan dari kaki (origin)
const HITBOX_WIDTH := 48.0              # lebar hitbox serangan (tegak lurus arah hadap)
const SWEEP_HALF_ANGLE := 70.0          # setengah sudut kerucut sapuan serangan (derajat)
const PROJECTILE_SPEED := 220.0         # kecepatan proyektil senjata jarak jauh
const ATTACK_ANIM := {"slice": "atk", "pierce": "atk", "crush": "atk", "ranged": "atk", "punch": "atk", "spin": "atk"}
## Jenis senjata yang memakai animasi sprite bawaan Raka (senjata sudah tergambar di sheet-nya).
const BAKED_ATTACK_ANIM := {"palu": "crush"}
const ATTACK_BASE_TIME := 0.5         # durasi animasi serang (8 frame / 16 fps); crush diperlambat

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var hitbox: Area2D = $Hitbox
@onready var hitbox_shape: CollisionShape2D = $Hitbox/CollisionShape2D
@onready var hurtbox: Area2D = $Hurtbox
@onready var camera: Camera2D = $Camera2D

var state: State = State.NORMAL
var controls_enabled: bool = true

var facing_dir: String = "down"        # down / side / up
var facing_flip: bool = false          # true = menghadap kiri
var facing_vec: Vector2 = Vector2.DOWN

var _attack_cooldown_left: float = 0.0
var _attack_damage: int = 0
var _attack_style: String = "slice"
var _attack_kind: String = ""             # slash / pierce / cast / slam (pedang & tongkat); kosong = serangan lain
var _attack_reach: float = 24.0
var _aim_dir: Vector2 = Vector2.RIGHT      # arah bidik tongkat (mengikuti kursor mouse, bebas 360 derajat)
var _sweep_angle: float = SWEEP_HALF_ANGLE
var _active_frames: Vector2i = ATTACK_ACTIVE_FRAMES   # frame animasi saat hitbox aktif (berbeda per senjata)
var _attack_weapon: Dictionary = {}
var _hit_targets: Array[Node] = []
var _weapon_layer: Sprite2D            # gambar senjata/kepalan saat menyerang (di luar sprite badan)
var _weapon_tween: Tween
var _fist_texture: Texture2D
var _dodge_left: float = 0.0
var _dodge_cooldown_left: float = 0.0
var _dodge_vec: Vector2 = Vector2.ZERO
var _invulnerable_left: float = 0.0
var _knockback_left: float = 0.0
var _knockback_vec: Vector2 = Vector2.ZERO
var _blink_tween: Tween
# Skill spesial (dibuka dengan Data Fragment di menu Kantong Pedagang)
var _spin_cooldown_left: float = 0.0
var _dash_cooldown_left: float = 0.0
var _skill_dash: bool = false
var _dash_speed: float = 0.0
var _dash_damage: int = 0
var _dash_hits: Array[Node] = []


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING  # top-down: tanpa "lantai", tidak ikut terbawa benda lain
	add_to_group("player")
	if sprite.sprite_frames == null:  # cadangan bila player_frames.tres belum terpasang di scene
		sprite.sprite_frames = PlayerSprites.build()
	PlayerSprites.add_attack_animations(sprite.sprite_frames)
	PlayerSprites.add_weapon_animations(sprite.sprite_frames)
	_build_weapon_layer()
	sprite.offset = Vector2(0, -16)  # kaki (y=48 di frame 64x64) tepat di origin
	sprite.frame_changed.connect(_on_frame_changed)
	sprite.animation_finished.connect(_on_animation_finished)
	hitbox.body_entered.connect(_on_hitbox_target)
	hitbox.area_entered.connect(_on_hitbox_target)
	hitbox.monitoring = false
	hurtbox.area_entered.connect(_on_hurtbox_area_entered)
	GameManager.player_died.connect(_die)
	DialogManager.dialog_started.connect(func(_id: String) -> void: set_controls_enabled(false))
	DialogManager.dialog_ended.connect(func(_id: String) -> void: set_controls_enabled(true))
	_play("idle")
	_ensure_ui.call_deferred()


## Memasang HUD dan Inventory sekali per scene permainan (tidak muncul di menu karena tanpa Player).
func _ensure_ui() -> void:
	var scene: Node = get_tree().current_scene
	if scene == null:
		return
	if get_tree().get_first_node_in_group("hud") == null:
		scene.add_child((load("res://scenes/ui/HUD.tscn") as PackedScene).instantiate())
	if get_tree().get_first_node_in_group("inventory_ui") == null:
		scene.add_child((load("res://scenes/ui/Inventory.tscn") as PackedScene).instantiate())
	# Menu Jeda (Esc), Peta Dunia (M), dan layar Menang/Kalah dipasang sekali per scene permainan
	for entry: Array in [["pause_menu", "res://scenes/ui/PauseMenu.tscn"], ["world_map_ui", "res://scenes/ui/WorldMap.tscn"], ["end_screen", "res://scenes/ui/EndScreen.tscn"], ["trade_menu", "res://scenes/ui/TradeMenu.tscn"]]:
		if get_tree().get_first_node_in_group(String(entry[0])) == null:
			scene.add_child((load(String(entry[1])) as PackedScene).instantiate())


## Mengaktifkan/menonaktifkan kontrol (dipakai saat dialog, menu, cutscene).
func set_controls_enabled(enabled: bool) -> void:
	controls_enabled = enabled


## Getaran kamera singkat (dipakai hantaman Golem dan efek berat lain).
func shake_camera(strength: float = 3.0, duration: float = 0.25) -> void:
	var tw: Tween = create_tween()
	var steps: int = maxi(2, int(duration / 0.04))
	for i in steps:
		var fade: float = 1.0 - float(i) / float(steps)
		tw.tween_property(camera, "offset", Vector2(randf_range(-1, 1), randf_range(-1, 1)) * strength * fade, 0.04)
	tw.tween_property(camera, "offset", Vector2.ZERO, 0.04)


## Batas kamera sesuai ukuran map (dalam piksel dunia).
func set_camera_limits(rect: Rect2i) -> void:
	camera.limit_left = rect.position.x
	camera.limit_top = rect.position.y
	camera.limit_right = rect.end.x
	camera.limit_bottom = rect.end.y


func is_invulnerable() -> bool:
	return state == State.DODGE or state == State.DEAD or _invulnerable_left > 0.0


# ---------------------------------------------------------------- Loop utama

func _physics_process(delta: float) -> void:
	_attack_cooldown_left = maxf(0.0, _attack_cooldown_left - delta)
	_dodge_cooldown_left = maxf(0.0, _dodge_cooldown_left - delta)
	_invulnerable_left = maxf(0.0, _invulnerable_left - delta)
	_spin_cooldown_left = maxf(0.0, _spin_cooldown_left - delta)
	_dash_cooldown_left = maxf(0.0, _dash_cooldown_left - delta)

	match state:
		State.NORMAL:
			_process_normal()
		State.ATTACK:
			velocity = velocity.move_toward(Vector2.ZERO, 600.0 * delta)
		State.DODGE:
			_dodge_left -= delta
			velocity = _dodge_vec * (_dash_speed if _skill_dash else dodge_speed)
			if _skill_dash:
				_dash_damage_step()
			if _dodge_left <= 0.0:
				_end_dodge()
		State.HIT:
			_knockback_left -= delta
			velocity = _knockback_vec * knockback_speed if _knockback_left > 0.0 else Vector2.ZERO
		State.DEAD:
			velocity = Vector2.ZERO
	move_and_slide()


func _process_normal() -> void:
	var dir: Vector2 = Vector2.ZERO
	if controls_enabled:
		dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		if dir != Vector2.ZERO:
			_update_facing(dir)  # arah hadap diperbarui dulu, supaya serangan/dodge memakai arah terbaru
		if Input.is_action_just_pressed("dodge") and _dodge_cooldown_left <= 0.0:
			if _start_dodge(dir):
				return
		if Input.is_action_pressed("attack") and _attack_cooldown_left <= 0.0 and not _mouse_over_button():
			if _start_attack():
				return
		for slot in WEAPON_SLOT_COUNT:
			if Input.is_action_just_pressed("weapon_%d" % (slot + 1)):
				_switch_weapon(slot)
		if Input.is_action_just_pressed("attack_alt") and _attack_cooldown_left <= 0.0 and not _mouse_over_button():
			if _start_attack(true):
				return
		if Input.is_action_just_pressed("skill_spin") and _start_spin():
			return
		if Input.is_action_just_pressed("skill_dash") and _start_skill_dash(dir):
			return

	if dir == Vector2.ZERO:
		velocity = Vector2.ZERO
		_play("idle")
		return
	_update_facing(dir)
	var running: bool = Input.is_key_pressed(KEY_SHIFT)
	velocity = dir * (run_speed if running else walk_speed)
	_play("run" if running else "walk")


# ---------------------------------------------------------------- Arah & animasi

func _update_facing(dir: Vector2) -> void:
	if absf(dir.x) >= absf(dir.y):
		facing_dir = "side"
		facing_flip = dir.x < 0.0
		facing_vec = Vector2.LEFT if facing_flip else Vector2.RIGHT
	elif dir.y < 0.0:
		facing_dir = "up"
		facing_flip = false
		facing_vec = Vector2.UP
	else:
		facing_dir = "down"
		facing_flip = false
		facing_vec = Vector2.DOWN


## Memainkan animasi <aksi>_<arah>. force = ulang dari awal walau sudah memainkan animasi yang sama.
func _play(action: String, force: bool = false) -> void:
	var anim: String = "%s_%s" % [action, facing_dir]
	if action != "atk":
		sprite.speed_scale = 1.0
	sprite.flip_h = facing_flip
	if force or sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)


# ---------------------------------------------------------------- Ganti senjata (tombol 1-6)

## Slot senjata: 1 = tangan kosong, 2 = pedang, 3 dst. = jenis senjata lain yang dimiliki
## (tombak, palu, busur, tongkat; urut seperti di weapons.json, hanya yang sudah dimiliki).
## Tiap slot berisi daftar id senjata sejenis, urut dari yang terkuat.
func _weapon_slots() -> Array:
	var equipped: String = String(GameManager.equipment.get("weapon", ""))
	var groups: Dictionary = {}    # weapon_type -> Array[String]
	for id: String in GameManager.item_db:
		var item: Dictionary = GameManager.item_db[id]
		if String(item.get("type", "")) != "weapon" or not (id == equipped or GameManager.has_item(id)):
			continue
		var kind: String = String(item.get("weapon_type", ""))
		if not groups.has(kind):
			groups[kind] = []
		groups[kind].append(id)
	for kind: String in groups:
		(groups[kind] as Array).sort_custom(func(x: String, y: String) -> bool:
			return float(GameManager.get_item(x).get("damage", 0)) > float(GameManager.get_item(y).get("damage", 0)))
	var slots: Array = [{"label": "Tangan kosong", "ids": []}, {"label": "Pedang", "ids": groups.get("pedang", [])}]
	for kind: String in groups:
		if kind != "pedang":
			slots.append({"label": kind.capitalize(), "ids": groups[kind]})
	return slots


## Pasang senjata untuk slot ke-(slot+1). Menekan slot yang sama lagi bergantian ke senjata sejenis lain
## (mis. Pedang Kayu <-> Pedang Besi). Senjata lama kembali ke tas.
func _switch_weapon(slot: int) -> void:
	var slots: Array = _weapon_slots()
	var pos: Vector2 = global_position + Vector2(0, -50)
	if slot >= slots.size():
		FloatingText.spawn(get_parent(), pos, "Slot %d: kosong" % (slot + 1), Color(1, 0.7, 0.6), 1.2)
		return
	var equipped: String = String(GameManager.equipment.get("weapon", ""))
	var ids: Array = slots[slot]["ids"]
	var label: String = String(slots[slot]["label"])
	if slot == 0:
		if equipped == "":
			FloatingText.spawn(get_parent(), pos, "1: Tangan kosong (dipakai)", Color(0.9, 0.9, 0.8), 1.2)
		elif GameManager.unequip("weapon"):
			AudioManager.play_sfx("menu_pilih")
			FloatingText.spawn(get_parent(), pos, "1: Tangan kosong", Color(0.7, 1.0, 0.7), 1.4)
		return
	if ids.is_empty():
		FloatingText.spawn(get_parent(), pos, "Belum punya %s" % label.to_lower(), Color(1, 0.7, 0.6), 1.4)
		return
	var at: int = ids.find(equipped)
	if at >= 0 and ids.size() == 1:
		FloatingText.spawn(get_parent(), pos, "%d: %s (dipakai)" % [slot + 1, GameManager.get_item_name(equipped)], Color(0.9, 0.9, 0.8), 1.2)
		return
	var target: String = String(ids[(at + 1) % ids.size()]) if at >= 0 else String(ids[0])
	if GameManager.equip(target):
		AudioManager.play_sfx("menu_pilih")
		FloatingText.spawn(get_parent(), pos, "%d: %s" % [slot + 1, GameManager.get_item_name(target)], Color(0.7, 1.0, 0.7), 1.4)


# ---------------------------------------------------------------- Serangan

func _start_attack(alt: bool = false) -> bool:
	var weapon: Dictionary = GameManager.get_item(GameManager.equipment.get("weapon", ""))
	var wtype: String = String(weapon.get("weapon_type", ""))
	if wtype == "pedang" or wtype == "tongkat":
		return _start_combo_attack(weapon, alt)
	if alt:
		return false   # serangan alternatif hanya untuk pedang dan tongkat
	_attack_kind = ""
	var style: String = weapon.get("attack_style", "punch")   # tanpa senjata = pukul tangan kosong
	var cost: float = float(weapon.get("stamina_cost", 0))
	if cost > 0.0 and not GameManager.use_stamina(cost):
		return false

	state = State.ATTACK
	_attack_style = style
	_attack_weapon = weapon
	var unarmed: bool = weapon.is_empty()
	if unarmed:
		_active_frames = UNARMED_ACTIVE_FRAMES
	elif String(weapon.get("weapon_type", "")) == "pedang":
		_active_frames = SWORD_ACTIVE_FRAMES
	else:
		_active_frames = ATTACK_ACTIVE_FRAMES
	var lunge: float = 90.0 if _active_frames == SWORD_ACTIVE_FRAMES else (50.0 if unarmed else 30.0)
	velocity = facing_vec * (0.0 if style == "ranged" else lunge)
	_attack_cooldown_left = float(weapon.get("cooldown", 0.4))
	_attack_damage = GameManager.get_attack_damage()
	_hit_targets.clear()
	_attack_reach = float(weapon.get("range", 24))
	_sweep_angle = SWEEP_HALF_ANGLE
	_setup_hitbox(_attack_reach)
	# Tangan kosong memakai animasi "hit" Raka; pedang/palu memakai sheet yang menggambar senjatanya.
	var baked: String = "hit" if unarmed else BAKED_ATTACK_ANIM.get(String(weapon.get("weapon_type", "")), "")
	if baked != "":
		# Animasi sprite bawaan Raka (tanpa lapisan senjata buatan kode).
		_hide_weapon()
		_play(baked, true)
	else:
		_play(ATTACK_ANIM.get(style, "atk"), true)
		sprite.speed_scale = 0.625 if style == "crush" else 1.0
		_play_weapon_anim(style, String(GameManager.equipment.get("weapon", "")), ATTACK_BASE_TIME / sprite.speed_scale)
	AudioManager.play_sfx("serang_tebas", 0.1)
	attacked.emit(style)
	return true


## Serangan pedang (slash / pierce) dan tongkat (cast / slam). alt = klik kanan / K.
## Data serangan alternatif ada di blok "alt" pada weapons.json.
func _start_combo_attack(weapon: Dictionary, alt: bool) -> bool:
	var sword: bool = String(weapon.get("weapon_type", "")) == "pedang"
	var info: Dictionary = weapon.get("alt", {}) if alt else weapon
	if alt and info.is_empty():
		return false
	var cost: float = float(info.get("stamina_cost", 0))
	if cost > 0.0 and not GameManager.use_stamina(cost):
		return false

	_attack_kind = ("pierce" if alt else "slash") if sword else ("slam" if alt else "cast")
	_aim_dir = facing_vec
	if not sword:
		# Tongkat: serangan mengarah ke kursor mouse; animasi memakai arah hadap terdekat (atas/bawah/kiri/kanan).
		var to_cursor: Vector2 = get_global_mouse_position() - (global_position + BODY_CENTER)
		if to_cursor.length() > 4.0:
			_aim_dir = to_cursor.normalized()
			_update_facing(to_cursor)
	state = State.ATTACK
	_attack_style = _attack_kind
	_attack_weapon = weapon
	_attack_cooldown_left = float(info.get("cooldown", 0.5))
	_attack_damage = GameManager.get_attack_damage()
	if alt:
		_attack_damage = roundi(float(_attack_damage) * float(info.get("damage_x", 1.0)))
	_hit_targets.clear()
	_hide_weapon()
	match _attack_kind:
		"slash":
			_active_frames = SWORD_ACTIVE_FRAMES
			_attack_reach = float(weapon.get("range", 24))
			_sweep_angle = SWEEP_HALF_ANGLE
			velocity = facing_vec * 40.0
		"pierce":
			_active_frames = SWORD_ACTIVE_FRAMES
			_attack_reach = float(info.get("range", 40))
			_sweep_angle = float(info.get("sudut", 35))
			velocity = facing_vec * 110.0
		"cast":
			_active_frames = Vector2i(STAFF_CAST_FRAME, STAFF_CAST_FRAME)
			velocity = Vector2.ZERO
		"slam":
			_active_frames = Vector2i(STAFF_SLAM_FRAME, STAFF_SLAM_FRAME)
			velocity = Vector2.ZERO
	if sword:
		_setup_hitbox(_attack_reach)
	_play("sword_slash" if _attack_kind == "slash" else ("sword_pierce" if _attack_kind == "pierce" else ("staff_cast" if _attack_kind == "cast" else "staff_slam")), true)
	AudioManager.play_sfx("serang_tebas", 0.1)
	attacked.emit(_attack_kind)
	return true


## Staff cast: melepas Magic_Bolt dari ujung tongkat ke arah kursor mouse.
func _fire_magic_bolt() -> void:
	# Tinggi bola disamakan dengan badan musuh (bukan dada Raka) agar tidak lewat di atas musuh pendek.
	var tip: Vector2 = global_position + Vector2(0, -10) + _aim_dir * STAFF_TIP_DIST
	MagicBolt.launch(get_parent(), tip, _aim_dir, _attack_damage)


## Staff slam: damage area (radius dari weapons.json, default 24 px) di ujung tongkat.
func _slam_damage() -> void:
	var radius: float = float(_attack_weapon.get("alt", {}).get("radius", 24))
	var center: Vector2 = global_position + BODY_CENTER + _aim_dir * STAFF_TIP_DIST
	var circle: CircleShape2D = CircleShape2D.new()
	circle.radius = radius
	var query: PhysicsShapeQueryParameters2D = PhysicsShapeQueryParameters2D.new()
	query.shape = circle
	query.transform = Transform2D(0.0, center)
	query.collision_mask = 4          # layer musuh
	query.collide_with_areas = true
	query.collide_with_bodies = true
	for hit: Dictionary in get_world_2d().direct_space_state.intersect_shape(query, 16):
		var victim: Node = hit["collider"] as Node
		if victim == null:
			continue
		if not victim.has_method("take_hit") and victim.get_parent() and victim.get_parent().has_method("take_hit"):
			victim = victim.get_parent()
		if victim.has_method("take_hit") and not (victim in _hit_targets):
			_hit_targets.append(victim)
			victim.take_hit(_attack_damage, global_position)
	_ring_effect(radius, _aim_dir * STAFF_TIP_DIST)
	AudioManager.play_sfx("hantam_tanah", 0.05)


# ---------------------------------------------------------------- Gambar senjata / kepalan

## Lapisan gambar senjata: ikon item (menunjuk ke atas, gagang di bawah) atau kepalan tangan.
func _build_weapon_layer() -> void:
	var img: Image = Image.create(7, 7, false, Image.FORMAT_RGBA8)
	for y in 7:
		for x in 7:
			var d: float = Vector2(x - 3, y - 3).length()
			if d <= 3.2:
				img.set_pixel(x, y, Color(0.82, 0.58, 0.4) if d <= 2.2 else Color(0.2, 0.12, 0.1))
	_fist_texture = ImageTexture.create_from_image(img)
	_weapon_layer = Sprite2D.new()
	_weapon_layer.centered = false
	_weapon_layer.visible = false
	add_child(_weapon_layer)


func _hide_weapon() -> void:
	if _weapon_tween:
		_weapon_tween.kill()
	if _weapon_layer:
		_weapon_layer.visible = false


## Menggerakkan senjata sesuai gaya serang dan arah hadap. dur = lama animasi serang (detik).
func _play_weapon_anim(style: String, weapon_id: String, dur: float) -> void:
	_hide_weapon()
	var w: Sprite2D = _weapon_layer
	var f: Vector2 = facing_vec
	var c: Vector2 = BODY_CENTER
	var base: float = f.angle() + PI * 0.5   # ikon menunjuk ke atas; putar agar menunjuk ke arah serang
	var unarmed: bool = style == "punch" or weapon_id == ""
	if unarmed:
		w.texture = _fist_texture
		w.offset = Vector2(-3, -3)
		w.scale = Vector2(1.3, 1.3)
	else:
		w.texture = ItemIcons.get_icon(weapon_id)
		w.offset = Vector2(-12, -22)          # titik putar = gagang
		w.scale = Vector2(1.3, 1.3) if style == "pierce" else Vector2.ONE
	w.modulate = Color.WHITE
	w.rotation = 0.0 if unarmed else base
	w.visible = true
	# Menghadap atas: senjata digambar di belakang badan; arah lain di depan badan.
	move_child(w, 0 if facing_dir == "up" else get_child_count() - 1)
	var wind: float = dur * 0.25
	var strike: float = dur * 0.4
	var rest: float = dur * 0.35
	var tw: Tween = create_tween()
	_weapon_tween = tw
	if unarmed or style == "pierce":
		# Tusuk / pukul lurus: tarik ke belakang lalu lesat ke depan.
		var reach: float = 16.0 if unarmed else 12.0
		w.position = c - f * 4.0
		tw.tween_property(w, "position", c - f * 9.0, wind)
		tw.tween_property(w, "position", c + f * reach, strike).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(w, "position", c + f * (reach - 4.0), rest)
	elif style == "slice":
		w.position = c + f * 4.0
		w.rotation = base - deg_to_rad(130.0)
		tw.tween_property(w, "rotation", base - deg_to_rad(110.0), wind)
		tw.tween_property(w, "rotation", base + deg_to_rad(80.0), strike).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(w, "rotation", base + deg_to_rad(90.0), rest)
	elif style == "crush":
		w.position = c + f * 4.0
		w.rotation = base - deg_to_rad(160.0)
		tw.tween_property(w, "rotation", base - deg_to_rad(175.0), wind)
		tw.tween_property(w, "rotation", base + deg_to_rad(10.0), strike).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_property(w, "rotation", base + deg_to_rad(10.0), rest)
	elif style == "spin":
		w.position = c
		w.rotation = base
		tw.tween_interval(wind)
		tw.tween_property(w, "rotation", base + TAU, strike * 1.2)
		tw.tween_interval(maxf(0.0, dur - wind - strike * 1.2))
	else:
		# Jarak jauh (busur / tongkat): dipegang ke depan, sedikit mundur saat melepas.
		var is_staff: bool = String(_attack_weapon.get("weapon_type", "")) == "tongkat"
		w.rotation = base if is_staff else f.angle()
		w.position = c + f * 10.0
		tw.tween_property(w, "position", c + f * 6.0, wind)
		tw.tween_property(w, "position", c + f * 12.0, strike)
		tw.tween_interval(rest)
	tw.tween_callback(func() -> void: w.visible = false)


## Posisi dan ukuran hitbox di depan arah hadap, sesuai jangkauan senjata (dibuat lebar agar mudah kena).
func _setup_hitbox(reach: float) -> void:
	var rect: RectangleShape2D = hitbox_shape.shape as RectangleShape2D
	var horizontal: bool = facing_vec.x != 0.0
	var length: float = reach + 12.0
	rect.size = Vector2(length, HITBOX_WIDTH) if horizontal else Vector2(HITBOX_WIDTH, length)
	hitbox.position = BODY_CENTER + facing_vec * (length * 0.5)


## Sapuan kerucut di depan Raka: musuh biasa yang berada dalam jangkauan dan sudut serang pasti kena,
## walau sedang bergerak atau tidak persis di tengah hitbox.
func _sweep_hit() -> void:
	var reach: float = _attack_reach + 12.0
	var center: Vector2 = global_position + BODY_CENTER
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en == null or en.is_in_group("boss") or not en.has_method("take_hit") or en in _hit_targets:
			continue
		var to_t: Vector2 = en.global_position + Vector2(0, -10) - center
		var dist: float = to_t.length()
		if dist > reach + 14.0:
			continue
		if dist < 16.0 or absf(facing_vec.angle_to(to_t)) <= deg_to_rad(_sweep_angle):
			_hit_targets.append(en)
			AudioManager.play_sfx("serang_pedang", 0.1)
			en.take_hit(_attack_damage, global_position)


func _on_frame_changed() -> void:
	if state != State.ATTACK:
		return
	if _attack_kind == "cast":
		if sprite.frame == STAFF_CAST_FRAME:
			_fire_magic_bolt()
		return
	if _attack_kind == "slam":
		if sprite.frame == STAFF_SLAM_FRAME:
			_slam_damage()
		return
	if _attack_style == "ranged":
		# Senjata jarak jauh: lepaskan proyektil di frame pertama yang aktif, tanpa hitbox jarak dekat.
		if sprite.frame == _active_frames.x:
			_fire_projectile()
		return
	if _attack_style == "spin":
		if sprite.frame == _active_frames.x:
			_spin_damage()
		return
	var active: bool = sprite.frame >= _active_frames.x and sprite.frame <= _active_frames.y
	hitbox.set_deferred("monitoring", active)
	if active:
		_sweep_hit()


## Menembakkan proyektil ke arah hadap (busur = cokelat, tongkat sihir = biru).
func _fire_projectile() -> void:
	var reach: float = float(_attack_weapon.get("range", 140))
	var color: Color = Color("#4fc3f7") if _attack_weapon.get("weapon_type", "") == "tongkat" else Color("#d9a066")
	Projectile.launch(get_parent(), global_position + BODY_CENTER, facing_vec, _attack_damage, true,
		PROJECTILE_SPEED, color, reach / PROJECTILE_SPEED)
	AudioManager.play_sfx("sihir", 0.1)


func _on_hitbox_target(target: Node) -> void:
	var victim: Node = target
	if not victim.has_method("take_hit") and victim.get_parent() and victim.get_parent().has_method("take_hit"):
		victim = victim.get_parent()
	if not victim.has_method("take_hit") or victim in _hit_targets:
		return
	_hit_targets.append(victim)
	AudioManager.play_sfx("serang_pedang", 0.1)
	victim.take_hit(_attack_damage, global_position)


# ---------------------------------------------------------------- Dodge

func _start_dodge(input_dir: Vector2) -> bool:
	if not GameManager.use_stamina(dodge_stamina):
		return false
	_dodge_vec = input_dir.normalized() if input_dir != Vector2.ZERO else facing_vec
	if input_dir != Vector2.ZERO:
		_update_facing(input_dir)
	state = State.DODGE
	set_collision_mask_value(3, false)  # tembus musuh selama dodge
	_dodge_left = dodge_time
	sprite.modulate.a = 0.5
	_play("run", true)
	AudioManager.play_sfx("dodge")
	return true


func _end_dodge() -> void:
	state = State.NORMAL
	_skill_dash = false
	_dodge_cooldown_left = dodge_cooldown
	sprite.modulate = Color.WHITE
	velocity = Vector2.ZERO
	_separate_from_enemies()
	set_collision_mask_value(3, true)


## Dorong Raka keluar bila berhenti menumpuk di badan musuh setelah dash/dodge.
func _separate_from_enemies() -> void:
	const MIN_DIST: float = 24.0
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en == null:
			continue
		var off: Vector2 = global_position - en.global_position
		if off.length() < MIN_DIST:
			var away: Vector2 = off.normalized() if off != Vector2.ZERO else -_dodge_vec
			global_position = en.global_position + away * MIN_DIST


# ---------------------------------------------------------------- Skill spesial (Data Fragment)

## Serangan Putar (U): menebas semua musuh di sekitar Raka.
func _start_spin() -> bool:
	var info: Dictionary = GameManager.skill_db.get("putar", {})
	if not GameManager.has_skill("putar") or _spin_cooldown_left > 0.0:
		return false
	if not GameManager.use_stamina(float(info.get("stamina", 30))):
		return false
	_spin_cooldown_left = float(info.get("cooldown", 4.0))
	state = State.ATTACK
	_attack_style = "spin"
	_attack_kind = ""
	velocity = Vector2.ZERO
	hitbox.set_deferred("monitoring", false)
	_play("atk", true)
	sprite.speed_scale = 1.0
	_play_weapon_anim("spin", String(GameManager.equipment.get("weapon", "")), ATTACK_BASE_TIME)
	AudioManager.play_sfx("skill_spesial")
	return true


func _spin_damage() -> void:
	var info: Dictionary = GameManager.skill_db.get("putar", {})
	var radius: float = float(info.get("radius", 56))
	var dmg: int = roundi(float(GameManager.get_attack_damage()) * float(info.get("damage_x", 1.5)))
	var center: Vector2 = global_position + BODY_CENTER
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en and en.has_method("take_hit") and en.global_position.distance_to(global_position) <= radius + 12.0:
			en.take_hit(dmg, center)
	_ring_effect(radius)


## Lingkaran putih yang membesar lalu memudar (efek visual Serangan Putar).
func _ring_effect(radius: float, offset: Vector2 = Vector2.ZERO) -> void:
	var ring: Line2D = Line2D.new()
	var pts: PackedVector2Array = PackedVector2Array()
	for i in range(33):
		pts.append(Vector2.from_angle(TAU * i / 32.0) * radius)
	ring.points = pts
	ring.width = 3.0
	ring.default_color = Color(1, 0.95, 0.7)
	ring.position = BODY_CENTER + offset
	ring.scale = Vector2(0.3, 0.3)
	add_child(ring)
	var tw: Tween = create_tween().set_parallel(true)
	tw.tween_property(ring, "scale", Vector2.ONE, 0.25)
	tw.tween_property(ring, "modulate:a", 0.0, 0.25)
	tw.chain().tween_callback(ring.queue_free)


## Dash Tebas (L): menerjang ke depan, kebal, melukai musuh yang dilewati.
func _start_skill_dash(input_dir: Vector2) -> bool:
	var info: Dictionary = GameManager.skill_db.get("dash", {})
	if not GameManager.has_skill("dash") or _dash_cooldown_left > 0.0:
		return false
	if not GameManager.use_stamina(float(info.get("stamina", 25))):
		return false
	_dash_cooldown_left = float(info.get("cooldown", 3.0))
	if input_dir != Vector2.ZERO:
		_update_facing(input_dir)
	_dodge_vec = facing_vec
	_dash_speed = 320.0
	_dodge_left = float(info.get("jarak", 120)) / _dash_speed
	_dash_damage = roundi(float(GameManager.get_attack_damage()) * float(info.get("damage_x", 1.2)))
	_dash_hits.clear()
	_skill_dash = true
	state = State.DODGE
	set_collision_mask_value(3, false)  # tembus musuh selama dash
	sprite.modulate = Color(0.7, 0.9, 1.0, 0.7)
	_play("run", true)
	AudioManager.play_sfx("skill_spesial")
	return true


func _dash_damage_step() -> void:
	for e in get_tree().get_nodes_in_group("enemy"):
		var en: Node2D = e as Node2D
		if en and en.has_method("take_hit") and not (en in _dash_hits) and en.global_position.distance_to(global_position) <= 26.0:
			_dash_hits.append(en)
			en.take_hit(_dash_damage, global_position)


# ---------------------------------------------------------------- Terkena serangan

func _on_hurtbox_area_entered(area: Area2D) -> void:
	if area.has_meta("damage"):
		take_hit(int(area.get_meta("damage")), area.global_position)


## Dipanggil musuh/proyektil. Diabaikan saat dodge (i-frame), kedip setelah kena, atau mati.
func take_hit(damage: int, from_pos: Vector2) -> void:
	if is_invulnerable():
		return
	GameManager.take_damage(damage)
	if state == State.DEAD:  # player_died sudah memicu _die()
		return
	AudioManager.play_sfx("kena_hit")
	hitbox.set_deferred("monitoring", false)
	_hide_weapon()
	state = State.HIT
	_knockback_left = knockback_time
	_knockback_vec = (global_position - from_pos).normalized()
	_invulnerable_left = hit_invulnerable_time
	_start_blink(hit_invulnerable_time)
	_play("hit", true)


func _start_blink(duration: float) -> void:
	if _blink_tween:
		_blink_tween.kill()
	_blink_tween = create_tween().set_loops(maxi(1, int(duration / 0.2)))
	_blink_tween.tween_property(sprite, "modulate:a", 0.3, 0.1)
	_blink_tween.tween_property(sprite, "modulate:a", 1.0, 0.1)
	_blink_tween.finished.connect(func() -> void: sprite.modulate.a = 1.0)


# ---------------------------------------------------------------- Mati

func _die() -> void:
	if state == State.DEAD:
		return
	state = State.DEAD
	velocity = Vector2.ZERO
	hitbox.set_deferred("monitoring", false)
	_hide_weapon()
	if _blink_tween:
		_blink_tween.kill()
	sprite.modulate.a = 1.0
	_play("death", true)
	AudioManager.play_sfx("death")
	died.emit()


func _on_animation_finished() -> void:
	match state:
		State.ATTACK:
			hitbox.set_deferred("monitoring", false)
			_hide_weapon()
			state = State.NORMAL
		State.HIT:
			state = State.NORMAL
		State.DEAD:
			death_finished.emit()


## Klik pada tombol UI (mis. Heal di HUD) tidak boleh ikut menyerang.
func _mouse_over_button() -> bool:
	return get_viewport().gui_get_hovered_control() is BaseButton
