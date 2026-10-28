extends Node
## Фасад Яндекс Игр. Вся игра вызывает только этот API.
## В вебе работает через JS-мост window.CC из web/shell.html (Yandex Games SDK v2).
## В редакторе и без SDK — безопасные заглушки: реклама «показывается» мгновенно, облака нет.
## Учтено для модерации:
##  * пауза и тишина при рекламе, покупке, сворачивании вкладки и по событиям game_api_pause/resume;
##  * LoadingAPI.ready() после первого экрана (он же убирает HTML-загрузчик);
##  * GameplayAPI.start/stop вокруг активного геймплея;
##  * язык из environment.i18n.lang.

signal ad_started
signal ad_finished
signal rewarded_result(tag: StringName, success: bool)
signal cloud_loaded(data: Dictionary)
signal pause_changed(paused: bool)
signal sdk_initialized
## Куплен товар. Потребляемые (валюта) списываются после этого сигнала — выдай награду и сохрани.
signal product_granted(id: String)
signal purchases_changed

## Товары каталога Яндекса (создать в консоли с такими же id).
const PRODUCTS: Dictionary = {
    "no_ads": {"consumable": false},
    "starter_pack": {"consumable": false},
    "wax_small": {"consumable": true},
    "wax_medium": {"consumable": true},
    "wax_large": {"consumable": true},
}
## Таблицы лидеров (создать в консоли с такими же техническими именами).
const LB_BEST_NIGHT: String = "bestnight"
const LB_DAILY: String = "dailynight"
const LB_ENDLESS: String = "endless"
## Значения по умолчанию для удалённой конфигурации (getFlags). Всё строки.
const DEFAULT_FLAGS: Dictionary = {
    "first_ad_night": "2",
    "ad_every_nights": "1",
    "hp_mult": "1.0",
    "cash_mult": "1.0",
}
const SUPPORTED_LANGS: Array[String] = ["ru", "en"]
const RU_LANGS: Array[String] = ["ru", "be", "kk", "uk", "uz"]

@export var pause_on_focus_loss: bool = true

var sdk_ok: bool = false
## mobile / tablet / desktop / tv
var device: String = "desktop"
var lang: String = ""
var tld: String = ""
var player_authorized: bool = false
var player_name: String = ""
var flags: Dictionary = DEFAULT_FLAGS.duplicate()
var owned: Dictionary = {}
var catalog: Array = []

var _pause_reasons: Dictionary = {}
var _gameplay_active: bool = false
var _initialized: bool = false
var _ad_busy: bool = false
var _js = null
var _cb_result = null
var _cb_event = null
var _req_id: int = 0
var _server_offset: float = 0.0

signal _js_reply(id: int, res: Dictionary)

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    if is_web():
        _js = JavaScriptBridge.get_interface("CC")
        if _js != null:
            _cb_result = JavaScriptBridge.create_callback(_on_js_result)
            _cb_event = JavaScriptBridge.create_callback(_on_js_event)
            _js.setHandlers(_cb_result, _cb_event)

func is_web() -> bool:
    return OS.has_feature("web")

func has_bridge() -> bool:
    return _js != null

func is_mobile() -> bool:
    return device == "mobile" or device == "tablet"

# ---------- инициализация ----------
## Вызвать один раз до первого экрана (await). Ждёт SDK, язык, облако (не дольше ~2 с), флаги.
func init_sdk() -> void:
    if _initialized:
        return
    _initialized = true
    if has_bridge():
        var r: Dictionary = await _request("init")
        var d: Dictionary = r.get("data", {})
        sdk_ok = bool(d.get("sdk", false))
        lang = str(d.get("lang", ""))
        device = str(d.get("device", "desktop"))
        tld = str(d.get("tld", ""))
        _log("init sdk=%s lang=%s device=%s err=%s" % [sdk_ok, lang, device, d.get("err")])
        if sdk_ok:
            _sync_server_time()
            _load_flags()
            _refresh_player()
            refresh_purchases()
            await _load_cloud_with_timeout(2.0)
    else:
        if OS.has_feature("mobile") or DisplayServer.is_touchscreen_available():
            device = "mobile"
    sdk_initialized.emit()

# ---------- язык ----------
func get_lang() -> String:
    var l: String = lang if lang != "" else OS.get_locale_language()
    if l in RU_LANGS:
        return "ru"
    if l in SUPPORTED_LANGS:
        return l
    return "en" if l != "" else "ru"

# ---------- жизненный цикл ----------
func game_ready() -> void:
    _send("loadingReady")
    _log("LoadingAPI.ready")

func gameplay_start() -> void:
    if _gameplay_active:
        return
    _gameplay_active = true
    _send("gameplay", {"on": true})
    _log("GameplayAPI.start")

func gameplay_stop() -> void:
    if not _gameplay_active:
        return
    _gameplay_active = false
    _send("gameplay", {"on": false})
    _log("GameplayAPI.stop")

# ---------- реклама ----------
func no_ads() -> bool:
    return owned.has("no_ads") or owned.has("starter_pack")

## Межстраничная реклама (только в паузах между экранами). await → была ли показана.
func show_fullscreen() -> bool:
    if _ad_busy or no_ads():
        return false
    _ad_busy = true
    _begin_ad()
    var shown: bool = false
    if sdk_ok:
        var r: Dictionary = await _request("fullscreen")
        shown = bool(r.get("data", {}).get("shown", false))
    else:
        await get_tree().create_timer(0.05, true, false, true).timeout
    _end_ad()
    _ad_busy = false
    return shown

## Реклама за награду. Результат придёт в rewarded_result(tag, success).
func show_rewarded(tag: StringName) -> void:
    if _ad_busy:
        rewarded_result.emit(tag, false)
        return
    _ad_busy = true
    _begin_ad()
    var ok: bool = false
    if sdk_ok:
        var r: Dictionary = await _request("rewarded")
        ok = bool(r.get("data", {}).get("rewarded", false))
    else:
        await get_tree().create_timer(0.4, true, false, true).timeout
        ok = true
    _end_ad()
    _ad_busy = false
    _log("rewarded %s -> %s" % [tag, ok])
    rewarded_result.emit(tag, ok)

func set_banner(on: bool) -> void:
    if sdk_ok:
        _send("banner", {"on": on})

func _begin_ad() -> void:
    set_paused(&"ad", true)
    ad_started.emit()

func _end_ad() -> void:
    set_paused(&"ad", false)
    ad_finished.emit()

# ---------- облачные сохранения ----------
func save_cloud(data: Dictionary, flush: bool = false) -> void:
    if sdk_ok:
        _send("setData", {"data": data, "flush": flush})

func load_cloud() -> void:
    if not sdk_ok:
        return
    var r: Dictionary = await _request("getData")
    if r.get("ok", false):
        var d: Variant = r.get("data", {}).get("data", {})
        if d is Dictionary and not (d as Dictionary).is_empty():
            cloud_loaded.emit(d)

func _load_cloud_with_timeout(limit: float) -> void:
    var state: Dictionary = {"done": false}
    var job: Callable = func() -> void:
        await load_cloud()
        state["done"] = true
    job.call()
    var t: float = 0.0
    while not state["done"] and t < limit:
        await get_tree().process_frame
        t += get_process_delta_time()

# ---------- игрок ----------
func _refresh_player() -> void:
    var r: Dictionary = await _request("player")
    if r.get("ok", false):
        player_authorized = bool(r["data"].get("authorized", false))
        player_name = str(r["data"].get("name", ""))

## Окно входа Яндекса (нужно для лидербордов у неавторизованных). await → вошёл ли.
func open_auth() -> bool:
    if not sdk_ok:
        return false
    set_paused(&"dialog", true)
    await _request("auth")
    set_paused(&"dialog", false)
    await _refresh_player()
    return player_authorized

# ---------- лидерборды ----------
func leaderboard_set(board: String, score: int) -> void:
    if sdk_ok:
        _send("lbSet", {"name": board, "score": score})

## await → {"entries": [{rank, score, name}], "userRank": int}
func leaderboard_get(board: String, top: int = 10) -> Dictionary:
    if not sdk_ok:
        return {"entries": [], "userRank": 0}
    var r: Dictionary = await _request("lbGet", {"name": board, "top": top})
    return r.get("data", {}) if r.get("ok", false) else {"entries": [], "userRank": 0}

# ---------- покупки ----------
func is_owned(id: String) -> bool:
    return owned.has(id)

## await → массив товаров каталога {id, title, price, ...}
func get_catalog() -> Array:
    if not sdk_ok:
        return []
    if catalog.is_empty():
        var r: Dictionary = await _request("catalog")
        if r.get("ok", false):
            catalog = r["data"].get("items", [])
    return catalog

func catalog_price(id: String) -> String:
    for item in catalog:
        if str(item.get("id", "")) == id:
            return str(item.get("price", ""))
    return ""

## Купить товар. await → успех. Награда выдаётся через product_granted.
func purchase(id: String) -> bool:
    if not sdk_ok:
        if OS.is_debug_build():
            _grant(id, "")
            return true
        return false
    set_paused(&"purchase", true)
    var r: Dictionary = await _request("purchase", {"id": id})
    set_paused(&"purchase", false)
    var d: Dictionary = r.get("data", {})
    if r.get("ok", false) and bool(d.get("ok", false)):
        _grant(str(d.get("id", id)), str(d.get("token", "")))
        return true
    _log("purchase %s failed: %s" % [id, d.get("err", "")])
    return false

## Восстановить покупки (на старте): постоянные — в owned, неизрасходованные потребляемые — выдать.
func refresh_purchases() -> void:
    if not sdk_ok:
        return
    var r: Dictionary = await _request("purchases")
    if not r.get("ok", false):
        return
    for p in r["data"].get("items", []):
        _grant(str(p.get("id", "")), str(p.get("token", "")))
    purchases_changed.emit()

func _grant(id: String, token: String) -> void:
    if id == "":
        return
    var consumable: bool = bool(PRODUCTS.get(id, {}).get("consumable", false))
    if not consumable:
        owned[id] = true
    product_granted.emit(id)
    if consumable and token != "" and sdk_ok:
        _send("consume", {"token": token})
    purchases_changed.emit()

# ---------- удалённая конфигурация ----------
func flag(name: String, fallback: Variant = null) -> Variant:
    var v: Variant = flags.get(name, DEFAULT_FLAGS.get(name, fallback))
    if fallback is float:
        return float(v)
    if fallback is int:
        return int(v)
    return v

func _load_flags() -> void:
    var r: Dictionary = await _request("flags", {"defaults": DEFAULT_FLAGS})
    if r.get("ok", false):
        var f: Variant = r["data"].get("flags", {})
        if f is Dictionary:
            flags.merge(f, true)

# ---------- ярлык и отзыв ----------
func can_shortcut() -> bool:
    if not sdk_ok:
        return false
    var r: Dictionary = await _request("shortcutCan")
    return r.get("ok", false) and bool(r["data"].get("can", false))

func show_shortcut() -> bool:
    if not sdk_ok:
        return false
    set_paused(&"dialog", true)
    var r: Dictionary = await _request("shortcut")
    set_paused(&"dialog", false)
    return r.get("ok", false) and bool(r["data"].get("ok", false))

func can_review() -> bool:
    if not sdk_ok:
        return false
    var r: Dictionary = await _request("reviewCan")
    return r.get("ok", false) and bool(r["data"].get("can", false))

func request_review() -> bool:
    if not sdk_ok:
        return false
    set_paused(&"dialog", true)
    var r: Dictionary = await _request("review")
    set_paused(&"dialog", false)
    return r.get("ok", false) and bool(r["data"].get("ok", false))

# ---------- время и вибрация ----------
## Unix-время в секундах (серверное, если SDK доступен).
func now_unix() -> float:
    return Time.get_unix_time_from_system() + _server_offset

## Номер текущего дня (UTC) по серверному времени — для «Ночи дня» и ежедневных наград.
func day_index() -> int:
    return int(floor(now_unix() / 86400.0))

func _sync_server_time() -> void:
    var r: Dictionary = await _request("serverTime")
    if r.get("ok", false):
        _server_offset = float(r["data"].get("ms", 0.0)) / 1000.0 - Time.get_unix_time_from_system()

func vibrate(ms: int) -> void:
    if not bool(Save.data.get("vibration", true)):
        return
    if has_bridge():
        _send("vibrate", {"ms": ms})
    elif OS.has_feature("mobile"):
        Input.vibrate_handheld(ms)

# ---------- пауза ----------
func set_paused(reason: StringName, on: bool) -> void:
    if on:
        _pause_reasons[reason] = true
    else:
        _pause_reasons.erase(reason)
    var paused: bool = not _pause_reasons.is_empty()
    if get_tree().paused != paused:
        get_tree().paused = paused
        pause_changed.emit(paused)
    var audio: Node = get_node_or_null("/root/Audio")
    if audio:
        audio.set_muted(reason, on)

func is_paused_by(reason: StringName) -> bool:
    return _pause_reasons.has(reason)

func _notification(what: int) -> void:
    if not pause_on_focus_loss or not is_inside_tree():
        return
    match what:
        NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_APPLICATION_PAUSED:
            set_paused(&"focus", true)
            _flush_save()
        NOTIFICATION_APPLICATION_FOCUS_IN, NOTIFICATION_APPLICATION_RESUMED:
            set_paused(&"focus", false)

func _flush_save() -> void:
    var save: Node = get_node_or_null("/root/Save")
    if save and save.has_method("flush"):
        save.flush()

# ---------- JS-мост ----------
func _send(method: String, args: Dictionary = {}) -> void:
    if _js != null:
        _js.request(0, method, JSON.stringify(args))

func _request(method: String, args: Dictionary = {}) -> Dictionary:
    if _js == null:
        return {"ok": false, "data": {"err": "no_bridge"}}
    _req_id += 1
    var id: int = _req_id
    _js.request(id, method, JSON.stringify(args))
    var out: Dictionary = {}
    while true:
        var res: Array = await _js_reply
        if int(res[0]) == id:
            out = res[1]
            break
    return out

func _on_js_result(args: Array) -> void:
    if args.is_empty():
        return
    var parsed: Variant = JSON.parse_string(str(args[0]))
    if parsed is Dictionary:
        call_deferred(&"_deliver", int(parsed.get("id", -1)), parsed)

func _deliver(id: int, res: Dictionary) -> void:
    _js_reply.emit(id, res)

func _on_js_event(args: Array) -> void:
    if args.is_empty():
        return
    var parsed: Variant = JSON.parse_string(str(args[0]))
    if parsed is Dictionary:
        call_deferred(&"_handle_event", str(parsed.get("e", "")), parsed.get("d", {}))

func _handle_event(e: String, d: Dictionary) -> void:
    match e:
        "pause":
            set_paused(&"sdk", bool(d.get("on", false)))
        "visibility":
            if pause_on_focus_loss:
                set_paused(&"hidden", bool(d.get("hidden", false)))
                if bool(d.get("hidden", false)):
                    _flush_save()

func _log(msg: String) -> void:
    if OS.is_debug_build():
        print("[Platform] ", msg)
