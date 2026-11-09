extends Node
## SaveManager: simpan/muat progres ke user://save.json (di Web tersimpan di penyimpanan browser).

signal game_saved
signal game_loaded

const SAVE_PATH := "user://save.json"
const SAVE_VERSION := 1


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


## Menyimpan state GameManager + QuestManager. Mengembalikan true bila berhasil.
func save_game() -> bool:
	var data: Dictionary = {
		"version": SAVE_VERSION,
		"game": GameManager.get_save_data(),
		"quests": QuestManager.get_save_data(),
	}
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		push_error("Gagal menulis save: %s" % error_string(FileAccess.get_open_error()))
		return false
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	game_saved.emit()
	return true


## Memuat save ke state game. Tidak pindah scene; pemanggil memakai GameManager.checkpoint_scene.
func load_game() -> bool:
	if not has_save():
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if not (parsed is Dictionary) or not (parsed.get("game") is Dictionary):
		push_error("File save rusak.")
		return false
	GameManager.apply_save_data(parsed["game"])
	QuestManager.apply_save_data(parsed.get("quests", {}))
	game_loaded.emit()
	return true


## Mulai game baru: reset semua state (file save lama baru tertimpa saat save berikutnya).
func new_game() -> void:
	GameManager.reset_state()
	QuestManager.reset_state()
	DialogManager.end_dialog()


func delete_save() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
