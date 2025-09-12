# Технический отчёт по парсеру PIK‑AI (Uploads‑Only)

Автор: Codex Assistant
Дата: 2025‑09‑10

## 1. Резюме

Система переведена в режим Uploads‑Only, без предзагруженных данных. Поддерживаются два реальных двигателя извлечения: Adobe PDF Services (job‑based) и Unstructured Hosted API (Partition). Результаты Adobe сохраняются только в GCS (`GCS_RESULTS_BUCKET`/`GCS_ADOBE_DEST_PREFIX`).

Ключевые достижения:
- Два движка: Unstructured (по умолчанию) и Adobe; переключение на `/upload`.
- Сохранение артефактов Adobe в GCS и предпросмотр на `/pipeline/adobe`.
- Интеграция логов событий в формате JSONL, health‑роуты для обоих движков.

## 2. Архитектура и поток

Высокоуровневый поток Uploads‑Only:

1) Пользователь загружает файл на `/upload` (PDF/PNG, ≤ 30 МБ)
2) UI показывает превью 1‑й страницы
3) Бэкенд запускает выбранный движок извлечения → нормализация блоков → сохранение raw/normalized и запись в БД (для Unstructured)
4) Для Adobe — сохраняем raw JSON в GCS и показываем на `/pipeline/adobe`; для Unstructured — переход на `/docs/:id`

## 3. Движки извлечения

### 3.1 Unstructured Hosted API

- Клиент: `lib/ingest/unstructured.ts`
- Endpoint: `${UNSTRUCTURED_API_URL}/general/v0/general`
- Метод: `POST multipart/form-data`
- Заголовки: `unstructured-api-key: <UNSTRUCTURED_API_KEY>`, `Accept: application/json`
- Поля формы: `files=<blob>`, `coordinates=true`, `hi_res=true`, `languages=eng`
- Логирование: событие `unstructured:partition { status, durationMs }`
- Нормализация: элементы → Block { page, bbox, role (heading|paragraph|list|table), text?, tableJson? }

### 3.2 Adobe PDF Services (job‑based)

- Клиент: `lib/pdf/adobeExtract.ts`
- Токен: product‑token (`lib/adobe/pdfToken.ts`)
- Поток: POST `/assets` → PUT uploadUri → POST `/operation/extractpdf` → polling → GET `/assets/{id}` → download ZIP → `structuredData.json`
- PNG: предварительный `Create PDF` (POST `/operation/createpdf`), затем обычный Extract
- Нормализация: элементы/элементы таблиц → Block (page, bbox, role, text?, tableJson?)

## 4. Visual‑First

Функциональность визиуализации зон (BM) и связанное выравнивание удалены на данном этапе.

## 5. Данные и БД

### 5.1 Модель (Prisma)

`prisma/schema.prisma:SourceDoc`
- `engine: String?` — 'adobe' | 'unstructured'
- `pages: Int?` — количество страниц (при наличии)

### 5.2 Хранилище артефактов
- Исходники загрузок: `data/uploads/` (gitignored)
- Raw JSON (Unstructured): `data/raw/…json`
- Нормализованные блоки (Unstructured): `data/normalized/…json`
- Артефакты Adobe: GCS `GCS_RESULTS_BUCKET/GCS_ADOBE_DEST_PREFIX`

## 6. API

- `POST /api/ingest/upload` — основная точка загрузки
  - Параметры формы: `file`, `engine` ('unstructured' | 'adobe')
  - Возвращает: Unstructured → `{ ok, engine, docId, pages, blocks, requestId }`; Adobe → `{ ok, engine: 'adobe', gcs: { bucket, object, uri } }`
  - Логи: `upload:received`, `upload:extract:start|done`, (для Unstructured) `upload:db:inserted`, `upload:success|error`

- `GET /api/docs` — список документов
- `GET /api/docs/:id` — документ + блоки (включает `engine`)
- (Удалено) `PATCH /api/docs/:id/canvas`
- `GET /api/pipeline/gcs/adobe/status` — листинг GCS артефактов Adobe
- `GET /api/pipeline/gcs/adobe/get?name=…` — получить содержимое артефакта
- `GET /api/docs/:id/pdf` — исходный PDF
- `GET /api/ingest/:id/report` — базовые метрики (см. §8)
- Health: `GET /api/health`, `GET /api/health/adobe`, `GET /api/health/unstructured`

## 7. UI

- `/upload`:
  - Переключатель движка (Unstructured по умолчанию)
  - Превью 1‑й страницы (pdfjs)
  - Для Unstructured — после завершения переход на `/docs/:id`; для Adobe — артефакт доступен на `/pipeline/adobe`

- `/docs/:id`:
  - `app/docs/[id]/OverlayPdf.tsx` — overlay блоков

- `/frames`:
  - Автоприсвоение (демо) работает от текущих блоков независимо от двигателя

*Раздел сравнения и BM‑визуализация исключены на текущем этапе.*

## 8. Отчёты и метрики

`GET /api/ingest/:id/report` возвращает:
- `engine`: использованный движок
- `totalBlocks`, `tablesCount`, `avgBlockLen`
- `emptyPages`, `emptyPagesShare`
- `byRole`

## 9. Логи и диагностика

- События: `logs/events/YYYY‑MM‑DD.jsonl`
  - Примеры: `upload:received`, `upload:extract:start`, `unstructured:partition {status,durationMs}`, `upload:db:inserted`, `upload:success`, `upload:error {error}`
- Просмотр:
  - `tail -f logs/events/$(date +%F).jsonl`
- Health‑роуты:
  - `/api/health` — БД/время
  - `/api/health/unstructured` — Partition с «ping.txt»
  - `/api/health/adobe` — product token, /assets, dry‑run extract

## 10. Внешний доступ

- Quick Tunnel (без аккаунта): Cloudflare
  - Команда: `npm run tunnel:cf` или `cloudflared tunnel --url http://localhost:3002`
  - Примечание: URL меняется при каждом запуске; держите процесс активным

## 11. Окружение

`.env.local` (минимум):
- `ADOBE_CLIENT_ID`, `ADOBE_CLIENT_SECRET`, `ADOBE_REGION?`
- `UNSTRUCTURED_API_URL`, `UNSTRUCTURED_API_KEY`
- `INGEST_ENGINE_DEFAULT=unstructured`
- `NEXT_PUBLIC_INGEST_ENGINE_DEFAULT=unstructured`

## 12. Известные вопросы и дорожная карта

1) Visual matching (pHash/анкеры)
- Сейчас используется быстрый fit‑to‑canonical; требуется улучшить matchScore/калибровку: двухкликовая привязка «pick two anchors» с пересчётом аффинного преобразования и сохранением через `PATCH /api/docs/:id/canvas`.

2) Раскладка текста по зонам и черновики
- Реализовать серверный маршрут `/api/docs/:id/drafts`: применять `canvasTransform` к bbox, раскладывать по полигонам (point‑in‑polygon), формировать черновики полей (top‑N блоков по площади/длине текста) и Evidence.

3) Стабилизация Unstructured/Adobe
- Добавить троттлинг/ретраи и коды ошибок в логах с `x-request-id`/`x-ms-request-id` там, где доступны.

4) Безопасность внешнего доступа
- Для `/upload` предусмотреть опциональный токен/Basic Auth при публикации туннеля.

5) UI/UX
- Включить «калибровку 2‑точки» и удобные ползунки; авто‑сохранение профиля документа.

## 13. Воспроизводимость / Быстрый старт

1) Установить зависимости, применить миграции:
```
npm install
npm run prisma:generate && npm run db:migrate && npm run db:seed
```
2) Заполнить `.env.local` (см. §11)

3) Запустить dev на 3002:
```
PORT=3002 npm run dev
```

4) Проверка health:
```
curl -s http://localhost:3002/api/health
curl -s http://localhost:3002/api/health/unstructured
```

5) Открыть `/upload`, выбрать Unstructured, загрузить PDF/PNG → дождаться редиректа на `/docs/:id`.

## 14. Приложение: основные файлы

- Клиент Unstructured: `lib/ingest/unstructured.ts`
- Клиент Adobe (Extract/Create PDF): `lib/pdf/adobeExtract.ts`
- Visual‑First:
  - Профиль: `lib/canvas/profiles/PIK_BusinessModel_v5.json`
  - Трансформы: `lib/canvas/transform.ts`
  - Выравнивание: `lib/canvas/visualAlign.ts`
- API upload: `app/api/ingest/upload/route.ts`
- Документы:
  - `app/api/docs/route.ts`
  - `app/api/docs/[id]/route.ts`
  - `app/api/docs/[id]/pdf/route.ts`
  - `app/api/docs/[id]/canvas/route.ts`
- Health:
  - `app/api/health/route.ts`
  - `app/api/health/unstructured/route.ts`
- UI:
  - `app/upload/page.tsx`
  - `app/docs/[id]/OverlayPdf.tsx`
  - `app/compare/page.tsx`
- Логи: `lib/log.ts`, `logs/events/*.jsonl`

---

Готов к расширению: калибровка по двум ориентирам, серверная раскладка черновиков, сохранение Evidence и авто‑заполнение фреймов.
