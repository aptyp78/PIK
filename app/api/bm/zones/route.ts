import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

export async function GET(req: NextRequest) {
  const docId = parseInt(String(req.nextUrl.searchParams.get('docId') || ''), 10);
  if (isNaN(docId)) return NextResponse.json({ error: 'docId required' }, { status: 400 });
  const zones = await prisma.zone.findMany({ where: { docId }, orderBy: { id: 'asc' } });
  return NextResponse.json({ zones });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { id, docId, key, name, status, text, confidence, owner, tags, history } = body || {};
  if (id) {
    const z = await prisma.zone.update({ where: { id }, data: { status, text, confidence, owner, tags, history } });
    return NextResponse.json({ ok: true, zone: z });
  }
  if (!docId || !key || !name) return NextResponse.json({ error: 'missing fields' }, { status: 400 });
  const created = await prisma.zone.create({ data: { docId, key, name, status: status || 'Empty', text: text || '' } });
  return NextResponse.json({ ok: true, zone: created });
}

