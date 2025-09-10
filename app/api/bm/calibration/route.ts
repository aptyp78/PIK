import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { docId, canvasTransform } = body || {};
  if (!docId || !canvasTransform) return NextResponse.json({ error: 'docId and canvasTransform required' }, { status: 400 });
  const updated = await prisma.sourceDoc.update({ where: { id: Number(docId) }, data: { canvasTransform: typeof canvasTransform === 'string' ? canvasTransform : JSON.stringify(canvasTransform) } });
  return NextResponse.json({ ok: true, id: updated.id });
}

