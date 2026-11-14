extends Node2D
## Event serangan (Ch1: Goblin menyerbu Dusun Larik). Mengawasi musuh di Objects yang namanya diawali `enemy_prefix`;
## saat semuanya mati, flag cerita `flag` disetel (langkah Quest Awal "usir Goblin"). Saat Raka pertama kali mendekat,
## tampil teks peringatan. Goblin event tidak hidup lagi saat istirahat di Bonfire (GameManager.reset_enemy_kills).

@export var enemy_prefix: String = "GoblinEvent"
@export var flag: String = "ch1_goblin_usir"
@export var announce_text: String = "Goblin menyerbu Dusun Larik!"
@export var announce_radius: float = 300.0
@export var done_text: String = "Goblin berhasil diusir!"

var _alive: Dictionary = {}     # Enemy -> true
var _announced: bool = false


func _ready() -> void:
	_setup.call_deferred()   # tunggu musuh yang sudah mati (tersimpan) menghapus dirinya


func _setup() -> void:
	if GameManager.has_story_flag(flag):
		return
	var objects: Node = get_parent().get_node_or_null("Objects")
	if objects == null:
		return
	for n in objects.get_children():
		if n is Enemy and String(n.name).begins_with(enemy_prefix) and not n.is_queued_for_deletion():
			_alive[n] = true
			(n as Enemy).died.connect(_on_enemy_died)
	if _alive.is_empty():
		GameManager.set_story_flag(flag)
		return
	_make_announce_area()


func _on_enemy_died(enemy: Enemy) -> void:
	_alive.erase(enemy)
	if _alive.is_empty() and not GameManager.has_story_flag(flag):
		var player: Node2D = get_tree().get_first_node_in_group("player") as Node2D
		if player != null:
			FloatingText.spawn(get_parent(), player.global_position + Vector2(0, -56), done_text, Color(0.6, 1, 0.6), 2.6)
		AudioManager.play_sfx("jingle_quest_selesai")
		GameManager.set_story_flag(flag)


## Area di sekitar posisi node ini: teks peringatan saat Raka masuk (sekali per sesi).
func _make_announce_area() -> void:
	var a: Area2D = Area2D.new()
	a.collision_layer = 0
	a.collision_mask = 2
	var s: CollisionShape2D = CollisionShape2D.new()
	var c: CircleShape2D = CircleShape2D.new()
	c.radius = announce_radius
	s.shape = c
	a.add_child(s)
	add_child(a)
	a.body_entered.connect(func(b: Node2D) -> void:
		if _announced or not b.is_in_group("player") or GameManager.has_story_flag(flag):
			return
		_announced = true
		AudioManager.play_sfx("peringatan_boss")
		FloatingText.spawn(get_parent(), b.global_position + Vector2(0, -56), announce_text, Color(1, 0.55, 0.4), 3.0))
