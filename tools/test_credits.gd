extends Node
## Uji credit scene (headless): data opening tiap chapter & ending ada, OpeningCredits menampilkan kartu judul + baris cerita
## dan memancarkan finished, EndCredits (epilog -> credit bergulir) memuat nama tim & dosen lalu selesai.
## Jalankan: godot --headless --path . res://tools/test_credits.tscn
const OC := preload("res://scripts/ui/OpeningCredits.gd")   # dipakai lewat preload (tidak bergantung cache class_name editor)
const EC := preload("res://scripts/ui/EndCredits.gd")

var fails: int = 0


func check(cond: bool, what: String) -> void:
	if cond:
		print("  OK   ", what)
	else:
		fails += 1
		print("  GAGAL ", what)


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _ready() -> void:
	for key in ["opening_ch1", "opening_ch2", "opening_ch3", "opening_ch4", "opening_ch5", "ending"]:
		check(OC.has_scene(key), "data credit '%s' ada" % key)
		var oc: OC = OC.new()
		oc.credits_key = key
		var done: Array = [false]
		oc.finished.connect(func() -> void: done[0] = true)
		add_child(oc)
		await frames(3)
		check(oc._title_label.text != "" and oc._lines.size() >= 3, "'%s': kartu judul '%s' + %d baris" % [key, oc._title_label.text, oc._lines.size()])
		oc._finish()
		await get_tree().create_timer(0.9).timeout
		check(done[0], "'%s': finished terpancar setelah dilewati" % key)
	# ending credit: epilog dilewati -> credit bergulir berisi tim & dosen -> selesai
	var ec: EC = EC.new()
	var ended: Array = [false]
	ec.finished.connect(func() -> void: ended[0] = true)
	add_child(ec)
	await frames(3)
	var epilog: OC = null
	for c in ec.get_children():
		if c is OC:
			epilog = c
	check(epilog != null and epilog.credits_key == "ending", "ending: epilog tampil lebih dulu")
	epilog._finish()
	await get_tree().create_timer(0.9).timeout
	await frames(3)
	check(ec._rolling and ec._roll != null, "ending: credit bergulir dimulai setelah epilog")
	var texts: Array[String] = []
	for l in ec._roll.get_children():
		if l is Label:
			texts.append((l as Label).text)
	var team: Dictionary = OC.load_data().get("team", {})
	var first_member: String = String(team.get("members", [{}])[0].get("name", "?"))
	check(texts.any(func(t: String) -> bool: return t.begins_with(first_member)), "ending: nama tim tercantum (%s)" % first_member)
	check(texts.has(String(team.get("lecturer", {}).get("name", "?"))), "ending: dosen pengampu tercantum")
	check(texts.has("Terima kasih sudah bermain!"), "ending: penutup 'Terima kasih sudah bermain!'")
	ec._finish()
	await get_tree().create_timer(1.1).timeout
	check(ended[0], "ending: finished terpancar")
	print("HASIL: ", "SEMUA OK" if fails == 0 else "%d GAGAL" % fails)
	get_tree().quit(1 if fails > 0 else 0)
