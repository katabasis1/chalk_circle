extends Resource
class_name ItemData
## Товар Домового или пойманный дух. Активный (action) или пассивный (global_stat).

enum Type { SPELL, CHARM, SPIRIT }

@export var id: StringName
@export var name: String
@export_multiline var info: String
@export_multiline var upgrade_info: String
@export var type: Type = Type.SPELL
@export var icon: Texture2D
@export var price: int = 120
@export var action: ActionData

@export_group("Upgrade")
@export var global_stat: String
@export var global_gain: float
@export var action_stat: String
@export var action_gain: float

var level: int = 0

func make_instance() -> ItemData:
    var dup: ItemData = duplicate()
    if dup.action:
        dup.action = dup.action.duplicate()
    return dup

## Применить покупку/поимку к состоянию забега. Возвращает true, если это улучшение.
func apply_to(state: GameState) -> bool:
    var upgrade: bool = false
    for other in state.items:
        if other.id == id:
            upgrade = true
            if other.action and other.action_stat != "":
                other.action.set(other.action_stat, float(other.action.get(other.action_stat)) + other.action_gain)
            other.level += 1
            if other.global_stat != "":
                _add_stat(state, other.global_stat, other.global_gain)
            return true
    var inst: ItemData = make_instance()
    inst.level = 1
    state.items.append(inst)
    if inst.global_stat != "":
        _add_stat(state, inst.global_stat, inst.global_gain)
    return upgrade

static func _add_stat(state: GameState, stat: String, gain: float) -> void:
    var cur: Variant = state.get(stat)
    if typeof(cur) == TYPE_INT:
        state.set(stat, int(cur) + int(round(gain)))
    else:
        state.set(stat, float(cur) + gain)

func level_in(state: GameState) -> int:
    for other in state.items:
        if other.id == id:
            return other.level
    return 0
