import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { point as qPoint } from '@/lib/qdrant';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const id = req.nextUrl.searchParams.get('id');
    if (!id) return NextResponse.json({ ok: false, error: 'id required', requestId: rid }, { status: 400 });
    const p = await qPoint(id);
    console.log(JSON.stringify({ step: 'qdrant:point', status: 'ok', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: true, point: p, requestId: rid });
  } catch (e: any) {
    console.log(JSON.stringify({ step: 'qdrant:point', status: 'error', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: false, error: e?.message || 'error', requestId: rid }, { status: 500 });
  }
}

