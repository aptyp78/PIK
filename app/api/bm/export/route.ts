import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';
import fs from 'fs/promises';
import path from 'path';
import { createGzip } from 'zlib';

export async function GET(_req: NextRequest) {
  // Export single doc (first) with JSON and original poster copy
  const doc = await prisma.sourceDoc.findFirst({ orderBy: { id: 'asc' } });
  if (!doc) return NextResponse.json({ error: 'No document initialized. Open /bm to initialize.' }, { status: 404 });
  const zones = await prisma.zone.findMany({ where: { docId: doc.id } });
  const evidences = await prisma.evidence.findMany({ where: { zoneId: { in: zones.map(z => z.id) } } });
  const posterPath = doc.path;
  // Build zip manually with gzip members is complex; instead, serve a tar.gz-like buffer replacement
  // Simpler: return JSON with base64 poster; acceptable for prototype
  try {
    const posterBuf = await fs.readFile(posterPath).catch(() => Buffer.from(''));
    const payload = {
      doc: { id: doc.id, title: doc.title, type: doc.type, canvasProfileId: doc.canvasProfileId, canvasTransform: doc.canvasTransform },
      zones,
      evidences,
      posterBase64: posterBuf.length ? posterBuf.toString('base64') : null,
    };
    const json = JSON.stringify(payload, null, 2);
    return new NextResponse(json, { status: 200, headers: { 'Content-Type': 'application/json', 'Content-Disposition': 'attachment; filename="bm-export.json"' } });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'export failed' }, { status: 500 });
  }
}

