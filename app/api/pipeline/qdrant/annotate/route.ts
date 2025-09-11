import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { scroll as qScroll } from '@/lib/qdrant';
import { setPayload } from '@/lib/qdrantWrite';
import extractUnstructured from '@/lib/ingest/unstructured';
import { extractWithRawJob, createPdfFromImage } from '@/lib/pdf/adobeExtract';
import path from 'path';
import fs from 'fs/promises';
import { downloadFileToTemp, getFileMeta } from '@/lib/google/drive';

type BBox = { x:number;y:number;w:number;h:number };

function normalize(s: string) {
  return (s || '')
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function score(a: string, b: string) {
  const A = normalize(a).split(' ').filter(Boolean);
  const B = normalize(b).split(' ').filter(Boolean);
  if (!A.length || !B.length) return 0;
  const setA = new Set(A);
  let common = 0;
  for (const t of B) if (setA.has(t)) common++;
  return common / Math.max(1, Math.min(A.length, B.length));
}

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const filename = url.searchParams.get('filename') || undefined;
    let fileId = url.searchParams.get('fileId') || process.env.DRIVE_FILE_ID || undefined;
    if (filename) fileId = undefined; // если указан filename, игнорируем fileId для отбора
    const limit = Number(url.searchParams.get('limit') || '100');

    // 1) Pull candidate points from Qdrant
    const should: any[] = [];
    if (filename) should.push({ key: 'metadata-filename', match: { value: filename } });
    if (fileId) should.push({ key: 'metadata-data_source-record_locator-file_id', match: { value: fileId } });
    const filter = should.length ? { should } : undefined;
    let q;
    try { q = await qScroll({ limit, filter }); }
    catch (e: any) {
      const msg = e?.message || '';
      if (/Index required but not found/i.test(msg)) {
        // strict mode: fall back to unfiltered scan and in-memory filter
        const qAll = await qScroll({ limit });
        const itemsAll = qAll.items || [];
        const fn = (p: any) => {
          const nm = p?.payload?.['metadata-filename'];
          const fid = p?.payload?.['metadata-data_source-record_locator-file_id'];
          return (!filename || nm === filename) && (!fileId || fid === fileId);
        };
        q = { items: itemsAll.filter(fn), next_offset: qAll.next_offset };
      } else throw e;
    }
    const items = q.items || [];
    if (!items.length) return NextResponse.json({ ok: false, error: 'No points to annotate', requestId: rid }, { status: 404 });

    // 2) Resolve local file path: prefer Google Drive download if fileId is known
    const name = filename || (items[0]?.payload?.['metadata-filename'] as string) || '';
    let local = '';
    if (fileId) {
      const metaName = name || (await getFileMeta(fileId).then(m=>m.name).catch(()=>fileId));
      local = await downloadFileToTemp(fileId, metaName);
    } else {
      // Try to infer fileId from payload if present
      const pid = items[0]?.payload?.['metadata-data_source-record_locator-file_id'];
      if (pid) {
        const metaName = name || (await getFileMeta(String(pid)).then(m=>m.name).catch(()=>String(pid)));
        local = await downloadFileToTemp(String(pid), metaName);
      } else if (name) {
        // As a last resort, try local dev file
        const ptry = path.join(process.cwd(), 'data', 'uploads', name);
        try { await fs.access(ptry); local = ptry; } catch { /* no local file */ }
      }
    }
    if (!local) return NextResponse.json({ ok: false, error: 'Cannot resolve file to annotate (missing fileId and local file)', requestId: rid }, { status: 404 });

    // 3) Extract blocks and index by page (prefer Adobe for better bbox on posters)
    let blocks: any[] = [];
    try {
      const ext = local.toLowerCase().split('.').pop();
      if (ext === 'png') {
        const tmpPdf = path.join(process.cwd(), 'data', 'uploads', `${path.basename(local, '.png')}.adobe.tmp.pdf`);
        try { await createPdfFromImage(local, tmpPdf); } catch {}
        ({ blocks } = await extractWithRawJob(tmpPdf));
        try { await fs.unlink(tmpPdf); } catch {}
      } else {
        ({ blocks } = await extractWithRawJob(local));
      }
    }
    catch { ({ blocks } = await extractUnstructured(local, path.basename(local))); }
    const byPage = new Map<number, { idx:number; text:string; bbox:BBox }[]>();
    for (let i=0;i<blocks.length;i++) {
      const b = blocks[i];
      const bb: BBox = { x: b.bbox[0], y: b.bbox[1], w: Math.max(0, b.bbox[2]-b.bbox[0]), h: Math.max(0, b.bbox[3]-b.bbox[1]) };
      const arr = byPage.get(b.page) || []; arr.push({ idx: i, text: b.text || '', bbox: bb }); byPage.set(b.page, arr);
    }

    // 4) Match and patch
    let patched = 0;
    for (const it of items) {
      const pl: any = it.payload || {};
      const pText = String(pl.text || '');
      const page1 = Number(pl['metadata-page_number'] ?? 0) || 0; // 1-based in payload
      const page0 = Math.max(0, page1 - 1);
      const cands = byPage.get(page0) || [];
      if (!cands.length) continue;
      let best: { bbox:BBox; score:number } | null = null;
      for (const c of cands) {
        const sc = score(pText, c.text);
        if (sc >= 0.6 && (!best || sc > best.score)) best = { bbox: c.bbox, score: sc };
      }
      if (best) {
        await setPayload([it.id], { bbox: best.bbox, page: page0 }, false);
        patched++;
      }
    }

    return NextResponse.json({ ok: true, matched: patched, total: items.length, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'annotate failed' }, { status: 500 });
  }
}
