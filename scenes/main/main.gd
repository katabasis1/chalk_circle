extends Node2D
## Корень игры: смена экранов через «кляксу», музыка, пост-эффект, хитстоп, добивание, реклама и пауза платформы.

enum State { MENU, FIGHT, SHOP, BOSS, END, VICTORY }

const MENU_SCENE: PackedScene = preload("res://scenes/menu/menu.tscn")
const FIGHT_SCENE: PackedScene = preload("res://scenes/fight/fight.tscn")
const SHOP_SCENE: PackedScene = preload("res://scenes/shop/shop.tscn")
const END_SCENE: PackedScene = preload("res://scenes/end/end.tscn")
const ROUNDS_PER_BOSS: int = 7
const MUSIC_FOR: Array[StringName] = [&"menu", &"fight", &"shop", &"boss", &"", &"menu"]
## Добивание (2.6), время — реальные секунды (× strength): стоп-кадр, потом замедление.
const KILL_FREEZE: float = 0.06
const KILL_SLOWMO_TIME: float = 0.45
const KILL_SLOWMO_SCALE: float = 0.25
## Мир выцветает на миг добивания (параметр desaturate пост-эффекта) и возвращает цвет за KILL_FADE после замедления.
const KILL_DESAT: float = 0.45
const KILL_FADE: float = 0.35
## Рывок камеры: доля пути от центра экрана к нечисти и приближение (× strength); влёт и возврат.
const PUNCH_SHIFT: float = 0.2
const PUNCH_ZOOM: float = 0.1
const PUNCH_IN: float = 0.09
const PUNCH_OUT: float = 0.4

var state: State = State.MENU
var _transitioning: bool = false
var _hitstop_active: bool = false
## Хитстоп в очереди: x — время (реальные с), y — масштаб времени. x = 0 — очереди нет.
var _hitstop_next: Vector2 = Vector2.ZERO
var _low_hp: float = 0.0
## Рывок камеры (2.6) поверх раскладки: zoom = _base_zoom × (1 + _punch_zoom × _punch), position = _punch_to × _punch.
## Тряска (Shaker) двигает offset камеры — не мешают друг другу.
var _base_zoom: float = 1.0
var _punch: float = 0.0
var _punch_to: Vector2 = Vector2.ZERO
var _punch_zoom: float = 0.0
var _punch_tween: Tween
var _kill_tween: Tween
## Сколько раз сыграли добивание — для смоук-теста.
var finishers: int = 0

@onready var scenes: Node2D = $World/Scenes
@onready var cam_shaker: Shaker = $World/Camera2D/Shaker
@onready var hud: Hud = $Hud
@onready var wipe: Wipe = $Wipe
@onready var background: Background = $Background
@onready var post: ColorRect = $Post/Rect
@onready var camera: Camera2D = $World/Camera2D

## Горизонтальная раскладка (десктоп / повёрнутый телефон), см. scripts/layout.gd.
var landscape: bool = false

var gs: GameState:
    get:
        return Globals.game_state

func _ready() -> void:
    Globals.shake_requested.connect(_on_shake)
    Globals.hitstop_requested.connect(_hitstop)
    Globals.post_pulse.connect(_on_pulse)
    Globals.finisher_requested.connect(_on_finisher)
    Platform.rewarded_result.connect(_on_rewarded)
    Platform.cloud_loaded.connect(Save.merge)
    # SDK, язык, устройство и облачное сохранение (не дольше ~2 с) — до первого экрана. HTML-загрузчик всё это время на экране.
    await Platform.init_sdk()
    TranslationServer.set_locale(Platform.get_lang())
    Audio.set_sound_enabled(bool(Save.data.get("sound", true)))
    get_viewport().size_changed.connect(_on_viewport_resized)
    _on_viewport_resized()
    set_state(State.MENU)
    Audio.music(&"menu", 1.5)
    await get_tree().process_frame
    Platform.game_ready()

func _process(delta: float) -> void:
    var low: float = 1.0 if (hud.vitals_visible and gs.health <= 1.0 and gs.health > 0.0) else 0.0
    _low_hp = move_toward(_low_hp, low, delta * 2.0)
    _post(&"low_hp", _low_hp)

# ---------------- смена экранов ----------------
func transition(new_state: State) -> void:
    if _transitioning:
        return
    _transitioning = true
    Globals.input_locked = true
    var old: State = state
    if (old == State.FIGHT or old == State.BOSS) and new_state != State.END:
        gs.rounds_won += 1
    Platform.gameplay_stop()
    Audio.music(&"", 0.35)
    Audio.sfx(&"wipe", -4.0)
    wipe.cover()
    await wipe.covered
    if new_state == State.SHOP and (old == State.FIGHT or old == State.BOSS):
        # Межстраничная реклама — только в паузе между экранами, под шторкой.
        await Platform.show_fullscreen()
    set_state(new_state)
    wipe.reveal(_title_for(new_state))
    await wipe.done
    Globals.input_locked = false
    _transitioning = false
    if new_state == State.FIGHT or new_state == State.BOSS:
        Platform.gameplay_start()
    if new_state == State.BOSS:
        await get_tree().create_timer(0.8, false).timeout
    Audio.music(MUSIC_FOR[new_state], 1.0)

func set_state(new_state: State) -> void:
    for child in scenes.get_children():
        child.queue_free()
    _reset_finisher()
    var vitals: bool = true
    match new_state:
        State.MENU:
            Globals.new_run()
            var menu = MENU_SCENE.instantiate()
            menu.play.connect(transition.bind(State.FIGHT))
            menu.continue_run.connect(_continue_run)
            scenes.add_child(menu)
            vitals = false
        State.FIGHT, State.BOSS:
            var fight = FIGHT_SCENE.instantiate()
            var is_boss: bool = new_state == State.BOSS
            fight.set(&"boss", is_boss)
            if is_boss and not gs.endless:
                fight.won.connect(transition.bind(State.VICTORY))
            else:
                fight.won.connect(transition.bind(State.SHOP))
            fight.died.connect(transition.bind(State.END))
            scenes.add_child(fight)
            Save.save_run(_snapshot(&"boss" if is_boss else &"fight"))
        State.SHOP:
            var shop = SHOP_SCENE.instantiate()
            if (gs.rounds_won + 1) % ROUNDS_PER_BOSS == 0:
                shop.done.connect(transition.bind(State.BOSS))
            else:
                shop.done.connect(transition.bind(State.FIGHT))
            scenes.add_child(shop)
            Save.save_run(_snapshot(&"shop"))
        State.END, State.VICTORY:
            var end = END_SCENE.instantiate()
            end.set(&"victory", new_state == State.VICTORY)
            end.play_again.connect(restart)
            end.to_menu.connect(transition.bind(State.MENU))
            end.endless.connect(_go_endless)
            end.revive.connect(_request_revive)
            scenes.add_child(end)
            vitals = false
            Save.finish_run(gs.rounds_won, new_state == State.VICTORY, gs.endless, not gs.revived, gs.best_combo)
    state = new_state
    for child in scenes.get_children():
        Layout.apply(child, landscape)
    hud.set_vitals_visible(vitals)
    background.set_mood(new_state)
    _post(&"desaturate", 0.65 if new_state == State.END else 0.0)
    Globals.log_event("state -> %s (night %d)" % [State.keys()[new_state], gs.night])

func _on_viewport_resized() -> void:
    var vp: Viewport = get_viewport()
    var was: bool = landscape
    landscape = Layout.is_landscape(vp)
    _base_zoom = Layout.camera_zoom(vp, landscape)
    _apply_camera()
    if was != landscape:
        for child in scenes.get_children():
            Layout.apply(child, landscape)
        Globals.log_event("layout -> %s" % ("landscape" if landscape else "portrait"))

func _title_for(s: State) -> String:
    match s:
        State.MENU:
            return tr("TITLE_GAME")
        State.FIGHT:
            return tr("WIPE_NIGHT") % gs.night
        State.SHOP:
            return tr("WIPE_SHOP")
        State.BOSS:
            return tr("WIPE_BOSS")
        State.END:
            return tr("WIPE_DEATH")
        State.VICTORY:
            return tr("WIPE_DAWN")
    return ""

## Чекпоинт забега: состояние на начало ночи / лавки + на какой экран вернуться.
func _snapshot(screen: StringName) -> Dictionary:
    var d: Dictionary = gs.to_dict()
    d["screen"] = str(screen)
    return d

## «Продолжить» из меню: восстановить забег и открыть экран, на котором его закрыли.
func _continue_run() -> void:
    var run: Dictionary = Save.get_run()
    if run.is_empty():
        transition(State.FIGHT)
        return
    Globals.load_run(run)
    var target: State = State.FIGHT
    match str(run.get("screen", "fight")):
        "shop":
            target = State.SHOP
        "boss":
            target = State.BOSS
    transition(target)

func restart() -> void:
    Globals.new_run()
    transition(State.FIGHT)

func _go_endless() -> void:
    gs.endless = true
    transition(State.SHOP)

func _request_revive() -> void:
    if gs.revived:
        return
    Platform.show_rewarded(&"revive")

func _on_rewarded(tag: StringName, success: bool) -> void:
    if tag != &"revive" or not success:
        return
    gs.revived = true
    gs.health = maxf(1.5, gs.max_health * 0.5)
    transition(State.BOSS if gs.last_fight_boss else State.FIGHT)

# ---------------- джус ----------------
func _on_shake(amount: float, time: float) -> void:
    cam_shaker.shake(amount, time)

## Пока идёт один хитстоп, следующий ждёт в очереди (одно место: самый долгий) и идёт сразу за ним.
## Так стоп-кадр удара и микро-замедление «Идеально» не глушат друг друга: сначала удар, потом замедление.
func _hitstop(time: float, slow: float) -> void:
    if _hitstop_active:
        if time > _hitstop_next.x:
            _hitstop_next = Vector2(time, slow)
        return
    _hitstop_active = true
    while time > 0.0:
        Engine.time_scale = slow
        await get_tree().create_timer(time, true, false, true).timeout
        time = _hitstop_next.x
        slow = _hitstop_next.y
        _hitstop_next = Vector2.ZERO
    Engine.time_scale = 1.0
    _hitstop_active = false

## Добивание (2.6): стоп-кадр, за ним замедление (очередь хитстопа), камера рывком к нечисти и обратно,
## мир выцветает и музыка глохнет, пока время замедлено. Всё в реальных секундах — от масштаба времени не зависит.
func _on_finisher(target: Vector2, strength: float) -> void:
    finishers += 1
    var freeze: float = KILL_FREEZE * strength
    var slow: float = KILL_SLOWMO_TIME * strength
    _hitstop(freeze, 0.05)
    _hitstop(slow, KILL_SLOWMO_SCALE)
    _punch_to = (target - (camera.get_parent() as Node2D).global_position) * PUNCH_SHIFT
    _punch_zoom = PUNCH_ZOOM * strength
    if _punch_tween:
        _punch_tween.kill()
    _punch_tween = create_tween().set_ignore_time_scale(true)
    _punch_tween.tween_method(_set_punch, _punch, 1.0, PUNCH_IN).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
    _punch_tween.tween_interval(freeze + slow - PUNCH_IN)
    _punch_tween.tween_method(_set_punch, 1.0, 0.0, PUNCH_OUT).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
    _pulse_param(&"shock", 1.0, 0.3)
    if _kill_tween:
        _kill_tween.kill()
    _post(&"desaturate", KILL_DESAT)
    Audio.set_muffled(true)
    _kill_tween = create_tween().set_ignore_time_scale(true)
    _kill_tween.tween_interval(freeze + slow)
    _kill_tween.tween_callback(Audio.set_muffled.bind(false))
    _kill_tween.tween_method(func(v: float) -> void: _post(&"desaturate", v), KILL_DESAT, 0.0, KILL_FADE).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)

func _set_punch(v: float) -> void:
    _punch = v
    _apply_camera()

func _apply_camera() -> void:
    camera.position = _punch_to * _punch
    var z: float = _base_zoom * (1.0 + _punch_zoom * _punch)
    camera.zoom = Vector2(z, z)

## Смена экрана: камера на место, цвет и звук — как были (добивание могло не доиграть под шторкой).
func _reset_finisher() -> void:
    if _punch_tween:
        _punch_tween.kill()
    _set_punch(0.0)
    if _kill_tween and _kill_tween.is_valid():
        _kill_tween.kill()
        Audio.set_muffled(false)

func _on_pulse(kind: StringName, amount: float) -> void:
    match kind:
        &"hurt":
            _pulse_param(&"hurt", amount, 0.45)
            _pulse_param(&"shock", 1.0, 0.35)
        &"hit":
            _pulse_param(&"shock", amount, 0.2)
        &"gold":
            _pulse_param(&"gold", amount, 0.9)
        &"dark":
            _pulse_param(&"dark", amount, 1.6)
        &"beat":
            _pulse_param(&"hurt", amount * 0.35, 0.3)

func _pulse_param(param: StringName, amount: float, time: float) -> void:
    var tw: Tween = create_tween()
    tw.tween_method(func(v: float) -> void: _post(param, v), amount, 0.0, time).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)

func _post(param: StringName, value: float) -> void:
    (post.material as ShaderMaterial).set_shader_parameter(param, value)
