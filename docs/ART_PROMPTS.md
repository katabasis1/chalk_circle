# ART PROMPTS — «Меловой круг» (для ChatGPT Images) — v2: ПЛОСКИЙ ВЕКТОР

Стиль: плоский векторный мультфильм. Билибин × готический кукольный мультфильм × панк-мультфильм.
Промты на английском: модель так точнее держит стиль. Пояснения на русском.

**Что изменилось по сравнению с v1**
* [STYLE] переписан: сначала идёт «FLAT 2D VECTOR CARTOON». Модель сильнее всего слушает начало промта.
* Убраны слова, которые тянули к детализации: *stop-motion* (давал фактуру глины и ткани), *graphic novel* (давал штриховку),
  *scratchy inking*, *print grain*, *varying line weight*, *dense ornament*.
* Добавлены прямые правила упрощения: одна ровная обводка, заливки без фактуры, максимум одна тень, волосы, дым и рой рисуются крупными пятнами.
  Свечение — плоской фигурой, без размытия. В конце стоит явный список запретов.
* В описаниях ассетов «dense / dozens / scratches / embroidery» заменены на конкретные малые числа и простые мотивы.
  Пример: «five or six pins» вместо «dozens of pins». Иначе модель дорисует всё, что перечислено.

---------------------------------------------------------------------------------------------------
## 0. Как пользоваться (прочитай один раз)

1. **Один персонаж — один чат.** Сначала база (IDLE), потом все его состояния в ТОМ ЖЕ чате.
   Для каждого состояния прикрепи картинку IDLE и вставь блок [TECH-STATE]. Так дизайн не «уплывёт».
2. **Как собрать промт:** `[STYLE]` + `[TECH-…]` + текст ассета. Можно один раз написать в начале чата:
   *"For every image in this chat apply these rules:"* + блоки, а дальше слать только текст ассетов.
   Каждые 5–6 картинок вставляй блоки заново: модель их забывает.
3. **Сначала тест стиля.** Сгенерируй «Мошкара IDLE» 3–4 раза и выбери лучший вариант. Потом попроси:
   *"Describe the visual style of this image in 90 words, as a reusable style prompt"*.
   Ответ дополни своим блоком [STYLE] и используй дальше: так вся игра будет в одном стиле.
   **Важно:** начни новый чат и не прикрепляй старые детализированные картинки как референс. Модель скопирует и уровень детализации.
4. **Если всё равно слишком детально.** В том же чате отправь:
   *"Too detailed. Redraw exactly the same image as a simpler flat vector cartoon: half as many details, bigger shapes, thicker even outline, solid flat fills, no texture, no hatching."*
   Обычно хватает одного-двух раз. Удачную упрощённую версию бери как референс IDLE для состояний.
5. **Прозрачный фон.** Скачай PNG и проверь. Иногда модель рисует шахматку прямо в пикселях — это фальшивая прозрачность.
   Тогда допиши: *"real alpha transparency, NOT a checkerboard pattern"*.
   **Запасной вариант:** допиши *"on a perfectly flat solid #FF00FF background, no gradient, no shadow"*
   (для зелёных и бирюзовых: Мошкара, Подпольник) или *"…#00FF00…"* (для остальных). Хромакей уберу скриптом.
   В плоском стиле с чёткой обводкой хромакей вырезается заметно чище.
6. **Размеры ChatGPT Images:** 1024×1024 (персонажи, иконки), 1024×1536 (вертикальные фоны), 1536×1024 (горизонтальные).
7. **Почему здесь не названы Бёртон и Gorillaz (Хьюлетт).** ChatGPT часто отказывается рисовать «в стиле» живых авторов.
   Gorillaz к тому же чужой бренд. Для публикации тоже безопаснее описывать приёмы, а не имена. Поэтому в [STYLE] расписаны их приёмы.
   Билибин умер в 1942 году, его работы — общественное достояние, его можно называть.
8. **Технические требования игры** (уже вписаны в блоки):
   * Глаза — самое яркое место. Шейдер врагов подсвечивает и пульсирует всё очень светлое.
     Поэтому белая одежда, кости и кожа должны быть приглушёнными (слоновая кость, серый), без чистого белого.
   * Сигнатурный цвет врага = цвет его атак на круге. Он должен читаться в глазах, свечении и одной детали.
   * Смерть, вспышку удара и «засасывание в склянку» игра рисует шейдером. Кадры для них не нужны.
   * Символы: никаких свастикоподобных знаков и «коловратов» (модерация Яндекса и закон). Только розетки, звёзды, ромбы.
9. **Куда класть:** `Chalk Circle/art_src/…` с именами файлов из таблиц. Я обрежу, выровняю,
   уменьшу до игровых размеров, уберу хромакей и подключу в сцены и `.tres`.
   Это делает `python3 tools/import_art.py` (можно запускать и самому): фон → прозрачность (альфа / хромакей /
   фальшивая шахматка / белый фон), обрезка, ресайз → `assets/art/gen/`, пересборка сцен, отчёт `docs/ART_STATUS.md`
   (что подключено, чего ждём, замечания) и превью `docs/art_preview.png`.

---------------------------------------------------------------------------------------------------
## 1. Общие блоки (копируй как есть)

### [STYLE]
```
FLAT 2D VECTOR CARTOON, minimal detail. Clean vector art for a stylish 2D mobile game, in the look of a modern 2D animated TV series. Dark Slavic folk-horror fairy tale: creepy, stylish, darkly funny.
Three influences, all SIMPLIFIED:
1) Ivan Bilibin's fairy-tale prints: bold black contours, flat poster-like color fields, decorative stylized silhouettes; folk ornament reduced to a few large simple motifs (dots, zigzags, triangles, simple rosettes), only on hems, belts and trims;
2) gothic puppet-cartoon look: spindly limbs, thin necks, oversized heads, huge round eyes with tiny pinprick pupils and dark rings, simple spirals and stripes, stitches as a few short dashes;
3) punk cartoon character design, like a 2D animated music video: lanky angular anatomy, sharp geometric shapes, slouchy attitude poses, flat cel colors.
Rendering: one even, bold dark outline around every shape; solid flat fills; at most one hard-edged shadow shape per color, no highlights. Hair, beards, cloth, smoke, mist and swarms are a few big solid shapes, never strands, folds or particles. Glows are flat solid shapes (a ring or simple rays), never soft blur. Big readable silhouette, clear at small size.
Limited palette, max 7 flat colors: ink black, bone ivory, moss green, rust red, faded indigo, candle amber, plus ONE saturated signature accent per character.
NO texture, no grain, no paper, no hatching, no cross-hatching, no fine lines, no tiny details, no gradients, no airbrush, no painterly brushwork, no realistic lighting, no 3D, no clay or felt look, no photorealism, no anime.
```

### [TECH-SPRITE] — база персонажа
```
Game sprite. Single character, full body, three-quarter view, centered; the whole figure visible with about 8% empty margin on every side, never cropped. Square 1024x1024. TRANSPARENT background (real PNG alpha): no scenery, no floor, no cast shadow, no frame, no white sticker outline, no text, no watermark. Flat vector cartoon with clean closed outlines and solid fills, low detail: if in doubt, leave it out. The glowing eyes are the brightest pixels in the image; every other light area (cloth, bone, skin, beard) stays muted ivory or grey, never pure white.
```

### [TECH-STATE] — состояния (прикрепи IDLE этого персонажа)
```
Use the attached image as a strict reference. Same character: identical design, face, proportions, costume, colors, outline thickness, and the same flat vector style with the same LOW level of detail; do not add new details, texture, shading or ornament. Same canvas and same framing: same scale, figure centered, its lowest point at the same height as in the reference. Same rules: transparent background (real PNG alpha), no floor, no shadow, no text; eyes are the brightest pixels. Change ONLY the pose and expression as follows:
```

### [TECH-ICON]
```
Game item icon, flat vector cartoon. Single object, centered, filling about 75% of a 1024x1024 square, slight three-quarter view. One bold simple shape with a thick even dark outline, 3-4 solid flat colors, one hard-edged shadow shape and at most one simple flat highlight shape. No texture, no grain, no fine detail; ornament at most one large simple motif. As simple and readable as a mobile game icon; must read clearly at 64 px. TRANSPARENT background (real PNG alpha), no scenery, no cast shadow, no text, no frame, no swastika-like or hooked-cross symbols.
```

### [TECH-BG] — фоны (НЕ прозрачные)
```
Full-bleed game background, flat vector cartoon like a background from a 2D animated series. NO characters, NO text, no frame, no border. Composed for a vertical phone screen, 1024x1536. Built from a few layered flat silhouette planes: the nearest plane darkest, distant planes lighter and hazier; each plane a solid color with at most one hard-edged shade. Trees, foliage, grass and clouds are big simple stylized shapes, never individual leaves or blades. No texture, no grain, no painterly brushwork, no gradients except a simple banded sky. The central column must stay calm, darker and low in contrast: an enemy is shown in the upper third, and a large glowing circle sits in the lower middle (around 65% of the height). Put the few details and the contrast toward the left and right edges and the bottom corners. Slightly desaturated, so bright characters and UI pop.
```

### [TECH-OVERLAY] — слои с пустым центром
```
Decorative overlay layer, flat vector cartoon: solid fills, even dark outline, no texture. Everything except the described ornament is fully TRANSPARENT (real PNG alpha); the center is completely empty. No text, no characters.
```

### [JAR] — шаблон «дух в склянке» (иконка для Бестиария и лавки; прикрепи IDLE врага)
```
A small old glass jar drawn as a simple flat shape, with a thick wax stopper wrapped in red thread and a round golden wax seal with a simple eight-petal rosette on the stopper. Inside the jar, trapped and shrunk to a tiny size: {CREATURE}. Use the attached character as the reference for the creature, simplified to its key shapes. The jar is filled with a flat glow in the creature's signature color; the glass has one or two flat pale highlight stripes, no scratches, no complex reflections.
```

---------------------------------------------------------------------------------------------------
## 2. Нечисть: 5 врагов × 5 состояний

| Состояние | Когда показывается в игре |
|---|---|
| `idle` | обычный вид, лёгкое покачивание (база для всех остальных состояний) |
| `attack` | враг выпускает атаку, или ты её ловишь |
| `hurt` | по врагу попал твой удар |
| `weak` | у врага ≤30% жизни, можно «запечатать». Золотые трещины = подсказка игроку «лови ПЕЧАТЬ» |
| `jar` | дух пойман — иконка для Бестиария и карточки в лавке ([TECH-ICON] + [JAR]) |

Файлы: `art_src/enemies/<id>_<state>.png`. В игре враг занимает примерно 440 px по высоте.

### 2.1 Мошкара (`moshkara`) — сигнатурный цвет #A6D23A, кислотно-зелёный
Дизайн: комариха-крестьянка по референсу `Жутковатый комар в народном наряде.png`.
**IDLE** — [STYLE] + [TECH-SPRITE] + (прикрепи референс)
```
Use the attached image as the character design reference: keep the costume, proportions, silhouette and pose, but redraw it MUCH simpler in the flat vector style described above. Do NOT copy its detailed rendering, texture or ornament density.
Character: MOSHKARA, a forest midge spirit: a gaunt, hunched mosquito-woman dressed as a Slavic peasant. Head: a pale grey-ivory oval mask-like face (muted, never white) with a short stitched scar on the forehead drawn as a few dashes; two huge round glowing acid-green eyes (#A6D23A) with tiny black pupils in dark sunken rings; a long thin black needle proboscis instead of a nose, pointing down; two long thin curved black antennae sweeping up and back. A moss-green headscarf tied at the neck, with 4-5 simple red-and-ivory dot flowers and loose ends hanging. A single strand of big red beads and a round copper amulet with a red tassel on a cord. A loose ivory linen shirt with wide ragged sleeves and one bold red diamond band on the shoulders and cuffs. A long dark moss-green skirt with a red apron panel with one simple diamond motif; the hem cut into 3-4 big ragged points. A small round brown pouch at the hip. Two long narrow insect wings from the back reaching the knees: flat pale grey-green shapes with 3-4 simple dark vein lines. Very thin black insect arms with long claw fingers; very thin black insect legs wrapped with ivory cloth bands, red pointed shoes. Three or four tiny midges buzzing around her head as small black dots. Acid green is the signature accent: eyes, a glowing drop at the proboscis tip, a thin acid-green edge on the wings. Pose: standing, hunched forward, head bowed and tilted, arms hanging loose, a sad, creepy stare.
```
**ATTACK** — [TECH-STATE] +
```
Lunging forward toward the viewer, wings spread wide and buzzing (two or three simple motion arcs), the long proboscis thrust forward like a needle with a bright acid-green drop at the tip, claw hands reaching forward, antennae swept back, the headscarf ends flying, eyes flaring bright acid green, a small cloud of midges (flat black dots) bursting around her.
```
**HURT** — [TECH-STATE] +
```
Recoiling backward, one wing bent and torn, the antennae bent, the headscarf knocked askew, a crack across the mask face, arms raised defensively, eyes squeezed into slits, a few midge dots scattering.
```
**WEAK** — [TECH-STATE] +
```
Collapsed to her knees, both wings drooping and torn, the proboscis sagging toward the ground, the headscarf sliding off her head, trembling; a few bold zigzag cracks of warm golden light shine through the mask face and the shirt, as if she is about to be captured; eyes dim and pleading.
```
**JAR** — [TECH-ICON] + [JAR], {CREATURE} =
```
the MOSHKARA shrunk into a tiny mosquito-woman in a green headscarf, pressing her needle proboscis against the glass, wings buzzing, acid-green eyes glaring
```

### 2.2 Свечеед (`svecheed`) — #FF8A2A, оранжевый
**IDLE**
```
Character: CANDLE-EATER, a gaunt church-thief ghoul that feeds on candle flames. Extremely tall and thin, with a long crane-like neck bent forward. Its head is a lump of half-melted yellowed wax shaped like a skull, with a burnt wick on the crown and two simple wax drips down the cheeks. Huge round sunken eyes glowing amber-orange (#FF8A2A) with tiny pupils. A long jaw with candle stubs sticking out as it chews. A ragged dark sexton's cassock with a simple striped hem; three stolen candles tied at the belt. Long pale fingers like candle stubs with a few wax drips. Signature orange: eyes, a flat ember glow in its throat, the smouldering wick. Pose: standing hunched, one hand bringing a lit candle to its mouth, the other behind its back, a greedy smile.
```
**ATTACK** (задувает искру)
```
Leaning in toward the viewer with cheeks puffed, blowing a thick stream of grey smoke drawn as a few big simple curls, one long hand pinching forward as if snuffing a flame, eyes blazing orange, the wick flaring.
```
**HURT**
```
Flinching back, its wax face sagging and melting to one side, a few drips flying off, both hands raised defensively, the wick sputtering.
```
**WEAK**
```
Slumped down, the body melted into a pooled wax heap from the waist down, head drooping, the wick only smoking; a few bold cracks of golden light glow through the wax.
```
**JAR** {CREATURE} =
```
the CANDLE-EATER shrunk into a tiny wax ghoul hugging a candle stub, its wick smoking, orange eyes glaring
```

### 2.3 Шептуха (`sheptuha`) — #B768FF, фиолетовый
**IDLE**
```
Character: WHISPERER, an old village witch-ghost who whispers hexes. A small hunched crone floating above the ground; her lower body ends in a ragged linen tail shape fading into violet mist. Long grey hair as one solid shape falls like a veil over half of her face; enormous pointed ears; huge round eyes glowing violet (#B768FF). Her mouth is sewn shut with three big red cross-stitches, and thin violet whisper-smoke curls out between them as simple spirals. Long crooked fingers with black nails, one finger raised to her lips in a "shhh". She wears a rushnyk-towel shawl with one bold red-and-black zigzag border. Signature violet: eyes, whisper mist, a violet trim on the shawl. Pose: floating, leaning slightly forward, head tilted, sly.
```
**ATTACK** (шёпот ускоряет круг)
```
Swooping forward toward the viewer, both hands cupped around her stitched mouth, a big simple spiral of violet whisper-smoke bursting toward the viewer, hair whipping back, eyes flaring.
```
**HURT**
```
Recoiling, covering her huge ears with both hands, one stitch torn, the mist breaking into a few flat puffs, eyes squeezed shut.
```
**WEAK**
```
Shrunken and folded in on herself, the hair veil torn, the ragged tail breaking up into mist, her colors faded and paler; a few bold cracks of golden light show through her.
```
**JAR** {CREATURE} =
```
the WHISPERER shrunk into a tiny floating crone pressing her huge ear to the glass, a violet mist swirl around her
```

### 2.4 Мотанка (`motanka`) — #E0283C, красный
**IDLE**
```
Character: RAG DOLL, a life-size Slavic folk motanka doll come alive. A bundled body of undyed linen wrapped with a few bands of string; a faceless round head with a bold red thread cross where the face should be, and only two tiny glowing red pinpoints (#E0283C) behind the threads. A long flax braid, an apron with a simple red diamond pattern, a headscarf knotted at the back. Spindly arms stitched at the joints with short dashes, five or six big sewing pins stuck into the body. She drags an enormous sewing needle like a spear, with a long red thread trailing behind. Signature red: the thread cross, the needle's thread, the apron pattern. Pose: standing perfectly still, head tilted at an unnatural angle, puppet-like.
```
**ATTACK** (укол / перекрут)
```
Lunging forward toward the viewer, thrusting the giant needle like a spear, the red thread whipping in one big spiral around her, head snapped to the other side, pins bristling.
```
**HURT**
```
Knocked back, a seam on her side torn open with a simple tuft of straw bursting out, head lolling, two pins falling out.
```
**WEAK**
```
Sagging like a puppet with cut strings, a few loose threads hanging from her arms, the head hanging by a few stitches, kneeling; golden light glows from the torn seams.
```
**JAR** {CREATURE} =
```
the RAG DOLL shrunk into a tiny faceless doll with a red thread cross, sitting with the giant needle across her knees
```

### 2.5 Подпольник (`podpolnik`) — #38D6B0, бирюзовый
**IDLE**
```
Character: UNDERFLOOR, the thing that lives beneath the floorboards. Only its upper body rises from a jagged hole in a small fragment of broken dark wooden floorboards at the bottom of the image (the plank fragment is part of the sprite, drawn as 3-4 simple planks). A grey, damp, flat-faced creature with a wide lipless grin showing a row of small triangle teeth, and shaggy wet black hair drawn as one solid shape with a single cobweb. Two very long thin arms with too many joints, fingers splayed on the planks. Cat-like eyeshine: two glowing teal eyes (#38D6B0). Signature teal: eyes, a few flat spots of glowing mould on the planks. Pose: peering up while leaning on the boards, head cocked, grinning.
```
**ATTACK** (утаскивает искру)
```
Both long arms shooting forward toward the viewer with hands wide open to grab, the body halfway out of the hole, mouth gaping, eyes blazing teal, a few simple splinter shapes flying.
```
**HURT**
```
Recoiling down into the hole up to its chest, one arm covering its face, a few splinters flying, eyes squeezed.
```
**WEAK**
```
Sunk almost entirely into the hole, only the head and one trembling hand clinging to the edge of the planks; golden light leaks from the cracks between the boards.
```
**JAR** {CREATURE} =
```
the UNDERFLOOR shrunk into a tiny grey creature with long arms pressed against the glass, teal eyes, a wood splinter lying beside it
```

---------------------------------------------------------------------------------------------------
## 3. Босс — Хозяйка болот (`hozyaika`) — #FF1F3D, багровый
Босса нельзя запечатать, поэтому вместо `weak` у неё есть `enraged` (вторая фаза, ≤50% жизни) и `defeated` (рассвет).
Файлы: `art_src/enemies/hozyaika_<state>.png`.

**IDLE** — [STYLE] + [TECH-SPRITE] +
```
Character: MISTRESS OF THE MARSH, the dead witch the hero guards for seven nights; the final boss. A tall, elegant, terrifying drowned bride. Pale blue-grey skin, very long black hair as one big flowing solid shape with two water lilies in it, huge round eyes glowing crimson (#FF1F3D) with tiny pupils, thin dark lips in a calm smile. A tall kokoshnik headdress drawn as one bold simple shape with a row of reed spikes, pearl dots and two small bones. A long-sleeved wedding sarafan in faded ivory and moss green with one simple bold hem pattern, the hem breaking into a few flat water drips. Thin skeletal hands with long fingers, one holding a sprig of bog cranberries. Two small floating funeral candles beside her. Signature crimson: eyes, cranberries, ribbons on the kokoshnik. Pose: hovering upright, arms slightly open, regal and perfectly still.
```
**ATTACK** — [TECH-STATE] +
```
Screaming toward the viewer with her jaw unhinged, hair whipping up like snakes, both skeletal hands raised casting a hex, flat crimson rays bursting from her eyes, the candles flaring.
```
**HURT**
```
Recoiling, hair flying and a few flat water drops splashing, one hand over her face, a fresh crack across the kokoshnik.
```
**ENRAGED** (вторая фаза)
```
Her enraged form: the kokoshnik cracked and burning with flat crimson flame shapes, the smile split wider than a human face allows, hair spreading into a huge spiky halo shape, the sarafan torn and floating, a flat crimson aura outline around her, four candles orbiting her.
```
**DEFEATED** (рассвет, победа)
```
Crumbling at dawn: her body falling apart from the feet up into a few reeds, water drops and lily petals, her face peaceful with eyes closed, colored in pale golden morning tones. No crimson glow left.
```

---------------------------------------------------------------------------------------------------
## 4. Домовой (лавка) и Чтец (меню)
Файлы: `art_src/npc/domovoy_<state>.png`, `art_src/npc/reader_<state>.png`.

### Домовой — сигнатурный цвет золото #FFD25A
**IDLE**
```
Character: DOMOVOY, the house spirit who runs a tiny night shop. Small, round and hairy; a big round grey beard drawn as one solid shape reaches down to the floor and hides most of his body; a big potato nose, two glinting golden eyes (#FFD25A) under bushy brows; bast lapti shoes; a red belt with three iron keys and a coin purse. He sits on an iron-bound wooden trunk next to a small candle lantern, a striped cat's tail curling out from behind him. Sly, greedy, but warm. Signature gold: eyes, coins, lantern light. Pose: sitting, counting coins on his palm, side-eye at the viewer.
```
**HAPPY** (после покупки) — [TECH-STATE] +
```
Delighted: grinning wide under the beard, eyes crinkled, tossing a coin into the air, the other hand stroking his beard.
```
**GRUMPY** (не хватает денег)
```
Arms crossed, frowning, beard bristling, eyebrows down, one foot tapping impatiently, the coin purse held tight.
```

### Чтец — герой (меню, финал)
**IDLE**
```
Character: THE READER, a young village girl hired to read prayers over the witch's coffin for seven nights. Thin and pale, huge round anxious eyes with tiny pupils, a long auburn braid with a faded blue ribbon, a muted ivory linen shirt with a simple red trim at the hem, an indigo sarafan, bast shoes. In one hand an open old book; in the other a skull-lantern on a stick whose eye sockets glow warm amber (the brightest spot). Pose: standing in three-quarter view, glancing nervously over her shoulder.
```
**SCARED**
```
Clutching the book to her chest, shoulders raised, eyes wide, the skull-lantern trembling in her hand.
```
**DAWN** (победа)
```
Exhausted but relieved: the book closed under her arm, the lantern out and lowered, a faint tired smile, eyes half-closed, pale warm morning tones on her face.
```

---------------------------------------------------------------------------------------------------
## 5. Иконки
Все: [STYLE] + [TECH-ICON] + текст. Файлы: `art_src/icons/<id>.png`. В игре 96–160 px.

### 5.1 Товары лавки (12)
| id | Предмет | Текст промта |
|---|---|---|
| `begone` | «Сгинь!» (заговор, 15 урона) | `A strip of birch bark with a carved banishing glyph, the glyph bursting with a few bold amber spark shapes, the bark edges curled and smoking.` |
| `blood` | Кровью (−0.5 жизни, 40 урона) | `A small bone-handled knife and a single drop of blood falling onto an old page with a simple ink sigil; the drop glows deep crimson.` |
| `salt` | Соль (сметает атаки) | `A carved wooden duck-shaped salt cellar (Russian solonka) with a simple painted pattern, spilling an arc of salt drawn as simple dots, like a protective line.` |
| `copper` | Медный грош (растёт) | `An old copper coin with a green patina rim and a simple stamped sun-face, with a small upward sparkle shape suggesting it grows stronger.` |
| `horseshoe` | Подкова (первый удар +50%) | `A rust-brown hand-forged iron horseshoe, open end up for luck, hanging on a nail and tied with a red thread.` |
| `wormwood` | Полынь (отбитая атака бьёт) | `A bundle of silver-grey wormwood drawn as a few simple leaf shapes, tied with red string, a thin green curl of smoke rising from it.` |
| `nail` | Железный гвоздь (+1 урона) | `A huge hand-forged iron coffin nail, slightly bent, with a red thread knot under the head.` |
| `rowan` | Рябиновые бусы (первая рана не считается) | `A necklace of bright red rowan berries strung on red thread with a small simple wooden eight-petal rosette charm.` |
| `purse` | Кошель («Другое» даром) | `A worn leather drawstring purse with a simple red stitched pattern, two copper coins spilling out of it.` |
| `ginger` | Пряник (отвар даром) | `A Russian printed gingerbread (pryanik) with a simple stamped bird shape and a few white icing lines, one bite missing.` |
| `jar` | Склянка (+1 склянка) | `An empty old glass jar with a wax stopper and red thread, a flat golden glow inside, a golden eight-petal seal on the stopper.` |
| `wax` | Восковая куколка (+1 здоровья) | `A small beeswax figurine doll wrapped in red thread, a few candle drips on it, a small flat warm glow in its chest.` |

### 5.2 Интерфейс
| id | Где | Текст промта |
|---|---|---|
| `seal` | секция ПЕЧАТЬ, метка босса | `A round golden wax seal stamp with a simple eight-petal folk rosette and a ring of simple dots, molten wax edges, glowing gold.` |
| `heart` | HUD, жизни | `A stylized folk heart made of deep red cloth, held together with a few big ivory stitches, one small patch.` |
| `coin` | HUD, деньги | `A simple chunky copper coin seen almost front-on, stamped sun-face, bold and readable even very small.` |
| `jar_hud` | HUD, склянки | `A simple chunky glass jar with a wax stopper and red thread, flat gold glow inside, bold and readable even very small.` |
| `sound_on` | кнопка звука | `A small brass bell with a red ribbon, ringing, with two little motion arcs.` |
| `sound_off` | кнопка звука | `The same small brass bell wrapped in a grey cloth, silent, with a small red X stitched on the cloth.` |

---------------------------------------------------------------------------------------------------
## 6. Элементы UI
[STYLE] + [TECH-OVERLAY] (кроме логотипа) + текст. Файлы: `art_src/ui/<id>.png`.

**logo_ru** — 1536×1024, прозрачный фон
```
Game logo lettering that reads exactly «МЕЛОВОЙ КРУГ» in Cyrillic, on two lines: "МЕЛОВОЙ" above "КРУГ". Decorative capitals inspired by Old Russian vyaz lettering and Bilibin's book titles, drawn as flat vector shapes: letters in flat ivory with a slightly rough hand-drawn chalk edge (no dust, no smudges, no texture), a thin crimson outline and a few simple drips. A simple chalk circle stroke sweeps behind the words; a candle and a tiny skull are worked into the letters as simple shapes. Transparent background (real PNG alpha), letters fill about 80% of the width, no other text.
```
> Проверяй каждую букву: кириллицу модель иногда путает. Если не выходит, используй `logo_frame` и наложи название шрифтом игры.

**logo_en** — то же самое, но `reads exactly "CHALK CIRCLE", on two lines: "CHALK" above "CIRCLE"`.

**logo_tr** — то же самое, но `reads exactly "TEBEŞİR ÇEMBERİ" in Turkish, on two lines: "TEBEŞİR" above "ÇEMBERİ"; keep the Turkish letters Ş, İ (dotted capital I) and Ç exactly`. Проверь точку над İ и седили у Ş и Ç.

**logo_frame** — 1536×1024
```
The same flat chalk-and-crimson title composition (chalk circle stroke, candle, tiny skull, a few simple folk motifs), but with NO letters at all: an empty horizontal space in the center where a title will be placed.
```

**card_frame** (карточка товара в лавке) — 1024×1536
```
Vertical ornamental card inspired by Ivan Bilibin's book-page borders, flat vector: thin double black frame lines with an ochre line between them, simple corners with one birch leaf and a tiny skull each, a pointed arch at the top with a simple onion-dome motif, a narrow band with one simple repeating motif at the bottom. The interior is a flat deep indigo-black, plain and dark for readable text. Outside the card: transparent. No text.
```

**medallion** (ячейка Бестиария) — 1024×1024
```
A round medallion frame: a simple birch-bark ring (ivory with short black dashes) bound with a red thread and two small golden rosettes, the inner area completely transparent, transparent outside.
```

**ring_ornament** (подложка под круг) — 1024×1024
```
A perfectly circular protective circle drawn in ivory chalk on the ground, seen straight from above, flat vector: a double circle line with a slightly rough chalk edge, simple folk signs (diamonds, dots, small stars) and small eight-petal rosettes between the lines; no dust, no smudges, no texture. Exactly circular and centered; the outer line touches about 95% of the canvas. The inside of the circle and everything outside it are fully transparent.
```

**banner** («НОЧЬ 3 / 7», заголовки) — 1536×1024
```
A horizontal ribbon banner made of a rushnyk towel, one bold red zigzag border and short fringe at both ends, a plain muted ivory center left blank for text; the banner occupies the middle third of the canvas, everything else transparent.
```

**tag** (табличка подписи секции) — 1024×1024
```
A small horizontal tag made of a flat strip of birch bark (ivory with a few black dashes) with a dark plain center for text, tied with a red thread at the left end; simple shape suitable for 9-slice stretching; everything else transparent.
```

**candle** (4 свечи вокруг круга; огонь рисует игра) — 1024×1024
```
A single tall thin beeswax church candle, slightly bent, a few simple thick wax drips down its side, NO flame: the wick is black and unlit. The candle is vertical, centered, about 85% of the canvas height. Transparent background.
```

**Частицы** (по желанию, 1024×1024, прозрачный фон, объект ~60% кадра):
`fx_chalk` — `a flat cartoon puff cloud of ivory chalk with a few loose dots`;
`fx_ember` — `a single flat glowing ember shape with a short spark trail`;
`fx_blood` — `a flat cartoon blood splash with a few droplets, deep crimson`;
`fx_gold` — `a four-pointed flat golden sparkle with a tiny simple rosette in the middle`;
`fx_chip` — `a single small jagged flake of ivory chalk with broken angular edges and one bright highlight` (сколы мела при ране, этап 2.5; крошки дуги здоровья, 2.7).

---------------------------------------------------------------------------------------------------
## 7. Фоны
[STYLE] + [TECH-BG] + текст. Файлы: `art_src/bg/<id>.png`.
Для ПК (ландшафт) сделай горизонтальную версию основного фона: допиши
*"the same scene composed for a wide 1536x1024 landscape screen: calm dark central third, detail on the left and right"*.
Я сделаю, чтобы игра сама выбирала фон под ориентацию экрана.

**bg_fight** (+ `bg_fight_wide`)
```
A night forest glade from a Slavic fairy tale. Along the left and right edges: tall birch trunks (muted ivory, not pure white, with a few black marks) and dark firs as simple stylized layered-triangle shapes in Bilibin's decorative manner, a few overhanging branch shapes framing the top. Far back in the upper center: a dark indigo sky in simple horizontal bands with a huge pale moon half hidden behind two flat cloud bands; a distant wooden chapel silhouette with a crooked onion dome and one dim amber window; on the right, a fence of stakes topped with small skulls with faintly glowing eye sockets. Ground: dark grass as flat shapes, a couple of simple ferns, two fly agaric mushrooms and a few small yellow flowers in the bottom corners, and a flat band of pale-green fog across the lower third. Palette: deep indigo, moss green, bone, faint amber. Calm, dark, empty central area.
```

**bg_boss** — 7-я ночь
```
The same forest glade on the seventh night, turned into a marsh: a blood-red full moon, dead leaning birches with hanging moss shapes, flat black water with a few water lilies and reeds in the bottom corners, an open empty wooden coffin on trestles far in the background, flat red-tinted mist bands, two raven silhouettes on the branches. Calm, dark central area.
```

**bg_shop** — угол Домового
```
The cosy-creepy interior of an old Russian log izba at night, the house spirit's corner behind a big clay stove (muted ivory, not pure white): a shelf with a few glass jars of strange things, two bundles of dried herbs and garlic hanging from a beam, a rushnyk towel with a simple red border, a spinning wheel silhouette, a cat's glowing eyes under a bench, warm amber light from the lower left drawn as flat shapes, big flat shadow shapes. The upper-center third is a calm dim area (the shopkeeper sits there); the lower middle is a calm dark area (item card and circle).
```

**bg_dawn** — победа
```
The same forest glade at dawn: a pale pink and gold sky in Bilibin's flat horizontal bands, a flat band of mist, birches lit from behind, the chapel window dark, a rooster silhouette crowing on a fence. Calm and relieved, yet still slightly eerie. Calm central area.
```

**bg_menu** (по желанию, иначе возьму `bg_fight`)
```
The same forest glade at deep dusk: the last violet band of light on the horizon, the moon rising, the chapel window warm and inviting, a few firefly dots near the ferns, a flat band of mist starting to creep. Calm central area.
```

**fg_sides** — передний план для параллакса ([STYLE] + [TECH-OVERLAY]), 1024×1536 (и `fg_sides_wide`, 1536×1024)
```
Foreground parallax layer: very dark, almost black flat silhouettes of birch and fir trunks along the far left and far right edges, a few drooping branch shapes across the top corners and a couple of fern silhouettes in the bottom corners, solid shapes without inner detail. Everything else is fully transparent.
```

**frame_bilibin** — орнаментальная рамка поверх экрана, по желанию ([STYLE] + [TECH-OVERLAY]), 1024×1536
```
A simplified flat Bilibin-style page border for a vertical phone screen: narrow vertical side bands with a few simple pale flowers and birch stems, a thin top band with simple periwinkle flowers, a bottom band with a tiny flat landscape strip (a lake with a small boat at dusk); thin black and ochre frame lines. The whole interior (about 90% of the width and 88% of the height) is fully transparent.
```

---------------------------------------------------------------------------------------------------
## 8. Порядок работы и чек-лист (~70 картинок)

1. **Тест стиля:** `moshkara_idle`, 3–4 варианта, в новом чате. Доводишь [STYLE] до нужного вайба (см. п. 0.3 и 0.4).
2. **IDLE всех врагов и босса** (6 шт.) и `bg_fight`. После этого игру уже можно пересобрать на новые арты.
3. **Состояния врагов:** attack, hurt, weak (15 шт.); босс: attack, hurt, enraged, defeated (4 шт.).
4. **Склянки духов** (5 шт.), **иконки** (12 товаров + 6 UI).
5. **Домовой** (3), **Чтец** (3), **логотип**, `card_frame`, `medallion`, `ring_ornament`, `banner`, `candle`.
6. **Остальные фоны** и слои: `bg_shop`, `bg_boss`, `bg_dawn`, `bg_fight_wide`, `fg_sides`; по желанию рамка и частицы.

Можно присылать партиями, хоть по одной картинке: подключу всё, что уже готово, остальное останется на старых SVG.
