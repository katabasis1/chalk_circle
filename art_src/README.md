# art_src — исходники арта нейросети

Сюда кладутся картинки из ChatGPT Images (промты — `docs/ART_PROMPTS.md`). Godot эту папку не видит (`.gdignore`), в сборку она не попадает.

```
art_src/
  enemies/  moshkara_idle.png, moshkara_attack.png … moshkara_jar.png, hozyaika_idle.png …
  npc/      domovoy_idle.png, domovoy_happy.png, reader_idle.png …
  icons/    begone.png … wax.png, seal.png, heart.png, coin.png, jar_hud.png, sound_on.png, sound_off.png
  ui/       logo_ru.png, card_frame.png, medallion.png, ring_ornament.png, banner.png, tag.png, candle.png, fx_*.png
  bg/       bg_fight.png, bg_fight_wide.png, bg_boss.png, bg_shop.png, bg_dawn.png, bg_menu.png, fg_sides.png …
```
Полный список с назначением и статусом — `docs/ART_STATUS.md`.

После добавления картинок (из корня проекта):
```
python3 tools/import_art.py
```
Скрипт сам уберёт фон (прозрачный PNG, хромакей #FF00FF/#00FF00, фальшивая шахматка, белый фон), обрежет, уменьшит,
положит результат в `assets/art/gen/`, пересоберёт сцены и данные (PNG заменит SVG-заглушку с тем же размером на экране)
и обновит отчёт `docs/ART_STATUS.md` и превью `docs/art_preview.png`.

* Имя файла = id из таблицы. Регистр и `-`/пробелы не важны: `Moshkara-Idle.png` тоже подойдёт. Папка тоже не важна, но лучше по таблице.
* Подходят `.png`, `.webp`, `.jpg` (jpg — только для фонов: у него нет прозрачности).
* Состояния одного персонажа обрезаются общей рамкой, поэтому рисуй их в одном кадре (TECH-STATE в промтах), иначе масштаб будет «прыгать».
* Неузнанные имена файлов перечислены в конце отчёта с подсказкой, как переименовать.

## Глаза нечисти для замаха (2.4)
Перед атакой у нечисти в глазах вспыхивают блики. Для SVG-заглушек точки глаз зашиты в `tools/build_data.py` (`EYES_SVG`).
Для PNG нейросети их надо указать в `art_src/eyes.json` — доли **итоговой** картинки `assets/art/gen/<id>.png`
(после `import_art.py`: x слева направо, y сверху вниз, 0…1), не больше двух глаз, `size` — радиус блика в долях высоты:
```json
{
  "moshkara_idle": {"eyes": [[0.40, 0.43], [0.60, 0.43]], "size": 0.018},
  "sheptuha_idle": {"eyes": [[0.46, 0.33]], "size": 0.016}
}
```
Потом `python3 tools/build_data.py`. Нет записи — `build_data.py` предупредит, нечисть будет замахиваться без бликов
(поза, свечение глаз и контур атаки на круге останутся).
