extends Control
class_name HpBar
## Дуга здоровья нечисти вокруг числа (2.7) с «призраком». Удар сразу срезает красную дугу, а срезанный кусок
## остаётся светлым меловым следом: миг держится и стекает к новому значению. Удары подряд копят след —
## видно, сколько снесла серия. С концов срезанной дуги сыплются крошки. Новая нечисть — дуга прорисовывается
## с нуля. Дуга растёт от верха круга в обе стороны (там же золотая отметка Печати), поэтому след виден на обоих концах.
## Всё в игровом времени: стоп-кадр и замедление удара держат след вместе с остальным миром.

## Красная дуга догоняет здоровье за SNAP_TIME; след держится GHOST_HOLD после последнего удара и стекает
## за GHOST_DRAIN; новая нечисть — дуга прорисовывается за REFILL_TIME (с).
const SNAP_TIME: float = 0.08
const GHOST_HOLD: float = 0.45
const GHOST_DRAIN: float = 0.4
const REFILL_TIME: float = 0.5
## Крупный удар (доля полного здоровья): ярче вспышка и вдвое больше крошек.
const BIG_CHUNK: float = 0.15
## Вспышка красной дуги при ударе (обычный / крупный): слабая — срез должен читаться, а не тонуть в белом.
const ARC_FLASH: float = 0.12
const ARC_FLASH_BIG: float = 0.3
## Середина толщины дуги (доля полуразмера узла; r_in 0.86 … r_out 0.96) — оттуда сыплются крошки.
const ARC_R: float = 0.91

## Доля здоровья: к которой идёт дуга / которую показывает сейчас / где след. Счётчики — для смоук-теста.
var ratio: float = 0.0
var shown: float = 0.0
var ghost: float = 0.0
var hits: int = 0
var drains: int = 0

var _arc_tween: Tween
var _ghost_tween: Tween
var _flash_tween: Tween

@onready var arc: ColorRect = $Arc
@onready var ghost_rect: ColorRect = $Ghost
@onready var crumbs_left: CPUParticles2D = $CrumbsLeft
@onready var crumbs_right: CPUParticles2D = $CrumbsRight

func _ready() -> void:
    _set_both(0.0)

## Здоровье нечисти. fresh — новая нечисть: дуга прорисовывается с нуля, без следа.
## Иначе удар: красная дуга срезается почти сразу, срезанное остаётся следом (или копится к уже висящему).
func set_hp(hp: int, max_hp: int, fresh: bool = false) -> void:
    var r: float = clampf(float(hp) / float(maxi(max_hp, 1)), 0.0, 1.0)
    if fresh:
        ratio = r
        _kill_tweens()
        _set_both(0.0)
        _arc_tween = create_tween()
        _arc_tween.tween_method(_set_both, 0.0, r, REFILL_TIME).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
        return
    if r >= ratio:
        # Подлечилась (у нечисти такого пока нет): след сразу встаёт на новое значение, красная дуга дорастает до него.
        ratio = r
        if _ghost_tween:
            _ghost_tween.kill()
        _set_ghost(maxf(ghost, r))
        if _arc_tween:
            _arc_tween.kill()
        _arc_tween = create_tween()
        _arc_tween.tween_method(_set_shown, shown, r, REFILL_TIME).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
        return
    var chunk: float = ratio - r
    ratio = r
    hits += 1
    # След — от того, что было видно до удара; если он уже висит выше (серия), остаётся там.
    _set_ghost(maxf(maxf(ghost, shown), r))
    if _arc_tween:
        _arc_tween.kill()
    _arc_tween = create_tween()
    _arc_tween.tween_method(_set_shown, shown, r, SNAP_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
    if _ghost_tween:
        _ghost_tween.kill()
    _ghost_tween = create_tween()
    _ghost_tween.tween_interval(GHOST_HOLD)
    _ghost_tween.tween_method(_set_ghost, ghost, r, GHOST_DRAIN).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
    _ghost_tween.tween_callback(_on_drained)
    var big: bool = chunk >= BIG_CHUNK
    _flash(big)
    _crumble(r, big)

func _on_drained() -> void:
    drains += 1

func _kill_tweens() -> void:
    for tw in [_arc_tween, _ghost_tween, _flash_tween]:
        if tw:
            (tw as Tween).kill()

func _set_both(v: float) -> void:
    shown = v
    ghost = v
    _apply()

func _set_shown(v: float) -> void:
    shown = v
    _apply()

func _set_ghost(v: float) -> void:
    ghost = v
    _apply()

## Красная дуга поверх следа; след прячем, когда он целиком под ней (иначе его ореол красит края красной дуги).
func _apply() -> void:
    (arc.material as ShaderMaterial).set_shader_parameter(&"arc_size", TAU * shown)
    (ghost_rect.material as ShaderMaterial).set_shader_parameter(&"arc_size", TAU * ghost)
    ghost_rect.visible = ghost > shown + 0.001

## Вспышка удара: след загорается белым и остывает до мела; красная дуга вспыхивает слабее (крупный удар — ярче).
func _flash(big: bool) -> void:
    if _flash_tween:
        _flash_tween.kill()
    _flash_tween = create_tween().set_parallel()
    _flash_tween.tween_method(_set_flash.bind(ghost_rect), 1.0, 0.0, 0.3)
    _flash_tween.tween_method(_set_flash.bind(arc), ARC_FLASH_BIG if big else ARC_FLASH, 0.0, 0.15)

func _set_flash(v: float, rect: ColorRect) -> void:
    (rect.material as ShaderMaterial).set_shader_parameter(&"flash", v)

## Крошки с обоих новых концов дуги: летят вдоль срезанного куска и падают. Угол растёт по часовой (y вниз),
## дуга от верха (−π/2) на ±π·r.
func _crumble(r: float, big: bool) -> void:
    var c: Vector2 = size * 0.5
    var rad: float = size.x * 0.5 * ARC_R
    for side in [1.0, -1.0]:
        var a: float = -PI * 0.5 + side * PI * r
        var p: CPUParticles2D = crumbs_right if side > 0.0 else crumbs_left
        p.position = c + Vector2(cos(a), sin(a)) * rad
        # Касательная в сторону срезанного куска.
        p.rotation = a + side * PI * 0.5
        var n: int = 12 if big else 6
        if p.amount != n:
            p.amount = n
        p.restart()
