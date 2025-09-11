import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { scroll as qScroll } from '@/lib/qdrant';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const limit = Math.min(2000, Math.max(100, parseInt(url.searchParams.get('limit') || '1000', 10)));
    const q = await qScroll({ limit, offset: undefined });
    const docs = new Map<string, { filename?: string; fileId?: string; count: number }>();
    for (const it of q.items || []) {
      const pl: any = it.payload || {};
      const filename = pl['metadata-filename'];
      const fileId = pl['metadata-data_source-record_locator-file_id'];
      const key = fileId || filename || String(it.id);
      const rec = docs.get(key) || { filename, fileId, count: 0 };
      rec.count += 1;
      docs.set(key, rec);
    }
    const items = Array.from(docs.entries()).map(([key, v]) => ({ key, filename: v.filename || null, fileId: v.fileId || null, count: v.count }));
    return NextResponse.json({ ok: true, items, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed', requestId: rid }, { status: 500 });
  }
}

