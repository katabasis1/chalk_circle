extends Resource
class_name NpcData
## Нечисть: внешний вид, атаки, дух для Печати.

@export var id: StringName
@export var name: String
@export var texture: Texture2D
@export var color: Color = Color.WHITE
@export var sprite_scale: float = 0.85
@export var sprite_offset: Vector2 = Vector2.ZERO
@export var float_amount: float = 6.0
## Замах (2.4): где на картинке глаза (UV 0..1, не больше двух) — там вспыхивают блики.
## Для SVG-заглушек и PNG нейросети точки разные: их ставит tools/build_data.py.
@export var eyes: PackedVector2Array = PackedVector2Array()
## Радиус блика (доля высоты картинки).
@export var eye_size: float = 0.016
@export var boss: bool = false
@export var actions: Array[ActionData] = []
## Дух, который достаётся при Печати (null — нельзя запечатать).
@export var spirit: ItemData

func get_scaled_actions(enemies_killed: int) -> Array[ActionData]:
    var out: Array[ActionData] = []
    if boss:
        out.assign(actions)
        return out
    if actions.is_empty() or enemies_killed == 0:
        return out
    if enemies_killed == 1:
        out.append(actions[0])
        return out
    out.assign(actions)
    return out

func get_scaled_hp(enemies_killed: int) -> int:
    return int((enemies_killed * 5 + 10 * pow(1.1, enemies_killed)) * (5.0 if boss else 1.0))
