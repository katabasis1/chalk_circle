extends Node2D
## Главное меню: круг с секциями «Начать» (или «Продолжить» + «Заново», если есть сохранённый забег) и «Бестиарий».

signal play
signal continue_run

const PLAY: ActionData = preload("res://data/actions/ui/play.tres")
const CONTINUE: ActionData = preload("res://data/actions/ui/continue.tres")
const NEW_RUN: ActionData = preload("res://data/actions/ui/new_run.tres")
const BESTIARY: ActionData = preload("res://data/actions/ui/bestiary.tres")

@onready var ring: Ring = $Ring
@onready var reader: Node2D = %Reader
@onready var bestiary: Control = %Bestiary
@onready var best_label: Label = %BestLabel
@onready var caught_label: Label = %CaughtLabel
@onready var slots: Control = %Slots

var _showing_bestiary: bool = false
var _has_run: bool = false

func _ready() -> void:
    _refresh()
    _setup_ring()
    bestiary.visible = false
    bestiary.modulate.a = 0.0
    # Облако могло догрузиться позже — обновим рекорд, бестиарий и «Продолжить».
    Save.changed.connect(_on_save_changed)

func _on_save_changed() -> void:
    _refresh()
    if Save.has_run() != _has_run:
        _setup_ring()

func _refresh() -> void:
    var best: int = int(Save.data.get("best_night", 0))
    best_label.text = tr("MENU_BEST") % best if best > 0 else Globals.device_text("MENU_HINT")
    var caught: int = 0
    for slot in slots.get_children():
        var id: StringName = StringName(slot.name)
        var known: bool = Save.has_spirit(id)
        if known:
            caught += 1
        var icon: TextureRect = slot.get_node("Icon")
        var name_l: Label = slot.get_node("Name")
        icon.self_modulate = Color.WHITE if known else Color(0, 0, 0, 0.9)
        name_l.text = tr("NPC_" + str(id).to_upper()) if known else "???"
    caught_label.text = tr("BESTIARY_CAUGHT") % [caught, slots.get_child_count()]

func _setup_ring() -> void:
    _has_run = Save.has_run()
    var ui: Array[ActionData] = []
    if _has_run:
        ui = [CONTINUE, NEW_RUN, BESTIARY]
    else:
        ui = [PLAY, BESTIARY]
    ring.set_ui(ui)
    if _has_run:
        var night: int = int(Save.get_run().get("rounds_won", 0)) + 1
        _label(ring.find_section(CONTINUE), tr("UI_CONTINUE_N") % night)

func _label(s: Section, text: String) -> void:
    if s == null:
        return
    if s.is_node_ready():
        s.set_text(text)
    else:
        s.label_override = text

func _on_ring_pressed(section: Section) -> void:
    if section.data == PLAY or section.data == NEW_RUN:
        play.emit()
    elif section.data == CONTINUE:
        continue_run.emit()
    elif section.data == BESTIARY:
        _toggle_bestiary()
        # Кнопка интерфейса «вечная»: возвращаем её на место.
        ring.add_section(BESTIARY)

func _toggle_bestiary() -> void:
    _showing_bestiary = not _showing_bestiary
    Audio.sfx(&"tick")
    var tw: Tween = create_tween().set_parallel()
    if _showing_bestiary:
        bestiary.visible = true
        tw.tween_property(bestiary, "modulate:a", 1.0, 0.25)
        tw.tween_property(reader, "modulate:a", 0.0, 0.2)
    else:
        tw.tween_property(bestiary, "modulate:a", 0.0, 0.2)
        tw.tween_property(reader, "modulate:a", 1.0, 0.25)
        tw.chain().tween_callback(bestiary.hide)
