import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { scroll as qScroll } from '@/lib/qdrant';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const filename = url.searchParams.get('filename') || undefined;
    const fileId = url.searchParams.get('fileId') || undefined;
    const limit = Math.min(2000, Math.max(1, parseInt(url.searchParams.get('limit') || '1000', 10)));
    const must: any[] = [];
    if (filename) must.push({ key: 'metadata-filename', match: { value: filename } });
    if (fileId) must.push({ key: 'metadata-data_source-record_locator-file_id', match: { value: fileId } });
    const filter = must.length ? { must } : undefined;
    const q = await qScroll({ limit, offset: undefined, filter });
    const tally: Record<string, { type: string; items: Record<string, number> }> = {};
    let blocks = 0;
    for (const it of q.items || []) {
      blocks++;
      const pl: any = it.payload || {};
      const ser = pl.element_serialized;
      if (!ser || typeof ser !== 'string') continue;
      try {
        const obj = JSON.parse(ser);
        const ents = obj?.metadata?.entities?.entities || [];
        for (const e of ents) {
          const t = String(e?.type || 'UNKNOWN');
          const val = String(e?.text || '').slice(0, 200);
          const bucket = (tally[t] ||= { type: t, items: {} });
          bucket.items[val] = (bucket.items[val] || 0) + 1;
        }
      } catch {}
    }
    const entities = Object.values(tally).map((g) => ({ type: g.type, total: Object.values(g.items).reduce((a,b)=>a+(b as number),0), top: Object.entries(g.items).sort((a,b)=>b[1]-a[1]).slice(0,20).map(([text,count])=>({ text, count })) }));
    return NextResponse.json({ ok: true, blocks, entities, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed', requestId: rid }, { status: 500 });
  }
}

