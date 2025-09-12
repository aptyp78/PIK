# PIK‑AI — Аудит (живое окружение + код) — 2025-09-12 13:55 CEST
Автор: GPT-5 Thinking

## 0) Резюме
Фронтенд (Next.js) и навигация живы; интеграция с Qdrant отображает документы и блоки. Данные Adobe в GCS присутствуют (38 JSON), но страницы `/pipeline/adobe` и `/pipeline/adobe/viewer` ломаются из‑за `ChunkLoadError` (динамический чанк не раздаётся через Cloudflare Tunnel), поэтому просмотр bbox невозможен. Нет runtime‑валидации артефактов и шаблонов зон, нет метрик покрытия и hash‑гарда PDF↔JSON — из‑за этого легко получить «пустые экраны» без явной причины. Требуются P0‑фиксы: восстановить раздачу чанков, добавить схемы, stats и быстрый hash‑guard; затем тесты и минимальные метрики.

## 1) Что проверено (live)
- Публичный URL: `https://throw-requirements-wallpaper-download.trycloudflare.com`.
- **Console** загружается; есть кнопки `Open Results / Run Platform Workflow / Create Qdrant Indexes` и форма Annotate.
- **Results (Qdrant)**: список документов виден; блоки (фрагменты текста) отображаются, сущности пусты.
- **Adobe (GCS)** и **Viewer**: переход ведёт к `ChunkLoadError` для `app/pipeline/adobe/page.js`; прямой вызов `/api/pipeline/gcs/adobe/status` — ok (count=38).
- Тестовые PDF, доступные локально: `/mnt/data/2023-06 - fastbreakOne - Expert Guide - Ecosystem Strategy  - English.pdf`, `/mnt/data/PIK 5-0 - Introduction - English.pdf`.

## 2) Диагноз (корневые причины)
1. **Сборка/раздача чанков**: динамический чанк страницы Adobe/Viewer не отдается туннелем → UI ломается.
2. **Отсутствие валидации и метрик**: нет JSON‑схем, stats и hash‑гарда → трудно диагностировать несоответствие PDF↔JSON и unmatched.
3. **Неполная обработка данных**: дубликаты блоков, пустые «сущности» в Results указывают на недостающую дедупликацию и/или роль полей.

## 3) Воспроизведение
1. Открыть `/pipeline/adobe` → Unhandled Runtime Error (`ChunkLoadError … app/pipeline/adobe/page.js`).
2. Открыть `/api/pipeline/gcs/adobe/status` → список из 38 элементов (префикс `Adobe_Destination/…`).
3. Открыть `/results` → список документов и блоки появляются, сущности — пусто.

## 4) Что нужно сделать (приоритеты)

### P0 — «чтобы заработало»
- **Fix chunks**: отключить code‑splitting для страниц `/pipeline/adobe` и `/pipeline/adobe/viewer` в production build ИЛИ настроить правильную раздачу `_next/static/chunks/**` через туннель.
- **Schema‑validation**: Zod/TypeBox схемы для шаблонов зон и ключевого подмножества Adobe JSON (`bbox`, `page`, `content`, `type`).
- **Stats в mapping**: в ответе и сохранении рядом с результатом — `total/matched/unmatched/coverage` + примеры unmatched.
- **PDF↔JSON hash‑guard**: `meta.pdfSignature={pageCount, sha256(firstPage)}` и проверка во Viewer/API.
- **Retry/backoff** для polling Adobe.

### P1 — «чтобы не ломалось»
- Unit‑тесты для `canvasMap` (границы 0/1; overlap‑приоритет).
- CLI `map:batch` по всем `Adobe_Destination/**` + экспорт CSV по зонам.
- Логи нормализации координат (первые N преобразований под флагом).

### P2 — «качество и масштаб»
- Редактор шаблонов зон + легенда цветов во Viewer.
- Версионирование Mapping‑результатов (`.vTIMESTAMP.json`) и детектор overlap в шаблонах.
- `/api/metrics` (dev) и простые счётчики (ingest/mapping/errors).

## 5) Изменения API и конфигурации (кратко)
- `GET /api/mapping/templates` — без изменений.
- `POST /api/mapping/map` — дополнить блоком `stats` и `meta.templateHash/pdfSignature`.
- Новые флаги env: `ADOBE_MAX_POLLS`, `ADOBE_BASE_DELAY_MS`, `LOG_NORMALIZED`.
- Конфиг `GCS_*` — централизовать в `config/index.ts`.

## 6) Риски и ходы снижения
- **Silent failure** без схем → → Включить валидацию и «жёлтую полосу» предупреждений в UI при unmatched>0.
- **Перегруз JSON** при больших файлах → → ленивый рендер страниц и ограничение payload в Viewer.
- **Security** (прямой доступ к именам объектов) → → sanitize/whitelist для `name` в API.

## 7) Определение готовности (DoD)
- `/pipeline/adobe` и `/pipeline/adobe/viewer` открываются через Cloudflare URL, все чанки грузятся.
- Для любого артефакта Adobe отображается PDF+bbox; видно coverage>=X% и список unmatched.
- В `Mapping/...stats.json` сохраняются метрики; unit‑тесты для `canvasMap` зелёные.
- Документация по env/портам консистентна (PORT не конфликтует).

## 8) Приложение — чек‑лист ревью PR
- [ ] Нет динамических чанков для проблемных страниц ИЛИ статические файлы `_next/static/**` гарантированно доступны.
- [ ] Схемы: шаблоны зон и Adobe JSON валидируются в рантайме.
- [ ] Ответ `/api/mapping/map` содержит `stats` и `meta`.
- [ ] Добавлены тесты `canvasMap` + snapshot кейсы.
- [ ] Лимиты polling Adobe и backoff.
