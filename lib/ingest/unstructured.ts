import fs from 'fs/promises';
import crypto from 'crypto';
import { logEvent } from '@/lib/log';

export interface UBlock {
  page: number;
  bbox: [number, number, number, number];
  role: string;
  text?: string;
  tableJson?: any;
  hash?: string;
}

function mapRole(t: string): string {
  const s = (t || '').toLowerCase();
  if (s.includes('title') || s.includes('heading') || s === 'header') return 'heading';
  if (s.includes('list')) return 'list';
  if (s.includes('table')) return 'table';
  return 'paragraph';
}

function toBBox(coords: any): [number, number, number, number] {
  try {
    const pts: [number, number][] = coords?.points || [];
    if (Array.isArray(pts) && pts.length >= 4) {
      const xs = pts.map((p) => Number(p?.[0]) || 0);
      const ys = pts.map((p) => Number(p?.[1]) || 0);
      const x0 = Math.min(...xs), y0 = Math.min(...ys), x1 = Math.max(...xs), y1 = Math.max(...ys);
      return [x0, y0, x1, y1];
    }
  } catch {}
  return [0, 0, 0, 0];
}

function hashBlock(b: UBlock): string {
  const h = crypto.createHash('sha1');
  h.update(String(b.page));
  h.update(b.role);
  h.update(JSON.stringify(b.bbox));
  if (b.text) h.update(b.text);
  return h.digest('hex');
}

export async function extractUnstructured(filePath: string, fileName: string) {
  const base = process.env.UNSTRUCTURED_API_URL || '';
  const key = process.env.UNSTRUCTURED_API_KEY || '';
  if (!base || !key) throw new Error('Unstructured API is not configured');
  const url = base.replace(/\/$/, '') + '/general/v0/general';
  const t0 = Date.now();
  const fd = new FormData();
  const buf = await fs.readFile(filePath);
  fd.append('files', new Blob([buf]), fileName || 'upload');
  fd.append('coordinates', 'true');
  fd.append('hi_res', 'true');
  fd.append('languages', 'eng');
  const res = await fetch(url, { method: 'POST', headers: { 'unstructured-api-key': key, 'Accept': 'application/json' }, body: fd });
  const dur = Date.now() - t0;
  await logEvent('unstructured:partition', { status: res.status, durationMs: dur });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Unstructured error ${res.status}: ${text.slice(0, 400)}`);
  }
  const json = await res.json();
  const items: any[] = Array.isArray(json) ? json : (Array.isArray(json?.elements) ? json.elements : []);

  const blocks: UBlock[] = [];
  for (const el of items) {
    const role = mapRole(el.type || el.category || '');
    const coords = el.coordinates || el.bbox || null;
    const bbox = toBBox(coords);
    const page1 = Number(el?.metadata?.page_number ?? el?.page_number ?? el?.coordinates?.page ?? 1) || 1;
    const page = Math.max(0, page1 - 1);
    const b: UBlock = { page, bbox, role };
    if (typeof el.text === 'string') b.text = el.text;
    if (role === 'table' && el?.text_as_html) b.tableJson = { html: el.text_as_html };
    b.hash = hashBlock(b);
    blocks.push(b);
  }
  return { raw: json, blocks };
}

export default extractUnstructured;
