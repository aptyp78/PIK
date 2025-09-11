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
    const limit = Math.min(1000, Math.max(1, parseInt(url.searchParams.get('limit') || '200', 10)));
    const offsetParam = url.searchParams.get('offset') || undefined;
    const offset = offsetParam ? (isNaN(Number(offsetParam)) ? offsetParam : Number(offsetParam)) : undefined;
    const must: any[] = [];
    if (filename) must.push({ key: 'metadata-filename', match: { value: filename } });
    if (fileId) must.push({ key: 'metadata-data_source-record_locator-file_id', match: { value: fileId } });
    const filter = must.length ? { must } : undefined;
    const q = await qScroll({ limit, offset, filter });
    const items = (q.items || []).map((it) => {
      const pl: any = it.payload || {};
      const text = pl.text || '';
      const page = pl.page ?? pl['metadata-page_number'] ?? null;
      const el = pl.element_serialized || null;
      return { id: it.id, page, text, element_serialized: el };
    });
    return NextResponse.json({ ok: true, items, next_offset: q.next_offset, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed', requestId: rid }, { status: 500 });
  }
}

