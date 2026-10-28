extends CanvasLayer
class_name Hud
## Верхняя панель: здоровье, склянки, деньги, ночь. Значения «подпрыгивают» при изменении.
## Награда за нечисть (2.6) прилетает монетками в счётчик: деньги уже в GameState, а счётчик догоняет по монетке.

const COIN_SCENE: PackedScene = preload("res://scenes/fx/coin.tscn")
const BURST_SCENE: PackedScene = preload("res://scenes/fx/burst.tscn")
const GOLD: Color = Color("ffd25a")
## Монеток — по одной на COIN_VALUE денег, но не меньше COINS_MIN и не больше COINS_MAX.
const COIN_VALUE: int = 15
const COINS_MIN: int = 5
const COINS_MAX: int = 16
## Монетки уходят в счётчик по очереди: пауза перед первой и шаг между соседними (с).
const COIN_HOLD: float = 0.12
const COIN_STAGGER: float = 0.045
## Звон долетевших монеток идёт вверх по пентатонике (полутоны), как ноты комбо.
const COIN_PITCH: Array[int] = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]

@onready var vitals: Control = %Vitals
@onready var health_label: Label = %HealthLabel
@onready var jars_label: Label = %JarsLabel
@onready var cash_label: Label = %CashLabel
@onready var coin_icon: TextureRect = %CoinIcon
@onready var coins: Node2D = %Coins
@onready var night_label: Label = %NightLabel
@onready var heart: TextureRect = %Heart
@onready var sound_button: Button = %SoundButton

var vitals_visible: bool = true
var _health: float = -1.0
var _jars: int = -1
var _cash: int = -1
var _night: int = -1
var _t: float = 0.0
## Деньги, которые ещё летят монетками: уже в GameState.cash, но счётчик их пока не показывает.
var _cash_hold: int = 0
var _coin_note: int = 0
var _bumps: Dictionary = {}
## Монеток выпущено / долетело — для смоук-теста.
var coins_launched: int = 0
var coins_arrived: int = 0

func _ready() -> void:
    _update_sound_button()
    Globals.coins_requested.connect(fly_coins)

func set_vitals_visible(on: bool) -> void:
    vitals_visible = on
    if not on:
        land_coins()
    var tw: Tween = create_tween()
    tw.tween_property(vitals, "modulate:a", 1.0 if on else 0.0, 0.3)

func _process(delta: float) -> void:
    _t += delta
    var gs: GameState = Globals.game_state
    if gs.health != _health:
        var lost: bool = gs.health < _health
        _health = gs.health
        health_label.text = "%.1f" % _health
        _bump(health_label, Color("ff3348") if lost else Color.WHITE)
    if gs.jars != _jars:
        _jars = gs.jars
        jars_label.text = str(_jars)
        _bump(jars_label, Color("ffd25a"))
    var cash: int = maxi(gs.cash - _cash_hold, 0)
    if cash != _cash:
        _cash = cash
        cash_label.text = str(_cash)
        # Монетки сыплются часто — каждая подбрасывает счётчик слабее, чем покупка в лавке.
        _bump(cash_label, GOLD, 1.25 if _cash_hold > 0 or Globals.coins_in_flight > 0 else 1.45)
    if gs.night != _night:
        _night = gs.night
        night_label.text = (tr("HUD_NIGHT_ENDLESS") % _night) if gs.endless else (tr("HUD_NIGHT") % [_night, 7])
    var low: bool = gs.health <= 1.0
    var beat: float = 1.0 + (0.18 * maxf(0.0, sin(_t * 7.0)) if low else 0.0)
    heart.pivot_offset = heart.size * 0.5
    heart.scale = Vector2(beat, beat)

func _bump(node: Control, color: Color, size: float = 1.45) -> void:
    var old: Tween = _bumps.get(node)
    if old:
        old.kill()
    node.pivot_offset = node.size * 0.5
    node.scale = Vector2(size, size)
    node.modulate = color
    var tw: Tween = create_tween().set_parallel()
    tw.tween_property(node, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    tw.tween_property(node, "modulate", Color.WHITE, 0.4)
    _bumps[node] = tw

## Монетки награды (2.6): веером из точки from (холст) и по очереди — в счётчик. Каждая несёт свою долю amount,
## доли в сумме — ровно amount.
func fly_coins(from: Vector2, amount: int) -> void:
    if amount <= 0:
        return
    var count: int = clampi(floori(float(amount) / COIN_VALUE), COINS_MIN, COINS_MAX)
    _cash_hold += amount
    _coin_note = 0
    var left: int = amount
    for i in count:
        var share: int = floori(float(left) / (count - i))
        left -= share
        var c: FlyCoin = COIN_SCENE.instantiate()
        coins.add_child(c)
        # Веер вверх и в стороны: из павшей нечисти монетки «выплёскиваются».
        var dir: Vector2 = Vector2.UP.rotated(randf_range(-1.9, 1.9))
        c.launch(from, dir * randf_range(60.0, 150.0), coin_icon, COIN_HOLD + COIN_STAGGER * i)
        c.arrived.connect(_on_coin_arrived.bind(share, i == count - 1))
        coins_launched += 1
        Globals.coins_in_flight += 1

## Все монетки в воздухе — сразу в счётчик, молча (меню / финал прячут панель, а забег мог смениться).
func land_coins() -> void:
    for c in coins.get_children():
        if c is FlyCoin:
            (c as FlyCoin).land()

## Монетка в счётчике: счётчик +доля, звон на ноту выше, иконка глотает монетку. Последняя — золотые искры.
func _on_coin_arrived(share: int, last: bool) -> void:
    coins_arrived += 1
    Globals.coins_in_flight = maxi(Globals.coins_in_flight - 1, 0)
    _cash_hold = maxi(_cash_hold - share, 0)
    if not vitals_visible:
        return
    var step: int = COIN_PITCH[mini(_coin_note, COIN_PITCH.size() - 1)]
    _coin_note += 1
    Audio.sfx(&"coin_drop", -8.0, 0.02, pow(2.0, step / 12.0))
    _bump(coin_icon, Color.WHITE, 1.3)
    if last:
        var b: Node2D = BURST_SCENE.instantiate()
        b.set(&"tint", GOLD)
        b.position = coin_icon.get_global_rect().get_center()
        b.scale = Vector2(0.5, 0.5)
        coins.add_child(b)

func _on_sound_button_pressed() -> void:
    var on: bool = not Audio.is_sound_enabled()
    Audio.set_sound_enabled(on)
    Save.set_flag("sound", on)
    _update_sound_button()
    Audio.sfx(&"tick")

func _update_sound_button() -> void:
    sound_button.text = tr("HUD_SOUND_ON") if Audio.is_sound_enabled() else tr("HUD_SOUND_OFF")
