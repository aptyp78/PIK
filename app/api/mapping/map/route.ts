import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { downloadText, uploadJson } from '@/lib/gcs';
import { loadTemplate, mapToZones } from '@/lib/mapping/canvasMap';

type Box = { page: number; x0: number; y0: number; x1: number; y1: number; text?: string; type?: string };

function toBoxes(json: any): Box[] {
  const out: Box[] = [];
  const elements: any[] = Array.isArray(json?.content) ? json.content : Array.isArray(json?.elements) ? json.elements : [];
  for (const el of elements) {
    const page1 = Number(el?.metadata?.page_number ?? el?.page_number ?? (typeof el?.page === 'number' ? el.page+1 : 1)) || 1;
    const page0 = Math.max(0, page1 - 1);
    let x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    try {
      const pts: any[] = el?.coordinates?.points || el?.coordinates || [];
      if (Array.isArray(pts) && pts.length) {
        const xs = pts.map((p: any) => Number(p?.[0]) || 0);
        const ys = pts.map((p: any) => Number(p?.[1]) || 0);
        x0 = Math.min(...xs); y0 = Math.min(...ys); x1 = Math.max(...xs); y1 = Math.max(...ys);
      } else {
        const b = el?.bounds || el?.Bounds || el?.bound || el?.Boundary;
        if (Array.isArray(b) && b.length >= 4) { x0=+b[0]||0; y0=+b[1]||0; x1=+b[2]||0; y1=+b[3]||0; }
      }
    } catch {}
    const text = typeof el?.text === 'string' ? el.text : (typeof el?.Text === 'string' ? el.Text : undefined);
    const type = String(el?.type || el?.Type || '');
    out.push({ page: page0, x0, y0, x1, y1, text, type });
  }
  return out;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const name: string = body?.name || '';
    const templateId: string = body?.template || 'PIK_PBM_v5';
    const save: boolean = Boolean(body?.save);
    if (!name) return NextResponse.json({ ok: false, error: 'name required' }, { status: 400 });
    const bucket = process.env.GCS_RESULTS_BUCKET || '';
    if (!bucket) return NextResponse.json({ ok: false, error: 'GCS_RESULTS_BUCKET missing' }, { status: 400 });
    const text = await downloadText(bucket, name);
    const json = JSON.parse(text);
    const boxes = toBoxes(json);
    const dims = new Map<number, { w: number; h: number }>();
    for (const b of boxes) {
      const d = dims.get(b.page) || { w: 0, h: 0 };
      d.w = Math.max(d.w, b.x1);
      d.h = Math.max(d.h, b.y1);
      dims.set(b.page, d);
    }
    const tpl = await loadTemplate(templateId);
    const mapped = mapToZones(boxes, dims, tpl);

    let stored: string | undefined;
    if (save) {
      const dstPrefix = (process.env.GCS_MAPPING_PREFIX || 'Mapping').replace(/\/$/, '');
      const outName = `${dstPrefix}/${templateId}/${name}`;
      await uploadJson(bucket, outName, { template: tpl, mapped, dims: Object.fromEntries(dims.entries()) });
      stored = outName;
    }

    return NextResponse.json({ ok: true, template: tpl.id, zones: tpl.zones, counts: mapped.counts, dims: Object.fromEntries(dims.entries()), stored, items: mapped.assigned.slice(0, 2000) });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'mapping failed' }, { status: 500 });
  }
}
