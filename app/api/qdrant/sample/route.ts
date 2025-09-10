import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { count as qCount, scroll as qScroll } from '@/lib/qdrant';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    let limit = parseInt(url.searchParams.get('limit') || '10', 10);
    if (isNaN(limit) || limit <= 0) limit = 10;
    if (limit > 100) limit = 100;
    const offsetParam = url.searchParams.get('offset');
    const offset = offsetParam ? (isNaN(Number(offsetParam)) ? offsetParam : Number(offsetParam)) : undefined;

    const [cnt, sc] = await Promise.all([qCount(), qScroll({ limit, offset })]);
    console.log(JSON.stringify({ step: 'qdrant:sample', status: 'ok', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: true, collection: process.env.QDRANT_COLLECTION || null, count: cnt, items: sc.items, next_offset: sc.next_offset, requestId: rid });
  } catch (e: any) {
    console.log(JSON.stringify({ step: 'qdrant:sample', status: 'error', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: false, error: e?.message || 'error', requestId: rid }, { status: 500 });
  }
}

