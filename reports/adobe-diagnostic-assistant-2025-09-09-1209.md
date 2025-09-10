# Adobe PDF Services – Diagnostic Report (assistant)

## 1) Summary
- Goal: Run real ingestion (no mock) via Adobe PDF Services Extract API.
- Status: Failing at the first job step (create upload asset). IMS OAuth succeeds, PDF Services returns 500.
- Key evidence: POST https://pdf-services.adobe.io/assets → 500 Internal Server Error with x-request-id=C2XZf9C5k9G9N73aQBB4L7KGdogsHYFS.
- API key: Verified correct (ADOBE_API_KEY matches the PDF Services “Client ID (API Key)”).
- Scopes/IMS: IMS v3 token successfully obtained with `ADOBE_SCOPES="openid AdobeID DCAPI"`.

## 2) Environment
- App: Next.js 14.2.32, Node 24.6.0, Prisma 6.15.0.
- Runtime: prod (`next start`), MOCK disabled (`MOCK_ADOBE=0`, `MOCK_ADOBE_AUTO=0`).
- Hostname: pdf-services.adobe.io (also tried `pdf-services-ue1.adobe.io` and `pdf-services-ew1.adobe.io`).

## 3) Config (sanitized)
- `ADOBE_ORG_ID`: present (…@AdobeOrg)
- `ADOBE_CLIENT_ID`: present (hex, 32 chars)
- `ADOBE_CLIENT_SECRET`: present
- `ADOBE_SCOPES`: `openid AdobeID DCAPI`
- `ADOBE_IMS_HOST`: `https://ims-na1.adobelogin.com`
- `ADOBE_API_KEY`: present (same value as PDF Services Client ID)
- Ingest protection: `INGEST_TOKEN` set

## 4) Reproduction steps
1. Obtain IMS token (S2S OAuth v3): OK
   - POST `https://ims-na1.adobelogin.com/ims/token/v3`
   - Body (x-www-form-urlencoded): `grant_type=client_credentials&client_id=…&client_secret=…&scope=openid AdobeID DCAPI`
   - Result: 200 (expires_in ≈ 86400)
2. Create upload asset: FAILS
   - POST `https://pdf-services.adobe.io/assets`
   - Headers: `Authorization: Bearer <ims_token>`, `x-api-key: <ADOBE_API_KEY>`, `x-gw-ims-org-id: <ADOBE_ORG_ID>`, `Accept: application/json`
   - Result: 500 Internal Server Error
   - Response headers included `x-request-id: C2XZf9C5k9G9N73aQBB4L7KGdogsHYFS`
3. App flow
   - API `POST /api/ingest` → tries job flow → 500 on /assets → fallback legacy → still fail → return 502 `{"error":"Adobe extract failed"}`

## 5) Diagnostics endpoints
- `GET /api/diagnostics/pdfservices`
  - DNS: pdf-services.adobe.io resolves (IPv4 OK)
  - `GET /assets`: 403 (expected without token)
  - `POST /assets`: 403 (expected without token)
- Direct with token (Node fetch in-process): consistently 500 on `POST /assets`.

## 6) Observations
- IMS token is valid and consistently issued (v3 flow OK).
- `x-api-key` matches the PDF Services API “Client ID (API Key)”.
- Adding `x-gw-ims-org-id` does not change the 500.
- Regional hosts tried: default, `ue1`, `ew1` → same behavior.
- Earlier, when using a non-PDF-Services key, we observed 403 `Client ID is invalid` — теперь 500, что подтверждает правильность ключа и изменившийся тип ошибки.

## 7) Hypotheses (root-cause)
1) Provisioning/entitlement issue on Adobe side for this project or org (common причина 500 на /assets).
2) Временный сбой в PDF Services (в ответе рекомендуют ограниченное число повторов).
3) Несогласованность привязки IMS проекта и PDF Services API (проект один, но backend не видит разрешений для org/account).

## 8) Next actions
- Повторить запрос через 10–15 минут (ретраи уже включены в код; при 5xx повторяем 3 раза с backoff).
- Если 500 сохраняется — открыть тикет в Adobe Support, указав:
  - Время и зону: 2025‑09‑09 ~12:09Z
  - Endpoint: `POST https://pdf-services.adobe.io/assets`
  - Headers (ключевые): `Authorization: Bearer <ims_token>`, `x-api-key: <client_id>`, `x-gw-ims-org-id: <org_id>`
  - x-request-id: `C2XZf9C5k9G9N73aQBB4L7KGdogsHYFS`
  - Описание: IMS токен валиден, PDF Services API подключён к проекту, но /assets стабильно отвечает 500.
- Альтернатива для теста: создать новый проект в Adobe Console, подключить туда “PDF Services API” + “OAuth Server‑to‑Server”, взять новый Client ID/Secret и проверить /assets.

## 9) Useful cURL (redacted)
- IMS token (v3):
```
curl -i -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
 -H 'Content-Type: application/x-www-form-urlencoded' \
 --data 'grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>&scope=openid AdobeID DCAPI'
```
- Create asset with token (should be 201/202/400; сейчас 500):
```
curl -i -X POST 'https://pdf-services.adobe.io/assets' \
 -H 'Authorization: Bearer <IMS_TOKEN>' \
 -H 'x-api-key: <ADOBE_API_KEY>' \
 -H 'x-gw-ims-org-id: <ADOBE_ORG_ID>' \
 -H 'Accept: application/json'
```

## 10) App/server details
- App build: Next 14.2.32 (prod) OK
- Prisma: schema valid; DB operational; mock ingest ранее работал → UI `/docs/:id` в порядке.
- Инжест без моков падает на первом шаге из‑за 500 на /assets.

---
Generated automatically by assistant.
