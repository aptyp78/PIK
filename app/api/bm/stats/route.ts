import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';
import { fetchBlocks } from '@/lib/qdrant';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const docIdParam = url.searchParams.get('docId');
    const doc = docIdParam
      ? await prisma.sourceDoc.findUnique({ where: { id: Number(docIdParam) }, select: { id: true } })
      : await prisma.sourceDoc.findFirst({ orderBy: { id: 'asc' }, select: { id: true } });
    const docId = doc?.id;
    if (!docId) return NextResponse.json({ ok: false, error: 'No document' }, { status: 404 });
    // pull first 1000 blocks to compute pages (prototype)
    const q = await fetchBlocks({ docId, limit: 1000 });
    const items = q.items || [];
    const pages = items.length ? Math.max(...items.map(b => Number(b.page||1))) : 0;
    console.log(JSON.stringify({ step: 'bm:stats', status: 'ok', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: true, docId, pages, totalBlocks: items.length, requestId: rid });
  } catch (e: any) {
    console.log(JSON.stringify({ step: 'bm:stats', status: 'error', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: false, error: e?.message || 'error', requestId: rid }, { status: 500 });
  }
}

