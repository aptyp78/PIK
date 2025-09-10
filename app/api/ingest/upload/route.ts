import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import path from 'path';
import fs from 'fs/promises';
import { randomUUID } from 'crypto';
import prisma from '@/lib/prisma';
import { extractWithRawJob, createPdfFromImage } from '@/lib/pdf/adobeExtract';
import extractUnstructured from '@/lib/ingest/unstructured';
import { logEvent } from '@/lib/log';

const MAX_SIZE = 30 * 1024 * 1024; // 30 MB

type Step =
  | 'Token'
  | 'Create Asset'
  | 'Upload File'
  | 'Create PDF'
  | 'Start Job'
  | 'Poll'
  | 'Download ZIP'
  | 'Parse'
  | 'Insert'
  | 'Recalc Pages';

function ok(body: any, headers?: HeadersInit) {
  const res = NextResponse.json(body);
  if (headers) Object.entries(headers).forEach(([k, v]) => res.headers.set(k, String(v)));
  return res;
}

function fail(status: number, error: string) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function POST(req: NextRequest) {
  const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
  const started = Date.now();
  try {
    const form = await req.formData();
    const file = form.get('file');
    if (!file || !(file instanceof File)) {
      await logEvent('upload:bad-request', { requestId: rid, reason: 'Missing file field' }, 'warn');
      return fail(400, 'Missing file field');
    }
    const name = file.name || 'upload';
    const size = (file as any).size ?? 0;
    if (!size || size <= 0) return fail(400, 'Empty upload');
    if (size > MAX_SIZE) return fail(413, 'File too large (max 30 MB)');
    const ext = (name.split('.').pop() || '').toLowerCase();
    if (!(ext === 'pdf' || ext === 'png')) return fail(400, 'Only .pdf and .png are allowed');

    const uploadsDir = path.join(process.cwd(), 'data', 'uploads');
    await fs.mkdir(uploadsDir, { recursive: true });
    const tempName = `${Date.now()}-${randomUUID()}.${ext}`;
    const tempPath = path.join(uploadsDir, tempName);
    // Persist temp upload
    const ab = await file.arrayBuffer();
    await fs.writeFile(tempPath, Buffer.from(ab));

    // Log initial receipt
    await logEvent('upload:received', { requestId: rid, name, size, ext });

    // Engine selection (form field 'engine' or env default)
    const engine = String(form.get('engine') || process.env.INGEST_ENGINE_DEFAULT || 'unstructured').toLowerCase();

    let raw: any, blocks: any[];
    let docPath: string = tempPath;
    if (engine === 'unstructured') {
      // PNG: send as-is; PDF: send as-is
      await logEvent('upload:extract:start', { requestId: rid, engine, path: tempPath });
      ({ raw, blocks } = await extractUnstructured(tempPath, name));
      docPath = tempPath;
      await logEvent('upload:extract:done', { requestId: rid, engine, blocks: blocks.length });
    } else {
      // Adobe engine (default fallback)
      // For PNG: convert to PDF first
      let localPdfPath = tempPath;
      if (ext === 'png') {
        await logEvent('upload:createpdf:start', { requestId: rid, tempPath });
        const outPdf = path.join(uploadsDir, `${Date.now()}-${randomUUID()}.pdf`);
        await createPdfFromImage(tempPath, outPdf);
        try { await fs.unlink(tempPath); } catch {}
        localPdfPath = outPdf;
        await logEvent('upload:createpdf:done', { requestId: rid, pdfPath: outPdf });
      }
      await logEvent('upload:extract:start', { requestId: rid, engine: 'adobe', path: localPdfPath });
      ({ raw, blocks } = await extractWithRawJob(localPdfPath));
      docPath = localPdfPath;
      await logEvent('upload:extract:done', { requestId: rid, engine: 'adobe', blocks: blocks.length });
    }

    // Persist raw and normalized
    const fileBase = path.basename(docPath, path.extname(docPath));
    const rawOut = path.join(process.cwd(), 'data', 'raw', `${fileBase}.json`);
    const normOut = path.join(process.cwd(), 'data', 'normalized', `${fileBase}.json`);
    await fs.mkdir(path.dirname(rawOut), { recursive: true });
    await fs.mkdir(path.dirname(normOut), { recursive: true });
    await fs.writeFile(rawOut, JSON.stringify(raw, null, 2), 'utf8');
    await fs.writeFile(normOut, JSON.stringify(blocks, null, 2), 'utf8');

    // Insert into DB
    const maxObserved = blocks.reduce((m, b) => (b.page > m ? b.page : m), -1);
    const pagesCount = maxObserved >= 0 ? maxObserved + 1 : null;
    const title = name.replace(/\.[^.]+$/, '');
    // Optional visual-first params from client
    const canvasTransform = String(form.get('canvasTransform') || '');
    const canvasProfileId = String(form.get('canvasProfileId') || 'PIK_BusinessModel_v5');
    const canvasMatchScore = Number(String(form.get('canvasMatchScore') || '0')) || null;
    const doc = await prisma.sourceDoc.create({
      data: { title, type: ext || 'pdf', path: docPath, engine, pages: pagesCount, canvasTransform: canvasTransform || null, canvasProfileId, canvasMatchScore: canvasMatchScore ?? undefined },
    });

    if (blocks.length) {
      const data = blocks.map((b) => ({
        sourceDocId: doc.id,
        page: b.page,
        bbox: JSON.stringify(b.bbox),
        role: b.role,
        text: b.text ?? null,
        tableJson: b.tableJson ? JSON.stringify(b.tableJson) : null,
        hash: null,
      }));
      const CHUNK = 2000;
      for (let i = 0; i < data.length; i += CHUNK) {
        const slice = data.slice(i, i + CHUNK);
        await prisma.block.createMany({ data: slice });
      }
    }

    await logEvent('upload:db:inserted', { requestId: rid, docId: doc.id, engine, pages: pagesCount, blocks: blocks.length });
    const res = ok({ ok: true, message: 'Upload & ingestion complete', engine, docId: doc.id, pages: pagesCount ?? 0, blocks: blocks.length, requestId: rid, durationMs: Date.now() - started });
    res.headers.set('x-request-id', rid);
    await logEvent('upload:success', { requestId: rid, docId: doc.id, durationMs: Date.now() - started, name, size });
    return res;
  } catch (e: any) {
    await logEvent('upload:error', { requestId: rid, error: e?.message || String(e) }, 'error');
    const res = NextResponse.json({ ok: false, error: e?.message || 'Upload failed', requestId: rid }, { status: 500 });
    res.headers.set('x-request-id', rid);
    return res;
  }
}
