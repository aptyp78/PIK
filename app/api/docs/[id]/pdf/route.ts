import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';
import fs from 'fs/promises';

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const id = parseInt(params.id, 10);
  if (isNaN(id)) return NextResponse.json({ error: 'Invalid id' }, { status: 400 });
  const doc = await prisma.sourceDoc.findUnique({ where: { id }, select: { path: true } });
  if (!doc?.path) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  try {
    const buf = await fs.readFile(doc.path);
    return new NextResponse(buf, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Cache-Control': 'no-store',
      },
    });
  } catch (e: any) {
    return NextResponse.json({ error: 'File not available' }, { status: 404 });
  }
}

