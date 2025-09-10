import path from 'path';
import fs from 'fs/promises';

export type IngestItemResult = {
  path: string;
  ok: boolean;
  docId?: number;
  pages?: number | null;
  blocks?: number;
  error?: string;
};

export type DemoIngestResult = {
  ok: boolean;
  totalDocs: number;
  totalBlocks: number;
  pagesMin: number | null;
  pagesMax: number | null;
  lastDocId?: number;
  items: IngestItemResult[];
  missing: string[];
};

function getBaseUrl(): string {
  // Prefer explicit base URL if provided; fallback to localhost dev server.
  const env = process.env.NEXT_PUBLIC_BASE_URL || process.env.BASE_URL;
  return (env && env.replace(/\/$/, '')) || 'http://localhost:3000';
}

function samplePdfNames(): string[] {
  return [
    'PIK 5-0 - Platform Experience - ENG.pdf',
    'PIK 5-0 - Ecosystem Forces Scan - ENG.pdf',
    'PIK 5-0 - Platform Business Model - ENG.pdf',
    'PIK 5-0 - NFX Reinforcement Engines - ENG.pdf',
    'PIK 5-0 - Platform Value Network Canvas - ENG.pdf',
    'PIK 5-0 - Introduction - English.pdf',
  ];
}

/**
 * Sequentially ingests fixed PIK sample PDFs via POST /api/ingest.
 * Returns an aggregate summary for the demo UI.
 */
export async function demoIngest(): Promise<DemoIngestResult> {
  const baseDir = path.join(process.cwd(), 'data');
  const names = samplePdfNames();
  const absPaths = names.map((n) => path.join(baseDir, n));

  // Filter out missing paths to improve UX.
  const existing: string[] = [];
  const missing: string[] = [];
  for (const p of absPaths) {
    try {
      await fs.access(p);
      existing.push(p);
    } catch {
      missing.push(p);
    }
  }

  const items: IngestItemResult[] = [];
  let totalBlocks = 0;
  let pagesMin: number | null = null;
  let pagesMax: number | null = null;
  let lastDocId: number | undefined;

  const baseUrl = getBaseUrl();

  for (const p of existing) {
    try {
      const res = await fetch(`${baseUrl}/api/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: p }),
        cache: 'no-store',
      });
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        items.push({ path: p, ok: false, error: `HTTP ${res.status} ${text.slice(0, 120)}` });
        continue;
      }
      const json = (await res.json()) as { docId: number; pages?: number | null; blocks?: number };
      const pages = json.pages ?? null;
      const blocks = json.blocks ?? 0;
      totalBlocks += blocks;
      if (typeof pages === 'number') {
        pagesMin = pagesMin == null ? pages : Math.min(pagesMin, pages);
        pagesMax = pagesMax == null ? pages : Math.max(pagesMax, pages);
      }
      lastDocId = json.docId || lastDocId;
      items.push({ path: p, ok: true, docId: json.docId, pages, blocks });
    } catch (e: any) {
      items.push({ path: p, ok: false, error: e?.message || 'Unknown error' });
    }
  }

  return {
    ok: items.some((i) => i.ok),
    totalDocs: items.filter((i) => i.ok).length,
    totalBlocks,
    pagesMin,
    pagesMax,
    lastDocId,
    items,
    missing,
  };
}

export default demoIngest;

