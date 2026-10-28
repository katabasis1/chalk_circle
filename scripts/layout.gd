extends RefCounted
class_name Layout
## Раскладка под ориентацию экрана. Сцены свёрстаны «портретом»: враг/Домовой/заголовок сверху, круг снизу.
## В горизонтальном окне (десктоп, повёрнутый телефон) прямые дети экрана раскладываются в две колонки:
## помеченные metadata/layout = "top" — влево, всё остальное (круг, свечи, подписи у круга) — вправо.
## Камера при этом приближается, чтобы круг был крупнее. Переключение на лету — Main._on_viewport_resized().

## Шире этого соотношения сторон — горизонтальная раскладка.
const LANDSCAPE_ASPECT: float = 1.15
## Сдвиги относительно портретных позиций (центр круга в портрете — (0, 210), врага — (0, -300)).
const TOP_SHIFT: Vector2 = Vector2(-360.0, 270.0)
const RING_SHIFT: Vector2 = Vector2(360.0, -210.0)
## Сколько мира должно поместиться в горизонтальном окне: две колонки с подписями.
const LANDSCAPE_WORLD: Vector2 = Vector2(1720.0, 1060.0)
const MAX_ZOOM: float = 1.25

static func is_landscape(vp: Viewport) -> bool:
    var s: Vector2 = vp.get_visible_rect().size
    return s.x > s.y * LANDSCAPE_ASPECT

static func camera_zoom(vp: Viewport, landscape: bool) -> float:
    if not landscape:
        return 1.0
    var s: Vector2 = vp.get_visible_rect().size
    return clampf(minf(s.x / LANDSCAPE_WORLD.x, s.y / LANDSCAPE_WORLD.y), 1.0, MAX_ZOOM)

## Разложить прямых детей экрана. Портретные позиции запоминаются при первом вызове (meta "portrait_pos").
static func apply(screen: Node, landscape: bool) -> void:
    for child in screen.get_children():
        var n2: Node2D = child as Node2D
        var ctl: Control = child as Control
        if n2 == null and ctl == null:
            continue
        if not child.has_meta(&"portrait_pos"):
            child.set_meta(&"portrait_pos", n2.position if n2 else ctl.position)
        var pos: Vector2 = child.get_meta(&"portrait_pos")
        if landscape:
            pos += TOP_SHIFT if str(child.get_meta(&"layout", "")) == "top" else RING_SHIFT
        if n2:
            n2.position = pos
        else:
            ctl.position = pos
        # Shaker держит «ноль» родителя — переносим его вместе с узлом.
        for sub in child.get_children():
            if sub is Shaker:
                (sub as Shaker).rebase()
