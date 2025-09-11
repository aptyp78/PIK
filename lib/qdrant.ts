// Server-only Qdrant client helpers (read-only)
// Do not import this module from client components.

type ScrollParams = { limit?: number; offset?: any; filter?: any };

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

export async function scroll({ limit = 10, offset, filter }: ScrollParams) {
  const { collection } = getBase();
  const body: any = { limit, with_payload: true, with_vectors: false };
  if (offset !== undefined) body.offset = offset;
  if (filter) body.filter = filter;
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

export async function fetchBlocks({ docId, limit = 100, offset, page, fileName, fileId, fileNames }: { docId?: string|number; limit?: number; offset?: any; page?: number; fileName?: string; fileId?: string; fileNames?: string[] }) {
  let filter: any | undefined;
  const must: any[] = [];
  if (docId != null) must.push({ key: 'docId', match: { value: typeof docId === 'number' ? docId : String(docId) } });
  if (page != null) must.push({ key: 'page', match: { value: page } });
  const should: any[] = [];
  if (fileName) should.push({ key: 'metadata-filename', match: { value: fileName } });
  if (Array.isArray(fileNames)) {
    for (const fn of fileNames) if (fn) should.push({ key: 'metadata-filename', match: { value: fn } });
  }
  if (fileId) should.push({ key: 'metadata-data_source-record_locator-file_id', match: { value: fileId } });
  if (must.length) filter = { must };
  if (should.length) filter = filter ? { ...filter, should } : { should };
  let sc;
  try { sc = await scroll({ limit, offset, filter }); }
  catch (e: any) {
    const msg = e?.message || '';
    if (/Index required but not found/i.test(msg)) {
      const scAll = await scroll({ limit, offset });
      const itemsAll = scAll.items || [];
      const fn = (p: any) => {
        const pl = p?.payload || {};
        const nm = pl['metadata-filename'];
        const fid = pl['metadata-data_source-record_locator-file_id'];
        const okName = !fileName && !(fileNames && fileNames.length) ? true : (nm && ((fileName && nm===fileName) || (fileNames||[]).includes(nm)));
        const okFid = !fileId ? true : (fid === fileId);
        return okName && okFid;
      };
      sc = { items: itemsAll.filter(fn), next_offset: scAll.next_offset } as any;
    } else { throw e; }
  }

  function bboxFromSerialized(el: any): { x:number;y:number;w:number;h:number } | null {
    try {
      const coords = el?.coordinates || el?.Coordinates || el?.coord;
      if (coords?.points && Array.isArray(coords.points) && coords.points.length) {
        const xs = coords.points.map((p: any)=>Number(p?.[0])||0);
        const ys = coords.points.map((p: any)=>Number(p?.[1])||0);
        const x0 = Math.min(...xs), y0 = Math.min(...ys), x1 = Math.max(...xs), y1 = Math.max(...ys);
        return { x: x0, y: y0, w: Math.max(0, x1-x0), h: Math.max(0, y1-y0) };
      }
      const b = el?.bounds || el?.Bounds;
      if (Array.isArray(b) && b.length>=4) {
        const x0=Number(b[0])||0, y0=Number(b[1])||0, x1=Number(b[2])||0, y1=Number(b[3])||0;
        return { x: x0, y: y0, w: Math.max(0, x1-x0), h: Math.max(0, y1-y0) };
      }
    } catch {}
    return null;
  }

  let items = sc.items.map((it) => {
    const pl = it.payload || {};
    let bbox = pl.bbox || pl.BBox || pl.bounds;
    let pageVal = pl.page ?? pl.Page ?? pl.metadata?.page_number ?? 0;
    let text = pl.text ?? pl.Text ?? pl.content ?? '';
    try {
      if (!bbox || pageVal == null || text === '') {
        const s = pl.element_serialized || pl.element || pl.raw || null;
        if (s && typeof s === 'string') {
          const el = JSON.parse(s);
          if (!bbox) bbox = bboxFromSerialized(el) || bbox;
          if (pageVal == null) pageVal = el?.metadata?.page_number ?? pageVal;
          if (!text) text = el?.text || '';
        }
      }
    } catch {}
    if (!bbox) bbox = { x:0,y:0,w:0,h:0 };
    return { id: it.id, page: pageVal || 0, bbox, text };
  });
  // If strict mode returned empty under filter, try a small unfiltered scan and in-memory filter
  if ((!items || items.length === 0) && (fileName || (fileNames && fileNames.length) || fileId)) {
    try {
      const scAll = await scroll({ limit, offset });
      const raw = scAll.items || [];
      const fnMatch = (pl: any) => {
        const nm = pl['metadata-filename'];
        const fid = pl['metadata-data_source-record_locator-file_id'];
        const okName = fileName ? nm === fileName : (fileNames && fileNames.length ? (nm && fileNames.includes(nm)) : true);
        const okFid = fileId ? fid === fileId : true;
        return okName && okFid;
      };
      items = raw.filter((it:any)=>fnMatch(it.payload||{})).map((it:any)=>{
        const pl = it.payload || {};
        let bbox = pl.bbox || pl.BBox || pl.bounds;
        let pageVal = pl.page ?? pl.Page ?? pl.metadata?.page_number ?? 0;
        let text = pl.text ?? pl.Text ?? pl.content ?? '';
        return { id: it.id, page: pageVal || 0, bbox: bbox || {x:0,y:0,w:0,h:0}, text };
      });
      return { items, nextOffset: scAll.next_offset };
    } catch {}
  }
  return { items, nextOffset: sc.next_offset };
}

export default { count, scroll, point };
