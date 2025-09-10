// Server-only Qdrant client helpers (read-only)
// Do not import this module from client components.

type ScrollParams = { limit?: number; offset?: any };

function getBase() {
  const url = process.env.QDRANT_URL?.replace(/\/$/, '');
  const collection = process.env.QDRANT_COLLECTION;
  const key = process.env.QDRANT_API_KEY_RO;
  if (!url || !collection || !key) {
    throw new Error('Qdrant env not configured');
  }
  return { url, collection, key };
}

async function qFetch(path: string, init: RequestInit = {}) {
  const { url, key } = getBase();
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'api-key': key,
  };
  if (init.headers) Object.assign(headers, init.headers as Record<string, string>);
  const res = await fetch(`${url}${path}`, { ...init, headers, cache: 'no-store' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Qdrant ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json();
}

export async function count(): Promise<number> {
  const { collection } = getBase();
  const j = await qFetch(`/collections/${encodeURIComponent(collection)}`);
  // Try typical shapes
  const c = j?.result?.points_count ?? j?.result?.config?.params?.points_count ?? j?.points_count;
  return typeof c === 'number' ? c : 0;
}

export async function scroll({ limit = 10, offset }: ScrollParams) {
  const { collection } = getBase();
  const body: any = { limit, with_payload: true, with_vectors: false };
  if (offset !== undefined) body.offset = offset;
  const j = await qFetch(`/collections/${encodeURIComponent(collection)}/points/scroll`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const items = (j?.result?.points || j?.result || j?.points || []).map((p: any) => ({ id: p?.id, payload: p?.payload }));
  const next = j?.result?.next_page_offset ?? j?.result?.next_offset ?? j?.next_offset ?? null;
  return { items, next_offset: next } as { items: { id: string | number; payload: any }[]; next_offset?: any };
}

export async function point(id: string | number) {
  const { collection } = getBase();
  // Prefer POST get endpoint for broader compatibility
  try {
    const j = await qFetch(`/collections/${encodeURIComponent(collection)}/points/get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [id], with_payload: true, with_vectors: false }),
    });
    const p = (j?.result || j?.points || []).find((x: any) => String(x?.id) === String(id));
    if (p) return { id: p.id, payload: p.payload };
  } catch (e) {
    // fallback to GET by id
  }
  try {
    const j = await qFetch(`/collections/${encodeURIComponent(collection)}/points/${encodeURIComponent(String(id))}`);
    const p = j?.result ?? j;
    if (p) return { id: p.id, payload: p.payload };
  } catch (e) {
    throw e;
  }
  throw new Error('Point not found');
}

export default { count, scroll, point };

