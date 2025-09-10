import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';
import fs from 'fs/promises';
import { BM_POSTER_PATHS, BM_ZONE_KEYS } from '@/lib/bm/constants';

async function findPosterPath(): Promise<{ path: string; type: string } | null> {
  for (const p of BM_POSTER_PATHS) {
    try { await fs.access(p); return { path: p, type: p.endsWith('.png') ? 'png' : 'pdf' }; } catch {}
  }
  return null;
}

export async function GET(_req: NextRequest) {
  const poster = await findPosterPath();
  if (!poster) return NextResponse.json({ ok: false, error: 'Place poster file at data/uploads/PIK-Platform-Business-Model.pdf (or .png) and refresh.' }, { status: 404 });
  // Ensure SourceDoc exists (single)
  let doc = await prisma.sourceDoc.findFirst({ where: { path: poster.path } });
  if (!doc) {
    doc = await prisma.sourceDoc.create({ data: { title: 'Platform Business Model', type: poster.type, path: poster.path, pages: 1, canvasProfileId: 'PIK_BusinessModel_v5', canvasTransform: JSON.stringify({ scaleX: 1, scaleY: 1, offsetX: 0, offsetY: 0, flipY: true }), canvasMatchScore: 0.7 } });
  }
  // Ensure zones exist
  for (const z of BM_ZONE_KEYS) {
    const exists = await prisma.zone.findFirst({ where: { docId: doc.id, key: z.key } });
    if (!exists) {
      await prisma.zone.create({ data: { docId: doc.id, key: z.key, name: z.name, status: 'Empty', text: '' } });
    }
  }
  const zones = await prisma.zone.findMany({ where: { docId: doc.id }, orderBy: { id: 'asc' } });
  return NextResponse.json({ ok: true, docId: doc.id, path: doc.path, type: doc.type, canvasProfileId: doc.canvasProfileId, canvasTransform: doc.canvasTransform, zones });
}

