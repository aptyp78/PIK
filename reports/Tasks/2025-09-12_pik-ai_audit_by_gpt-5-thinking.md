# PIK‑AI — Аудит проекта (12.09.2025)

## 1) Резюме и охват
- Цель: извлечение структуры PDF (Adobe), хранение результатов в GCS, предпросмотр (PDF+bbox), детерминированный маппинг элементов в зоны канваса.
- Стадия: рабочий прототип. Потоки Adobe/GCS и Viewer завершены; детерминированный маппинг реализован (шаблоны в JSON, центроид‑на‑зону).
- Вне фокуса: продовая авторизация, SLA, устойчивость к пиковым нагрузкам, Named Tunnels Cloudflare.

## 2) Архитектура (высокоуровнево)
- Front/Backend: Next.js 14 (app router), TypeScript.
- Обработка PDF: Adobe PDF Services (async jobs).
- Хранилище результатов: Google Cloud Storage (GCS) — `GCS_RESULTS_BUCKET/Adobe_Destination`.
- Источник PDF: `GCS_SOURCE_BUCKET[/GCS_SOURCE_PREFIX]`.
- Просмотр: pdf.js фон + overlay bbox; визуализация маппинга зон (пунктирными окнами) и распорка по цветам.
- БД (локальная): Prisma/SQLite для сценариев Unstructured (вторично).

## 3) Основные потоки
- Adobe Batch из GCS: `scripts/adobeBatchFromGcs.ts` → JSON в `Adobe_Destination`.
- Viewer: `/pipeline/adobe/viewer` → `GET /api/pipeline/gcs/pdf`, `GET /api/pipeline/gcs/adobe/get`.
- Маппинг зон: `POST /api/mapping/map { name, template, save? }` → zones, counts, items (с zoneId).
- Frames Grid: `/pipeline/frames` — тайлы с подсветкой зон и счётчиками.

## 4) Хранилища и форматы
- Adobe JSON: сырой structuredData.json (элементы: text, type, bounds/coordinates, metadata.page_number).
- Mapping JSON (опц., при save=true): `GCS_RESULTS_BUCKET/Mapping/<template>/<name>.json` — { template, mapped: { assigned[], counts }, dims }.
- Шаблоны канваса: `lib/mapping/templates/<id>.json` — { id, title, version, zones: [{ id, title, box: [x1,y1,x2,y2] }] } (0..1, PDF‑координаты, начало снизу‑слева).

## 5) Маршруты и API (ключевые)
- GCS listing: `GET /api/pipeline/gcs/adobe/status`.
- GCS JSON get: `GET /api/pipeline/gcs/adobe/get?name=…`.
- GCS PDF stream: `GET /api/pipeline/gcs/pdf?name=…`.
- Templates list: `GET /api/mapping/templates`.
- Mapping: `POST /api/mapping/map`.
- Qdrant (опц.): `GET /api/qdrant/*`, `POST /api/qdrant/indexes`, `POST /api/pipeline/qdrant/annotate`.

## 6) Безопасность / секреты
- Секреты в `.env.local`; ключ GCS — `GCS_SA_KEY_FILE` (JSON). Не коммитим: `.gitignore` включает `secrets/`, `*.pem`.
- Внешний доступ: Quick Tunnel Cloudflare (временный), по HTTP/2. Для прод — Named Tunnel с аккаунтом и политиками.
- Риск: публичный URL без auth; в проде требуется защитный слой (Basic/Auth proxy/Cloudflare Access).

## 7) Конфигурация окружения
- Adobe: `ADOBE_CLIENT_ID`, `ADOBE_CLIENT_SECRET`, `ADOBE_REGION?`, `ADOBE_ELEMENTS` (по умолчанию text,tables).
- GCS: `GCS_SOURCE_BUCKET`, `GCS_RESULTS_BUCKET`, `GCS_ADOBE_DEST_PREFIX=Adobe_Destination`, `GCS_MAPPING_PREFIX=Mapping`, `GCS_SA_KEY_FILE`.
- Qdrant: `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_API_KEY_RO/RW`.
- Прочее: `INGEST_ENGINE_DEFAULT`.

## 8) Качество / риски / рекомендации
- Координаты: Adobe даёт bounds/coordinates → приводим к bbox; редкие PDF могут требовать нормализации/масштабных поправок.
- Производительность: batch синхронный, без параллелизма/квот — добавить concurrency с лимитами, ретраи, метрики.
- Наблюдаемость: добавить structured logs/trace-id, метрики по API (p95) и объёму JSON.
- Доступ: оформить Named Tunnel или Edge/Ingress; прикрутить Basic/Auth токен к API/Viewer.
- UI: добавить легенду типов, фильтры (heading/table), подсказки при hover, миниатюры (thumb) в гриде.
- Безопасность: валидировать `name` в GCS‑API (проверка префикса уже есть; закрепить allow‑list).

## 9) Чек‑лист аудита
- [x] Adobe→GCS поток активен (батч/одиночный).
- [x] Viewer рендерит PDF фон + overlay.
- [x] Mapping работает по шаблону (PIK_PBM_v5).
- [x] Секреты не в git, .gitignore обновлён.
- [x] Публичный URL доступен (через Cloudflare HTTP/2), нестабилен — это временно.
- [ ] Добавить auth на внешние маршруты.
- [ ] Метрики и алёрты (ошибки Adobe/GCS, размер артефактов, медленные ответы).

## 10) Runbook (кратко)
- Запуск dev: `npm run dev` (порт 3002 в текущей сессии).
- Туннель: `npm run tunnel:cf` → URL `*.trycloudflare.com` (жив, пока процесс активен).
- Батч Adobe: `npx tsx scripts/adobeBatchFromGcs.ts --limit=0`.
- Вьюер: `/pipeline/adobe/viewer` (param `name=Adobe_Destination/...pdf.json`).
- Frames Grid: `/pipeline/frames`.

---

*** Конец отчёта ***

