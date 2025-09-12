import fs from 'fs/promises';
import path from 'path';

export type Zone = { id: string; title?: string; box: [number, number, number, number] };
export type Template = { id: string; title?: string; version?: string; zones: Zone[] };

export async function loadTemplate(templateId: string): Promise<Template> {
  const p = path.join(process.cwd(), 'lib', 'mapping', 'templates', `${templateId}.json`);
  const text = await fs.readFile(p, 'utf8');
  const j = JSON.parse(text);
  if (!j?.zones || !Array.isArray(j.zones)) throw new Error('Invalid template');
  return j as Template;
}

export function centroidOf(x0: number, y0: number, x1: number, y1: number) {
  return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
}

export function mapToZones(
  boxes: { page: number; x0: number; y0: number; x1: number; y1: number; text?: string; type?: string }[],
  pageDims: Map<number, { w: number; h: number }>,
  template: Template
) {
  const out: any[] = [];
  for (const b of boxes) {
    const dims = pageDims.get(b.page) || { w: 1, h: 1 };
    const { cx, cy } = centroidOf(b.x0, b.y0, b.x1, b.y1);
    const nx = dims.w ? cx / dims.w : 0;
    const ny = dims.h ? cy / dims.h : 0;
    let zoneId: string | null = null;
    for (const z of template.zones) {
      const [x1, y1, x2, y2] = z.box;
      if (nx >= x1 && nx <= x2 && ny >= y1 && ny <= y2) { zoneId = z.id; break; }
    }
    out.push({ ...b, zoneId });
  }
  const counts: Record<string, number> = {};
  for (const it of out) { if (it.zoneId) counts[it.zoneId] = (counts[it.zoneId] || 0) + 1; }
  return { assigned: out, counts };
}

