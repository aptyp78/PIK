import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const id = parseInt(params.id, 10);
  if (isNaN(id)) return NextResponse.json({ error: 'Invalid id' }, { status: 400 });
  let body: any = {};
  try { body = await req.json(); } catch {}
  const canvasTransform = typeof body?.canvasTransform === 'string' ? body.canvasTransform : JSON.stringify(body?.canvasTransform || {});
  const data: any = { canvasTransform };
  if (body?.canvasProfileId) data.canvasProfileId = String(body.canvasProfileId);
  if (typeof body?.canvasMatchScore === 'number') data.canvasMatchScore = body.canvasMatchScore;
  const updated = await prisma.sourceDoc.update({ where: { id }, data });
  return NextResponse.json({ ok: true, id: updated.id });
}

