extends RefCounted
class_name Registry
## Каталог игровых данных: товары Домового, духи, нечисть.
## Новый контент добавляй сюда — лавка, бой и загрузка сохранённого забега берут списки отсюда.

const ITEMS: Array = [
    preload("res://data/items/begone.tres"),
    preload("res://data/items/blood.tres"),
    preload("res://data/items/salt.tres"),
    preload("res://data/items/copper.tres"),
    preload("res://data/items/horseshoe.tres"),
    preload("res://data/items/wormwood.tres"),
    preload("res://data/items/nail.tres"),
    preload("res://data/items/rowan.tres"),
    preload("res://data/items/purse.tres"),
    preload("res://data/items/gingerbread.tres"),
    preload("res://data/items/jar.tres"),
    preload("res://data/items/wax.tres"),
]
const SPIRITS: Array = [
    preload("res://data/spirits/swarm.tres"),
    preload("res://data/spirits/light.tres"),
    preload("res://data/spirits/whisper.tres"),
    preload("res://data/spirits/thread.tres"),
    preload("res://data/spirits/grip.tres"),
]
const ENEMIES: Array = [
    preload("res://data/npcs/moshkara.tres"),
    preload("res://data/npcs/svecheed.tres"),
    preload("res://data/npcs/sheptuha.tres"),
    preload("res://data/npcs/motanka.tres"),
    preload("res://data/npcs/podpolnik.tres"),
]
const BOSS: NpcData = preload("res://data/npcs/hozyaika.tres")

## Товар или дух по id (для загрузки сохранённого забега). null — нет такого (контент удалён).
static func item(id: StringName) -> ItemData:
    for it in ITEMS:
        if (it as ItemData).id == id:
            return it
    for it in SPIRITS:
        if (it as ItemData).id == id:
            return it
    return null

static func npc(id: StringName) -> NpcData:
    for n in ENEMIES:
        if (n as NpcData).id == id:
            return n
    if BOSS.id == id:
        return BOSS
    return null
