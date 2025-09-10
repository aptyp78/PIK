import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { autoAssign } from '@/lib/mapping/pik';

export const runtime = 'nodejs';

/*
 * API: POST /api/frames/autoassign?docId=...
 * Body: optional { llm?: boolean }
 * Returns: { ok, docId, frames: FrameAssignment[] }
 */
export async function POST(req: NextRequest) {
  const url = new URL(req.url);
  const docParam = url.searchParams.get('docId');
  const docId = Number(docParam);
  if (!docParam || Number.isNaN(docId)) return NextResponse.json({ error: 'Missing or invalid docId' }, { status: 400 });
  try {
    const blocks = await prisma.block.findMany({ where: { sourceDocId: docId }, select: { id: true, page: true, bbox: true, role: true, text: true } });
    if (blocks.length === 0) return NextResponse.json({ error: 'No blocks for document' }, { status: 404 });
    const frames = autoAssign(blocks as any);
    return NextResponse.json({ ok: true, docId, frames });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'Server error' }, { status: 500 });
  }
}

