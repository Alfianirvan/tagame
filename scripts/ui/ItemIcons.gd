class_name ItemIcons
extends RefCounted
## Pencari ikon item: ikon khusus di assets/items/icons/<id>.png, atau ikon slot bila armor.

const ICON_DIR := "res://assets/items/icons/"
const SLOT_ICON := {
	"helm": "res://assets/ui/icons/helm.png",
	"armor": "res://assets/ui/icons/armor.png",
	"shield": "res://assets/ui/icons/perisai.png",
	"accessory": "res://assets/ui/icons/aksesori_cincin.png",
	"weapon": "res://assets/items/icons/pedang_kayu.png",
}

static var _cache: Dictionary = {}


static func get_icon(id: String) -> Texture2D:
	if _cache.has(id):
		return _cache[id]
	var tex: Texture2D = null
	var path: String = ICON_DIR + id + ".png"
	if ResourceLoader.exists(path):
		tex = load(path)
	elif GameManager.get_item(id).get("type", "") == "note":
		tex = load(ICON_DIR + "catatan.png")   # semua catatan materi memakai ikon kertas
	else:
		var slot: String = GameManager.get_slot_for(id)
		if SLOT_ICON.has(slot):
			tex = load(SLOT_ICON[slot])
	_cache[id] = tex
	return tex
