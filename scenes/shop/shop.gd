extends Node2D
## Лавка Домового. Как в оригинале: одна вещь, «другое», отвар (+0.5 здоровья), «дальше».

signal done

const POP_SCENE: PackedScene = preload("res://scenes/fx/pop.tscn")
const BUY: ActionData = preload("res://data/actions/ui/buy.tres")
const SNACK: ActionData = preload("res://data/actions/ui/snack.tres")
const REROLL: ActionData = preload("res://data/actions/ui/reroll.tres")
const DONE: ActionData = preload("res://data/actions/ui/done.tres")
const GOLD: Color = Color("ffd25a")
const TYPE_KEYS: Array[String] = ["TYPE_SPELL", "TYPE_CHARM", "TYPE_SPIRIT"]

var snack_price: int = 20
var reroll_price: int = 20
var free_snacks_left: int = 0
var free_rerolls_left: int = 0
var item: ItemData
var busy: bool = false
## «ДАЛЬШЕ» нажато; если шла покупка — выходим, когда она доиграет.
var leaving: bool = false

@onready var ring: Ring = $Ring
@onready var pops: Node2D = $Pops
@onready var anim: AnimationPlayer = $Domovoy/AnimationPlayer
@onready var card: Control = %Card
@onready var item_contents: Control = %ItemContents
@onready var sold_out: Label = %SoldOut
@onready var item_icon: TextureRect = %ItemIcon
@onready var item_title: Label = %ItemTitle
@onready var item_type: Label = %ItemType
@onready var item_info: Label = %ItemInfo
@onready var card_shaker: Shaker = %CardShaker

var gs: GameState:
    get:
        return Globals.game_state

func _ready() -> void:
    free_snacks_left = int(gs.free_snacks)
    free_rerolls_left = int(gs.free_rerolls)
    item = Registry.ITEMS[randi() % Registry.ITEMS.size()]
    _show_item()
    update_ui()
    anim.play(&"idle")

func _show_item() -> void:
    var level: int = item.level_in(gs)
    var upgrade: bool = level > 0
    item_title.text = tr(item.name) + ("+".repeat(level) if level <= 3 else "+%d" % level)
    item_type.text = tr("TYPE_UPGRADE") if upgrade else tr(TYPE_KEYS[item.type])
    item_info.text = tr(item.upgrade_info if upgrade else item.info)
    item_icon.texture = item.icon
    item_icon.visible = item.icon != null

func _on_ring_pressed(section: Section) -> void:
    if leaving:
        return
    var data: ActionData = section.data
    if data == DONE:
        leaving = true
        if not busy:
            done.emit()
        return
    if busy:
        update_ui()
        return
    if data == BUY:
        if gs.cash < item.price:
            return
        busy = true
        gs.cash -= item.price
        var used_snacks: int = int(gs.free_snacks) - free_snacks_left
        var used_rerolls: int = int(gs.free_rerolls) - free_rerolls_left
        item.apply_to(gs)
        free_snacks_left = int(gs.free_snacks) - used_snacks
        free_rerolls_left = int(gs.free_rerolls) - used_rerolls
        pop(tr("POP_BOUGHT"), section.center, false, GOLD, true)
        Audio.sfx(&"buy")
        Globals.pulse(&"gold", 0.5)
        _smile()
        update_ui()
        await get_tree().create_timer(0.45, false).timeout
        busy = false
        if leaving:
            done.emit()
            return
        reroll()
    elif data == SNACK:
        if free_snacks_left > 0:
            free_snacks_left -= 1
        elif gs.cash >= snack_price:
            gs.cash -= snack_price
            snack_price += 10
        else:
            return
        gs.health = minf(gs.health + 0.5, gs.max_health)
        pop(tr("POP_YUM"), section.center)
        Audio.sfx(&"buy")
        _smile()
    elif data == REROLL:
        if free_rerolls_left > 0:
            free_rerolls_left -= 1
        elif gs.cash >= reroll_price:
            gs.cash -= reroll_price
            reroll_price += 10
        else:
            return
        pop(tr("POP_REROLL"), section.center)
        Audio.sfx(&"coin")
        _smile()
        reroll()
    update_ui()

func reroll() -> void:
    var valid: Array = Registry.ITEMS + gs.items + gs.items + gs.items
    var next_item: ItemData = item
    for i in 100:
        next_item = valid[randi() % valid.size()]
        if next_item.id != item.id:
            break
    item = next_item
    _show_item()
    card_shaker.shake(10.0, 0.2)
    card.scale = Vector2(1.08, 1.08)
    create_tween().tween_property(card, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    update_ui()

func update_ui() -> void:
    # Нажатая секция умирает — «ДАЛЬШЕ» всегда возвращаем на круг, пока не уходим.
    if not leaving:
        ring.add_section_if_not_exist(DONE)
    var can_buy: bool = gs.cash >= item.price
    sold_out.visible = not can_buy
    item_contents.modulate.a = 1.0 if can_buy else 0.35
    if can_buy:
        _label(ring.add_section_if_not_exist(BUY), "%s  %d" % [tr("SHOP_BUY"), item.price])
    else:
        ring.remove_section(BUY)

    var reroll_ok: bool = free_rerolls_left > 0 or gs.cash >= reroll_price
    if reroll_ok:
        _label(ring.add_section_if_not_exist(REROLL), "%s  %s" % [tr("SHOP_REROLL"), tr("SHOP_FREE") if free_rerolls_left > 0 else str(reroll_price)])
    else:
        ring.remove_section(REROLL)

    var snack_ok: bool = (free_snacks_left > 0 or gs.cash >= snack_price) and gs.health < gs.max_health
    if snack_ok:
        _label(ring.add_section_if_not_exist(SNACK), "%s  %s" % [tr("SHOP_SNACK"), tr("SHOP_FREE") if free_snacks_left > 0 else str(snack_price)])
    else:
        ring.remove_section(SNACK)

func _label(s: Section, text: String) -> void:
    if s == null:
        return
    if s.is_node_ready():
        if s.label.text != text:
            s.set_text(text)
    else:
        s.label_override = text

func _smile() -> void:
    anim.stop()
    anim.play(&"smile")
    anim.queue(&"idle")

func pop(text: String, angle: float, small: bool = false, color: Color = Color.WHITE, big: bool = false) -> void:
    var p: Node2D = POP_SCENE.instantiate()
    p.set(&"text", text)
    p.set(&"small", small)
    p.set(&"big", big)
    p.modulate = color
    p.position = 246.0 * Vector2.RIGHT.rotated(angle)
    pops.add_child(p)
