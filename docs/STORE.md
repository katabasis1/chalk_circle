# Материалы каталога Яндекс Игр — «Меловой круг»

Иконка, обложка, скриншоты, видео и тексты страницы игры на ru / en / tr.
Точные размеры и лимиты символов **сверь с подсказками в консоли разработчика** перед загрузкой: Яндекс их иногда меняет.
Ниже указано то, что было актуально при подготовке, с запасом по размеру.

Сборка готовых файлов: исходники кладёшь в `art_src/store/`, затем запускаешь `python3 tools/make_store.py`, результат появляется в `store/`
(подробнее — в разделе 6). Godot папки `art_src/` и `store/` не видит, в сборку игры они не попадают.

---------------------------------------------------------------------------------------------------
## 1. Что загружать

| Материал | Размер | Язык | Исходник → итог |
|---|---|---|---|
| Иконка | 512×512 PNG | одна на все языки, **без текста** | `art_src/store/icon.png` → `store/icon_512.png` |
| Обложка | 800×470 PNG | на каждый язык (на ней логотип) | `art_src/store/cover.png` + `logo_<lang>` → `store/<lang>/cover_800x470.png` |
| Скриншоты, телефон | 1080×1920 (9:16) | на каждый язык (в кадре интерфейс) | `art_src/store/screens/<lang>/*.png` → `store/<lang>/screens/` |
| Скриншоты, ПК | 1920×1080 (16:9) | на каждый язык | то же |
| Видео (по желанию, но поднимает конверсию) | 16:9 и/или 9:16, 15–30 с | можно одно, без текста | см. раздел 4 |

Правила модерации для промоматериалов (коротко):
* Всё, что показано, должно быть в игре: никаких сцен, которых нет в геймплее, никаких «нарисованных» скриншотов.
* На иконке не должно быть текста, рамок, значков «NEW» или «TOP», логотипов Яндекса и других платформ.
* Нельзя призывов вида «лучшая игра» или «№1», ссылок, упоминаний других площадок и цен.
* Никаких свастикоподобных символов и «коловратов» (то же правило, что в `docs/ART_PROMPTS.md`). Без крови и натурализма — у нас «мультяшный» хоррор.
* Возрастной рейтинг: **12+** (мультяшный хоррор, без крови и жестокости). Если модерация попросит — 16+.

---------------------------------------------------------------------------------------------------
## 2. Иконка 512×512

Иконка — главный фактор, от которого зависит, нажмут ли на игру в каталоге. Сделай 2–3 варианта, сравни их на телефоне в размере 64 px,
оставь самый читаемый. Генерировать в 1024×1024, `make_store.py` уменьшит.

**ICON-A — круг и глаза (рекомендую)**: [STYLE] + текст:
```
Game app icon, square 1024x1024, full-bleed artwork that fills the whole square (no transparent background, no rounded corners, no frame, no border, no text, no letters). Composition: a thick glowing bone-ivory chalk circle seen from slightly above fills most of the frame, drawn as one bold hand-drawn ring. A bright candle-amber spark with a short flat flame tail races along the ring at the upper right. Outside the ring, deep ink-black and faded indigo darkness with three pairs of huge round glowing acid-green eyes with tiny pinprick pupils, and one spindly black clawed hand reaching toward the chalk line from the lower left, stopping right at it. Inside the ring: calm dark ground with one simple chalk rosette. Very high contrast, a few bold shapes, max 5 flat colors, must read clearly at 64 px.
```

**ICON-B — Хозяйка за чертой**: [STYLE] + текст:
```
Game app icon, square 1024x1024, full-bleed artwork filling the whole square (no transparent background, no rounded corners, no frame, no text). Close-up: the pale blue-grey face of a drowned witch bride with a tall dark kokoshnik, huge round crimson (#FF1F3D) glowing eyes with tiny pupils and a thin calm smile, peeking from black darkness over a thick glowing bone-ivory chalk line that crosses the bottom third of the image diagonally. A small candle-amber spark burns on the chalk line. Her long black hair is one big solid shape framing the face. Very high contrast, bold simple shapes, max 5 flat colors, readable at 64 px.
```

**ICON-C — Мошкара в склянке** (если хочется «милее» и шире аудитория): [STYLE] + [JAR] с `{CREATURE}` = Мошкара (прикрепи `moshkara_idle`) + текст:
```
App icon, square 1024x1024, full-bleed: the jar is large and centered, filling 80% of the frame, over a background of ink-black darkness with a glowing bone-ivory chalk circle behind the jar. No text, no frame, no rounded corners.
```

Проверка: уменьши до 64×64 и 32×32. Должен читаться силуэт: круг и глаза, лицо или склянка. Если детали превращаются в кашу — упрости промпт.

---------------------------------------------------------------------------------------------------
## 3. Обложка 800×470

Генерируй в 1536×1024 и держи всё важное в центральной полосе: `make_store.py` подрежет верх и низ до 800×470 (это 1,7:1).
Логотип накладывается отдельно (`logo_ru` / `logo_en` / `logo_tr` из `art_src/ui/`, импортированные `tools/import_art.py`),
поэтому на самой картинке **текста нет**, а левая треть оставлена тёмной и спокойной под название.

**COVER**: [STYLE] + текст:
```
Wide game cover illustration, 1536x1024, flat vector cartoon like a key art frame from a 2D animated series. No text, no letters, no logo, no frame. Keep the important content inside the middle horizontal band (top and bottom 15% will be cropped). Composition: the LEFT THIRD is calm, dark, low-contrast night forest (a title will be placed there). In the CENTER-RIGHT: a forest clearing at night with a large glowing bone-ivory chalk circle on the ground, seen from slightly above, four candles burning around it; inside the circle a lanky young reader in a dark indigo kaftan holds an open book, a bright candle-amber spark racing along the chalk ring. Behind the circle, a closed dark coffin on two stools. Around the circle, at the edge of the candle light, the five monsters lurk: a swarm of midges with one big face and acid-green eyes, a hunched candle-eater with an orange flame-wick head, a thin purple whispering hag, a red rag doll with button eyes and loose threads, a black furry thing with long claws crawling out from under floorboards. Huge round glowing eyes everywhere in the dark trees. Creepy but darkly funny, high contrast, max 7 flat colors.
```

**COVER-alt (без логотипа сбоку, логотип сверху по центру)**: замени первую часть на `the TOP 30% is calm dark sky with a moon (a title will be placed there)`, а сцену поставь в нижние 70% по центру. Тогда запускай с `--logo-pos top`.

---------------------------------------------------------------------------------------------------
## 4. Скриншоты и видео

**Скриншоты — только настоящие кадры из игры**, без дорисовок. Подписи поверх не делаем (так безопаснее для модерации).
Снимать после этапа 3 (новый арт) и, лучше, после этапа 4 (весь контент).

Как снять в точном размере:
1. **Веб-сборка в Chrome**: DevTools → Device Toolbar (Ctrl+Shift+M) → задать размер 360×640 и DPR 3 (телефон, получится 1080×1920)
   или 1920×1080 и DPR 1 (ПК) → меню «⋮» → *Capture screenshot*.
2. **В редакторе Godot**: в отладочном запуске **F12** сохраняет кадр окна в `user://screenshots/` (путь печатается в Output).
   Размер окна = размер скриншота: для ПК — полный экран 1920×1080 (F11 в ОС или `--fullscreen`), для телефона — `--resolution 1080x1920`, если позволяет монитор.

Список кадров (по 5–6 на ориентацию, в этом порядке — первые два видны в каталоге сразу):

| # | Кадр | Что должно быть видно |
|---|---|---|
| 1 | Бой, разгар | Мошкара или Мотанка, 4–5 секций на круге, красная атака, искра со шлейфом, комбо ×5+, всплывающий урон |
| 2 | Печать | Слабый враг, золотая секция «ПЕЧАТЬ», замедление, золотое свечение |
| 3 | Поимка | Карточка «НОВЫЙ ДУХ» с духом в склянке |
| 4 | Лавка Домового | Домовой, 3 карточки товаров с иконками и ценами |
| 5 | Босс | Хозяйка болот (лучше вторая фаза), трещины на круге, тревога |
| 6 | Бестиарий или итог забега | Медальоны пойманных духов или экран рассвета с рекордом |

**Видео 15–30 с** (лучше вертикальное и горизонтальное; первые 3 секунды решают): 0–3 с — сразу бой и попадание с комбо (без логотипа в начале);
3–8 — красная атака, отбил, «Идеально»; 8–14 — Печать → склянка → «НОВЫЙ ДУХ»; 14–19 — лавка, покупка; 19–26 — босс, вторая фаза, добивание;
26–30 — логотип и меловой круг. Запись: OBS с веб-сборки или Movie Maker Godot (`--write-movie out.avi`). Звук игры оставляем.

---------------------------------------------------------------------------------------------------
## 5. Тексты страницы игры

Поля в консоли: название, короткое описание (SEO и карточка в каталоге), описание «Об игре», «Как играть».
Тексты описывают **полную релизную версию**. Перед публикацией проверь список в конце раздела: всё упомянутое должно уже быть в игре.

### Русский (ru)
**Название:** Меловой круг

**Короткое описание** (≈150 символов):
Хоррор в одну кнопку: семь ночей в меловом круге. Отбивай нечисть заговорами, лови духов в склянки и доживи до рассвета.

**Об игре:**
Тебя наняли чтецом: семь ночей читать заговоры над гробом мёртвой ведьмы. Ты стоишь в меловом круге посреди лесной поляны. Нечисть не может переступить черту, но очень старается.

По кругу бежит искра заговора. Жми в тот миг, когда она проходит над нужной секцией: бей своими заговорами и отбивай атаки, пока они не догорели.

• Одна кнопка: тап, клик или пробел. Научиться — секунда, мастерство — на всю ночь.
• Печать: когда враг ослаб, вспыхивает золотая секция. Попади, и дух окажется в склянке и станет твоим заговором.
• Мошкара, Свечеед, Шептуха, Мотанка, Подпольник: у каждого свои подлые приёмы. А на седьмую ночь встаёт сама Хозяйка болот.
• Лавка Домового: обереги, заговоры и отвары между ночами.
• Серии попаданий и «Идеально» — для тех, кто любит точность.
• Бестиарий: собери всех духов.
• Каждый забег разный. Сколько ночей продержишься ты?

**Как играть:**
Искра бежит по меловому кругу. Нажимай (тап, клик или пробел), когда она над секцией.
Светлые секции — твои удары. Красные — атаки нечисти: отбей их, пока не догорели, иначе потеряешь здоровье.
Промах на миг останавливает искру. Золотая «Печать» появляется, когда у врага мало сил: попади, чтобы поймать духа.
Между ночами загляни в лавку Домового.

### English (en)
**Title:** Chalk Circle

**Short description:**
A one-button folk horror: seven nights inside a chalk circle. Fend off evil spirits with chants, trap them in jars and survive till dawn.

**About:**
You've been hired as a reader: seven nights of chanting over a dead witch's coffin. You stand in a chalk circle in the middle of a forest clearing. Evil spirits can't cross the line, but they try really hard.

A spark of the chant runs around the circle. Tap the moment it passes over the right section: strike with your chants and fend off attacks before they burn out.

• One button: tap, click or Space. Learn it in a second, master it all night long.
• The Seal: when an enemy weakens, a golden section flares up. Hit it, and the spirit is trapped in a jar and becomes your own chant.
• Midgeswarm, Candle-Eater, Whisperer, Rag Doll, Underfloor: each has its own dirty tricks. And on the seventh night, the Mistress of the Marsh herself rises.
• The Domovoy's shop: charms, chants and brews between nights.
• Hit streaks and "Perfect" hits for those who love precision.
• Bestiary: catch them all.
• Every run is different. How many nights can you last?

**How to play:**
The spark runs around the chalk circle. Press (tap, click or Space) when it's over a section.
Light sections are your strikes. Red ones are enemy attacks: catch them before they burn out, or you'll lose health.
A miss freezes the spark for a moment. The golden Seal appears when an enemy is weak: hit it to catch the spirit.
Visit the Domovoy's shop between nights.

### Türkçe (tr)
**Başlık:** Tebeşir Çemberi

**Kısa açıklama:**
Tek tuşla oynanan folk korku oyunu: tebeşir çemberinde yedi gece. Kötü ruhları büyülerle püskürt, onları kavanozlara hapset ve şafağa kadar dayan.

**Oyun hakkında:**
Seni bir okuyucu olarak tuttular: yedi gece boyunca ölü bir cadının tabutu başında büyü okuyacaksın. Orman açıklığının ortasında, tebeşirle çizilmiş bir çemberin içindesin. Kötü ruhlar çizgiyi geçemez ama çok uğraşırlar.

Çemberin üzerinde bir büyü kıvılcımı koşuyor. Kıvılcım doğru bölümün üzerinden geçtiği anda dokun: kendi büyülerinle saldır, düşman saldırılarını sönmeden önce savuştur.

• Tek tuş: dokun, tıkla ya da Boşluk tuşuna bas. Öğrenmesi bir saniye, ustalaşması bütün gece.
• Mühür: düşman zayıfladığında altın bir bölüm parlar. İsabet ettir, ruh kavanoza hapsolsun ve senin büyün olsun.
• Sinek Sürüsü, Mum Yiyen, Fısıltıcı, Bez Bebek, Döşemealtı: her birinin kendine özgü sinsi numaraları var. Yedinci gece ise Bataklığın Hanımı'nın ta kendisi kalkar.
• Ev İyesi'nin dükkânı: geceler arasında muskalar, büyüler ve iksirler.
• İsabet serileri ve "Kusursuz" vuruşlar: hassasiyeti sevenler için.
• Bestiyer: bütün ruhları topla.
• Her oyun farklı. Sen kaç gece dayanabilirsin?

**Nasıl oynanır:**
Kıvılcım tebeşir çemberinin üzerinde koşar. Bir bölümün üzerindeyken bas (dokun, tıkla ya da Boşluk).
Açık renkli bölümler senin vuruşların. Kırmızılar düşman saldırıları: sönmeden yakala, yoksa can kaybedersin.
Iska kıvılcımı bir anlığına durdurur. Altın Mühür, düşmanın gücü azaldığında belirir: ruhu yakalamak için isabet ettir.
Geceler arasında Ev İyesi'nin dükkânına uğra.

### Глоссарий для турецкой локализации (этап 6.1) — держать единым с текстами выше
| ru | en | tr |
|---|---|---|
| Меловой круг | Chalk Circle | Tebeşir Çemberi |
| Чтец | Reader | Okuyucu |
| Искра | Spark | Kıvılcım |
| Печать | Seal | Mühür |
| Склянка | Jar | Kavanoz |
| Дух | Spirit | Ruh |
| Заговор | Chant | Büyü |
| Оберег | Charm | Muska |
| Отвар | Brew | İksir |
| Домовой | Domovoy | Ev İyesi |
| Мошкара | Midgeswarm | Sinek Sürüsü |
| Свечеед | Candle-Eater | Mum Yiyen |
| Шептуха | Whisperer | Fısıltıcı |
| Мотанка | Rag Doll | Bez Bebek |
| Подпольник | Underfloor | Döşemealtı |
| Хозяйка болот | Mistress of the Marsh | Bataklığın Hanımı |
| Бестиарий | Bestiary | Bestiyer |
| Идеально | Perfect | Kusursuz |
| Ночь | Night | Gece |

### Категории и теги
Категории выбери из списка в консоли. Подходят: **Аркады**, **Казуальные**, **Хоррор** (или «Страшные», если есть), «На реакцию», «Рогалики», «Для одного игрока».
Ключевые слова для поиска: хоррор, нечисть, ведьма, одна кнопка, рогалик, реакция, славянские сказки, монстры, коллекция.

### Перед публикацией — сверить тексты с игрой
* «Серии попаданий и Идеально» — пункт плана 2.1–2.2.
* «Бестиарий» — 2.17.
* «Карточка НОВЫЙ ДУХ» (скриншот 3) — 2.12.
* «Хозяйка болот, вторая фаза» (скриншот 5) — 4.3.
* Если появятся лидерборды или «Ночь дня» (4.7–4.8), добавь строку: «• Таблицы рекордов и Ночь дня: одинаковый забег для всех» / «• Leaderboards and the Night of the Day: the same run for everyone» / «• Liderlik tabloları ve Günün Gecesi: herkes için aynı oyun».

---------------------------------------------------------------------------------------------------
## 6. Сборка файлов: `tools/make_store.py`

```
art_src/store/icon.png                    квадрат ≥512 (лучше 1024)
art_src/store/cover.png                   1536×1024 (или любой ≥800×470)
art_src/store/screens/ru/*.png            скриншоты ru (портрет и ландшафт вперемешку)
art_src/store/screens/en/*.png            …en
art_src/store/screens/tr/*.png            …tr
```
```
python3 tools/make_store.py                    # логотип слева (под COVER)
python3 tools/make_store.py --logo-pos top     # логотип сверху по центру (под COVER-alt)
```
Результат:
* `store/icon_512.png`, а также `store/icon_preview.png` (как иконка выглядит в 64 и 32 px);
* `store/<lang>/cover_800x470.png`;
* `store/<lang>/screens/*.png` в 1080×1920 или 1920×1080.

Логотип берётся из `assets/art/gen/logo_<lang>.png` (это `art_src/ui/logo_<lang>.png` после `tools/import_art.py`).
Если его нет, обложка собирается без логотипа, и скрипт об этом предупредит.
Скриншот с другими пропорциями (отклонение больше 3%) не растягивается: скрипт его пропустит и напишет об этом.
