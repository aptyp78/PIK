# Проект PIK‑AI — Аудит и Технический Отчёт

Дата: 2025‑09‑12

## 1. Резюме

- Назначение: загрузка и парсинг PDF (и PNG для Unstructured) по методологии PIK, хранение результатов (текст, таблицы, координаты), предпросмотр и детерминированный маппинг элементов на зоны канваса.
- Источники: PDF в GCS `GCS_SOURCE_BUCKET`.
- Результаты Adobe: только GCS `GCS_RESULTS_BUCKET/Adobe_Destination/...pdf.json`.
- Веб‑UI: предпросмотр JSON, вьюер «PDF + bbox», выбор шаблона зон и цветной маппинг по центроиду.
- Технологии: Next.js 14, TypeScript, Prisma (SQLite), GCS SDK, pdf.js, Adobe PDF Services, (опц.) Unstructured, (опц.) Qdrant.

## 1.1 Ссылки (для быстрого доступа)

- Внешняя (публичная) ссылка на проект: https://throw-requirements-wallpaper-download.trycloudflare.com
  - Адрес выдан Cloudflare Quick Tunnel и активен, пока работает процесс туннеля (запущен с параметром `--protocol http2` для обхода сетевых ограничений UDP/QUIC).
  - Пример страниц (добавьте к базовому URL):
    - `/pipeline/adobe/viewer` — вьюер «PDF + bbox + маппинг зон»
    - `/pipeline/adobe` — список артефактов Adobe (GCS)
    - `/results` — обзор Qdrant
    - Пример глубокой ссылки на вьюер c артефактом:
      `/pipeline/adobe/viewer?name=Adobe_Destination%2FPIK-5-Core-Kit%2F2023-fastbreakOne-Expert-Guide-Ecosystem-Strategy%2FL2%20-%20Ecosystem%20Strategy%20Map.pdf.json`

- Локальная ссылка (dev): http://localhost:3002
  - `/pipeline/adobe/viewer`
  - `/pipeline/adobe`
  - `/results`

## 2. Архитектура и основные модули

- Веб‑приложение: `app/*` (Next.js, API и UI), SSR `nodejs` runtime.
- Adobe PDF Services клиент: `lib/pdf/adobeExtract.ts`.
- Хранилище GCS: `lib/gcs.ts` (list/upload/download, text/buffer).
- Вьюер: `app/pipeline/adobe/viewer/page.tsx`, `app/pipeline/adobe/viewer/Client.tsx` — фон‑PDF (pdf.js) + overlay bbox.
- Сервисы GCS для вьюера:
  - `GET /api/pipeline/gcs/adobe/status` — листинг `Adobe_Destination`.
  - `GET /api/pipeline/gcs/adobe/get?name=...` — JSON артефакт.
  - `GET /api/pipeline/gcs/pdf?name=...` — PDF из `GCS_SOURCE_BUCKET`.
- Детерминированный маппинг (Canvas Mapping):
  - Шаблоны: `lib/mapping/templates/*.json` (пример `PIK_PBM_v5.json`).
  - Ядро: `lib/mapping/canvasMap.ts` — centroid → норм.координаты → попадание в окно зоны.
  - API: `GET /api/mapping/templates`, `POST /api/mapping/map` (вход `{ name, template, save? }`).
- Батч‑парсинг Adobe из GCS источника: `scripts/adobeBatchFromGcs.ts`.

## 3. Потоки данных

### 3.1 Adobe (PDF)
- Ввод: `GCS_SOURCE_BUCKET[/GCS_SOURCE_PREFIX]` (`*.pdf`), опционально `/upload` c `engine=adobe` (только PDF).
- Парсинг: `extractWithRawJob` (upload asset → start → poll → download ZIP → `structuredData.json`).
- Вывод: `GCS_RESULTS_BUCKET/Adobe_Destination/<path>.pdf.json`.
- Просмотр: `/pipeline/adobe` и `/pipeline/adobe/viewer`.

### 3.2 Unstructured (опц.)
- Ввод: `/upload?engine=unstructured` (PDF/PNG — PNG допустим).
- Вывод: локальная БД (SQLite) — таблица `Block` (страница `/docs/:id`).

### 3.3 Qdrant (опц.)
- Просмотр: `/results`, `/pipeline/final`, `GET /api/qdrant/*`.
- Пост‑процесс bbox: `POST /api/pipeline/qdrant/annotate` — сопоставляет текст и дописывает `bbox/page` в payload точек.

## 4. UI маршруты

- `/pipeline/adobe` — список JSON из `Adobe_Destination`.
- `/pipeline/adobe/viewer` — фон‑PDF + bbox; фильтры «Только текст», «Без огромных»; выбор шаблона зон, цветная подсветка по зоне.
- `/results` — обзор по Qdrant.
- `/pipeline/final` — sample точек из Qdrant.
- `/upload` — загрузка (Adobe: только PDF; Unstructured: PDF/PNG).

## 5. API эндпоинты (ключевые)

- GCS/Viewer:
  - `GET /api/pipeline/gcs/adobe/status`
  - `GET /api/pipeline/gcs/adobe/get?name=Adobe_Destination/...pdf.json`
  - `GET /api/pipeline/gcs/pdf?name=<path>.pdf`
- Mapping (Canvas):
  - `GET /api/mapping/templates`
  - `POST /api/mapping/map` — тело `{ name, template, save? }`; возвращает `{ zones, items:[{..., zoneId}], counts, dims }`. При `save:true` пишет `GCS_RESULTS_BUCKET/Mapping/<template>/<name>`.
- Qdrant (опц.):
  - `GET /api/qdrant/sample`, `GET /api/qdrant/point`, `GET /api/qdrant/stats`, `POST /api/qdrant/indexes`.
  - `POST /api/pipeline/qdrant/annotate?fileId|filename&limit=N` (bbox/page patch).

## 6. Шаблоны зон (детерминированный маппинг)

- Формат: `lib/mapping/templates/<id>.json`:
  ```json
  {
    "id": "PIK_PBM_v5",
    "title": "Platform Business Model v5",
    "version": "5.0",
    "zones": [ { "id": "...", "title": "...", "box": [x1,y1,x2,y2] } ]
  }
  ```
  где `box` — нормализованные координаты в долях (0..1) от ширины/высоты страницы; начало координат — внизу слева (как у PDF).
- Алгоритм: для каждого элемента Adobe берём bbox → центроид (cx,cy) → нормализуем (cx/w, cy/h) → ищем зону, чей `box` содержит точку.
- Версионирование: `id` шаблона (например, `PIK_PBM_v5`, `PIK_PBM_v5_1`).

## 7. Конфигурация окружения (основное)

- Adobe PDF Services:
  - `ADOBE_CLIENT_ID`, `ADOBE_CLIENT_SECRET`, `ADOBE_REGION?`
  - `ADOBE_ELEMENTS` — список сущностей для извлечения (по умолчанию `text,tables`).
- GCS:
  - `GCS_SOURCE_BUCKET`, `GCS_SOURCE_PREFIX?` — исходные PDF.
  - `GCS_RESULTS_BUCKET` — бакет для результатов.
  - `GCS_ADOBE_DEST_PREFIX` — префикс для JSON Adobe (напр., `Adobe_Destination`).
  - `GCS_MAPPING_PREFIX` — префикс для результатов маппинга (по умолчанию `Mapping`).
  - `GCS_SA_KEY_FILE` — путь к JSON ключу сервис‑аккаунта.
- Qdrant (опц.): `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_API_KEY_RO`, `QDRANT_API_KEY_RW`.
- Unstructured (опц.): `UNSTRUCTURED_API_URL`, `UNSTRUCTURED_API_KEY`, `UNSTRUCTURED_WORKFLOW_ID`, `UNS_SOURCE_CONNECTOR_ID`, `UNS_DEST_QDRANT_ID`.
- Прочее: `INGEST_ENGINE_DEFAULT` (`unstructured|adobe`).

## 8. База данных (Prisma/SQLite)

- **SourceDoc**: `{ id, title, type, path, engine?, pages?, createdAt }`.
- **Block**: `{ id, sourceDocId, page, bbox, role, text?, tableJson?, hash? }`.
- Удалены: canvas‑поля и модели `Zone`, `Evidence` (BM), связанные API удалены.

## 9. Безопасность и доступы

- Секреты в `.env.local`. Ключи Adobe/Unstructured не логируются.
- GCS: сервис‑аккаунт с минимумом прав (`Storage Object Viewer/Creator` по необходимости).
- Ограничить исходящий доступ (Adobe/Unstructured/Qdrant/GCS) в проде; учесть квоты.

## 10. Запуск и эксплуатация

- Dev: `npm install` → `npm run dev` (примерно `http://localhost:3000` или заданный `PORT`).
- Батч Adobe из GCS: `npx tsx scripts/adobeBatchFromGcs.ts --limit=0`
- Вьюер: `/pipeline/adobe/viewer` (можно `?name=Adobe_Destination/...pdf.json`).
- REST‑маппинг: `POST /api/mapping/map` с `save:true` для записи результата в GCS.

### 10.1 Публичная ссылка (туннель Cloudflare)

- Требуется установленный `cloudflared`.
- Запуск: `npm run tunnel:cf` (или `cloudflared tunnel --url http://localhost:3002`).
- Скрипт: `scripts/tunnel-cloudflare.sh`.
- В консоли появится внешний URL вида `https://<random>.trycloudflare.com` — подставьте его вместо `YOUR-PUBLIC-URL` выше.

## 11. Диагностика

- Здоровье Adobe: `GET /api/health/adobe` (сети и базовые проверки).
- Список Adobe JSON: `GET /api/pipeline/gcs/adobe/status`.
- Стрим PDF из источника: `GET /api/pipeline/gcs/pdf?name=...`.
- Список шаблонов: `GET /api/mapping/templates`.

## 12. Ограничения и риски

- Adobe: PNG не обрабатываем (только PDF); для PNG используйте Unstructured.
- Координаты/страницы: приведение через max(x/y) — редкие документы могут требовать тонкой подстройки.
- Viewer: рассчитан на артефакты `Adobe_Destination` и соответствующие им PDF из `GCS_SOURCE_BUCKET` с тем же путём.

## 13. Рекомендации и дорожная карта

- Уточнить зоны канваса под реальные постеры (отредактировать `lib/mapping/templates/PIK_PBM_v5.json`).
- Добавить редактор шаблонов в UI (опционально) и легенду цветов.
- Добавить фильтры по типам элементов (heading/table/paragraph...).
- Добавить батч‑маппинг всего `Adobe_Destination` и выгрузку сводных отчётов по зонам (CSV/JSON).

---

### Приложение A — Ключевые файлы

- Парсинг Adobe: `lib/pdf/adobeExtract.ts`
- GCS helper: `lib/gcs.ts`
- Viewer: `app/pipeline/adobe/viewer/page.tsx`, `app/pipeline/adobe/viewer/Client.tsx`
- API: `app/api/pipeline/gcs/adobe/status`, `app/api/pipeline/gcs/adobe/get`, `app/api/pipeline/gcs/pdf`
- Mapping: `lib/mapping/templates/*.json`, `lib/mapping/canvasMap.ts`, `app/api/mapping/templates`, `app/api/mapping/map`
- Батч: `scripts/adobeBatchFromGcs.ts`

## 14. Аудит и оценка зрелости

### 14.1 Сильные стороны
- Чёткое разделение: ingestion (Adobe/Unstructured) / storage (GCS+SQLite) / mapping / viewer.
- Детерминированный маппинг (простая трассируемость, воспроизводимость).
- Лёгкая расширяемость добавлением новых шаблонов зон (JSON).
- Использование GCS как единого источника артефактов (прозрачно для batch и UI).
- Минимальная связность между модулем Qdrant и основным конвейером (опциональность).

### 14.2 Выявленные пробелы / техдолг
- Нет интеграционных и регрессионных тестов (особенно: mapping edge cases, расхождение bbox Adobe/pdf.js).
- Отсутствие нормальной схемы валидации входных JSON (шаблоны + артефакты Adobe) — риск silent failure.
- Нет версионирования результатов маппинга (кроме id шаблона) — сложнее повторное сравнение.
- Отсутствует слой нормализации координат с диагностикой (логика спрятана в canvasMap без трейсинга).
- Нет unified event логов (pipeline steps: fetch → extract → store → map).
- Потенциальный single-thread batch (scripts/adobeBatchFromGcs.ts) — не задокументированы лимиты параллелизма.
- Нет мониторинга (health endpoints минимальны; latency / size метрики отсутствуют).
- Неполный security hardening: нет явного перечисления ролей GCS и key rotation policy.
- Нечёткая политика очистки промежуточных ZIP (Adobe) — потенциальное накопление локальных артефактов (если кешируются).
- Viewer не валидирует соответствие страниц JSON/PDF (нет hash/pageCount cross-check).
- Нет deduplication/хэширования элементов (поля hash? используются только в Block частично).
- Нет SLA для batch-процессов; не управляются ретраи (экспоненциальные паузы?).

### 14.3 Классификация рисков
- Функциональные: рассинхронизация координат из-за различий DPI/pdf.js vs Adobe.
- Операционные: ручной перезапуск batch, отсутствие retry & dead-letter очереди.
- Данные: отсутствие схемной валидации → «тихий» пропуск зон или неверное попадание.
- Security: риск утечки сервис-аккаунта при dev‑доступах (нет секции rotation).
- Масштаб: рост количества PDF приведёт к линейному времени batch без шардирования.

### 14.4 Рекомендованные метрики
- Ingestion:
  - pdf_ingest_latency_ms (p50/p95)
  - adobe_job_poll_cycles (avg/max)
- Mapping:
  - mapping_items_total, mapping_unmatched_total
  - zone_coverage_ratio (matched / total)
- Viewer:
  - viewer_payload_size_bytes (p95)
- Ошибки:
  - extraction_fail_total, mapping_fail_total
- Диагностика качества:
  - avg_items_per_page, large_bbox_outliers (bbox area > threshold)

### 14.5 Предлагаемая зрелость (оценка 1–5)
- Архитектура: 3 (простая и ясная, но нет resilience)
- Тестирование: 1 (отсутствует)
- Observability: 1–2 (минимум health)
- Security hygiene: 2
- Data quality controls: 2
- Automation CI/CD: 1 (не описано)
- Scalability readiness: 2

### 14.6 Приоритетные действия

P0 (немедленно):
1. Добавить JSON schema валидацию для: a) шаблонов зон b) Adobe structuredData.json (минимальный subset).
2. Логирование метрик unmatched зон + сохранение отчёта (counts + coverage) рядом с результатом Mapping.
3. Хэширование соответствия PDF ↔ JSON (pageCount + checksum первой страницы) — быстрый guard в viewer/API.
4. Retry/poll policy для Adobe: лимит циклов + экспоненциальная задержка.

P1 (следующий спринт):
1. Набор unit тестов для canvasMap (граничные x=0/1, y=0/1, пересечения зон, приоритет при overlap).
2. Добавить CLI/скрипт batch mapping всех артефактов Adobe (с агрегированием CSV).
3. Вынести нормализацию координат в отдельный модуль с трассировкой (debug лог).
4. Ввести простую prom-like метрику (в файл или stdout) + endpoint /api/metrics (dev).
5. Автоматическая проверка консистентности шаблонов (нет пересекающихся зон > N%).

P2 (план):
1. Переход на фоновые очереди (например, Cloud Tasks / simple worker pool) для batch Adobe.
2. Версионирование результатов Mapping (Mapping/<template>/<doc>.vTIMESTAMP.json).
3. Добавить редактор шаблонов в UI + визуализация heatmap попаданий.
4. Автоматический отчёт покрытия зон (top N заполненных / пустых).
5. Интеграция alerting (ошибки извлечения > threshold).

### 14.7 Улучшения архитектуры
- Ввести слой domain services: ExtractService / MappingService / ReportService — уменьшит дубли лога.
- Вынести конфигурацию префиксов в единый config.ts, сейчас разбросано по env + вызовам.
- Добавить адаптер для альтернативных движков (Adobe|Unstructured) с единым результатом (интерфейс NormalizedBlock).

### 14.8 Предложение по расширению mapping результата
Пример расширенного JSON (добавить):
{
  "stats": {
    "total": 123,
    "matched": 118,
    "unmatched": 5,
    "coverage": 0.959,
    "zones": { "ZoneA": 34, "ZoneB": 12, "...": 0 }
  },
  "meta": {
    "templateVersion": "5.0",
    "templateHash": "sha256:...",
    "generatedAt": "2025-09-12T10:22:00Z"
  }
}

### 14.9 Контроль качества данных
- Валидация bbox: (x2 > x1 && y2 > y1 && все в пределах страницы).
- Отсев huge boxes (выше N% площади) и логирование.
- Обнаружение «пустых» зон → добавить в aggregated отчёт.

### 14.10 Минимальный тестовый набор
- canvasMap: точка в центре зоны; точка на границе (включить правило inclusive?).
- Overlap: при пересечении — фиксированный порядок (например, первый в массиве).
- Template schema: отказ при пропуске id/title/zones[].box длиной != 4.
- Adobe artifact: отсутствует pages → ошибка.
- Mapping API: save=true записывает и доступен через GCS листинг.

### 14.11 Быстрые выигрыши (Quick Wins)
- Добавить script validate-templates.ts (JSON.parse + schema).
- Добавить npm script "lint:zones".
- В viewer: подсветить unmatched (серый/штрих).
- В mapping ответ: counts.unmatched + массив первых N примерных элементов.

### 14.12 Риски при масштабировании
- GCS list пагинация (при >1k объектов) — убедиться в корректном переборе.
- Потенциально большие structuredData.json → стриминг? (сейчас, вероятно, целиком в память).
- При параллельных Adobe job: лимиты API Adobe (нужен rate limiter).

### 14.13 Рекомендуемая структура каталогов (необязательное)
- src/
  - config/
  - services/
  - adapters/ (adobe, unstructured)
  - mapping/
  - api/
  - scripts/
  - viewers/

### 14.14 Итог
Система функционально целостна, но требует усиления наблюдаемости, тестируемости и контроля качества данных для надёжного масштабирования и воспроизводимости.

## 15. Расширенный roadmap (конспект)

| Этап | Цель | Артефакт |
| ---- | ---- | -------- |
| Sprint 1 | Валидация + метрики | schema + metrics endpoint |
| Sprint 2 | Batch mapping + отчёты | CSV/JSON coverage |
| Sprint 3 | Версионирование + редактор зон | vN шаблонов |
| Sprint 4 | Очереди + алерты | worker + alerts |
| Sprint 5 | Нормализация движков | unified blocks |

(Таблица укорочена для отчёта.)

## 16. Детальный аудит кода

### 16.1 Методика
Статический обзор архитектурных точек (файлы из Приложения A), предположительные паттерны на основе описанных API. Цель: минимизировать скрытые риски при масштабировании и повысить надёжность.

### 16.2 Сводка ключевых замечаний (Top)
- Типизация: вероятно недостаточная строгость структур Adobe/Mapping (нужен runtime guard).
- Ошибки: разнородный стиль (throw vs возвращаемые объекты) → усложнённое логирование.
- Валидация входа API: отсутствуют схемы (risk injection / silent mismatch).
- Конфигурация: env читается точечно — нет единой нормализации + fallback.
- Производительность: парсинг больших JSON целиком в память (нет stream / chunk).
- Конкурентность: polling Adobe без лимита retry/backoff.
- Mapping: линейный перебор зон для каждого элемента (сейчас ок, но предусмотрите индексацию).
- Логирование: отсутствие структуры (level, context, docId).
- Тесты: отсутствуют snapshot/edge кейсы координат и деградации DPI.
- Безопасность: прямой проксирующий доступ к именам объектов в GCS без нормализации.
- Наблюдаемость: нет correlation id сквозного (request → mapping).

### 16.3 Типизация и модели
Проблема: Неявные структуры JSON (Adobe) → риск undefined полей.
Рекомендации:
- Ввести тип ExtractedItem с union:
  type ExtractedItem = { kind: 'text'; bbox: BBox; content: string; page: number } | { kind: 'table'; bbox: BBox; rows: string[][]; page: number }
- Использовать Zod / TypeBox для runtime проверки перед маппингом.
Пример (упрощённо):
```ts
// adobeTypes.ts
export interface BBox { x1:number; y1:number; x2:number; y2:number; page:number }
export type BlockKind = 'text' | 'table';
export interface TextBlock { kind:'text'; bbox:BBox; content:string }
export interface TableBlock { kind:'table'; bbox:BBox; rows:string[][] }
export type AnyBlock = TextBlock | TableBlock;
```

### 16.4 Обработка ошибок
Текущий риск: разнородные ошибки → потеря контекста (doc, phase).
Рекомендации:
- Ввести AppError(code, message, meta).
- Центральный helper:
```ts
export function fail(code:string, message:string, meta?:Record<string,unknown>): never {
  const err = new Error(message) as any;
  err.code = code; err.meta = meta;
  throw err;
}
```
- Middleware для API: маппинг code → HTTP статус.

### 16.5 Валидация шаблонов зон
Проблема: Возможны пересечения и неверные box массивы.
Решения:
- Schema + проверка пересечений > overlapThreshold.
- Кешировать hash(templateJSON) → класть в результат mapping.meta.templateHash.

### 16.6 Алгоритм маппинга
Текущее: O(N * Z). При росте можно:
- Предпостроить uniform grid (8×8) → список зон по ячейке.
- Или построить interval trees по X / Y.
Quick win (микрооптимизация):
```ts
// Предварительно нормализовать зоны в структуру с precalc width/height.
interface ZoneIdx { id:string; box:[number,number,number,number] }
```

### 16.7 Нормализация координат
Риск: Разный origin (PDF снизу-слева vs canvas сверху-слева).
Действия:
- Вынести normalizePoint(pageWidth, pageHeight, [x1,y1,x2,y2]) в отдельный модуль.
- Добавить debug флаг: LOG_NORMALIZED=1 → журнал первых N преобразований.

### 16.8 GCS слой
Риски:
- Повтор кода list / get / stream.
- Отсутствие safe join (name может содержать '../').
Рекомендации:
- sanitizeObjectName(name) → reject ../ и непечатаемые.
- Добавить функцию getJson<T>(bucket, key, schema?) → central parsing + validation.
- Включить опцию диапазонного чтения (range) при больших PDF (если понадобится частичный просмотр).

### 16.9 Adobe polling
Рекомендации:
- Конфигурируемые параметры: MAX_POLLS, BASE_DELAY_MS, JITTER.
- Экспоненциальная формула: delay = min(BASE * 2**attempt, MAX_DELAY).
- Логирование каждые K циклов.

### 16.10 Viewer
Риски:
- Нет проверки соответствия pageCount.
- Возможные большие payload → UI лаг.
Рекомендации:
- Lazy load страниц (виртуализация).
- Отдельно помечать unmatched элементы (CSS класс).
- Профилировать время рендера (performance.now()) при dev.

### 16.11 API уровень
Checklist:
- Все POST → body schema validate.
- GET /.../get?name= → ограничить длину и whitelist regexp.
- Добавить X-Request-Id (если нет) → прокинуть в логи.

### 16.12 Логирование и метрики
Рекомендации:
- logger.info({phase:'mapping', doc, matched, unmatched})
- Метрики (простейший регистр):
```ts
const metrics = { mapping_items_total:0, mapping_unmatched_total:0 };
export function incr(name:string, v=1){ metrics[name]=(metrics[name]||0)+v; }
```
- Endpoint /api/metrics (dev only).

### 16.13 Тестирование (минимальный план)
Unit:
- bbox normalize (границы 0/1).
- canvasMap: попадание в каждую зону + пересечение.
- template validator: invalid box length, пересечения.
Integration:
- end-to-end: загрузка → fake Adobe JSON → mapping → проверка статистики.
Property-based (опц.):
- Генерация случайных зон + точек (fast-check) → проверка детерминизма.

### 16.14 Производительность
Узкие места:
- Полный JSON parse large structuredData.
Опции:
- Если структура допускает: stream + pick только нужные поля (например, через JSON.parse chunk libs).
- Кеш результатов hashing (SHA256) для immutable артефактов.

### 16.15 Безопасность
- Redact fields: секреты не логировать (фильтр logger).
- Отдельный модуль accessPolicy.ts — описать какие префиксы разрешены для чтения UI.
- Защитить от слишком длинных путей ( > 512 chars → reject).

### 16.16 Конфигурация
Ввести config/index.ts:
```ts
export const cfg = {
  adobe: { elements: (process.env.ADOBE_ELEMENTS||'text,tables').split(',') },
  gcs: {
    sourceBucket: reqEnv('GCS_SOURCE_BUCKET'),
    resultsBucket: reqEnv('GCS_RESULTS_BUCKET'),
    adobePrefix: process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination',
    mappingPrefix: process.env.GCS_MAPPING_PREFIX || 'Mapping'
  },
  mapping: { maxOverlapRatio: 0.05 }
};
```

### 16.17 Quick Wins (код)
1. Добавить schema валидацию шаблонов.
2. Central logger + AppError.
3. stats в mapping результат (coverage, unmatchedSamples).
4. sanitizeObjectName для GCS API.
5. Retry policy для Adobe.

### 16.18 Refactor Tracks (глубже)
Track A (Reliability): errors + retry + metrics.
Track B (Data Quality): schemas + template overlap detector.
Track C (Perf): zone index + streaming large JSON (при достижении порога >10MB).
Track D (DX): config unification + тестовые фикстуры.

### 16.19 Пример целевого интерфейса MappingService
```ts
interface MappingResult {
  items: (AnyBlock & { zoneId?:string })[];
  stats: { total:number; matched:number; unmatched:number; coverage:number; perZone:Record<string,number> };
  meta: { templateId:string; templateHash:string; generatedAt:string };
}
export class MappingService {
  constructor(private template:Template){ /* precompute index */ }
  map(blocks:AnyBlock[]): MappingResult { /* ... */ }
}
```

### 16.20 Итог
Кодовая база готова к ускоренному усилению без фундаментальных переписываний. Основные выгоды придут от стандартизации (config, errors, schemas) и введения минимальных метрик + тестов.

---
## 17. Обзор последних изменений (Review)

### 17.1 Что добавлено
- 1.1 Ссылки: быстрый доступ (public/dev) + пример глубокой ссылки на вьюер.
- 10.1 Туннель Cloudflare: процедура публикации dev окружения.
- Расширен финальный аудит (раздел 16) — детализирована техническая часть (типизация, ошибки, метрики, perf).
- Единообразие терминов (mapping, zones) сохранено.

### 17.2 Консистентность и замечания
- Порт: в разделе 10 указан 3000, в 1.1/10.1 упомянут 3002 — требуется унификация (либо задать переменную PORT в .env и ссылаться абстрактно).
- Public URL плейсхолдер: стоит явно подсказать «может отличаться при каждом запуске cloudflared» (мини‑примечание?).
- Deep link пример: корректно URL‑кодирован; можно сократить для читаемости (вынести в отдельный файл examples.md, опционально).
- Нумерация: введение 1.1 нормально; не конфликтует с остальной структурой.
- Аудит (16.*): покрывает большую часть замечаний из 14.x — ок, пересечений критичных нет.
- Нет отдельной пометки о связи hash PDF ↔ JSON (указано как действие в 14.6, но ещё не отражено в структуре результата) — можно отметить как «Pending».

### 17.3 Рекомендуемые точечные правки (микро)
1. В раздел 10 добавить фразу: «(По умолчанию PORT=3000; если переопределён — синхронизируйте с секциями 1.1 и 10.1)».
2. В 14.6 (P0) после пункта про hash — указать имя предлагаемого поля (например: meta.pdfSignature).
3. В 16.8 (GCS слой) — упомянуть лимит размера одного ответа viewer (e.g. >5MB warn).
4. Добавить в roadmap (раздел 15) «Sprint 1: pdfSignature guard» (если примете пункт 2).

### 17.4 Краткий статус по зрелости после правок
- Documentation coverage: + (улучшено за счёт 1.1, 10.1, 16).
- Actionability: + (появились конкретные интерфейсы и quick wins).
- Still pending: schemas (не отражены как реализованные), metrics endpoint (не создан).

### 17.5 Следующее минимальное действие
Создать файл schema/zoneTemplate.schema.json + util validateTemplates (соответствует P0) и зафиксировать пример расширенного mapping.json (раздел 14.8) в docs/examples.

(Раздел носит обзорный характер; при обновлениях можно консолидировать в CHANGELOG.)

---
