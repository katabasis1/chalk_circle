# Сборка web-версии для Яндекс Игр

## 1. Обычный экспорт (без своего шаблона)
1. Godot 4.7 → Проект → Экспорт → пресет **Yandex Web** (уже настроен: свой HTML `web/shell.html`, без потоков).
2. Экспорт в `build/web/` → заархивируй **содержимое** папки (index.html в корне архива) → загрузи черновик в консоль Яндекс Игр.

Стандартный шаблон тяжёлый: в нём 3D, физика, сеть, ICU и т. п. Это лишние мегабайты и секунды загрузки.

## 2. Лёгкий шаблон (рекомендуется для релиза)
Профиль: `export/custom.py`. Он выключает 3D, продвинутые Control-ы, навигацию, XR, сеть, лишние форматы картинок
и текстовый сервер с ICU (оставлен «запасной», он покрывает кириллицу, латиницу и турецкий).

### Шаг 1 (по желанию, даёт ещё −10–20 %) — профиль классов
В редакторе: **Проект → Инструменты → Engine Compilation Configuration Editor** → кнопка **Detect from Project** →
сохрани как `export/chalk.gdbuild`. Скрипт сборки подхватит его сам (`build_profile=`).
Перед этим открой и прогони все экраны, чтобы редактор увидел все классы.

### Шаг 2 — собрать шаблон
Нужны: `git`, `python3`, `scons` (`pip install scons`), Emscripten (`emsdk`) той версии, что указана в документации Godot
для 4.7 (раздел *Compiling for the Web*).
```
source ~/emsdk/emsdk_env.sh
GODOT_SRC=~/src/godot ./export/build_template.sh
```
Результат: `export/templates/web_release_slim.zip`. Сборка идёт 15–40 минут.

### Шаг 3 — подключить
Проект → Экспорт → Yandex Web → **Custom Template → Release** = `export/templates/web_release_slim.zip`
(или в `export_presets.cfg`: `custom_template/release="res://export/templates/web_release_slim.zip"`).
Экспортируй **без** галочки *Export With Debug*.

### Если сборка или игра сломалась
| Симптом | Что вернуть в `custom.py` |
|---|---|
| SCons: «Unknown variable …» | Это предупреждение. Переменную можно удалить из профиля |
| Ошибка про `optimize=size_extra` | `optimize = "size"` |
| Пустые квадраты вместо текста | `module_text_server_adv_enabled = "yes"` |
| Текстуры чёрные или белые | `module_webp_enabled`, `module_bcdec_enabled`, `module_squish_enabled = "yes"` |
| Нет звука | `module_ogg_enabled`, `module_vorbis_enabled = "yes"` |
| Ошибка про отсутствующий класс | убери его из `chalk.gdbuild` или пересоздай профиль кнопкой Detect |

## 3. Проверка перед загрузкой
* Размер: смотри `index.wasm` и `index.pck` в `build/web/`. Цель: wasm заметно меньше стандартного (обычно в 1.5–2 раза), pck < 5 МБ.
* Локально: `python3 -m http.server -d build/web 8080` → http://localhost:8080. SDK Яндекса локально не загрузится —
  игра работает в режиме заглушек (`Platform.sdk_ok = false`), это нормально.
* В черновике Яндекса: язык, реклама, облако, пауза при сворачивании — по `docs/YANDEX_CHECKLIST.md`.
