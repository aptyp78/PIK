import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { getJobStatus, downloadArtifact } from '@/lib/unstructured';
import { logEvent } from '@/lib/log';
import fs from 'fs/promises';
import path from 'path';

export async function GET(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const jobId = url.searchParams.get('jobId');
    if (!jobId) return NextResponse.json({ ok: false, error: 'Missing jobId', requestId: rid }, { status: 400 });
    const wf = (process.env.UNSTRUCTURED_WORKFLOW_ID || url.searchParams.get('workflowId') || '').trim();

    // Local fallback job: immediately finished (artifact already saved by /run)
    if (jobId.startsWith('local-')) {
      const dir = path.join(process.cwd(), 'data', 'artifacts');
      const artifactSaved = path.join(dir, 'last_partition.json');
      await logEvent('ingest:status', { requestId: rid, status: 'finished', durationMs: Date.now() - t0 });
      const res = NextResponse.json({ ok: true, status: 'finished', artifactSaved, requestId: rid });
      res.headers.set('x-request-id', rid);
      return res;
    }
    if (!wf) return NextResponse.json({ ok: false, error: 'Missing workflowId (set UNSTRUCTURED_WORKFLOW_ID or pass ?workflowId=)', requestId: rid }, { status: 400 });

    const st = await getJobStatus(wf, jobId);

    // Optional artifact fallback
    const bmSource = (process.env.BM_SOURCE || 'qdrant').toLowerCase();
    let artifactSaved: string | undefined;
    if ((st.status === 'finished' || st.status === 'succeeded' || st.status === 'done') && bmSource === 'artifact') {
      const part = (st.artifacts || []).find((a: any) => /partition/i.test(a?.type || a?.name || '')) || (st.artifacts || [])[0];
      const urlStr = part?.url || part?.download_url || part?.href;
      if (urlStr) {
        try {
          const blob = await downloadArtifact(String(urlStr));
          const ab = await blob.arrayBuffer();
          const dir = path.join(process.cwd(), 'data', 'artifacts');
          await fs.mkdir(dir, { recursive: true });
          const out = path.join(dir, 'last_partition.json');
          await fs.writeFile(out, Buffer.from(ab));
          artifactSaved = out;
          await logEvent('ingest:artifact:saved', { requestId: rid, path: out });
        } catch (e: any) {
          await logEvent('ingest:artifact:error', { requestId: rid, error: e?.message || String(e) }, 'warn');
        }
      }
    }

    await logEvent('ingest:status', { requestId: rid, status: st.status, durationMs: Date.now() - t0 });
    const res = NextResponse.json({ ok: true, status: st.status, startedAt: st.startedAt, finishedAt: st.finishedAt, errors: st.errors, artifactSaved, requestId: rid });
    res.headers.set('x-request-id', rid);
    return res;
  } catch (e: any) {
    await logEvent('ingest:status:error', { requestId: rid, error: e?.message || String(e) }, 'error');
    const res = NextResponse.json({ ok: false, error: e?.message || 'Failed to get status', requestId: rid }, { status: 500 });
    res.headers.set('x-request-id', rid);
    return res;
  }
}
