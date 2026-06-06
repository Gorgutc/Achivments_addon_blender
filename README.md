# Achievements Addon v0.1 — Руководство разработчика

Аддон геймификации для Blender 5.0+.
Основная проверяемая среда — Blender 5.1 stable; Blender 5.2 alpha используется как canary.
105 достижений, 9 уроков, XP-система с 10 уровнями, награды.
Каталог достижений и уроков теперь находится в `achievements/catalog.py`; корневой `__init__.py` остаётся Blender runtime entrypoint и импортирует legacy-имена каталога для совместимости.

Rule/progress evaluation is isolated in `achievements/engine.py`; Blender scene predicates remain in the runtime entrypoint.
Reward manifest/access/fallback planning is isolated in `achievements/rewards.py`; Blender asset linking remains in the runtime operator.
UI tab, pagination, scene-property, popup-width, overlay-geometry, and storage-filter contracts are isolated in `achievements/ui.py`; Blender layout and GPU drawing remain in the runtime adapter.
Offline sync planning is isolated in `achievements/sync.py`; the backend is disabled by default, networking is not wired into normal add-on use, and pinned UI state is excluded from sync payloads.

---

## Установка

### Вариант 1 — ZIP (release-задача)
1. `Edit → Preferences → Add-ons → Install from Disk...`
2. Выбрать release ZIP, подготовленный отдельной release-задачей. В текущем репозитории ZIP-артефакт не хранится.
3. Включить галочку «Achievements»

### Вариант 2 — Локальная проверка из рабочей папки
1. `Edit → Preferences → Add-ons → Install from Disk...`
2. Использовать папку/пакет, где рядом с корневым `__init__.py` есть пакет `achievements/`. Один файл `__init__.py` больше не является полной локальной установкой после миграции каталога.
3. Включить галочку «Achievements»

---

## Где хранятся данные

Ожидаемые пользовательские ассеты и прогресс хранятся вне репозитория:

```
~/BlenderAchievements/
├── achievements_data.json     ← Прогресс (авто-создаётся)
├── textures/                  ← Иконки достижений и уроков
│   ├── first_vertex_gray.png
│   ├── first_vertex_color.png
│   └── ...
└── rewards/                   ← .blend файлы наград
    ├── gold_plastic.blend
    ├── crown_mesh.blend
    └── ...
```

> Данные переживают переустановку Blender.
> Удаляются только при ручном удалении папки `~/BlenderAchievements/`.
> `achievements_data.json` хранится в текущей schema `1.0.0`; старый JSON мигрируется автоматически, а поврежденный JSON переносится рядом как `achievements_data.json.corrupt*`.

---

## Проверка разработки

Быстрый gate перед сдачей:

```bash
uv run python scripts/verify_frozen.py
uv run python scripts/verify_codex_plugin.py
uv run ruff check .
uv run pytest
```

Blender smoke запускается только через временные `HOME`, `USERPROFILE` и `BLENDER_USER_RESOURCES`; эти проверки не должны писать в реальный `~/BlenderAchievements`:

```bash
uv run python scripts/run_blender_smoke.py --suite register
uv run python scripts/run_blender_smoke.py --suite lifecycle_stress
uv run python scripts/run_blender_smoke.py --suite persistence
uv run python scripts/run_blender_smoke.py --suite engine
uv run python scripts/run_blender_smoke.py --suite rewards
uv run python scripts/run_blender_smoke.py --suite ui_visual
```

---

## Карта основных файлов

| Строки        | Что содержит                                  | Для чего редактировать                |
|---------------|-----------------------------------------------|---------------------------------------|
| **1–9**       | `bl_info`                                     | Имя аддона, автор, версия             |
| **46–52**     | Пути (`DATA_DIR`, `ICONS_DIR`, `REWARDS_DIR`) | Изменить папку хранения данных        |
| **58–66**     | Сетка карточек (`GRID_COLS`, `PAGE_SIZE`)     | Кол-во столбцов/строк в окне          |
| **72–83**     | Уведомления (`NOTIFY_*`)                      | Размер/длительность уведомлений       |
| **94**        | `_REWARD_SALT`                                | Соль хеша для защиты наград           |
| `achievements/catalog.py` | Категории, `ACHIEVEMENTS_DEF`, `LESSONS_DEF`, валидаторы каталога | Добавить/переименовать категории, достижения, уроки |
| `achievements/events.py` | Active-time, session, scene snapshot helpers | Править учет активности без импорта `bpy` |
| `achievements/lifecycle.py` | Idempotent registration helpers | Править hot-reload lifecycle без прямого изменения handler/timer wiring |
| `achievements/persistence.py` | Schema migration, atomic JSON writes, corrupt recovery | Править сохранение прогресса без импорта `bpy` |
| `achievements/sync.py` | Offline queue, disabled backend, deterministic conflicts | Plan future cloud sync without network calls in normal add-on use |
| **139–143**   | `DIFFICULTY_XP`                               | Очки XP за сложность                  |
| **156–167**   | `LEVEL_TITLES`                                | Звания уровней                        |
| **190–196**   | `_difficulty_label()`                         | Метки сложности на карточках           |
| **449**       | `_IDLE_TIMEOUT`                               | Тайм-аут бездействия (сек.)           |
| **813–1527**  | `_check_complex_step()`                       | Логика проверки комплексных достижений |

---

## 1. ГДЕ МЕНЯТЬ ТЕКСТЫ

### 1.1 Названия и описания достижений

**Файл `achievements/catalog.py`** — массив `ACHIEVEMENTS_DEF`

```python
{
    "id": "first_vertex",
    "title": "Первый шаг",              # ← НАЗВАНИЕ карточки
    "description": "Создать 1 вершину",  # ← ОПИСАНИЕ под названием
    ...
}
```

Для многошаговых достижений также есть текст шагов:
```python
"steps": [
    {"label": "Mirror", "check": "has_mirror"},         # ← label = текст шага
    {"label": "Subdivision", "check": "has_subsurf"},
]
```

### 1.2 Названия категорий

**Файл `achievements/catalog.py`:**
```python
ACH_CATEGORIES = [
    ("EDITING",    "Редактирование"),   # ← Второй элемент — отображаемое имя
    ("MATERIALS",  "Материалы"),
    ("GEO_NODES",  "Геометрические ноды"),
    ("TIME",       "Время в Blender"),
    ("RENDERING",  "Рендеринг"),
]
# Аналогично LESSON_CATEGORIES (строка 119) и REWARD_CATEGORIES (строка 127)
```

### 1.3 Звания уровней

**Строки 156–167:**
```python
LEVEL_TITLES = {
    1: "Новичок",      2: "Начинающий",    3: "Ньюблинг",
    4: "Ученик",       5: "Умелец",        6: "Мастеровой",
    7: "Эксперт",      8: "Виртуоз",       9: "Гуру",
    10: "Легенда",
}
```

### 1.4 Метки сложности

**Строки 190–196:**
```python
"easy":   ("Легко",  "SOLO_ON"),  # текст + иконка Blender
"medium": ("Средне", "TIME"),
"hard":   ("Сложно", "ERROR"),
```

### 1.5 Вкладки интерфейса

**Строка 2325** (внутри `register()`):
```python
items=[("TASKS", "Задания", ""), ("DONE", "Выполнено", ""),
       ("LESSONS", "Уроки", ""), ("STORAGE", "Хранилище", "")],
```

---

## 2. ГДЕ МЕНЯТЬ ИЛЛЮСТРАЦИИ (ИКОНКИ)

### 2.1 Иконки достижений

**Папка:** `~/BlenderAchievements/textures/`
**Формат:** PNG, 128×128 px (отображается 100×100)

У каждого достижения два поля (строки 251–357):
```python
"icon_gray": "first_vertex_gray.png",   # Заблокированное состояние
"icon_color": "first_vertex_color.png", # Разблокированное состояние
```

**Чтобы заменить:**
1. Создайте два PNG: `название_gray.png` и `название_color.png`
2. Положите в `~/BlenderAchievements/textures/`
3. Укажите имена в полях `icon_gray` / `icon_color`

> Если файл не найден — используется встроенная иконка FUND.

### 2.2 Иконки уроков

**Файл `achievements/catalog.py`** — поле `"icon"` в `LESSONS_DEF`:
```python
"icon": "lesson_verts.png"   # файл из textures/
```

### 2.3 Встроенные иконки Blender (для Blender 5.0+)

| Иконка     | Использование           | Примечание                   |
|------------|-------------------------|------------------------------|
| `FUND`     | Кнопка в хедере         | Вместо TROPHY (не существует)|
| `UNPINNED` | Кнопка «Закрепить»      | Вместо PIN (не существует)   |
| `PINNED`   | Кнопка «Открепить»      |                              |
| `SOLO_ON`  | Сложность «Легко»       | Вместо SOLO (не существует)  |

---

## 3. ГДЕ МЕНЯТЬ ССЫЛКИ НА УРОКИ

### 3.1 URL уроков

**Файл `achievements/catalog.py`** — массив `LESSONS_DEF`:
```python
{
    "id": "lesson_vertices_basics",
    "title": "Основы вершин",
    "description": "Создание, удаление, перемещение",
    "category": "EDITING",
    "url": "https://www.youtube.com/watch?v=lesson_verts",  # ← ССЫЛКА НА УРОК
    "icon": "lesson_verts.png",
},
```

Замените placeholder-ссылки на реальные URL видеоуроков.
Ссылка открывается в браузере при нажатии кнопки «Открыть урок».

### 3.2 URL в наградах-туториалах

Некоторые достижения имеют `"reward_type": "tutorial"`:
```python
"reward_data": {"url": "https://www.youtube.com/watch?v=time1"}   # ← ЗАМЕНИТЬ
```

**Быстрый поиск всех URL:**
```bash
grep -n '"url"' achievements/catalog.py
```

---

## 4. ГДЕ ДОБАВЛЯТЬ ФАЙЛЫ НАГРАД (.blend)

### 4.1 Папка наград

```
~/BlenderAchievements/rewards/
```

### 4.2 Типы наград и как подготовить .blend

| `reward_type` | Что в .blend              | Как применяется                |
|---------------|---------------------------|--------------------------------|
| `material`    | Материал                  | Назначается на активный объект |
| `mesh`        | Объект (меш)              | Добавляется в сцену            |
| `geo_nodes`   | Node Group                | Добавляется как GN-модификатор |
| `tutorial`    | Нет .blend, только URL    | Открывает ссылку в браузере    |
| `none`        | Нет награды               | —                              |

### 4.3 Как создать .blend для награды

**Материал:**
1. Откройте Blender → создайте материал с именем `ACH_GoldPlastic` (точно как в `"name"`)
2. `File → Save As` → `~/BlenderAchievements/rewards/gold_plastic.blend`

**Меш:**
1. Создайте объект с именем `ACH_CrownMesh` (точно как в `"name"`)
2. Сохраните как `rewards/crown_mesh.blend`

**Geometry Nodes:**
1. Создайте Node Group с именем `ACH_ArrayPattern` (точно как в `"name"`)
2. Сохраните как `rewards/array_pattern.blend`

> **Критично:** имя датаблока внутри .blend ОБЯЗАНО совпадать с полем `"name"` в `reward_data`.

### 4.4 Пример записи награды в ACHIEVEMENTS_DEF

```python
{
    "id": "thousand_vertices",
    ...
    "reward_type": "material",                                    # ← ТИП НАГРАДЫ
    "reward_data": {
        "name": "ACH_GoldPlastic",                                # ← ИМЯ ВНУТРИ .blend
        "description": "Золотистый пластик",                      # ← ОТОБРАЖАЕМОЕ ИМЯ
        "blend_file": "rewards/gold_plastic.blend",               # ← ПУТЬ К ФАЙЛУ
    },
    "reward_category": "SHADERS",   # ← Категория в хранилище
    ...
}
```

### 4.5 Полный список .blend файлов наград

Это ожидаемые имена пользовательских или release-packaged ассетов; сами `.blend` файлы не хранятся в текущем репозитории.

| .blend файл              | Тип        | Датаблок внутри        | Достижение                  |
|--------------------------|------------|------------------------|-----------------------------|
| `gold_plastic.blend`     | material   | `ACH_GoldPlastic`     | Тысяча вершин               |
| `stone_mat.blend`        | material   | `ACH_StoneMat`        | Тысяча граней               |
| `time_mat.blend`         | material   | `ACH_TimeMat`         | 5 часов погружения          |
| `rainbow_mat.blend`      | material   | `ACH_RainbowMat`      | Коллекция материалов        |
| `render_glow.blend`      | material   | `ACH_RenderGlow`      | Сто кадров                  |
| `chrome_metal.blend`     | material   | `ACH_ChromeMetal`     | Десять тысяч вершин         |
| `wire_mat.blend`         | material   | `ACH_WireMat`         | Полигональный бог           |
| `life_mat.blend`         | material   | `ACH_LifeMat`         | Материальный мастер         |
| `smooth_mat.blend`       | material   | `ACH_SmoothMat`       | Гладкий куб                 |
| `render_glow.blend`      | material   | `ACH_RenderGlowComplex`| Первый рендер              |
| `erase_mat.blend`        | material   | `ACH_EraseMat`        | Физик                       |
| `crown_mesh.blend`       | mesh       | `ACH_CrownMesh`       | Миллион вершин              |
| `erase_sphere.blend`     | mesh       | `ACH_EraseSphere`     | Архитектор высокого поли    |
| `clock_mesh.blend`       | mesh       | `ACH_ClockMesh`       | Пятьдесят часов             |
| `perfect_sphere.blend`   | mesh       | `ACH_PerfectSphere`   | Сфера из куба               |
| `star_mesh.blend`        | mesh       | `ACH_StarMesh`        | Легенда Blender             |
| `array_pattern.blend`    | geo_nodes  | `ACH_ArrayPattern`    | Фабрика сеток               |
| `scatter_grass.blend`    | geo_nodes  | `ACH_ScatterGrass`    | Сто тысяч вершин            |
| `time_vortex.blend`      | geo_nodes  | `ACH_TimeVortex`      | Сотня часов                 |
| `arch_geo.blend`         | geo_nodes  | `ACH_ArchGeo`         | Архитектор                  |
| `procedural_geo.blend`   | geo_nodes  | `ACH_ProceduralGeo`   | Процедурный мастер          |

> Если .blend не найден, аддон создаёт заглушку: случайный цвет (материал), икосферу (меш), или пустой модификатор (geo_nodes).

---

## 5. КАК ДОБАВИТЬ НОВОЕ ДОСТИЖЕНИЕ

### Стат-достижение (подсчёт статистики)

Добавьте словарь в `ACHIEVEMENTS_DEF` в `achievements/catalog.py`:

```python
{
    "id": "my_new_ach",                     # Уникальный ID (snake_case)
    "title": "Мой новый",                   # Название (русский)
    "description": "Описание условия",      # Описание (русский)
    "goal": 500,                             # Числовая цель
    "stat_key": "vertices_created",          # Ключ статистики (см. ниже)
    "category": "EDITING",                   # Категория
    "check_type": "stat",                    # Тип: стат-проверка
    "difficulty": "medium",                  # easy / medium / hard
    "reward_type": "none",                   # Тип награды
    "reward_data": {},                       # Данные награды
    "reward_category": "MESHES",             # Категория в хранилище
    "lesson_id": None,                       # ID связанного урока или None
    "icon_gray": "my_new_ach_gray.png",
    "icon_color": "my_new_ach_color.png",
},
```

**Доступные `stat_key`:**
| Ключ                | Что считает                        |
|---------------------|------------------------------------|
| `vertices_created`  | Созданные вершины                  |
| `vertices_deleted`  | Удалённые вершины                  |
| `edges_created`     | Созданные рёбра                    |
| `faces_created`     | Созданные грани                    |
| `meshes_1000plus`   | Меши с 1000+ вершинами             |
| `materials_applied` | Применённые материалы              |
| `renders_completed` | Завершённые рендеры                |
| `time_spent`        | Время активной работы (в секундах) |

### Комплексное достижение (проверка сцены)

1. Добавьте словарь с `"check_type": "complex"` и `"stat_key": "_complex"`
2. Добавьте проверку в функцию `_check_complex_step()` (строка 813):

```python
if step_check == "my_custom_check":
    return some_blender_condition
```

### Удаление достижения

1. Удалите словарь из `ACHIEVEMENTS_DEF`
2. Если комплексное — удалите кейс из `_check_complex_step()`
3. Старый прогресс останется в JSON, но будет проигнорирован

---

## 6. XP-СИСТЕМА

| Параметр          | Строки   | Описание                                     |
|-------------------|----------|----------------------------------------------|
| `DIFFICULTY_XP`   | 139–143  | Очки за сложность: easy=5, medium=10, hard=20|
| `XP_LEVELS`       | 147–153  | Пороги уровней (удваиваются от 20)           |
| `LEVEL_TITLES`    | 156–167  | Русские звания для каждого уровня             |

Итого: уровень 10 требует 20460 XP суммарно.

---

## 7. БЫСТРЫЙ ПОИСК

```bash
# Все русские тексты:
grep -n '[А-Яа-яЁё]' achievements/catalog.py

# Все URL:
grep -n 'http' achievements/catalog.py

# Все .blend файлы наград:
grep -n 'blend_file' achievements/catalog.py

# Все иконки:
grep -n 'icon_gray\|icon_color' achievements/catalog.py

# Все stat_key:
grep -n 'stat_key' achievements/catalog.py

# Все проверки комплексных шагов:
grep -n 'step_check ==' __init__.py
```

---

## 8. ИЗВЕСТНЫЕ ОГРАНИЧЕНИЯ v0.1

- Иконки — заглушки (без реальных PNG файлов, используется FUND)
- URL уроков — заглушки (placeholder YouTube ссылки)
- .blend файлы наград — не включены (создаётся заглушка при отсутствии)
- Нет кнопки «Сбросить достижения» (по требованию)
- Cloud sync is a disabled offline stub only: no production backend, no normal-use network calls, and no pinned overlay state sync by default.
