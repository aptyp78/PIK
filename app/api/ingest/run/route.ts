import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { upsertWorkflow, runWorkflow, listJobs } from '@/lib/unstructured';
import { logEvent } from '@/lib/log';
import fs from 'fs/promises';
import path from 'path';
import { extractWithRawJob } from '@/lib/pdf/adobeExtract';
import extractUnstructured from '@/lib/ingest/unstructured';

async function findPosterPath(): Promise<{ path: string; type: string } | null> {
  const candidates = [
    'data/uploads/PIK-Platform-Business-Model.pdf',
    'data/uploads/PIK-Platform-Business-Model.png',
    'data/uploads/PIK 5-0 - Platform Business Model - ENG.pdf',
    'data/uploads/PIK 5-0 - Platform Business Model - ENG.png',
  ];
  for (const p of candidates) {
    try { await fs.access(p); return { path: p, type: p.toLowerCase().endsWith('.png') ? 'png' : 'pdf' }; } catch {}
  }
  try {
    const items = await fs.readdir('data/uploads').catch(() => []);
    const cand = items.find((n) => /platform\s*business\s*model/i.test(n) && /(\.pdf|\.png)$/i.test(n));
    if (cand) {
      const p = `data/uploads/${cand}`;
      return { path: p, type: p.toLowerCase().endsWith('.png') ? 'png' : 'pdf' };
    }
  } catch {}
  return null;
}

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const started = Date.now();
  try {
    const body = await req.json().catch(() => ({}));
    const driveFileId: string | null = body?.driveFileId || process.env.DRIVE_FILE_ID || null;
    const driveFilenameRegex: string | null = body?.driveFilenameRegex || process.env.DRIVE_FILENAME_REGEX || null;
    const externalId: string | number | null = body?.externalId || null;

    await logEvent('ingest:run:start', { requestId: rid, hasFileId: Boolean(driveFileId), hasRegex: Boolean(driveFilenameRegex) });

    const needPlatform = true;
    const wfIdEnv = (process.env.UNSTRUCTURED_WORKFLOW_ID || '').trim();
    const srcConn = (process.env.UNS_SOURCE_CONNECTOR_ID || '').trim();
    const dstConn = (process.env.UNS_DEST_QDRANT_ID || '').trim();
    const fileId = (process.env.DRIVE_FILE_ID || '').trim();
    const srcLooksLikeFileId = srcConn && fileId && srcConn === fileId;
    const platformReady = Boolean((wfIdEnv || (srcConn && dstConn)) && !srcLooksLikeFileId && (process.env.UNSTRUCTURED_API_URL || '').includes('platform.unstructuredapp.io'));

    if (platformReady) {
      const workflowId = await upsertWorkflow();
      let jobId: string;
      try {
        jobId = await runWorkflow(workflowId, { driveFileId, driveFilenameRegex, externalId });
      } catch (e: any) {
        const msg = e?.message || '';
        if (/\b409\b/.test(msg) || /running job in progress/i.test(msg)) {
          // Fetch latest job for this workflow and return it to the client
          const jobs = await listJobs(workflowId, 1);
          const j = jobs?.[0];
          if (j?.id) {
            jobId = String(j.id);
          } else {
            throw e;
          }
        } else {
          throw e;
        }
      }
      await logEvent('ingest:run:ok', { requestId: rid, workflowId: 'wf_' + String(workflowId).slice(-6), jobId: 'jb_' + String(jobId).slice(-6), durationMs: Date.now() - started });
      const res = NextResponse.json({ ok: true, workflowId, jobId, requestId: rid });
      res.headers.set('x-request-id', rid);
      return res;
    }

    // Fallback: local extraction (prefer Unstructured Hosted; else Adobe) → save artifact for /bm (BM_SOURCE=artifact)
    const poster = await findPosterPath();
    if (!poster) {
      const res = NextResponse.json({ ok: false, error: 'Poster not found. Place file at data/uploads/*Platform Business Model*.pdf|.png', requestId: rid }, { status: 404 });
      res.headers.set('x-request-id', rid);
      return res;
    }
    let raw: any, blocks: any[] = [];
    try {
      ({ raw, blocks } = await extractUnstructured(path.resolve(poster.path), path.basename(poster.path)));
    } catch {
      ({ raw, blocks } = await extractWithRawJob(path.resolve(poster.path)));
    }
    const dir = path.join(process.cwd(), 'data', 'artifacts');
    await fs.mkdir(dir, { recursive: true });
    const out = path.join(dir, 'last_partition.json');
    const outBlocks = path.join(dir, 'last_blocks.json');
    await fs.writeFile(out, JSON.stringify(raw, null, 2), 'utf8');
    await fs.writeFile(outBlocks, JSON.stringify(blocks, null, 2), 'utf8');
    const jobId = `local-${Date.now()}`;
    await logEvent('ingest:run:fallback', { requestId: rid, jobId, artifact: out, durationMs: Date.now() - started });
    const res = NextResponse.json({ ok: true, workflowId: 'local', jobId, requestId: rid });
    res.headers.set('x-request-id', rid);
    return res;
  } catch (e: any) {
    await logEvent('ingest:run:error', { requestId: rid, error: e?.message || String(e) }, 'error');
    const res = NextResponse.json({ ok: false, error: e?.message || 'Failed to start ingestion', requestId: rid }, { status: 500 });
    res.headers.set('x-request-id', rid);
    return res;
  }
}
