class_name QueueCustomers
extends PuzzleBase
## Puzzle Chapter 3 – Queue (FIFO). Pelanggan datang satu per satu dan masuk ke BELAKANG antrean (enqueue).
## Layani dengan memilih hidangan sesuai pesanan lalu klik pelanggan PALING DEPAN (dequeue). 6 pelanggan.

const DISHES: Array[String] = ["Roti", "Sup", "Teh", "Ikan"]
const DISH_COLORS: Array[Color] = [Color(0.85, 0.65, 0.35), Color(0.9, 0.5, 0.35), Color(0.5, 0.75, 0.45), Color(0.45, 0.65, 0.85)]
const TOTAL := 6
const START_COUNT := 3
const ARRIVE_INTERVAL := 3.0

var customers: Array[Dictionary] = []   # {name, dish}
var queue: Array[int] = []              # indeks pelanggan di antrean (depan = indeks 0)
var arrived: int = 0
var served: int = 0
var selected_dish: int = -1
var customer_buttons: Dictionary = {}   # id pelanggan -> Button
var dish_buttons: Array[Button] = []
var _queue_box: Control
var _counter: Label
var _timer: Timer


func _init() -> void:
	puzzle_title = "Layani Pelanggan"
	instruction = "Antrean ini adalah QUEUE (FIFO: yang datang lebih dulu dilayani lebih dulu). Pilih hidangan sesuai pesanan, lalu klik pelanggan yang tepat."


func _build_content() -> void:
	var front: Label = make_label("DEPAN (dilayani dulu)", 10, BAD)
	front.position = Vector2(4, 0)
	content.add_child(front)
	var back: Label = make_label("BELAKANG (pendatang baru)", 10, GOOD)
	back.position = Vector2(380, 0)
	content.add_child(back)
	_queue_box = Control.new()
	_queue_box.position = Vector2(0, 16)
	content.add_child(_queue_box)
	var prompt: Label = make_label("Pilih hidangan, lalu klik pelanggan:", 11, INK)
	prompt.position = Vector2(4, 100)
	content.add_child(prompt)
	for i in DISHES.size():
		var b: Button = make_button(DISHES[i], Vector2(100, 34), DISH_COLORS[i])
		b.position = Vector2(4 + i * 108, 120)
		b.pressed.connect(_on_dish_pressed.bind(i))
		content.add_child(b)
		dish_buttons.append(b)
	_counter = make_label("", 12, INK)
	_counter.position = Vector2(4, 168)
	content.add_child(_counter)
	_timer = Timer.new()
	_timer.wait_time = ARRIVE_INTERVAL
	_timer.one_shot = false
	_timer.timeout.connect(_arrive)
	add_child(_timer)


func _reset() -> void:
	customers.clear()
	for i in TOTAL:
		customers.append({"name": String.chr(65 + i), "dish": randi() % DISHES.size()})
	queue.clear()
	arrived = 0
	served = 0
	selected_dish = -1
	for i in START_COUNT:
		queue.append(arrived)
		arrived += 1
	_select_dish_visual()
	_refresh()
	_timer.start()
	report_progress(0, TOTAL)


func _on_closed() -> void:
	_timer.stop()


## Pelanggan baru bergabung di belakang antrean (enqueue).
func _arrive() -> void:
	if arrived >= TOTAL or is_solved:
		_timer.stop()
		return
	queue.append(arrived)
	show_message("Pelanggan %s bergabung di BELAKANG antrean (enqueue)." % customers[arrived]["name"], true)
	arrived += 1
	if arrived >= TOTAL:
		_timer.stop()
	_refresh()


func _refresh() -> void:
	for child in _queue_box.get_children():
		child.queue_free()
		_queue_box.remove_child(child)
	customer_buttons.clear()
	for pos in queue.size():
		var id: int = queue[pos]
		var c: Dictionary = customers[id]
		var b: Button = make_button("%s\n%s" % [c["name"], DISHES[c["dish"]]], Vector2(84, 60), Color(0.9, 0.8, 0.65) if pos > 0 else Color(1.0, 0.9, 0.5))
		b.position = Vector2(4 + pos * 92, 0)
		b.pressed.connect(_on_customer_pressed.bind(id))
		_queue_box.add_child(b)
		customer_buttons[id] = b
	_counter.text = "Dilayani: %d / %d      Menunggu: %d" % [served, TOTAL, queue.size()]


func _on_dish_pressed(dish: int) -> void:
	selected_dish = dish
	_select_dish_visual()
	show_message("Hidangan %s dipilih. Klik pelanggan yang memesannya." % DISHES[dish], true)


func _select_dish_visual() -> void:
	for i in dish_buttons.size():
		dish_buttons[i].modulate = Color(1, 1, 1) if i == selected_dish else Color(0.8, 0.8, 0.8)


func _on_customer_pressed(id: int) -> void:
	if is_solved:
		return
	if selected_dish < 0:
		show_message("Pilih hidangan dulu.")
		return
	if id != queue[0]:
		show_message("Jangan menyerobot! Antrean dilayani sesuai urutan datang: yang paling DEPAN dulu (FIFO).")
		return
	var c: Dictionary = customers[id]
	if int(c["dish"]) != selected_dish:
		show_message("Pesanan %s adalah %s, bukan %s." % [c["name"], DISHES[c["dish"]], DISHES[selected_dish]])
		return
	queue.pop_front()   # dequeue: keluar dari DEPAN
	served += 1
	selected_dish = -1
	_select_dish_visual()
	_refresh()
	report_progress(served, TOTAL)
	show_message("Pelanggan %s dilayani (dequeue)." % c["name"], true)
	if served == TOTAL:
		_timer.stop()
		complete_puzzle()
