extends Node
## AudioManager: bus Master/Music/SFX, musik dengan crossfade, SFX berpool, volume tersimpan.

const MUSIC_BUS := "Music"
const SFX_BUS := "SFX"
const MUSIC_DIR := "res://assets/audio/music/"
const SFX_DIR := "res://assets/audio/sfx/"
const SETTINGS_PATH := "user://settings.cfg"
const SFX_POOL_SIZE := 8
const SILENT_DB := -60.0

var music_volume: float = 0.8   # linear 0..1
var sfx_volume: float = 1.0

var current_music: String = ""
var _gesture_done: bool = false

var _music_players: Array[AudioStreamPlayer] = []
var _active_music: int = 0
var _music_tween: Tween
var _sfx_players: Array[AudioStreamPlayer] = []
var _sfx_cache: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_buses()
	for i in 2:
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.bus = MUSIC_BUS
		p.volume_db = SILENT_DB
		add_child(p)
		_music_players.append(p)
	for i in SFX_POOL_SIZE:
		var p: AudioStreamPlayer = AudioStreamPlayer.new()
		p.bus = SFX_BUS
		add_child(p)
		_sfx_players.append(p)
	_load_settings()
	_apply_volumes()


func _setup_buses() -> void:
	for bus_name in [MUSIC_BUS, SFX_BUS]:
		if AudioServer.get_bus_index(bus_name) == -1:
			AudioServer.add_bus()
			var idx: int = AudioServer.bus_count - 1
			AudioServer.set_bus_name(idx, bus_name)
			AudioServer.set_bus_send(idx, "Master")


# ---------------------------------------------------------------- Web: audio baru boleh bunyi setelah interaksi pertama

## Browser menahan audio sampai ada klik/tombol pertama. Setelah itu pastikan musik yang diminta benar-benar berbunyi.
func _input(event: InputEvent) -> void:
	if _gesture_done:
		return
	if (event is InputEventMouseButton and event.pressed) or (event is InputEventKey and event.pressed) or (event is InputEventScreenTouch and event.pressed):
		_gesture_done = true
		if current_music != "" and not _music_players[_active_music].playing:
			var m: String = current_music
			current_music = ""
			play_music(m, 0.5)


# ---------------------------------------------------------------- Musik

## Memutar musik <nama>.ogg dari assets/audio/music dengan crossfade.
func play_music(music_name: String, fade_time: float = 1.0) -> void:
	if music_name == current_music and _music_players[_active_music].playing:
		return
	var path: String = MUSIC_DIR + music_name + ".ogg"
	if not ResourceLoader.exists(path):
		push_warning("Musik tidak ditemukan: %s" % path)
		return
	var stream: AudioStream = load(path)
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	current_music = music_name

	var old_player: AudioStreamPlayer = _music_players[_active_music]
	_active_music = 1 - _active_music
	var new_player: AudioStreamPlayer = _music_players[_active_music]
	new_player.stream = stream
	new_player.volume_db = SILENT_DB
	new_player.play()

	if _music_tween:
		_music_tween.kill()
	_music_tween = create_tween().set_parallel(true)
	_music_tween.tween_property(new_player, "volume_db", 0.0, fade_time)
	_music_tween.tween_property(old_player, "volume_db", SILENT_DB, fade_time)
	_music_tween.chain().tween_callback(old_player.stop)


func stop_music(fade_time: float = 1.0) -> void:
	current_music = ""
	if _music_tween:
		_music_tween.kill()
	_music_tween = create_tween().set_parallel(true)
	for p in _music_players:
		_music_tween.tween_property(p, "volume_db", SILENT_DB, fade_time)
	_music_tween.chain().tween_callback(_stop_all_music)


func _stop_all_music() -> void:
	for p in _music_players:
		p.stop()


# ---------------------------------------------------------------- SFX

## Memutar efek suara <nama>.wav (atau .ogg) dari assets/audio/sfx.
## Bunyi menu lama terlalu panjang/ramai (menu_pilih 2 detik); dialihkan ke klik pendek sederhana.
const SFX_ALIAS := {"menu_pilih": "klik_ui", "menu_batal": "klik_batal"}


func play_sfx(sfx_name: String, pitch_variation: float = 0.0) -> void:
	var stream: AudioStream = _get_sfx(SFX_ALIAS.get(sfx_name, sfx_name))
	if stream == null:
		return
	var player: AudioStreamPlayer = _free_sfx_player()
	player.stream = stream
	player.pitch_scale = 1.0 + randf_range(-pitch_variation, pitch_variation)
	player.play()


func _get_sfx(sfx_name: String) -> AudioStream:
	if _sfx_cache.has(sfx_name):
		return _sfx_cache[sfx_name]
	var stream: AudioStream = null
	for ext in [".wav", ".ogg"]:
		var path: String = SFX_DIR + sfx_name + ext
		if ResourceLoader.exists(path):
			stream = load(path)
			break
	if stream == null:
		push_warning("SFX tidak ditemukan: %s" % sfx_name)
	_sfx_cache[sfx_name] = stream
	return stream


func _free_sfx_player() -> AudioStreamPlayer:
	for p in _sfx_players:
		if not p.playing:
			return p
	return _sfx_players[0]  # semua sibuk: pakai yang pertama


# ---------------------------------------------------------------- Volume

func set_music_volume(value: float) -> void:
	music_volume = clampf(value, 0.0, 1.0)
	_apply_volumes()
	_save_settings()


func set_sfx_volume(value: float) -> void:
	sfx_volume = clampf(value, 0.0, 1.0)
	_apply_volumes()
	_save_settings()


func _apply_volumes() -> void:
	_set_bus_linear(MUSIC_BUS, music_volume)
	_set_bus_linear(SFX_BUS, sfx_volume)


func _set_bus_linear(bus_name: String, linear: float) -> void:
	var idx: int = AudioServer.get_bus_index(bus_name)
	AudioServer.set_bus_mute(idx, linear <= 0.001)
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(linear, 0.001)))


func _load_settings() -> void:
	var cfg: ConfigFile = ConfigFile.new()
	if cfg.load(SETTINGS_PATH) == OK:
		music_volume = float(cfg.get_value("audio", "music", music_volume))
		sfx_volume = float(cfg.get_value("audio", "sfx", sfx_volume))


func _save_settings() -> void:
	var cfg: ConfigFile = ConfigFile.new()
	cfg.set_value("audio", "music", music_volume)
	cfg.set_value("audio", "sfx", sfx_volume)
	cfg.save(SETTINGS_PATH)
