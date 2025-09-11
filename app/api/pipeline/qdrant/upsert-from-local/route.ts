import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import path from 'path';
import fs from 'fs/promises';
import extractUnstructured from '@/lib/ingest/unstructured';
import { upsertPoints } from '@/lib/qdrantWrite';

const VEC_SIZE = 1536;

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const filename = url.searchParams.get('filename');
    if (!filename) return NextResponse.json({ ok: false, error: 'filename is required' }, { status: 400 });
    const local = path.join(process.cwd(), 'data', 'uploads', filename);
    try { await fs.access(local); } catch {
      return NextResponse.json({ ok: false, error: `Local file not found: ${filename}` }, { status: 404 });
    }

    const { blocks } = await extractUnstructured(local, path.basename(local));
    const vec = new Array(VEC_SIZE).fill(0);
    const points = blocks.map((b, i) => ({
      id: (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${i}`),
      vector: vec,
      payload: {
        text: b.text || '',
        page: b.page,
        bbox: { x: b.bbox[0], y: b.bbox[1], w: Math.max(0, b.bbox[2]-b.bbox[0]), h: Math.max(0, b.bbox[3]-b.bbox[1]) },
        role: b.role,
        'metadata-filename': filename,
      },
    }));
    // chunk
    const CH = 256;
    let inserted = 0;
    for (let i = 0; i < points.length; i += CH) {
      const slice = points.slice(i, i + CH);
      await upsertPoints(slice);
      inserted += slice.length;
    }
    return NextResponse.json({ ok: true, inserted, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'upsert failed', requestId: rid }, { status: 500 });
  }
}
