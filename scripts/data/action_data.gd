extends Resource
class_name ActionData
## Одна секция на круге: заговор игрока, атака нечисти, Печать или кнопка интерфейса.

enum Size { SMALL, MEDIUM, LARGE }
enum Lifetime { FOREVER, LONG, NORMAL, SHORT, FLASH }
enum Kind { PLAYER, ENEMY, SEAL, UI }

const SIZES: Array[float] = [0.05, 0.1, 0.2]
const LIFETIMES: Array[float] = [-1.0, 3.2, 2.2, 1.4, 0.8]

## Ключ перевода (locale/strings.csv). Пусто — без подписи.
@export var text: String = ""
@export var kind: Kind = Kind.PLAYER
@export var size: Size = Size.MEDIUM
@export var lifetime: Lifetime = Lifetime.NORMAL
## 0..1 — фиксированное место на круге (доля оборота), -1 — случайное.
@export var fixed_location: float = -1.0
## Скорость движения секции по кругу (рад/с).
@export var move_speed: float = 0.0

@export_group("Effects")
@export var repeats: float = 0.0
@export var damage: float = 0.0
@export var percent_enemy_hp_damage: float = 0.0
@export var damage_gain: float = 0.0
@export var damage_per_enemy_attack: float = 0.0
@export var next_attack_bonus: float = 0.0
@export var fatal_money: int = 0
@export var parry: bool = false
@export var reverse: bool = false
@export var teleport: bool = false
@export var speedup: float = 0.0
@export var blind: float = 0.0
@export var hurt_on_press: bool = false
@export var hurt_on_expire: bool = false

var actual_size: float:
    get:
        return SIZES[size]

var actual_lifetime: float:
    get:
        return LIFETIMES[lifetime]

var is_special: bool:
    get:
        return reverse or teleport or speedup > 0.0 or blind > 0.0 or move_speed != 0.0
