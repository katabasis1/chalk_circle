extends Node
## Дымовой тест с ботом-игроком (в экспорт не попадает: tools/* исключена).
## С окном:   открой tools/smoke_test.tscn и нажми F6 — бот будет играть у тебя на глазах.
## Без окна:  godot --headless --path . res://tools/smoke_test.tscn
## Бот жмёт «тап» НАСТОЯЩИМИ кликами мыши (Input.parse_input_event), то есть проверяет и то,
## что клики не съедает какой-нибудь Control. Проходит меню → бои → лавку → смерть/воскрешение →
## заново, печатает отчёт и закрывает игру (код выхода 0 — OK, 1 — FAIL).
## Внимание: пишет в настоящий user://-сейв (рекорд, бестиарий).

const MainScript = preload("res://scenes/main/main.gd")

@export var speed: float = 2.0
## Сколько игровых секунд играть.
@export var duration: float = 300.0
## Шанс в секунду специально промахнуться (проверка штрафа за промах).
@export var miss_per_sec: float = 0.25
## Сколько секунд бот «ходит» по лавке, прежде чем нажать «ДАЛЬШЕ».
@export var shop_browse: float = 3.0
## Доля боевых секций, по которым бот целится в центр («Идеально», 2.2).
@export var perfect_aim: float = 0.5
## Доля заряжающихся атак (замах, 2.4), по которым бот нарочно тапает: это должен быть промах, а не попадание.
@export var charge_probe: float = 0.3

@onready var main: Node = $Main

var _t: float = 0.0
var _ring: Ring = null
var _expect_press: int = 0
var _got_press: int = 0
var _expect_miss: int = 0
var _got_miss: int = 0
var _frames: Dictionary = {}
var _shop_time: float = 0.0
var _release: bool = false
var _max_night: int = 0
var _max_killed: int = 0
var _max_spirits: int = 0
var _max_combo: int = 0
var _combo_breaks: int = 0
var _combat_misses: int = 0
var _bad_misses: int = 0
var _aim: Dictionary = {}
var _aimed: int = 0
var _max_perfect: int = 0
## Снаряды (2.3) по каждому бою: id экрана → Vector2i(выпущено, долетело).
var _bolts: Dictionary = {}
## Замах (2.4): сигналы круга боя, проверка позы нечисти, атаки без замаха, тапы по заряду.
var _tele_started: int = 0
var _tele_armed: int = 0
var _tele_cancelled: int = 0
var _windups: int = 0
var _no_windup: int = 0
var _unwarned: int = 0
var _charge_taps: int = 0
var _charge_pressed: int = 0
var _seen: Dictionary = {}
var _probed: Dictionary = {}
## Раны (2.5): трещины на круге = потерянное здоровье. id круга → Vector2i(трещин раскрылось, затянулось).
var _cracks: Dictionary = {}
var _wound_gs: GameState = null
var _last_wc: int = 0
var _hurts: int = 0
var _heals: int = 0
var _wound_bad_frames: int = 0
var _wound_mismatch: int = 0
var _wound_placed: int = 0
var _wound_far: int = 0
var _min_gap: float = INF
var _save_bad: int = 0
## Добивание и монетки (2.6): id боя → добиваний; замедление и рывок камеры замечены; камера вернулась на место;
## счётчик денег сходится с GameState, когда монетки долетели; бой не уходит с монетками в воздухе.
var _finishers: Dictionary = {}
var _slowmo_seen: bool = false
var _punch_seen: bool = false
var _punch_since: int = -1
var _cam_bad_frames: int = 0
var _cam_stuck: int = 0
var _cash_bad_frames: int = 0
var _cash_mismatch: int = 0
var _coins_cut: int = 0
## Дуга здоровья (2.7): id боя → Vector2i(ударов по дуге, следов стекло); след ниже дуги (кадров), след виден;
## дуга отстаёт от здоровья нечисти / след не стёк / число не то — по 3 кадра подряд = 1 раз.
var _hpbars: Dictionary = {}
var _ghost_below: int = 0
var _ghost_seen: bool = false
var _hp_key: int = 0
var _hp_last: int = -1
var _hp_changed_at: float = 0.0
var _hp_lag: int = 0
var _hp_lag_frames: int = 0
var _ghost_stuck: int = 0
var _ghost_stuck_frames: int = 0
var _hp_text_bad: int = 0
var _hp_text_frames: int = 0
var _last_combo: int = 0
var _last_state: String = ""
var _log: PackedStringArray = []

func _ready() -> void:
    Platform.pause_on_focus_loss = false
    print("[smoke] старт: speed=%.1f, duration=%.0f" % [speed, duration])

func _process(delta: float) -> void:
    if not bool(main.get("_hitstop_active")):
        Engine.time_scale = speed
    _t += delta
    var st: String = MainScript.State.keys()[int(main.get("state"))]
    _frames[st] = int(_frames.get(st, 0)) + 1
    var gs: GameState = Globals.game_state
    if st != _last_state:
        if (_last_state == "FIGHT" or _last_state == "BOSS") and st == "SHOP" and Globals.coins_in_flight > 0:
            _coins_cut += 1
        _log.append("%.0fs %s" % [_t, st])
        _last_state = st
        _check_save_wounds(gs)
    _max_night = maxi(_max_night, gs.night)
    _max_killed = maxi(_max_killed, gs.enemies_killed)
    _max_spirits = maxi(_max_spirits, gs.spirits_caught)
    _max_combo = maxi(_max_combo, gs.best_combo)
    _max_perfect = maxi(_max_perfect, gs.perfect_hits)
    var fight: Node = _current_screen()
    if fight and "bolts_sent" in fight:
        _bolts[fight.get_instance_id()] = Vector2i(int(fight.get("bolts_sent")), int(fight.get("bolts_landed")))
    if fight and "combo" in fight:
        var c: int = int(fight.get("combo"))
        if c < _last_combo:
            _combo_breaks += 1
        _last_combo = c
    else:
        _last_combo = 0
    _watch_wounds(gs, st)
    _watch_finisher(gs, st, fight)
    _watch_hp_bar(fight)
    if _release:
        _click(false)
        _release = false
        return
    if _t >= duration:
        _report()
        return
    _shop_time = _shop_time + delta if st == "SHOP" else 0.0
    var ring: Ring = _current_ring()
    if ring != _ring:
        _bind(ring)
    if ring == null or Globals.input_locked or ring.stopped or not ring.pause_timer.is_stopped():
        return
    if ring.telegraph:
        _watch_attacks(ring)
    # Где будет искра, когда клик дойдёт (событие обработается в начале следующего кадра).
    var dir: float = -1.0 if ring.reversed else 1.0
    var ang: float = fposmod(ring.pivot.rotation + ring.rps * TAU * delta * dir, TAU)
    var over: Section = null
    var nearest: float = INF
    for s in ring.live_sections():
        var d: float = s.hit_distance(ang)
        if d < nearest:
            nearest = d
            over = s
    if nearest > -0.04:
        # Тап по заряжающейся атаке (замах, 2.4): секции ещё нет — должен быть промах.
        if nearest > 0.15 and ring.telegraph and ring.miss_buffer.is_stopped() and _probe_charge(ring, ang, delta):
            _charge_taps += 1
            _expect_miss += 1
            _click(true)
            return
        # Нарочный промах — только когда искра далеко от любых секций.
        if nearest > 0.15 and (st == "FIGHT" or st == "BOSS") and ring.miss_buffer.is_stopped() and randf() < miss_per_sec * delta:
            _expect_miss += 1
            _click(true)
        return
    if _wants(st, over.data):
        if (st == "FIGHT" or st == "BOSS") and _aims_center(over):
            # Ждём центр: >0 — центр ещё впереди искры. Проскочили за кадр — жмём как есть.
            var ahead: float = angle_difference(ang, over.center) * dir
            if ahead > over.perfect_tolerance():
                return
            _aimed += 1
        _expect_press += 1
        _click(true)

## Каждая атака нечисти на круге боя должна появиться через замах (charge_time > 0).
func _watch_attacks(ring: Ring) -> void:
    for s in ring.live_sections():
        var id: int = s.get_instance_id()
        if _seen.has(id):
            continue
        _seen[id] = true
        if s.data.kind == ActionData.Kind.ENEMY and s.charge_time <= 0.0:
            _unwarned += 1

## Искра будет глубоко внутри заряжающейся атаки и заряд не кончится раньше клика — один раз на секцию решаем, тапать ли.
func _probe_charge(ring: Ring, ang: float, delta: float) -> bool:
    for s in ring.live_sections():
        if not s.charging or s.charge_time - float(s.get("_charge_t")) < delta * 3.0:
            continue
        if absf(angle_difference(ang, s.center)) > 0.5 * s.size * TAU - 0.03:
            continue
        var id: int = s.get_instance_id()
        if not _probed.has(id):
            _probed[id] = randf() < charge_probe
            return bool(_probed[id])
    return false

func _aims_center(s: Section) -> bool:
    if not s.can_be_perfect():
        return false
    var id: int = s.get_instance_id()
    if not _aim.has(id):
        _aim[id] = randf() < perfect_aim
    return bool(_aim[id])

func _wants(st: String, data: ActionData) -> bool:
    match st:
        "MENU":
            return data.text == "UI_PLAY"
        "FIGHT", "BOSS":
            return true
        "SHOP":
            if data.text == "SHOP_DONE":
                return _shop_time > shop_browse
            return true
        "END":
            # Сначала пробуем воскрешение за рекламу, потом «заново».
            if not Globals.game_state.revived:
                return data.text == "UI_REVIVE"
            return data.text == "UI_AGAIN"
        "VICTORY":
            return data.text == "UI_ENDLESS"
    return false

func _current_screen() -> Node:
    var scenes: Node = main.get_node("World/Scenes")
    for i in range(scenes.get_child_count() - 1, -1, -1):
        var screen: Node = scenes.get_child(i)
        if not screen.is_queued_for_deletion():
            return screen
    return null

func _current_ring() -> Ring:
    var screen: Node = _current_screen()
    if screen == null:
        return null
    return screen.get_node_or_null("Ring") as Ring

func _bind(ring: Ring) -> void:
    _ring = ring
    if ring == null:
        return
    ring.pressed.connect(_on_pressed)
    ring.missed.connect(_on_missed.bind(ring))
    if ring.wounds:
        ring.expired.connect(_on_expired)
    if ring.telegraph:
        ring.telegraph_started.connect(_on_telegraph_started.bind(ring))
        ring.telegraph_armed.connect(func(_s: Section) -> void: _tele_armed += 1)
        ring.telegraph_cancelled.connect(func(_s: Section) -> void: _tele_cancelled += 1)

## Раны (2.5): число трещин на круге = потерянное здоровье (круг догоняет за кадр-другой), раны в бою, лечение в лавке.
func _watch_wounds(gs: GameState, st: String) -> void:
    if gs != _wound_gs:
        _wound_gs = gs
        _last_wc = gs.wound_count()
    var ring: Ring = _current_ring()
    if ring != null and ring.wounds:
        _cracks[ring.get_instance_id()] = Vector2i(ring.cracks_opened, ring.cracks_healed)
        if ring.crack_count() != gs.wound_count():
            _wound_bad_frames += 1
            if _wound_bad_frames == 3:
                _wound_mismatch += 1
                _log.append("%.0fs трещин %d при %d ранах" % [_t, ring.crack_count(), gs.wound_count()])
        else:
            _wound_bad_frames = 0
    else:
        _wound_bad_frames = 0
    var wc: int = gs.wound_count()
    if wc > _last_wc and (st == "FIGHT" or st == "BOSS"):
        _hurts += wc - _last_wc
    elif wc < _last_wc and st == "SHOP":
        _heals += _last_wc - wc
    if wc != _last_wc:
        for i in gs.wounds.size():
            for j in range(i + 1, gs.wounds.size()):
                _min_gap = minf(_min_gap, absf(angle_difference(gs.wounds[i], gs.wounds[j])))
    _last_wc = wc

## Добивание (2.6): замедление и рывок камеры случаются, камера возвращается на место (позиция 0, зум раскладки),
## счётчик денег в HUD сходится с GameState, когда все монетки долетели.
func _watch_finisher(gs: GameState, st: String, fight: Node) -> void:
    if fight and (st == "FIGHT" or st == "BOSS") and "finishers" in fight:
        _finishers[fight.get_instance_id()] = int(fight.get("finishers"))
    if bool(main.get("_hitstop_active")) and is_equal_approx(Engine.time_scale, MainScript.KILL_SLOWMO_SCALE):
        _slowmo_seen = true
    var cam: Camera2D = main.get("camera")
    var punch: float = float(main.get("_punch"))
    var now: int = Time.get_ticks_msec()
    if punch > 0.0:
        if punch > 0.9 and cam.position.length() > 1.0:
            _punch_seen = true
        if _punch_since < 0:
            _punch_since = now
        elif now - _punch_since > 3000:
            _cam_stuck += 1
            _log.append("%.0fs камера застряла в рывке" % _t)
            _punch_since = now
        _cam_bad_frames = 0
    else:
        _punch_since = -1
        if cam.position != Vector2.ZERO or not is_equal_approx(cam.zoom.x, float(main.get("_base_zoom"))):
            _cam_bad_frames += 1
            if _cam_bad_frames == 3:
                _cam_stuck += 1
                _log.append("%.0fs камера не вернулась: %s, зум %.3f" % [_t, cam.position, cam.zoom.x])
        else:
            _cam_bad_frames = 0
    var hud: Hud = main.get("hud")
    if Globals.coins_in_flight == 0 and (hud.cash_label.text != str(gs.cash) or int(hud.get("_cash_hold")) != 0):
        _cash_bad_frames += 1
        if _cash_bad_frames == 3:
            _cash_mismatch += 1
            _log.append("%.0fs счётчик %s при %d денег" % [_t, hud.cash_label.text, gs.cash])
    else:
        _cash_bad_frames = 0

## Дуга здоровья (2.7): след никогда не ниже красной дуги и после удара виден; красная дуга догоняет здоровье
## нечисти (с запасом на прорисовку новой), след стекает после серии, число в центре = здоровье.
func _watch_hp_bar(fight: Node) -> void:
    if fight == null or not ("hp_bar" in fight):
        _hp_last = -1
        return
    var bar: HpBar = fight.get("hp_bar")
    _hpbars[fight.get_instance_id()] = Vector2i(bar.hits, bar.drains)
    if bar.ghost < bar.shown - 0.002:
        _ghost_below += 1
    if bar.ghost > bar.shown + 0.02:
        _ghost_seen = true
    var ev: Variant = fight.get("enemy")
    if not is_instance_valid(ev) or (ev as Enemy).dead:
        _hp_last = -1
        return
    var e: Enemy = ev
    if e.get_instance_id() != _hp_key or e.hp != _hp_last:
        _hp_key = e.get_instance_id()
        _hp_last = e.hp
        _hp_changed_at = _t
        _hp_lag_frames = 0
        _ghost_stuck_frames = 0
        return
    var since: float = _t - _hp_changed_at
    var want: float = float(e.hp) / float(maxi(e.max_hp, 1))
    if since > HpBar.REFILL_TIME + 0.3 and absf(bar.shown - want) > 0.01:
        _hp_lag_frames += 1
        if _hp_lag_frames == 3:
            _hp_lag += 1
            _log.append("%.0fs дуга %.2f при здоровье %.2f" % [_t, bar.shown, want])
    else:
        _hp_lag_frames = 0
    if since > HpBar.GHOST_HOLD + HpBar.GHOST_DRAIN + 0.4 and bar.ghost > bar.shown + 0.005:
        _ghost_stuck_frames += 1
        if _ghost_stuck_frames == 3:
            _ghost_stuck += 1
            _log.append("%.0fs след застрял: %.2f над %.2f" % [_t, bar.ghost, bar.shown])
    else:
        _ghost_stuck_frames = 0
    var hp_label: Label = fight.get("hp_label")
    if hp_label.text != str(e.hp):
        _hp_text_frames += 1
        if _hp_text_frames == 3:
            _hp_text_bad += 1
            _log.append("%.0fs в центре %s при здоровье %d" % [_t, hp_label.text, e.hp])
    else:
        _hp_text_frames = 0

## Атака догорела и ранила: трещина должна встать там, где её прорвали (или рядом, если место занято).
## Бой подключён к expired раньше (из .tscn), так что рана к этому моменту уже нанесена.
func _on_expired(s: Section) -> void:
    var gs: GameState = Globals.game_state
    if s.data == null or not s.data.hurt_on_expire or gs.wounds.is_empty() or gs.wound_count() <= _last_wc:
        return
    _wound_placed += 1
    if absf(angle_difference(gs.wounds[-1], s.center)) > GameState.WOUND_GAP * 7.5:
        _wound_far += 1

## Чекпоинт забега (1.4) не должен терять и двигать трещины: to_dict → from_dict даёт те же углы.
func _check_save_wounds(gs: GameState) -> void:
    var copy: GameState = GameState.from_dict(gs.to_dict())
    if copy.wounds.size() != gs.wounds.size():
        _save_bad += 1
        return
    for i in gs.wounds.size():
        if not is_equal_approx(copy.wounds[i], gs.wounds[i]):
            _save_bad += 1
            return

## Нажатая секция, у которой заряд так и не кончился, — значит, атаку поймали во время замаха (так быть не должно).
func _on_pressed(s: Section) -> void:
    _got_press += 1
    if s.charge_time > 0.0 and float(s.get("_charge_t")) < s.charge_time:
        _charge_pressed += 1

## Обработчик боя подключён раньше (из .tscn): нечисть к этому моменту уже должна замахнуться.
func _on_telegraph_started(_s: Section, ring: Ring) -> void:
    _tele_started += 1
    var enemy: Enemy = ring.get_parent().get("enemy") as Enemy
    if enemy == null or enemy.dead:
        return
    if enemy.is_winding_up():
        _windups += 1
    else:
        _no_windup += 1

## Обработчик боя подключён раньше (из .tscn), поэтому к этому моменту комбо уже должно обнулиться.
func _on_missed(_angle: float, ring: Ring) -> void:
    _got_miss += 1
    var screen: Node = ring.get_parent()
    if "combo" in screen and not ring.player_actions.is_empty():
        _combat_misses += 1
        if int(screen.get("combo")) != 0:
            _bad_misses += 1

func _click(down: bool) -> void:
    var e: InputEventMouseButton = InputEventMouseButton.new()
    e.button_index = MOUSE_BUTTON_LEFT
    e.pressed = down
    var win: Vector2 = Vector2(DisplayServer.window_get_size())
    if win.x < 2.0:
        win = get_viewport().get_visible_rect().size
    # Чуть ниже центра — там круг, а не HUD.
    e.position = win * Vector2(0.5, 0.6)
    e.global_position = e.position
    Input.parse_input_event(e)
    if down:
        _release = true

func _report() -> void:
    set_process(false)
    Engine.time_scale = 1.0
    print("[smoke] ---- отчёт ----")
    print("[smoke] путь: ", ", ".join(_log))
    print("[smoke] кадров на экранах: ", _frames)
    print("[smoke] тапы по секциям: ожидалось %d, дошло до круга %d" % [_expect_press, _got_press])
    print("[smoke] нарочные промахи: ожидалось %d, засчитано %d" % [_expect_miss, _got_miss])
    print("[smoke] макс. ночь %d, изгнано %d, духов поймано %d, рекорд в сейве %d" % [
        _max_night, _max_killed, _max_spirits, int(Save.data.get("best_night", 0))])
    print("[smoke] комбо: лучшее %d, сбросов %d (промахов в бою %d, из них не сбросили %d), рекорд в сейве %d" % [
        _max_combo, _combo_breaks, _combat_misses, _bad_misses, int(Save.data.get("best_combo", 0))])
    print("[smoke] «Идеально»: прицельных тапов %d, засчитано %d" % [_aimed, _max_perfect])
    var bolts: Vector2i = Vector2i.ZERO
    for v in _bolts.values():
        bolts += v
    print("[smoke] снаряды: выпущено %d, долетело %d" % [bolts.x, bolts.y])
    print("[smoke] замах: начато %d (нечисть замахнулась %d, не замахнулась %d), вспыхнуло %d, сорвано %d; атак без замаха %d; тапов по заряду %d, из них засчитано попаданием %d" % [
        _tele_started, _windups, _no_windup, _tele_armed, _tele_cancelled, _unwarned, _charge_taps, _charge_pressed])
    var cracks: Vector2i = Vector2i.ZERO
    for v in _cracks.values():
        cracks += v
    print("[smoke] раны: получено %d, трещин раскрылось %d; залечено в лавке %d, трещин затянулось %d; не там, где прорвали, %d из %d; круг и здоровье расходились %d раз; ближе всего трещины %s рад; чекпоинт терял раны %d раз" % [
        _hurts, cracks.x, _heals, cracks.y, _wound_far, _wound_placed, _wound_mismatch,
        "—" if _min_gap == INF else "%.2f" % _min_gap, _save_bad])
    var fin: int = 0
    for v in _finishers.values():
        fin += int(v)
    var hud: Hud = main.get("hud")
    print("[smoke] добивание: %d (Main сыграл %d), замедление %s, рывок камеры %s, камера застревала %d раз; монеток вылетело %d, долетело %d, в полёте %d; счётчик расходился с деньгами %d раз; в лавку с монетками в воздухе %d раз" % [
        fin, int(main.get("finishers")), "да" if _slowmo_seen else "нет", "да" if _punch_seen else "нет", _cam_stuck,
        hud.coins_launched, hud.coins_arrived, Globals.coins_in_flight, _cash_mismatch, _coins_cut])
    var hpb: Vector2i = Vector2i.ZERO
    for v in _hpbars.values():
        hpb += v
    print("[smoke] дуга здоровья: ударов %d, следов стекло %d, след виден %s, след ниже дуги %d кадров; дуга отставала от здоровья %d раз, след застревал %d раз, число расходилось %d раз" % [
        hpb.x, hpb.y, "да" if _ghost_seen else "нет", _ghost_below, _hp_lag, _ghost_stuck, _hp_text_bad])
    var problems: PackedStringArray = []
    if _expect_press > 5 and _got_press < _expect_press * 0.7:
        problems.append("клики не доходят до круга (их перехватывает Control?)")
    if not _frames.has("FIGHT"):
        problems.append("бой так и не начался")
    if not _frames.has("SHOP") and not _frames.has("END"):
        problems.append("ни лавки, ни конца — бой завис?")
    if _max_killed == 0:
        problems.append("не изгнано ни одной нечисти")
    if _got_press > 30 and _max_combo < 2:
        problems.append("комбо не растёт")
    if _aimed > 15 and _max_perfect == 0:
        problems.append("«Идеально» не срабатывает (бот целился в центр %d раз)" % _aimed)
    if _got_press > 30 and bolts.x == 0:
        problems.append("удары не выпускают снаряды")
    elif bolts.x > 10 and bolts.y < bolts.x * 0.8:
        problems.append("снаряды не долетают (%d из %d)" % [bolts.y, bolts.x])
    if _max_killed >= 3 and _tele_started == 0:
        problems.append("нечисть атакует без замаха (замахов 0)")
    if _unwarned > 0:
        problems.append("атака нечисти появилась сразу, без замаха (%d раз)" % _unwarned)
    if _tele_started > 5 and _tele_armed == 0:
        problems.append("заряженные атаки не вспыхивают")
    if _no_windup > maxi(2, int(_tele_started * 0.1)):
        problems.append("нечисть не замахивается (%d из %d)" % [_no_windup, _tele_started])
    if _charge_pressed > 0:
        problems.append("заряжающуюся атаку можно поймать (%d раз)" % _charge_pressed)
    if _bad_misses > 0:
        problems.append("промах в бою не сбросил комбо (%d раз)" % _bad_misses)
    if _hurts > 0 and cracks.x == 0:
        problems.append("раны не оставляют трещин на круге (ран %d)" % _hurts)
    if _wound_mismatch > 0:
        problems.append("число трещин не совпадает со здоровьем (%d раз)" % _wound_mismatch)
    if _heals > 0 and cracks.y == 0:
        problems.append("лечение в лавке не затягивает трещины")
    if _wound_placed >= 4 and _wound_far * 2 > _wound_placed:
        problems.append("трещины встают не там, где атака прорвала круг (%d из %d)" % [_wound_far, _wound_placed])
    if _min_gap < 0.1:
        problems.append("трещины слиплись (%.2f рад между ними)" % _min_gap)
    if _save_bad > 0:
        problems.append("чекпоинт теряет раны (%d раз)" % _save_bad)
    if _max_killed >= 2 and fin == 0:
        problems.append("добивание не срабатывает (повержено %d)" % _max_killed)
    if fin > 0 and not _slowmo_seen:
        problems.append("добивание без замедления")
    if fin > 0 and not _punch_seen:
        problems.append("добивание без рывка камеры")
    if _cam_stuck > 0:
        problems.append("камера не возвращается после рывка (%d раз)" % _cam_stuck)
    if _max_killed > 0 and hud.coins_launched == 0:
        problems.append("награда не летит монетками в счётчик")
    if hud.coins_arrived + Globals.coins_in_flight != hud.coins_launched:
        problems.append("монетки теряются по дороге (вылетело %d, долетело %d, в полёте %d)" % [hud.coins_launched, hud.coins_arrived, Globals.coins_in_flight])
    if _cash_mismatch > 0:
        problems.append("счётчик денег не сходится с GameState после монеток (%d раз)" % _cash_mismatch)
    if _coins_cut > 0:
        problems.append("бой ушёл в лавку, не дождавшись монеток (%d раз)" % _coins_cut)
    if bolts.y > 0 and hpb.x == 0:
        problems.append("дуга здоровья не замечает ударов (HpBar.set_hp)")
    if hpb.x > 0 and not _ghost_seen:
        problems.append("после удара нет следа («призрака») на дуге здоровья")
    if hpb.x >= 3 and hpb.y == 0:
        problems.append("след на дуге здоровья не стекает")
    if _ghost_below > 0:
        problems.append("след ниже красной дуги (%d кадров)" % _ghost_below)
    if _hp_lag > 0:
        problems.append("дуга здоровья отстаёт от здоровья нечисти (%d раз)" % _hp_lag)
    if _ghost_stuck > 0:
        problems.append("след на дуге не стекает после серии (%d раз)" % _ghost_stuck)
    if _hp_text_bad > 0:
        problems.append("число в центре круга не равно здоровью нечисти (%d раз)" % _hp_text_bad)
    if problems.is_empty():
        print("[smoke] OK")
    else:
        print("[smoke] FAIL: ", "; ".join(problems))
    get_tree().quit(0 if problems.is_empty() else 1)
