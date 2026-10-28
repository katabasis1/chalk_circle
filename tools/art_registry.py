"""Реестр арта «Мелового круга»: какие картинки нейросети ждёт игра, куда их класть и что они заменяют.
Источник правды для tools/import_art.py (импорт) и tools/artlib.py (art()/art_scale() в генераторах сцен).

Новый ассет: добавь строку сюда → положи PNG в art_src/<dir>/<id>.png → python3 tools/import_art.py.

Поля Asset:
  id        имя файла без расширения (уникально во всём проекте) → assets/art/gen/<id>.png
  dir       подпапка art_src/
  kind      sprite  — персонаж/предмет на прозрачном фоне, обрезается по контуру (у группы — общей рамкой)
            icon    — иконка: обрезка, квадрат, объект ~90% кадра
            overlay — слой/рамка: холст НЕ обрезается (важно положение), только ресайз
            logo    — надпись: обрезка по контуру
            bg      — непрозрачный фон: ресайз «cover» под размер
  px        макс. сторона итогового PNG (для bg — (w, h))
  fallback  SVG из assets/art/, который показывается, пока картинки нет (None — ассет новый, без заглушки)
  fill      какую долю коробки заглушки займёт новая картинка (art_scale). 1.0 = вписать в коробку SVG целиком
  group     ассеты одной группы режутся ОБЩЕЙ рамкой (состояния персонажа не «прыгают» по размеру)
  key       цвет хромакея по умолчанию, если фон не прозрачный: 'magenta' / 'green' / None (авто)
  uses      где используется в игре (для отчёта docs/ART_STATUS.md)
"""
from dataclasses import dataclass, field


@dataclass
class Asset:
    id: str
    dir: str
    kind: str
    px: object
    fallback: str = None
    fill: float = 1.0
    group: str = None
    key: str = None
    uses: str = ''
    section: str = ''


ASSETS = []


def add(*a, **kw):
    ASSETS.append(Asset(*a, **kw))


# ---------------- нечисть: 5 врагов × 5 состояний ----------------
ENEMIES = {  # id: (подпись, хромакей по документу)
    'moshkara': ('Мошкара', 'magenta'),
    'svecheed': ('Свечеед', 'green'),
    'sheptuha': ('Шептуха', 'green'),
    'motanka': ('Мотанка', 'green'),
    'podpolnik': ('Подпольник', 'magenta'),
}
ENEMY_STATES = {
    'idle': 'бой: обычный вид, бестиарий в меню',
    'attack': 'бой: замах/атака (этап 3.2)',
    'hurt': 'бой: получил удар (этап 3.2)',
    'weak': 'бой: ≤30% жизни, можно Печать (этап 3.2)',
}
for nid, (title, key) in ENEMIES.items():
    for st, use in ENEMY_STATES.items():
        add(f'{nid}_{st}', 'enemies', 'sprite', 600, fallback=f'enemy_{nid}.svg' if st == 'idle' else None,
            fill=0.92, group=nid, key=key, uses=f'{title} — {use}', section='Нечисть')
    add(f'{nid}_jar', 'enemies', 'icon', 256, fallback=f'enemy_{nid}.svg', key=key,
        uses=f'{title} — дух в склянке: иконка духа (data/spirits), карточка Печати', section='Нечисть')

# ---------------- босс ----------------
BOSS_STATES = {
    'idle': 'бой: обычный вид (data/npcs/hozyaika.tres)',
    'attack': 'бой: атака (этап 3.2)',
    'hurt': 'бой: удар (этап 3.2)',
    'enraged': 'бой: 2-я фаза ≤50% (этап 4.3)',
    'defeated': 'рассвет, финал (этап 4.10)',
}
for st, use in BOSS_STATES.items():
    add(f'hozyaika_{st}', 'enemies', 'sprite', 640, fallback='boss_hozyaika.svg' if st == 'idle' else None,
        fill=0.95, group='hozyaika', key='green', uses=f'Хозяйка — {use}', section='Босс')

# ---------------- Домовой и Чтец ----------------
for st, use in {'idle': 'лавка (scenes/shop)', 'happy': 'лавка: после покупки (этап 4.5)',
                'grumpy': 'лавка: не хватает денег (этап 4.5)'}.items():
    add(f'domovoy_{st}', 'npc', 'sprite', 576, fallback='domovoy.svg' if st == 'idle' else None,
        fill=0.95, group='domovoy', key='green', uses=f'Домовой — {use}', section='Домовой и Чтец')
for st, use in {'idle': 'меню (scenes/menu)', 'scared': 'финал: смерть (этап 2.16)',
                'dawn': 'финал: победа (этап 2.16)'}.items():
    add(f'reader_{st}', 'npc', 'sprite', 448, fallback='reader.svg' if st == 'idle' else None,
        fill=0.95, group='reader', key='green', uses=f'Чтец — {use}', section='Домовой и Чтец')

# ---------------- иконки товаров ----------------
ITEM_ICONS = {  # id файла: (id товара в data/items, заглушка, подпись)
    'begone': ('begone', 'ember.svg', '«Сгинь!»'),
    'blood': ('blood', 'heart.svg', 'Кровью'),
    'salt': ('salt', 'runes.svg', 'Соль'),
    'copper': ('copper', 'coin.svg', 'Медный грош'),
    'horseshoe': ('horseshoe', None, 'Подкова'),
    'wormwood': ('wormwood', None, 'Полынь'),
    'nail': ('nail', None, 'Железный гвоздь'),
    'rowan': ('rowan', None, 'Рябиновые бусы'),
    'purse': ('purse', 'coin.svg', 'Кошель'),
    'ginger': ('gingerbread', None, 'Пряник'),
    'jar': ('jar', 'jar.svg', 'Склянка'),
    'wax': ('wax', 'candle.svg', 'Восковая куколка'),
}
for fid, (item_id, fb, title) in ITEM_ICONS.items():
    add(fid, 'icons', 'icon', 256, fallback=fb, uses=f'товар «{title}»: карточка лавки (data/items/{item_id}.tres)', section='Иконки товаров')

# ---------------- иконки интерфейса ----------------
add('seal', 'icons', 'icon', 160, fallback='seal.svg', uses='секция ПЕЧАТЬ на круге', section='Иконки интерфейса')
add('heart', 'icons', 'icon', 128, fallback='heart.svg', uses='HUD: жизни', section='Иконки интерфейса')
add('coin', 'icons', 'icon', 128, fallback='coin.svg', uses='HUD: деньги; монетки награды (fx/coin)', section='Иконки интерфейса')
add('jar_hud', 'icons', 'icon', 128, fallback='jar.svg', uses='HUD: склянки', section='Иконки интерфейса')
add('sound_on', 'icons', 'icon', 128, uses='кнопка звука: вкл (этап 2.14)', section='Иконки интерфейса')
add('sound_off', 'icons', 'icon', 128, uses='кнопка звука: выкл (этап 2.14)', section='Иконки интерфейса')

# ---------------- элементы UI ----------------
add('logo_ru', 'ui', 'logo', 1024, uses='меню: логотип (ru) (этап 3.5), обложка каталога (tools/make_store.py)', section='Элементы UI')
add('logo_en', 'ui', 'logo', 1024, uses='меню: логотип (en) (этап 3.5), обложка каталога en', section='Элементы UI')
add('logo_tr', 'ui', 'logo', 1024, uses='меню: логотип (tr) (этап 6.1), обложка каталога tr', section='Элементы UI')
add('logo_frame', 'ui', 'overlay', 1024, uses='меню: рамка под название шрифтом (этап 3.5)', section='Элементы UI')
add('card_frame', 'ui', 'overlay', 768, uses='лавка: рамка карточки товара (этап 3.5)', section='Элементы UI')
add('medallion', 'ui', 'overlay', 256, uses='бестиарий: ячейка (этап 2.17)', section='Элементы UI')
add('ring_ornament', 'ui', 'overlay', 768, fallback='runes.svg', uses='подложка под круг (scenes/ring)', section='Элементы UI')
add('banner', 'ui', 'overlay', 1024, uses='заголовки «НОЧЬ 3/7» (этап 3.5)', section='Элементы UI')
add('tag', 'ui', 'overlay', 512, uses='табличка подписи секции (этап 3.5)', section='Элементы UI')
add('candle', 'ui', 'sprite', 192, fallback='candle.svg', uses='4 свечи вокруг круга (scenes/fx/candle)', section='Элементы UI')
for fx, use in {'fx_chalk': 'меловая пыль', 'fx_ember': 'угольки искры', 'fx_blood': 'брызги при ране', 'fx_gold': 'блёстки Печати'}.items():
    add(fx, 'ui', 'icon', 128, uses=f'частицы: {use} (этап 2.10/3.x)', section='Элементы UI')
add('fx_chip', 'ui', 'icon', 64, fallback='chip.svg', uses='частицы: сколы мела при ране (scenes/fx/chips), крошки дуги здоровья (fight/hp_bar)', section='Элементы UI')

# ---------------- фоны ----------------
add('bg_fight', 'bg', 'bg', (1024, 1536), fallback='bg.svg', uses='фон боя, лавки и меню (scenes/bg)', section='Фоны')
add('bg_fight_wide', 'bg', 'bg', (1536, 1024), uses='фон боя для ПК/ландшафта (этап 3.3)', section='Фоны')
add('bg_boss', 'bg', 'bg', (1024, 1536), uses='фон 7-й ночи (этап 3.4)', section='Фоны')
add('bg_shop', 'bg', 'bg', (1024, 1536), uses='фон лавки (этап 3.3)', section='Фоны')
add('bg_dawn', 'bg', 'bg', (1024, 1536), uses='фон победы (этап 3.4)', section='Фоны')
add('bg_menu', 'bg', 'bg', (1024, 1536), uses='фон меню (этап 3.3)', section='Фоны')
add('fg_sides', 'bg', 'overlay', 1024, uses='передний план, параллакс (этап 3.3)', section='Фоны')
add('fg_sides_wide', 'bg', 'overlay', 1536, uses='передний план для ландшафта (этап 3.3)', section='Фоны')
add('frame_bilibin', 'bg', 'overlay', 1024, uses='рамка поверх экрана, по желанию (этап 3.5)', section='Фоны')

BY_ID = {a.id: a for a in ASSETS}
assert len(BY_ID) == len(ASSETS), 'повторяющийся id в реестре арта'
