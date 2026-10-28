extends Node
## Глобальное состояние забега + шина FX-событий (тряска, хитстоп, вспышки пост-эффекта).

signal shake_requested(amount: float, time: float)
signal hitstop_requested(time: float, scale: float)
signal post_pulse(kind: StringName, amount: float)
signal finisher_requested(target: Vector2, strength: float)
signal coins_requested(from: Vector2, amount: int)

var game_state: GameState = GameState.new()
## Блокирует ввод на время смены экрана.
var input_locked: bool = false
## Монетки добивания ещё летят в счётчик (2.6): бой ждёт их перед лавкой. Ведёт Hud.
var coins_in_flight: int = 0

func new_run() -> void:
    game_state = GameState.new()
    log_event("new run")

## Восстановить забег из чекпоинта (Save.get_run()).
func load_run(run: Dictionary) -> void:
    game_state = GameState.from_dict(run)
    log_event("run restored: night %d" % game_state.night)

## Текст под устройство: KEY_MOBILE / KEY_DESKTOP, если такой ключ есть в переводе, иначе KEY.
func device_text(key: String) -> String:
    var k: String = key + ("_MOBILE" if Platform.is_mobile() else "_DESKTOP")
    var s: String = tr(k)
    return s if s != k else tr(key)

func shake(amount: float, time: float = 0.2) -> void:
    shake_requested.emit(amount, time)

## Стоп-кадр (scale 0.05) или микро-замедление (scale 0.3 — «Идеально»). time — в реальных секундах.
func hitstop(time: float = 0.05, scale: float = 0.05) -> void:
    hitstop_requested.emit(time, scale)

func pulse(kind: StringName, amount: float = 1.0) -> void:
    post_pulse.emit(kind, amount)

## Добивание (2.6): стоп-кадр → замедление, рывок камеры к target (мировые координаты), мир выцветает, музыка глохнет.
## strength 1 — обычная нечисть, больше — Хозяйка (дольше и сильнее). Делает Main.
func finisher(target: Vector2, strength: float = 1.0) -> void:
    finisher_requested.emit(target, strength)

## Награда монетками (2.6): from — точка на экране (координаты холста, см. get_canvas_transform()),
## amount — сколько денег несут все монетки вместе. Деньги к этому моменту уже в GameState — счётчик HUD догоняет.
func coins(from: Vector2, amount: int) -> void:
    coins_requested.emit(from, amount)

## F12 в отладочном запуске — скриншот окна в user://screenshots (для материалов каталога, docs/STORE.md).
func _input(event: InputEvent) -> void:
    if not OS.is_debug_build():
        return
    var k: InputEventKey = event as InputEventKey
    if k and k.pressed and not k.echo and k.keycode == KEY_F12:
        _screenshot()

func _screenshot() -> void:
    var img: Image = get_viewport().get_texture().get_image()
    DirAccess.make_dir_recursive_absolute("user://screenshots")
    var stamp: String = Time.get_datetime_string_from_system().replace(":", "-")
    var path: String = "user://screenshots/%s_%dx%d.png" % [stamp, img.get_width(), img.get_height()]
    img.save_png(path)
    print("[ChalkCircle] screenshot → ", ProjectSettings.globalize_path(path))

func log_event(msg: String) -> void:
    if OS.is_debug_build():
        print("[ChalkCircle] ", msg)
