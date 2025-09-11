import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { fetchBlocks } from '@/lib/qdrant';
import prisma from '@/lib/prisma';
import profile from '@/lib/canvas/profiles/PIK_BusinessModel_v5.json';
import { applyTransformBBox, pointInPolygon } from '@/lib/canvas/transform';

function parseTransform(str?: string | null) {
  try { return str ? JSON.parse(str) : null; } catch { return null; }
}

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const docIdParam = url.searchParams.get('docId');
    const limit = Math.min(100, Math.max(1, parseInt(url.searchParams.get('limit') || '50', 10)));
    const offset = url.searchParams.get('offset') || undefined;
    const pageParam = url.searchParams.get('page');
    const overrideFilename = url.searchParams.get('filename') || undefined;
    const overrideFileId = url.searchParams.get('fileId') || undefined;

    const doc = docIdParam
      ? await prisma.sourceDoc.findUnique({ where: { id: Number(docIdParam) }, select: { canvasTransform: true, id: true, path: true } })
      : await prisma.sourceDoc.findFirst({ orderBy: { id: 'asc' }, select: { canvasTransform: true, id: true, path: true } });
    const docId = doc?.id;
    const page = pageParam ? Number(pageParam) : undefined;
    const tr = parseTransform(doc?.canvasTransform) || { scaleX:1, scaleY:1, offsetX:0, offsetY:0, flipY:true };
    const fileNameBase = (doc?.path || '').split('/').pop();
    const fileName = overrideFilename || fileNameBase;
    const fileNames = fileName ? [fileName, fileName.replace(/\.[^.]+$/, '.png')] : undefined;
    const fileId = overrideFileId || undefined;

    const bmSource = (process.env.BM_SOURCE || 'qdrant').toLowerCase();
    if (bmSource === 'artifact') {
      // Fallback: read last saved normalized blocks or raw partition artifact and map locally
      const fs = await import('fs/promises');
      const pBlocks = 'data/artifacts/last_blocks.json';
      const pRaw = 'data/artifacts/last_partition.json';
      let used = 'blocks';
      let items: any[] = [];
      try {
        const txt = await fs.readFile(pBlocks, 'utf8');
        const arr = JSON.parse(txt);
        if (Array.isArray(arr)) {
          items = arr.map((b: any, i: number) => {
            const [x0,y0,x1,y1] = Array.isArray(b?.bbox) ? b.bbox as [number,number,number,number] : [0,0,0,0];
            const tb = applyTransformBBox([x0,y0,x1,y1] as any, tr, undefined);
            const cx = (tb[0] + tb[2]) / 2; const cy = (tb[1] + tb[3]) / 2;
            let zone: string | null = null;
            for (const z of (profile as any).zones || []) {
              try { if (pointInPolygon([cx, cy], z.polygon)) { zone = z.id || null; break; } } catch {}
            }
            return { id: `b-${i}`, page: Number(b?.page ?? 0), bbox: { x: tb[0], y: tb[1], w: tb[2]-tb[0], h: tb[3]-tb[1] }, text: String(b?.text || ''), zone };
          });
        } else {
          items = [];
        }
      } catch {
        used = 'raw';
        let json: any = null;
        try { json = JSON.parse(await fs.readFile(pRaw, 'utf8')); } catch {}
        const elements: any[] = Array.isArray(json) ? json : (Array.isArray(json?.elements) ? json.elements : Array.isArray(json?.content) ? json.content : []);
        items = elements.map((el: any, i: number) => {
          const page1 = Number(el?.metadata?.page_number ?? el?.page_number ?? el?.page ?? 1) || 1;
          const page0 = Math.max(0, page1 - 1);
          // Try coordinates.points, else bounds array
          const pts: [number, number][] = el?.coordinates?.points || el?.coordinates || [];
          let x0=0,y0=0,x1=0,y1=0;
          if (Array.isArray(pts) && pts.length) {
            const xs = pts.map((p: any)=>Number(p?.[0])||0);
            const ys = pts.map((p: any)=>Number(p?.[1])||0);
            x0 = Math.min(...xs); y0 = Math.min(...ys); x1 = Math.max(...xs); y1 = Math.max(...ys);
          } else if (Array.isArray(el?.bounds) && el.bounds.length >= 4) {
            x0 = Number(el.bounds[0])||0; y0 = Number(el.bounds[1])||0; x1 = Number(el.bounds[2])||0; y1 = Number(el.bounds[3])||0;
          }
          const tb = applyTransformBBox([x0,y0,x1,y1] as any, tr, undefined);
          const cx = (tb[0] + tb[2]) / 2; const cy = (tb[1] + tb[3]) / 2;
          let zone: string | null = null;
          for (const z of (profile as any).zones || []) {
            try { if (pointInPolygon([cx, cy], z.polygon)) { zone = z.id || null; break; } } catch {}
          }
          return { id: `a-${i}`, page: page0, bbox: { x: tb[0], y: tb[1], w: tb[2]-tb[0], h: tb[3]-tb[1] }, text: String(el?.text||''), zone };
        });
      }
      console.log(JSON.stringify({ step: 'bm:blocks', status: 'ok', used, durationMs: Date.now() - t0 }));
      return NextResponse.json({ ok: true, items, next_offset: null, requestId: rid });
    }

    const q = await fetchBlocks({ limit, offset, page, fileName, fileId, fileNames });
    const items = q.items.map((b: any) => {
      const tb = applyTransformBBox([b.bbox.x, b.bbox.y, b.bbox.x + b.bbox.w, b.bbox.y + b.bbox.h] as any, tr, undefined);
      const cx = (tb[0] + tb[2]) / 2; const cy = (tb[1] + tb[3]) / 2;
      let zone: string | null = null;
      for (const z of (profile as any).zones || []) {
        try { if (pointInPolygon([cx, cy], z.polygon)) { zone = z.id || null; break; } } catch {}
      }
      return { id: b.id, page: b.page ?? 1, bbox: { x: tb[0], y: tb[1], w: tb[2]-tb[0], h: tb[3]-tb[1] }, text: b.text || '', zone };
    });
    console.log(JSON.stringify({ step: 'bm:blocks', status: 'ok', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: true, items, next_offset: q.nextOffset, requestId: rid });
  } catch (e: any) {
    console.log(JSON.stringify({ step: 'bm:blocks', status: 'error', durationMs: Date.now() - t0 }));
    return NextResponse.json({ ok: false, error: e?.message || 'error', requestId: rid }, { status: 500 });
  }
}
