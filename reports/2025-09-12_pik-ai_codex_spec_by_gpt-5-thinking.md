# PIK‑AI — ТЗ на доработку (Codex‑формат) — 2025-09-12 13:55 CEST
Автор: GPT-5 Thinking

## 1) Цель
Восстановить работоспособность разделов Adobe/Viewer, ввести минимальные гарантийные проверки качества данных и метрики, обеспечить воспроизводимость маппинга зон и диагностируемость ошибок.

## 2) Объём (Scope)
### Входит
- Починка сборки/раздачи чанков страниц `/pipeline/adobe` и `/pipeline/adobe/viewer` (Next.js).
- Runtime‑валидация шаблонов зон и артефактов Adobe.
- Расширение ответа маппинга `stats` и `meta` + сохранение отчётов.
- PDF↔JSON hash‑guard в API и Viewer.
- Минимальные ретраи/бекофф для polling Adobe.
- Unit‑тесты `canvasMap` и CLI batch‑маппинга.
- Метрики (dev) `/api/metrics` и простые счётчики.

### Не входит
- Полный редактор зон (UI advanced), масштабирование на очереди и алертинг — как P2+.

## 3) Пользовательские истории
- **Viewer‑User:** как аналитик, хочу открыть `Viewer` и видеть bbox и покрытие по зонам, чтобы быстро оценить качество извлечения.
- **Pipeline‑Owner:** как владелец конвейера, хочу видеть `stats` и предупреждения об unmatched, чтобы знать, где править шаблоны.
- **DevOps:** как оператор, хочу стабильный билд без выпавших чанков в туннеле.

## 4) Требования и критерии приёмки (AC)
1. **ChunkLoadError отсутствует** при открытии `/pipeline/adobe` и `/pipeline/adobe/viewer` через публичный URL.
   - *AC:* Lighthouse/простой e2e‑тест подтверждает, что `_next/static/chunks/**` доступны.
2. **Schema‑validation:** при некорректных данных Viewer показывает предупреждение и список проблем.
   - *AC:* подмена поля `bbox` ломает валидацию → UI выдаёт явное предупреждение (без падения).
3. **Mapping stats:** `POST /api/mapping/map` возвращает `stats.total/matched/unmatched/coverage` и сохраняет `{doc}.stats.json` в `GCS_RESULTS_BUCKET/Mapping/<template>/<name>.stats.json` при `save:true`.
   - *AC:* для тестового документа создаётся файл со статистикой.
4. **PDF signature:** Viewer и API проверяют соответствие `pageCount/sha256(firstPage)`; при расхождении — предупреждение.
   - *AC:* подмена PDF ведёт к блокировке подсветки и жёлтому баннеру.
5. **Retry/backoff:** polling Adobe ограничен `MAX_POLLS` и экспоненциальной задержкой, ошибки логируются.
   - *AC:* при временной ошибке выполняются не более N попыток, затем возврат осмысленной ошибки.
6. **Тесты:** покрытие `canvasMap` базовыми кейсами (границы, пересечения).
   - *AC:* `npm test` зелёный; минимум 6 тестов пройдены.
7. **Метрики:** `/api/metrics` (dev) возвращает простые счётчики (mapping_items_total, mapping_unmatched_total).
   - *AC:* счётчики инкрементируются при вызове маппинга.

## 5) Проектирование
### 5.1 Frontend (Next.js)
- Отключить динамический импорт для проблемных страниц или пересобрать с принудительным inlining.
- Проверить public‑path для `_next/static` под Cloudflare Tunnel; при необходимости задать `assetPrefix` и `basePath`.
- Viewer: полоса предупреждений, фильтр «только текст», подсветка unmatched (серым). Lazy‑render страниц.

### 5.2 Backend/API
- Модуль `schema/zoneTemplate.schema.json` + валидатор `validateTemplates.ts`.
- Модуль `adobeTypes.ts` (минимальные типы блоков) + `getJson<T>(..., schema?)`.
- Расширить `/api/mapping/map`: добавить поля `stats` и `meta.templateHash/pdfSignature`.
- Добавить `sanitizeObjectName(name)` в GCS‑эндпоинты.
- `/api/metrics` (dev) — простой регистр счётчиков в памяти.

### 5.3 Конфигурация
- Централизованный `config/index.ts` с секцией `gcs`, `adobe`, `mapping`.
- Новые переменные: `ADOBE_MAX_POLLS`, `ADOBE_BASE_DELAY_MS`, `LOG_NORMALIZED`.
- Унифицировать `PORT` и упоминания в документации (3000 vs 3002).

## 6) Нефункциональные требования
- Надёжность: грациозные ошибки без падения UI; предупреждения в Viewer.
- Наблюдаемость: логи с `phase` и `doc`, базовые метрики.
- Безопасность: валидация и санитайз `name`/путей; запрет `../`.

## 7) План работ (итерации)
**Sprint 1 (P0):**
- Fix chunks / assetPrefix.
- JSON‑схемы + валидатор.
- Mapping stats + сохранение.
- PDF signature guard.
- Retry/backoff.

**Sprint 2 (P1):**
- Тесты `canvasMap` и CLI batch‑маппинга.
- `/api/metrics` и лог нормализации координат.
- Документация по PORT и Cloudflare Tunnel.

**Sprint 3 (P2):**
- UI улучшения (легенда, подсветка unmatched), версионирование mapping.

## 8) Структура артефактов
- `schema/zoneTemplate.schema.json`
- `scripts/validate-templates.ts`
- `lib/mapping/canvasMap.ts` (расширение с `stats`)
- `app/api/mapping/map/route.ts` (или аналог) — расширенный ответ
- `app/api/pipeline/gcs/*` — sanitize+валидатор
- `app/pipeline/adobe/page.tsx`, `app/pipeline/adobe/viewer/page.tsx` — фиксы чанков

## 9) Тест‑план
- Unit: `canvasMap`, валидатор шаблонов, sanitize имени объекта.
- E2E (smoke): открытие `/pipeline/adobe` и `/viewer` через public URL.
- Негативные: испорченный JSON, несовпадающий PDF.

## 10) Определение готовности (DoD)
- Все AC из раздела 4 выполнены и подтверждены тестами.
- Документация и примеры env обновлены.
- В репозитории есть пример `.stats.json` для тестового документа.

## 11) Каталоги задач (Issue‑шаблоны)
- feat(viewer): fix chunk delivery via assetPrefix
- feat(mapping): add stats and meta to response
- chore(schema): add zoneTemplate.schema + validator
- feat(api): pdfSignature guard
- chore(pipeline): retry/backoff for Adobe polling
- test(canvasMap): boundaries and overlap
- chore(dev): /api/metrics (dev only)
