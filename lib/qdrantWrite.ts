// Qdrant write client (server-only). Uses RW key.

type QPointId = string | number;

function getBase() {
  const url = process.env.QDRANT_URL?.replace(/\/$/, '');
  const collection = process.env.QDRANT_COLLECTION;
  const key = process.env.QDRANT_API_KEY_RW || process.env.QDRANT_API_KEY_RO;
  if (!url || !collection || !key) throw new Error('Qdrant write env not configured');
  return { url, collection, key };
}

async function qFetch(path: string, init: RequestInit = {}) {
  const { url, key } = getBase();
  const headers: Record<string, string> = { 'Accept': 'application/json', 'api-key': key };
  if (init.headers) Object.assign(headers, init.headers as Record<string, string>);
  const res = await fetch(`${url}${path}`, { ...init, headers, cache: 'no-store' });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Qdrant ${res.status}: ${t.slice(0, 300)}`);
  }
  const ct = res.headers.get('content-type') || '';
  return /json/i.test(ct) ? res.json() : res.text();
}

export async function setPayload(points: QPointId[], patch: Record<string, unknown>, overwrite = false) {
  const { collection } = getBase();
  const body = { payload: patch, points, overwrite } as any;
  return qFetch(`/collections/${encodeURIComponent(collection)}/points/payload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function upsertPoints(points: { id?: QPointId; vector: number[]; payload: Record<string, unknown> }[]) {
  const { collection } = getBase();
  const body = { points } as any;
  return qFetch(`/collections/${encodeURIComponent(collection)}/points?wait=true`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export default { setPayload, upsertPoints };

