// List GCS artifacts under Qdrant destination for the latest Unstructured job
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

  const bucket = process.env.GCS_RESULTS_BUCKET || '';
  const prefix = (process.env.GCS_QDRANT_DEST_PREFIX || '').replace(/\/$/, '') + '/';
  const keyFile = process.env.GCS_SA_KEY_FILE || process.env.GDRIVE_SA_PRIVATE_KEY || '';
  if (!bucket || !prefix) throw new Error('GCS_RESULTS_BUCKET or GCS_QDRANT_DEST_PREFIX missing');
  if (!keyFile) throw new Error('GCS_SA_KEY_FILE (or GDRIVE_SA_PRIVATE_KEY) missing');

  // Get latest job time to filter recent objects
  const uns = await import('../lib/unstructured');
  const wfId = (process.env.UNSTRUCTURED_WORKFLOW_ID || '').trim();
  const { listJobs, getJobStatus } = uns as any;
  let jobStart: Date | null = null;
  try {
    const jobs = await listJobs(wfId, 1);
    const j = jobs?.[0];
    const jobId = String(j?.id || j?.job_id || j?.uuid || '');
    if (jobId) {
      const st = await getJobStatus(wfId, jobId);
      if (st?.startedAt) jobStart = new Date(st.startedAt);
    }
  } catch {}

  const { Storage } = await import('@google-cloud/storage');
  const storage = new Storage({ keyFilename: path.resolve(keyFile) });
  const [files] = await storage.bucket(bucket).getFiles({ prefix, autoPaginate: false, maxResults: 2000 });

  // Sort by updated desc
  const items = files
    .map((f: any) => ({ name: f.name, size: Number(f.metadata?.size || 0), updated: new Date(f.metadata?.updated || f.metadata?.timeCreated || Date.now()) }))
    .sort((a, b) => b.updated.getTime() - a.updated.getTime());

  // Filter near last job start if available (±15 minutes window)
  let filtered = items;
  if (jobStart) {
    const startMs = jobStart.getTime();
    const window = 15 * 60 * 1000;
    filtered = items.filter((it) => Math.abs(it.updated.getTime() - startMs) <= window);
    if (filtered.length === 0) filtered = items.slice(0, 50);
  } else {
    filtered = items.slice(0, 50);
  }

  console.log(JSON.stringify({ ok: true, bucket, prefix, total: items.length, shown: filtered.length, latest: filtered.slice(0, 50) }, null, 2));
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e?.message || String(e) }));
  process.exit(1);
});

