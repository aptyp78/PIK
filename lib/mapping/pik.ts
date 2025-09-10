import type { FrameTemplate } from '@/lib/data/frames';
import { frames as ALL_FRAMES } from '@/lib/data/frames';

export type BBox = [number, number, number, number];
export type Block = { id: number; page: number; bbox: string | BBox; role: string; text: string | null };

export type Evidence = { blockId: number; page: number; bbox: BBox; textSnippet: string };
export type FieldAssignment = { name: string; value: string | null; evidence: Evidence[] };
export type FrameAssignment = { slug: string; name: string; fields: FieldAssignment[] };

const TARGET_FRAMES = new Set(['platform-experience', 'platform-business-model']);

export function getTargetFrames(): FrameTemplate[] {
  return ALL_FRAMES.filter(f => TARGET_FRAMES.has(f.slug));
}

function normalizeText(s: string): string {
  return s.toLowerCase().replace(/\s+/g, ' ').replace(/[^a-z0-9\s]/g, '').trim();
}

function isAllCaps(s: string) {
  const letters = s.replace(/[^a-zA-Z]/g, '');
  return letters.length >= 2 && letters === letters.toUpperCase();
}

function parseBBox(bbox: string | BBox): BBox {
  if (Array.isArray(bbox)) return bbox;
  try { return JSON.parse(bbox) as BBox; } catch { return [0,0,0,0]; }
}

function isLikelyHeading(b: Block): boolean {
  if (!b.text) return false;
  const t = b.text.trim();
  if (/heading/i.test(b.role)) return true;
  if (isAllCaps(t) && t.length <= 80) return true;
  if (t.length <= 60 && /^[A-Z]/.test(t)) return true;
  return false;
}

function wordsIncluded(haystack: string, needle: string) {
  const hs = new Set(haystack.split(' ').filter(Boolean));
  const ns = needle.split(' ').filter(Boolean);
  return ns.every(w => hs.has(w));
}

export function autoAssign(blocks: Block[]): FrameAssignment[] {
  const frames = getTargetFrames();
  // Precompute normalized text and heading flags
  const enriched = blocks.map(b => ({
    ...b,
    bboxArr: parseBBox(b.bbox),
    norm: b.text ? normalizeText(b.text) : '',
    isHead: isLikelyHeading(b),
    y0: (() => { const bb = parseBBox(b.bbox); return Math.min(bb[1], bb[3]); })(),
  }));

  const byPage = new Map<number, typeof enriched>();
  for (const b of enriched) {
    const arr = byPage.get(b.page) || [];
    arr.push(b);
    byPage.set(b.page, arr);
  }
  for (const arr of byPage.values()) arr.sort((a, b) => a.y0 - b.y0 || a.id - b.id);

  const results: FrameAssignment[] = frames.map((f) => ({ slug: f.slug, name: f.name, fields: [] }));
  for (const fr of results) {
    const tmpl = frames.find(ff => ff.slug === fr.slug)!;
    for (const fieldName of tmpl.fields) {
      const needle = normalizeText(fieldName);
      let value: string | null = null;
      const evidence: Evidence[] = [];
      // Strategy 1: find heading that matches field name words on same page
      let matchedHead: typeof enriched[number] | undefined;
      for (const arr of byPage.values()) {
        const head = arr.find(b => b.isHead && b.norm && wordsIncluded(b.norm, needle));
        if (head) { matchedHead = head; break; }
      }
      if (matchedHead) {
        const arr = byPage.get(matchedHead.page)!;
        // Collect 1-3 following blocks until next heading
        const idx = arr.findIndex(x => x.id === matchedHead!.id);
        const followers = [] as typeof enriched;
        for (let i = idx + 1; i < arr.length && followers.length < 3; i++) {
          const b = arr[i];
          if (b.isHead) break;
          if (b.text && b.text.trim().length > 0) followers.push(b);
        }
        const parts = followers.map(b => (b.text || '').trim()).filter(Boolean);
        if (parts.length > 0) {
          value = parts.join(' ');
          for (const b of followers) evidence.push({ blockId: b.id, page: b.page, bbox: parseBBox(b.bbox), textSnippet: (b.text || '').slice(0, 200) });
        } else {
          // Use heading itself as evidence
          value = matchedHead.text!.slice(0, 120);
          evidence.push({ blockId: matchedHead.id, page: matchedHead.page, bbox: parseBBox(matchedHead.bbox), textSnippet: matchedHead.text!.slice(0, 200) });
        }
      }
      // Strategy 2: fallback: any block containing words
      if (!value) {
        const any = enriched.find(b => b.norm && wordsIncluded(b.norm, needle));
        if (any) {
          value = (any.text || '').slice(0, 160);
          evidence.push({ blockId: any.id, page: any.page, bbox: parseBBox(any.bbox), textSnippet: (any.text || '').slice(0, 200) });
        }
      }
      fr.fields.push({ name: fieldName, value, evidence });
    }
  }
  return results;
}

