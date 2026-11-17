extends Node
## Uji keseimbangan (headless): pertahanan memotong damage secara persen (bukan flat sampai tinggal 1), serangan & HP
## musuh naik per chapter (data/difficulty.json), dan jangkauan bola sihir tongkat mengikuti "range" senjata.
##   godot --headless --fixed-fps 60 --path . res://tools/test_balance.tscn

var fails: int = 0

## Perlengkapan khas pemain di tiap chapter (hadiah quest + toko yang wajar).
const GEAR := {
	1: {"weapon": "pedang_kayu", "helm": "helm_kulit"},
	2: {"weapon": "pedang_besi", "helm": "helm_kulit", "shield": "perisai_kayu"},
	3: {"weapon": "pedang_besi", "helm": "helm_kulit", "shield": "perisai_kayu", "armor": "zirah_rantai"},
	4: {"weapon": "tongkat_sihir", "helm": "helm_rantai", "shield": "perisai_besi", "armor": "zirah_salju"},
	5: {"weapon": "tongkat_sihir_plus", "helm": "helm_baja", "shield": "perisai_legendaris", "armor": "armor_legendaris", "accessory": "cincin_penjaga"},
}


func check(cond: bool, label: String) -> void:
	if not cond:
		fails += 1
	print("  ", "OK    " if cond else "GAGAL ", label)


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


## Damage yang benar-benar diterima Raka dari pukulan bernilai `raw` di chapter `ch`.
func taken(raw: int, ch: int) -> int:
	var scaled: int = maxi(1, roundi(float(raw) * GameManager.enemy_mult(ch, "enemy_damage")))
	return GameManager.reduce_by_defense(scaled)


func _ready() -> void:
	GameManager.reset_state()
	var prev_orc: int = 0
	var prev_king: int = 0
	for ch in range(1, 6):
		for slot in GameManager.SLOTS:
			GameManager.equipment[slot] = GEAR[ch].get(slot, "")
		var d: int = GameManager.get_defense()
		var orc: int = taken(8, ch)
		var warrior: int = taken(13, ch)
		var boss: int = taken(10, ch)
		var orc_hp: int = roundi(24 * GameManager.enemy_mult(ch, "enemy_hp"))
		print("Ch%d pertahanan %2d | Orc %2d -> %2d HP | Orc Warrior 13 -> %2d | serangan boss 10 -> %2d | HP Orc %d" % [
			ch, d, roundi(8 * GameManager.enemy_mult(ch, "enemy_damage")), orc, warrior, boss, orc_hp])
		check(orc > 1 and warrior > 1, "Ch%d: armor tidak menghapus damage sampai 1" % ch)
		check(orc >= prev_orc, "Ch%d: pukulan Orc tidak lebih lemah dari chapter sebelumnya" % ch)
		check(boss >= prev_king, "Ch%d: serangan boss tidak lebih lemah dari chapter sebelumnya" % ch)
		prev_orc = orc
		prev_king = boss
	# pertahanan tetap berguna: dengan armor lebih kecil dari tanpa armor
	for slot in GameManager.SLOTS:
		GameManager.equipment[slot] = ""
	var naked: int = taken(20, 5)
	for slot in GameManager.SLOTS:
		GameManager.equipment[slot] = GEAR[5].get(slot, "")
	check(taken(20, 5) < naked, "armor tetap mengurangi damage (%d < %d)" % [taken(20, 5), naked])

	# tongkat: damage & jangkauan diturunkan, bola sihir mengikuti range
	var ts: Dictionary = GameManager.get_item("tongkat_sihir")
	check(int(ts["damage"]) <= 10 and int(ts["range"]) <= 90, "Tongkat Sihir: damage %d, jangkauan %d px" % [ts["damage"], ts["range"]])
	var bolt: MagicBolt = MagicBolt.launch(self, Vector2.ZERO, Vector2.RIGHT, 5, float(ts["range"]))
	check(absf(bolt.lifetime * bolt.speed - float(ts["range"])) < 1.0, "bola sihir terbang %.0f px (= range)" % (bolt.lifetime * bolt.speed))
	bolt.queue_free()

	# HP musuh di scene asli: Ch1 tetap, Ch5 lebih tebal
	var hp_by_ch: Dictionary = {}
	for pair in [[1, "res://scenes/world/Ch1_HutanIndeks.tscn"], [5, "res://scenes/world/Ch5_PohonDunia.tscn"]]:
		var r: Node = (load(pair[1]) as PackedScene).instantiate()
		add_child(r)
		await frames(3)
		for e: Node in get_tree().get_nodes_in_group("enemy"):
			if e is Enemy and (e as Enemy).enemy_id == "orc" and r.is_ancestor_of(e):
				hp_by_ch[pair[0]] = (e as Enemy).max_hp
				break
		r.queue_free()
		await frames(3)
	print("HP Orc di scene: ", hp_by_ch)
	check(hp_by_ch.get(1, 0) == 24, "Orc Ch1 tetap 24 HP")
	check(hp_by_ch.get(5, 0) > 24, "Orc Ch5 lebih tebal (%d HP)" % hp_by_ch.get(5, 0))
	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
