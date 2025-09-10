import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

export async function GET(_req: NextRequest) {
  const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
  const t0 = Date.now();
  try {
    const stepStart = Date.now();
    const [docs, blocks] = await Promise.all([
      prisma.sourceDoc.count(),
      prisma.block.count(),
    ]);
    try {
      // Structured marker log for prod collection
      console.log(JSON.stringify({ level: 'info', step: 'db', durationMs: Date.now() - stepStart, requestId: rid }));
    } catch {}
    const body = { ok: true, docs, blocks, time: new Date().toISOString(), requestId: rid, durationMs: Date.now() - t0 };
    const res = NextResponse.json(body);
    res.headers.set('x-request-id', rid);
    return res;
  } catch (e: any) {
    const body = { ok: false, step: 'db', error: e?.message || 'error', requestId: rid };
    try {
      console.error('[health:error]', rid, body.error);
      // Structured error marker
      console.log(JSON.stringify({ level: 'error', step: 'db', durationMs: Date.now() - t0, requestId: rid }));
    } catch {}
    const res = NextResponse.json(body, { status: 500 });
    res.headers.set('x-request-id', rid);
    return res;
  }
}
