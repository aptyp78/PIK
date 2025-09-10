import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { count as qCount } from '@/lib/qdrant';

export async function GET(_req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const collection = process.env.QDRANT_COLLECTION || null;
    const points_count = await qCount();
    console.log(JSON.stringify({ step: 'qdrant:stats', status: 'ok', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: true, collection, points_count, requestId: rid });
  } catch (e: any) {
    console.log(JSON.stringify({ step: 'qdrant:stats', status: 'error', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: false, error: e?.message || 'error', requestId: rid }, { status: 500 });
  }
}

