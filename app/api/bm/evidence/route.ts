import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { zoneId, rect } = body || {};
  if (!zoneId || !rect) return NextResponse.json({ error: 'zoneId and rect required' }, { status: 400 });
  const { page = 1, x, y, w, h } = rect;
  const ev = await prisma.evidence.create({ data: { zoneId, page, x, y, w, h } });
  return NextResponse.json({ ok: true, evidence: ev });
}

export async function GET(req: NextRequest) {
  const zoneId = parseInt(String(req.nextUrl.searchParams.get('zoneId') || ''), 10);
  if (isNaN(zoneId)) return NextResponse.json({ error: 'zoneId required' }, { status: 400 });
  const list = await prisma.evidence.findMany({ where: { zoneId }, orderBy: { id: 'asc' } });
  return NextResponse.json({ evidences: list });
}

