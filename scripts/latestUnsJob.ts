// Print the latest Unstructured Platform job for the configured workflow
import fs from 'fs';
import path from 'path';

function loadDotEnv(file: string) {
  try {
    const txt = fs.readFileSync(file, 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (!m) continue;
      const [, k, vraw] = m;
      const v = vraw.startsWith('"') && vraw.endsWith('"') ? vraw.slice(1, -1) : vraw;
      if (!(k in process.env)) process.env[k] = v;
    }
  } catch {}
}

async function main() {
  loadDotEnv(path.join(process.cwd(), '.env.local'));

  const wfId = (process.env.UNSTRUCTURED_WORKFLOW_ID || '').trim();
  if (!wfId) throw new Error('UNSTRUCTURED_WORKFLOW_ID is not set');

  const uns = await import('../lib/unstructured');
  const { listJobs, getJobStatus } = uns as any;

  const jobs = await listJobs(wfId, 1);
  if (!jobs || jobs.length === 0) {
    console.log(JSON.stringify({ ok: true, workflowId: wfId, latest: null, message: 'No jobs found' }, null, 2));
    return;
  }
  const j = jobs[0];
  const jobId = String(j?.id || j?.job_id || j?.uuid || '');
  const st = jobId ? await getJobStatus(wfId, jobId) : null;

  // Extract a compact view
  const compact = {
    id: jobId,
    status: st?.status || j?.status || j?.state || null,
    startedAt: st?.startedAt || j?.created_at || j?.started_at || null,
    finishedAt: st?.finishedAt || j?.finished_at || null,
    errors: st?.errors || j?.errors || null,
  } as const;

  console.log(JSON.stringify({ ok: true, workflowId: wfId, latest: compact }, null, 2));
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e?.message || String(e) }));
  process.exit(1);
});

