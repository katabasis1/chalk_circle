extends Node2D
class_name Enemy
## Нечисть. Вся «анимация» — AnimationPlayer в enemy.tscn, которая крутит свойства flash/dissolve/swirl → шейдер creature.
## Замах (2.4): windup() — пока атака заряжается на круге (отклонилась назад, глаза вспыхнули),
## cast() — атака сорвалась на круг (рывок вперёд), calm() — замах сорвался, обратно в idle.

signal died(sealed: bool)
signal hp_changed(hp: int, max_hp: int)

var data: NpcData
var hp: int = 10
var max_hp: int = 10
var been_hit: bool = false
var dead: bool = false

var flash: float = 0.0:
    set(value):
        flash = value
        _set_param(&"flash", value)
var dissolve: float = 0.0:
    set(value):
        dissolve = value
        _set_param(&"dissolve", value)
var swirl: float = 0.0:
    set(value):
        swirl = value
        _set_param(&"swirl", value)
var eye_glow: float = 1.4:
    set(value):
        eye_glow = value
        _set_param(&"eye_glow", value)
var eye_flash: float = 0.0:
    set(value):
        eye_flash = value
        _set_param(&"eye_flash", value)

## Длина анимации «windup» в enemy.tscn: play() растягивает её ровно под время заряда секции.
const WINDUP_LEN: float = 0.5

var _mat: ShaderMaterial

@onready var sprite: Sprite2D = %Sprite
@onready var body_shaker: Shaker = %BodyShaker
@onready var aura: Sprite2D = %Aura
@onready var hit_burst: CPUParticles2D = %HitBurst
@onready var death_burst: CPUParticles2D = %DeathBurst
@onready var seal_burst: CPUParticles2D = %SealBurst
@onready var anim: AnimationPlayer = $AnimationPlayer

func setup(d: NpcData, hp_value: int) -> void:
    data = d
    hp = hp_value
    max_hp = hp_value

func _ready() -> void:
    _mat = sprite.material as ShaderMaterial
    sprite.texture = data.texture
    sprite.scale = Vector2.ONE * data.sprite_scale
    sprite.position = data.sprite_offset
    aura.modulate = Color(data.color, 0.55)
    hit_burst.color = data.color.lightened(0.3)
    death_burst.color = data.color
    body_shaker.float_amount = data.float_amount
    _set_param(&"flash_color", Color(1.0, 0.95, 0.85))
    _set_param(&"burn_color", data.color.lightened(0.2))
    _setup_eyes()
    anim.play(&"appear")
    anim.queue(&"idle")
    Audio.sfx(&"enemy_appear", -2.0)

func hurt(damage: float) -> void:
    if dead or int(damage) <= 0:
        return
    been_hit = true
    var dmg: int = int(damage)
    hp -= dmg
    Globals.game_state.damage_dealt += dmg
    body_shaker.shake(8.0 + minf(dmg, 40.0) * 0.4, 0.22)
    hit_burst.restart()
    hp_changed.emit(maxi(hp, 0), max_hp)
    if hp <= 0:
        hp = 0
        die()
        return
    _play(&"hurt")

func attack() -> void:
    if dead:
        return
    _play(&"attack")

## Замах (2.4): атака заряжается time секунд. Поза и вспышка глаз держатся до cast()/calm().
func windup(time: float) -> void:
    if dead or anim.current_animation == &"appear":
        return
    # Две атаки подряд (ярость Печати): уже замахнулась — не начинаем заново.
    if anim.assigned_animation == &"windup":
        return
    anim.clear_queue()
    anim.play(&"windup", 0.06, WINDUP_LEN / maxf(time, 0.05))

## Атака вспыхнула на круге: рывок вперёд → idle. Замах успели сбить ударом (hurt) — обычный выпад
## из покоя, иначе «cast» дёрнул бы тело из позы замаха, которой уже нет.
func cast() -> void:
    if dead:
        return
    _play(&"cast" if is_winding_up() else &"attack")

## Замах сорвался (атаку отбили) — плавно обратно в idle. Если уже играет что-то другое (удар), не мешаем.
func calm() -> void:
    if dead or anim.assigned_animation != &"windup":
        return
    anim.clear_queue()
    anim.play(&"idle", 0.2)

func is_winding_up() -> bool:
    return not dead and anim.assigned_animation == &"windup"

func die() -> void:
    dead = true
    anim.clear_queue()
    anim.play(&"die")
    death_burst.restart()
    Audio.sfx(&"enemy_die", -1.0)
    died.emit(false)

## Дух затягивает в склянку.
func seal_away() -> void:
    if dead:
        return
    dead = true
    anim.clear_queue()
    anim.play(&"seal")
    seal_burst.restart()
    died.emit(true)

## Короткая реакция → снова idle. Очередь чистим, чтобы «idle» не копились.
func _play(anim_name: StringName) -> void:
    # Не рвём «появление» (иначе шейдер застрянет полупрозрачным) — тряска и искры и так есть.
    if anim.current_animation == &"appear":
        return
    anim.clear_queue()
    anim.play(anim_name)
    anim.queue(&"idle")

## Куда бить снарядом (2.3): середина спрайта (вместе с парением и тряской тела).
func hit_point() -> Vector2:
    return sprite.global_position

## Над нечистью — сюда всплывают цифры урона (2.3). Высота — по реальному размеру картинки.
func label_point() -> Vector2:
    var h: float = 300.0
    if sprite.texture:
        h = sprite.texture.get_height() * absf(sprite.global_scale.y)
    return sprite.global_position - Vector2(0.0, h * 0.3)

## Глаза для вспышки при замахе: точки в UV картинки из NpcData (нет точек — горит только яркое, без бликов).
func _setup_eyes() -> void:
    var eyes: PackedVector2Array = data.eyes
    _set_param(&"eye_count", mini(eyes.size(), 2))
    if eyes.size() > 0:
        _set_param(&"eye_a", eyes[0])
    if eyes.size() > 1:
        _set_param(&"eye_b", eyes[1])
    _set_param(&"eye_size", data.eye_size)
    _set_param(&"eye_color", data.color.lerp(Color.WHITE, 0.25))

func hp_ratio() -> float:
    return float(hp) / float(maxi(max_hp, 1))

func _set_param(param: StringName, value: Variant) -> void:
    if _mat:
        _mat.set_shader_parameter(param, value)
