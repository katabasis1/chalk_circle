extends Node2D
## Ночь: три нечисти подряд (или Хозяйка). Логика урона — как в оригинале + механика Печати.
## Печать: когда у нечисти ≤30% здоровья, впереди искры на пару секунд вспыхивает золотая секция.
## Поймал — дух уходит в склянку и становится твоей новой секцией (как поимка в коллекционных играх).
## Комбо: каждое попадание подряд — нота выше; с 5 и 10 попаданий урон +25% / +50%. Промах или рана — сброс.
## «Идеально»: нажатие точно по центру секции (риска на дуге) — урон ×1.5, золотая вспышка, звон, микро-замедление.
## Удар долетает: от секции к нечисти летит меловой снаряд (bolt), урон и цифра над врагом — в момент попадания.
## Дуга здоровья (HpBar): удар срезает её сразу, срезанный кусок держится светлым следом и стекает.
## Добивание: удар, который валит нечисть, — стоп-кадр и замедление, камера рывком к ней (Main); награда
## монетками летит из нечисти в счётчик (Hud), и в лавку уходим, только когда они долетят.

signal won
signal died

const ENEMY_SCENE: PackedScene = preload("res://scenes/enemy/enemy.tscn")
const POP_SCENE: PackedScene = preload("res://scenes/fx/pop.tscn")
const BOLT_SCENE: PackedScene = preload("res://scenes/fx/bolt.tscn")
const SEAL_ACTION: ActionData = preload("res://data/actions/seal.tres")
const ENEMIES_PER_NIGHT: int = 3
const SEAL_THRESHOLD: float = 0.3
const POP_R: float = 246.0
const GOLD: Color = Color("ffd25a")
const BLOOD: Color = Color("ff3348")
## Ноты комбо (полутоны от основного тона, пентатоника): каждое попадание подряд — на ступень выше, потолок — 2 октавы.
const COMBO_PITCH: Array[int] = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]
## Цвет счётчика по ступени комбо: мел → золото (+25%) → огонь (+50%).
const COMBO_COLORS: Array[Color] = [Color("efe6d2"), Color("ffd25a"), Color("ff8a3a")]
const COMBO_BROKEN: Color = Color("8a8378")
## «Идеально» (2.2): множитель урона и микро-замедление (реальные секунды, масштаб времени).
const PERFECT_MULT: float = 1.5
const PERFECT_SLOWMO_TIME: float = 0.09
const PERFECT_SLOWMO_SCALE: float = 0.3
## Снаряд (2.3) огибает центр круга (дуга здоровья r=150 + запас), чтобы не перечёркивать число.
const BOLT_AVOID_R: float = 185.0
## Добивание (2.6): сила для Main (время, приближение) — у Хозяйки сильнее. Сколько ждать монетки перед лавкой (с).
const BOSS_FINISHER: float = 1.6
const COINS_WAIT: float = 2.5

@export var boss: bool = false

var n: int = 0
var next_attack_bonus: float = 0.0
var extra_money: int = 0
var enemies_data: Array = []
var free_hits: int = 0
var enemy: Enemy
var finished: bool = false
var seal_offered: bool = false
## Попаданий подряд (живёт всю ночь, между врагами не сбрасывается).
var combo: int = 0
var _combo_y: float = 0.0
## Снаряды (2.3): выпущено / долетело — для смоук-теста.
var bolts_sent: int = 0
var bolts_landed: int = 0
## Добиваний за бой — для смоук-теста.
var finishers: int = 0
var _combo_tween: Tween

@onready var ring: Ring = $Ring
@onready var slot: Node2D = $EnemySlot
@onready var pops: Node2D = $Pops
@onready var bolts: Node2D = $Bolts
@onready var blind_timer: Timer = $BlindTimer
@onready var center: Node2D = $Center
@onready var name_label: Label = %NameLabel
@onready var hp_label: Label = %HpLabel
@onready var hp_bar: HpBar = %HpBar
@onready var seal_mark: ColorRect = %SealMark
@onready var hint: Label = %Hint
@onready var combo_label: Label = %ComboLabel
@onready var combo_bonus_label: Label = %ComboBonus

var gs: GameState:
    get:
        return Globals.game_state

func _ready() -> void:
    gs.last_fight_boss = boss
    free_hits = int(gs.nullified_hits)
    if boss:
        enemies_data = [Registry.BOSS]
    else:
        var pool: Array = Registry.ENEMIES.duplicate()
        pool.shuffle()
        enemies_data = pool.slice(0, ENEMIES_PER_NIGHT)
    center.modulate.a = 0.0
    _combo_y = combo_label.position.y
    combo_label.modulate.a = 0.0
    combo_bonus_label.modulate.a = 0.0
    hint.visible = not bool(Save.data.get("tutorial", false))
    if hint.visible:
        hint.text = Globals.device_text("HINT_TAP")
    await get_tree().create_timer(1.6 if boss else 0.35, false).timeout
    add_enemy()

# ---------------- враги ----------------
func add_enemy() -> void:
    if enemies_data.is_empty() or finished:
        return
    var data: NpcData = enemies_data.pop_back()
    enemy = ENEMY_SCENE.instantiate()
    enemy.setup(data, data.get_scaled_hp(gs.enemies_killed))
    enemy.died.connect(_on_enemy_died)
    enemy.hp_changed.connect(_on_hp_changed)
    slot.add_child(enemy)
    ring.enemy_color = data.color
    seal_offered = false
    name_label.text = tr(data.name)
    name_label.modulate = data.color.lightened(0.35)
    _show_hp(enemy.hp, enemy.max_hp, true)
    var can_seal: bool = data.spirit != null and not data.boss
    seal_mark.visible = can_seal
    (seal_mark.material as ShaderMaterial).set_shader_parameter(&"arc_size", TAU * SEAL_THRESHOLD)
    create_tween().tween_property(center, "modulate:a", 1.0, 0.4)
    # Ждём конца анимации появления (0.8 с), потом даём действия.
    await get_tree().create_timer(0.85, false).timeout
    if finished or enemy == null or enemy.dead:
        return
    ring.player_actions = gs.actions
    ring.enemy_actions = data.get_scaled_actions(gs.enemies_killed)
    ring.shuffle()

func _on_hp_changed(hp: int, max_hp: int) -> void:
    _show_hp(hp, max_hp, false)

## Число и дуга здоровья (2.7: дуга срезается сразу, срезанное стекает следом — HpBar). fresh — новая нечисть.
func _show_hp(hp: int, max_hp: int, fresh: bool) -> void:
    hp_label.text = str(hp)
    hp_bar.set_hp(hp, max_hp, fresh)
    hp_label.pivot_offset = hp_label.size * 0.5
    hp_label.scale = Vector2(1.3, 1.3)
    create_tween().tween_property(hp_label, "scale", Vector2.ONE, 0.2)

func _on_enemy_died(sealed: bool) -> void:
    gs.enemies_killed += 1
    # Где нечисть пала — оттуда полетят монетки и там всплывёт «+N» (пока тело не растаяло и не ушло в склянку).
    var fell_at: Vector2 = enemy.hit_point()
    var label_at: Vector2 = enemy.label_point()
    ring.stop_combat()
    blind_timer.stop()
    _on_blind_timer_timeout()
    if hint.visible:
        Save.set_flag("tutorial", true)
        create_tween().tween_property(hint, "modulate:a", 0.0, 0.5)
    create_tween().tween_property(center, "modulate:a", 0.0, 0.3)
    await get_tree().create_timer(0.8 if sealed else 0.6, false).timeout
    var money: int = (300 if boss else 100) + extra_money
    extra_money = 0
    gs.cash += money
    gs.money_earned += money
    pop("+%d" % money, PI * 0.5, false, GOLD, false, pops.to_local(label_at))
    Globals.coins(get_viewport().get_canvas_transform() * fell_at, money)
    Audio.sfx(&"coin")
    await get_tree().create_timer(0.5, false).timeout
    if is_instance_valid(enemy):
        enemy.queue_free()
    enemy = null
    n += 1
    if finished:
        return
    if n < ENEMIES_PER_NIGHT and not boss:
        add_enemy()
    else:
        # Последняя нечисть ночи: монетки должны долететь до счётчика раньше, чем шторка закроет бой.
        var waited: float = 0.0
        while Globals.coins_in_flight > 0 and waited < COINS_WAIT:
            await get_tree().process_frame
            waited += get_process_delta_time()
        if finished:
            return
        finished = true
        won.emit()

# ---------------- круг ----------------
func _on_ring_pressed(section: Section) -> void:
    var action: ActionData = section.data
    if action == null or finished:
        return
    if action.kind == ActionData.Kind.SEAL:
        _try_seal(section)
        return
    if enemy == null or enemy.dead:
        return
    _combo_hit()
    var angle: float = section.center
    var perfect: bool = section.perfect and section.can_be_perfect()
    if perfect:
        _perfect_fx(angle)
    # Комбо и «Идеально» умножаются: ×10 комбо + центр = ×1.5 × 1.5.
    var mult: float = (1.0 + GameState.combo_bonus(combo)) * (PERFECT_MULT if perfect else 1.0)
    var popped: bool = false
    var is_enemy_action: bool = action.kind == ActionData.Kind.ENEMY

    var enemy_attack_count: int = 0
    for other in ring.live_sections():
        if other.data.hurt_on_expire:
            enemy_attack_count += 1
            if action.parry:
                other.die(true)
                pop(tr("POP_PARRIED"), other.center, true)

    var attack_bonus: float = next_attack_bonus
    for i in range(int(1 + action.repeats)):
        if enemy == null or enemy.dead:
            break
        var damage: float = action.damage
        damage += enemy.hp * action.percent_enemy_hp_damage
        damage += action.damage_per_enemy_attack * enemy_attack_count
        if damage > 0.0 or action.damage_per_enemy_attack > 0.0:
            damage += gs.bonus_damage
        if damage > 0.0:
            if not enemy.been_hit:
                damage *= 1.0 + gs.first_hit_bonus
            damage *= 1.0 + attack_bonus
            damage *= mult
            next_attack_bonus = 0.0
            _deal(damage, angle, action, perfect)
            popped = true
            if action.damage_gain > 0.0:
                action.damage += action.damage_gain
        if action.next_attack_bonus > 0.0:
            next_attack_bonus = action.next_attack_bonus
            if not popped:
                popped = _special(tr("POP_PREPARED"), angle, false)
        if action.reverse:
            ring.reversed = not ring.reversed
            if not popped:
                popped = _special(tr("POP_REVERSED"), angle, is_enemy_action)
        if action.teleport:
            ring.teleport(0.5)
            if not popped:
                popped = _special(tr("POP_TELEPORTED"), angle, is_enemy_action)
        if action.speedup > 0.0:
            ring.bonus_rps += action.speedup
            if not popped:
                popped = _special(tr("POP_SPEDUP"), angle, is_enemy_action)
        if action.blind > 0.0:
            ring.blind = true
            Audio.set_muffled(true)
            Globals.pulse(&"dark", 1.0)
            blind_timer.start(action.blind / gs.rps)
            if not popped:
                popped = _special(tr("POP_BLINDED"), angle, is_enemy_action)
        if action.hurt_on_expire:
            var dodge: float = gs.dodge_damage
            if dodge > 0.0:
                dodge += gs.bonus_damage
                if not enemy.been_hit:
                    dodge *= 1.0 + gs.first_hit_bonus
                dodge *= mult
                # Цифры урона теперь над нечистью, а не на круге, — второй снаряд не спорит с надписью.
                _deal(dodge, angle, action, perfect)
                popped = true
            if not popped:
                popped = true
                pop(tr("POP_DODGED"), angle, true)
                Audio.sfx(&"dodge")
        if not popped and action.damage_per_enemy_attack > 0.0 and enemy_attack_count == 0:
            popped = true
            pop(tr("POP_WHIFFED"), angle, true)
            Audio.sfx(&"whiff")
        if action.hurt_on_press:
            hurt(angle)
        if i < int(action.repeats):
            await get_tree().create_timer(0.1, false).timeout
            angle += TAU / 16.0 * (-1.0 if ring.reversed else 1.0)
    _check_seal()

func _special(text: String, angle: float, enemy_triggered: bool) -> bool:
    pop(text, angle, true)
    Audio.sfx(&"special")
    if enemy_triggered and enemy:
        enemy.attack()
    return true

## Удар: от секции (angle на круге) к нечисти летит меловой снаряд; урон — когда долетит (_on_bolt_landed).
## crit — удар «Идеально»: снаряд и цифра золотые, крупные.
func _deal(damage: float, angle: float, action: ActionData, crit: bool = false) -> void:
    var dmg: int = int(damage)
    if dmg <= 0 or enemy == null:
        return
    var tier: int = GameState.combo_tier(combo)
    var b: Bolt = BOLT_SCENE.instantiate()
    b.from = ring.to_global(Ring.RADIUS * Vector2.RIGHT.rotated(angle))
    b.target = enemy
    b.avoid = center.global_position
    b.avoid_r = BOLT_AVOID_R
    b.tint = GOLD if crit else COMBO_COLORS[tier]
    b.heavy = crit or dmg >= 15
    b.landed.connect(_on_bolt_landed.bind(enemy, dmg, action, crit, tier))
    bolts.add_child(b)
    bolts_sent += 1
    Audio.sfx(&"cast", -6.0, 0.08)

## Снаряд долетел: урон, цифра над нечистью, звук, тряска. Пока летел, нечисть могла пасть или забег — кончиться.
func _on_bolt_landed(target: Enemy, dmg: int, action: ActionData, crit: bool, tier: int) -> void:
    bolts_landed += 1
    if finished or not is_instance_valid(target) or target.dead:
        return
    var will_kill: bool = target.hp - dmg <= 0
    if will_kill and action.fatal_money > 0:
        extra_money = action.fatal_money
    target.hurt(dmg)  # damage_dealt считает сам Enemy.hurt
    var big: bool = dmg >= 15 or will_kill
    # Под бонусом комбо цифры урона окрашены в цвет ступени — видно, что бьёшь сильнее.
    var col: Color = Color.WHITE if tier == 0 else Color.WHITE.lerp(COMBO_COLORS[tier], 0.75)
    if crit:
        col = GOLD.lightened(0.3)
    pop("-%d" % dmg, 0.0, false, col, big or crit, pops.to_local(target.label_point()) + Vector2(randf_range(-60.0, 60.0), 0.0))
    Audio.sfx(&"hit_big" if big else &"hit", -1.0)
    Globals.shake(5.0 + minf(dmg, 40.0) * 0.25, 0.15)
    if will_kill:
        _finisher(target)
    else:
        if big:
            Globals.hitstop(0.04)
            Globals.pulse(&"hit", 0.6)
        _check_seal()

## Добивание (2.6): стоп-кадр → замедление, рывок камеры, выцветание и глухая музыка — делает Main (Globals.finisher);
## здесь — звук «удар + время тянется». Печать (поимка) — своя сцена, без добивания.
func _finisher(target: Enemy) -> void:
    finishers += 1
    Globals.finisher(target.hit_point(), BOSS_FINISHER if boss else 1.0)
    Audio.sfx(&"finisher", 0.0 if boss else -2.0, 0.03, 0.85 if boss else 1.0)

func _on_ring_expired(section: Section) -> void:
    var action: ActionData = section.data
    if action == null or finished:
        return
    if action.kind == ActionData.Kind.SEAL:
        pop(tr("POP_ESCAPED"), section.center, true, GOLD)
        ring.frenzy = false
        return
    if action.hurt_on_expire:
        # Атака догорела — серия попаданий прервана (даже если бусы уберегли от раны).
        _combo_break()
        if free_hits > 0:
            pop(tr("POP_NULLIFIED"), section.center, true)
        else:
            pop(tr("POP_OUCH"), section.center, false, BLOOD, true)
        hurt(section.center)
        if enemy:
            enemy.attack()

func _on_ring_missed(angle: float) -> void:
    pop(tr("POP_MISS"), angle, true, ring.enemy_color)
    # Промах между врагами (на круге пусто) комбо не рвёт — бить было не по чему.
    if not ring.player_actions.is_empty():
        _combo_break()

# ---------------- замах нечисти (2.4) ----------------
## Атака заряжается на круге: нечисть отклоняется назад, глаза вспыхивают.
func _on_ring_telegraph_started(section: Section) -> void:
    if finished or enemy == null or enemy.dead:
        return
    enemy.windup(section.charge_time)
    Audio.sfx(&"windup", -5.0, 0.05)

## Атака вспыхнула и стала настоящей секцией: рывок вперёд.
func _on_ring_telegraph_armed(_section: Section) -> void:
    if finished or enemy == null or enemy.dead:
        return
    enemy.cast()
    Audio.sfx(&"ignite", -6.0, 0.08)

## Атаку отбили, пока она заряжалась (или бой кончился): если других замахов нет — нечисть успокаивается.
func _on_ring_telegraph_cancelled(_section: Section) -> void:
    if enemy == null or enemy.dead or ring.charging_count() > 0:
        return
    enemy.calm()

## Рана: полжизни и трещина на круге там, где атака прорвала черту (angle < 0 — в свободном месте, 2.5).
func hurt(angle: float = -1.0) -> void:
    if finished:
        return
    if free_hits > 0:
        free_hits -= 1
        Audio.sfx(&"dodge")
        return
    gs.health = maxf(gs.health - GameState.WOUND_STEP, 0.0)
    gs.add_wound(angle)
    Audio.sfx(&"hurt")
    Globals.shake(16.0, 0.3)
    Globals.hitstop(0.08)
    Globals.pulse(&"hurt", 1.0)
    if gs.health <= 0.0:
        finished = true
        ring.stopped = true
        ring.clear()
        died.emit()

# ---------------- Печать ----------------
func _can_seal() -> bool:
    return not boss and enemy != null and not enemy.dead and enemy.data.spirit != null and gs.jars > 0

func _check_seal() -> void:
    if seal_offered or not _can_seal():
        return
    if enemy.hp_ratio() > SEAL_THRESHOLD:
        return
    seal_offered = true
    var s: Section = ring.add_section_ahead(SEAL_ACTION, 0.3, 0.65)
    ring.frenzy = true
    # Ярость: сразу атака с замахом (2.4). Атак нет (первая нечисть за ночь) — просто рык.
    if ring.add_enemy_action() == null:
        enemy.attack()
    Audio.sfx(&"seal_appear")
    Globals.pulse(&"gold", 0.6)
    pop(tr("POP_SEAL_NOW"), s.center, true, GOLD)
    if not bool(Save.data.get("seal_hint", false)):
        Save.set_flag("seal_hint", true)
        hint.text = tr("HINT_SEAL")
        hint.modulate = Color(GOLD, 1.0)
        hint.visible = true

func _try_seal(section: Section) -> void:
    if not _can_seal():
        return
    _combo_hit()
    var spirit: ItemData = enemy.data.spirit
    gs.jars -= 1
    gs.spirits_caught += 1
    var upgraded: bool = spirit.apply_to(gs)
    var first_time: bool = Save.add_spirit(enemy.data.id)
    ring.frenzy = false
    pop(tr("POP_SEALED"), section.center, false, GOLD, true)
    var title: String = tr(spirit.name) + (" +" if upgraded else "")
    if first_time:
        title = tr("POP_NEW_SPIRIT") + "\n" + title
    pop(title, PI * 0.5, true, GOLD, false, Vector2(0, 40))
    Audio.sfx(&"seal")
    Globals.pulse(&"gold", 1.0)
    Globals.hitstop(0.12)
    Globals.shake(10.0, 0.3)
    enemy.seal_away()

# ---------------- комбо ----------------
## Попадание по секции в бою: комбо +1, нота выше. На ступенях (5 / 10) — фанфара и бонус урона.
func _combo_hit() -> void:
    combo += 1
    gs.best_combo = maxi(gs.best_combo, combo)
    var tier: int = GameState.combo_tier(combo)
    if combo >= 2:
        var step: int = COMBO_PITCH[mini(combo - 2, COMBO_PITCH.size() - 1)]
        Audio.sfx(&"combo", -8.0 + 2.0 * tier, 0.0, pow(2.0, step / 12.0))
    if GameState.COMBO_TIERS.has(combo):
        Audio.sfx(&"combo_up", -3.0, 0.0)
        Globals.pulse(&"gold", 0.3 + 0.2 * tier)
        var pct: int = roundi(GameState.combo_bonus(combo) * 100.0)
        pop(tr("POP_COMBO_TIER") % [combo, pct], PI * 0.5, true, COMBO_COLORS[tier], false, Vector2(0, -20))
    _show_combo()

## «Идеально»: надпись снаружи круга (чтобы не спорить с цифрой урона), звон, вспышка, микро-замедление.
func _perfect_fx(angle: float) -> void:
    gs.perfect_hits += 1
    pop(tr("POP_PERFECT"), angle, true, GOLD, false, (POP_R + 64.0) * Vector2.RIGHT.rotated(angle))
    Audio.sfx(&"perfect", -2.0, 0.03)
    Globals.pulse(&"gold", 0.25)
    Globals.pulse(&"hit", 0.35)
    # В конце кадра: стоп-кадр самого удара (_deal) встанет первым, замедление — за ним.
    Globals.hitstop.call_deferred(PERFECT_SLOWMO_TIME, PERFECT_SLOWMO_SCALE)

## Промах или рана: серия обнулилась. Большую серию жалко — звук «мел крошится».
func _combo_break() -> void:
    if combo == 0:
        return
    var was: int = combo
    combo = 0
    if was >= GameState.COMBO_TIERS[0]:
        Audio.sfx(&"combo_break", -4.0)
    if was >= 2:
        _drop_combo()

func _show_combo() -> void:
    if combo < 2:
        return
    var tier: int = GameState.combo_tier(combo)
    var col: Color = COMBO_COLORS[tier]
    var bonus: float = GameState.combo_bonus(combo)
    if _combo_tween:
        _combo_tween.kill()
    combo_label.text = tr("HUD_COMBO") % combo
    combo_label.position.y = _combo_y
    combo_label.rotation = 0.0
    combo_label.modulate = col
    combo_label.pivot_offset = combo_label.size * 0.5
    combo_label.scale = Vector2.ONE * (1.3 + 0.15 * tier)
    if bonus > 0.0:
        combo_bonus_label.text = tr("HUD_COMBO_BONUS") % roundi(bonus * 100.0)
        combo_bonus_label.modulate = col
    else:
        combo_bonus_label.modulate.a = 0.0
    _combo_tween = create_tween()
    _combo_tween.tween_property(combo_label, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

## Счётчик «осыпается»: сереет, падает и гаснет.
func _drop_combo() -> void:
    if _combo_tween:
        _combo_tween.kill()
    combo_label.modulate = Color(COMBO_BROKEN, combo_label.modulate.a)
    combo_label.pivot_offset = combo_label.size * 0.5
    _combo_tween = create_tween().set_parallel()
    _combo_tween.tween_property(combo_label, "position:y", _combo_y + 26.0, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
    _combo_tween.tween_property(combo_label, "rotation", randf_range(-0.25, 0.25), 0.5)
    _combo_tween.tween_property(combo_label, "modulate:a", 0.0, 0.5)
    _combo_tween.tween_property(combo_bonus_label, "modulate:a", 0.0, 0.2)

func _on_blind_timer_timeout() -> void:
    ring.blind = false
    Audio.set_muffled(false)

func _on_heartbeat_timer_timeout() -> void:
    if not finished and gs.health <= 1.0 and gs.health > 0.0:
        Audio.sfx(&"heartbeat", -3.0, 0.0)
        Globals.pulse(&"beat", 0.5)

## Всплывающий текст. angle — где на круге; fixed_pos — если задан, ставим в эту точку центра.
func pop(text: String, angle: float, small: bool = false, color: Color = Color.WHITE, big: bool = false, fixed_pos: Variant = null) -> void:
    var p: Node2D = POP_SCENE.instantiate()
    p.set(&"text", text)
    p.set(&"small", small)
    p.set(&"big", big)
    p.modulate = color
    if fixed_pos is Vector2:
        p.position = fixed_pos
    else:
        p.position = POP_R * Vector2.RIGHT.rotated(angle)
    pops.add_child(p)
