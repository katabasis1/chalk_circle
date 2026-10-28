extends Node2D
## Финал забега: «Ты пал» или «Рассвет». Секции: заново, в меню, воскреснуть (реклама за награду), до петухов (бесконечный).

signal play_again
signal endless
signal to_menu
signal revive

const AGAIN: ActionData = preload("res://data/actions/ui/again.tres")
const ENDLESS: ActionData = preload("res://data/actions/ui/endless.tres")
const MENU: ActionData = preload("res://data/actions/ui/menu.tres")
const REVIVE: ActionData = preload("res://data/actions/ui/revive.tres")

@export var victory: bool = false

@onready var ring: Ring = $Ring
@onready var title: Label = %Title
@onready var subtitle: Label = %Subtitle
@onready var stats: Label = %Stats

func _ready() -> void:
    var gs: GameState = Globals.game_state
    title.text = tr("END_VICTORY") if victory else tr("END_DEATH")
    subtitle.text = tr("END_VICTORY_SUB") if victory else tr("END_DEATH_SUB")
    stats.text = tr("END_STATS") % [gs.rounds_won, gs.enemies_killed, gs.spirits_caught, gs.damage_dealt, gs.money_earned, gs.best_combo, gs.perfect_hits]
    var ui: Array[ActionData] = [AGAIN, MENU]
    if victory:
        ui.append(ENDLESS)
    elif not gs.revived:
        ui.append(REVIVE)
    ring.set_ui(ui)
    title.modulate = Color("ffd25a") if victory else Color("ff3348")
    Platform.rewarded_result.connect(_on_rewarded_result)

## Реклама не досмотрена / ошибка — возвращаем «Воскреснуть» на круг.
func _on_rewarded_result(tag: StringName, success: bool) -> void:
    if tag == &"revive" and not success and not Globals.game_state.revived:
        ring.add_section_if_not_exist(REVIVE)

func _on_ring_pressed(section: Section) -> void:
    var data: ActionData = section.data
    if data == AGAIN:
        play_again.emit()
    elif data == MENU:
        to_menu.emit()
    elif data == ENDLESS:
        endless.emit()
    elif data == REVIVE:
        revive.emit()
