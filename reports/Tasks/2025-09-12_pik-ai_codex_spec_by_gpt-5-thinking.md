# PIK‑AI — Спецификация (Codex) по состоянию на 12.09.2025

## 1. Цель
Создать устойчивый конвейер: (а) парсинг PDF через Adobe → JSON в GCS; (б) предпросмотр (PDF + bbox); (в) детерминированный маппинг элементов на зоны канваса по шаблонам; (г) подготовка к пакетной обработке и отчётности.

## 2. Glossary
- Artifact: JSON из Adobe (`Adobe_Destination/...pdf.json`).
- Template: JSON с нормализованными зонами (0..1) — `lib/mapping/templates/<id>.json`.
- Mapping: результат присвоения zoneId каждому элементу (по центроиду); агрегаты counts.

## 3. Контракты API
- `GET /api/pipeline/gcs/adobe/status?limit=N`
  - Ответ: `{ ok, bucket, prefix, count, files:[{name,size,updated}] }`.
- `GET /api/pipeline/gcs/adobe/get?name=...`
  - Ответ: `{ ok, name, size, json? , raw? }`.
- `GET /api/pipeline/gcs/pdf?name=...`
  - Ответ: `application/pdf` (буфер).
- `GET /api/mapping/templates`
  - Ответ: `{ ok, templates:[{ id }] }`.
- `POST /api/mapping/map`
  - Вход: `{ name:string, template:string, save?:boolean }`
  - Ответ: `{ ok, template, zones, counts, dims, items:[{ page,x0,y0,x1,y1,type?,text?,zoneId? }], stored? }`.

## 4. Форматы
### 4.1 Template (zones)
```
{
  "id": "PIK_PBM_v5",
  "title": "Platform Business Model v5",
  "version": "5.0",
  "zones": [
    { "id": "left-rail", "title": "Left Rail", "box": [0.04, 0.08, 0.22, 0.92] },
    { "id": "main-area", "title": "Main Area", "box": [0.24, 0.08, 0.96, 0.92] }
  ]
}
```
- box: [x1,y1,x2,y2], 0..1; начало координат — низ‑слева, в духе PDF.

### 4.2 Mapping JSON (при save=true)
```
{
  "template": { ... },
  "mapped": {
    "assigned": [ { "page":0, "x0":..., "y0":..., "x1":..., "y1":..., "zoneId":"main-area" } ],
    "counts": { "main-area": 128, "left-rail": 42 }
  },
  "dims": { "0": { "w": 1024, "h": 1450 } }
}
```

## 5. Алгоритм маппинга (детерминированный)
1) Построить bbox элемента из `coordinates.points` или `bounds`.
2) Центроид: `cx=(x0+x1)/2`, `cy=(y0+y1)/2`.
3) Страничные габариты: `w=max(x1)`, `h=max(y1)` по странице.
4) Нормализация: `nx=cx/w`, `ny=cy/h`.
5) Перебор зон (в порядке определения): если `nx∈[x1,x2] && ny∈[y1,y2]` → `zoneId=zone.id`.
6) Вернуть `assigned[]` и `counts{zoneId}`.

## 6. UI
- Viewer (`/pipeline/adobe/viewer`): фон‑PDF (pdf.js), overlay bbox; выбор шаблона; отрисовка зон (пунктир) и элементов цветом зоны. Фильтры: “Только текст”, “Без огромных”.
- Frames Grid (`/pipeline/frames`): сетка постеров (до 6) — рендер карточек‑тайлов по данным маппинга; кликом — переход в подробный Viewer.

## 7. Батч и эксплуатация
- Парсинг PDF→JSON: `npx tsx scripts/adobeBatchFromGcs.ts --limit=0`.
- Маппинг (пакетно) — TODO: добавить скрипт `scripts/mapAll.ts` (пройтись по Adobe_Destination; опц. `save:true`).

## 8. Настройки
- Adobe: `ADOBE_ELEMENTS=text,tables` по умолчанию; можно ограничить до text для лёгкости.
- GCS: префиксы `Adobe_Destination` / `Mapping` конфигурируемые; сервис‑аккаунт в `GCS_SA_KEY_FILE`.

## 9. Безопасность / доступ
- Публичный доступ только через временный Cloudflare Quick Tunnel (для демо); в проде — Named Tunnel + Access.
- Secrets вне git; в CI — использовать секреты окружения/менеджер секретов.

## 10. Дальнейшее
- Редактор зон в UI (точное задание границ шаблона на PDF) и версияция.
- Типизация элементов (heading/paragraph/table) + легенда/фильтры.
- Пакетный маппинг + выгрузка отчётов (CSV/JSON) по зонам (топ фраз/плотность/таблицы).
- Auth слой (Basic/Auth token/Access) для публичного URL.

*** Конец спецификации ***

