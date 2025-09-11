// Server-only Unstructured Platform API client
// Never import this module from client components.
import { logEvent } from '@/lib/log';

type ConnectorType = 'source' | 'destination';

type UpsertParams = {
  name?: string;
  // Optional explicit IDs; falls back to env
  sourceConnectorId?: string;
  destQdrantConnectorId?: string;
};

type RunParams = {
  driveFileId?: string | null;
  driveFilenameRegex?: string | null;
  // Arbitrary metadata to tag downstream payloads (if supported)
  externalId?: string | number | null;
};

function baseUrl(): string {
  const u = (process.env.UNSTRUCTURED_API_URL || '').replace(/\/$/, '');
  if (!u) throw new Error('UNSTRUCTURED_API_URL is not set');
  return u;
}

function apiKey(): string {
  const k = process.env.UNSTRUCTURED_API_KEY || '';
  if (!k) throw new Error('UNSTRUCTURED_API_KEY is not set');
  return k;
}

function mask(value: string | number | undefined | null): string {
  if (value == null) return '';
  const s = String(value);
  if (s.length <= 6) return '***';
  return s.slice(0, 3) + '***' + s.slice(-2);
}

async function uFetch(path: string, init: RequestInit = {}) {
  const url = `${baseUrl()}${path}`;
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'unstructured-api-key': apiKey(),
  };
  if (init.body && !('Content-Type' in (init.headers || {}))) headers['Content-Type'] = 'application/json';
  if (init.headers) Object.assign(headers, init.headers as Record<string, string>);
  const t0 = Date.now();
  const res = await fetch(url, { ...init, headers, cache: 'no-store' });
  const durationMs = Date.now() - t0;
  const requestId = res.headers.get('x-request-id') || undefined;
  await logEvent('uns:fetch', { step: path, status: res.status, durationMs, requestId });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Unstructured ${res.status}: ${text.slice(0, 300)}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (/application\/json/i.test(ct)) return res.json();
  return res;
}

export async function listConnectors(type: ConnectorType): Promise<{ id: string; name: string; type: string }[]> {
  const t0 = Date.now();
  try {
    const j = await uFetch(`/connectors?type=${encodeURIComponent(type)}`, { method: 'GET' });
    const items = Array.isArray(j?.results) ? j.results : Array.isArray(j) ? j : [];
    await logEvent('uns:listConnectors', { step: 'listConnectors', status: 'ok', durationMs: Date.now() - t0 });
    return items.map((c: any) => ({ id: String(c.id || c.connector_id || c.uuid || ''), name: String(c.name || c.title || ''), type: String(c.type || c.kind || '') }));
  } catch (e: any) {
    await logEvent('uns:listConnectors', { step: 'listConnectors', status: 'error', error: e?.message || String(e), durationMs: Date.now() - t0 });
    // Non-fatal; return empty to allow caller to proceed with explicit IDs
    return [];
  }
}

export async function upsertWorkflow(params: UpsertParams = {}): Promise<string> {
  const t0 = Date.now();
  const existing = (process.env.UNSTRUCTURED_WORKFLOW_ID || '').trim();
  if (existing) return existing;

  const srcId = params.sourceConnectorId || process.env.UNS_SOURCE_CONNECTOR_ID || '';
  const dstId = params.destQdrantConnectorId || process.env.UNS_DEST_QDRANT_ID || '';
  const collection = process.env.QDRANT_COLLECTION || '';
  if (!srcId || !dstId || !collection) throw new Error('Missing connector IDs or QDRANT_COLLECTION');

  // Determine embed provider from env
  const embedProvider = (process.env.UNS_EMBED_PROVIDER || (process.env.AZURE_OPENAI_API_KEY ? 'azure_openai' : process.env.OPENAI_API_KEY ? 'openai' : 'openai')).toLowerCase();
  const embedModel = process.env.UNS_EMBED_MODEL || 'text-embedding-3-small'; // 1536 dims

  const body = {
    name: params.name || 'PIK-Auto-Workflow',
    steps: [
      {
        name: 'source',
        type: 'source',
        connector_id: srcId,
        params: {
          // Фильтры и recursive переопределим на запуске / оставим дефолт коннектора
          extensions: ['pdf', 'png'],
        },
      },
      {
        name: 'partition',
        type: 'partition',
        strategy: 'hi_res',
        params: {
          coordinates: true,
          hi_res: true,
          languages: ['eng'],
          exclude: ['Image', 'Header', 'Footer', 'PageNumber'],
          infer_table_structure: true,
        },
      },
      {
        name: 'embed',
        type: 'embed',
        provider: embedProvider,
        params: {
          model: embedModel,
          dimensions: 1536,
        },
      },
      {
        name: 'destination',
        type: 'destination',
        connector_id: dstId,
        params: {
          collection_name: collection,
          upsert: true,
          auto_create_collection: false,
        },
      },
    ],
  } as const;

  const j = await uFetch('/workflows', { method: 'POST', body: JSON.stringify(body) });
  const workflowId = j?.id || j?.workflow_id || j?.uuid;
  if (!workflowId) throw new Error('Failed to create workflow: missing id');
  await logEvent('uns:upsertWorkflow', { step: 'upsertWorkflow', status: 'ok', durationMs: Date.now() - t0 });
  return String(workflowId);
}

export async function runWorkflow(workflowId: string, runParams: RunParams): Promise<string> {
  const t0 = Date.now();
  const body: any = { params: {} };
  const hasFileId = Boolean(runParams.driveFileId);
  const regex = runParams.driveFilenameRegex || process.env.DRIVE_FILENAME_REGEX || '';
  const fileId = runParams.driveFileId || process.env.DRIVE_FILE_ID || '';
  const srcParams: any = { extensions: ['pdf', 'png'] };
  if (String(process.env.UNS_RECURSIVE || '').toLowerCase() === 'true' || process.env.UNS_RECURSIVE === '1') srcParams.recursive = true;
  if (hasFileId || fileId) srcParams.file_id = hasFileId ? runParams.driveFileId : fileId;
  else if (regex) srcParams.filename_regex = regex;
  body.params.source = srcParams;
  if (runParams.externalId != null) body.external_id = String(runParams.externalId);
  // Platform: POST /workflows/{id}/run → 202 + { id, status }
  const j = await uFetch(`/workflows/${encodeURIComponent(workflowId)}/run`, { method: 'POST', body: JSON.stringify(body) });
  const jobId = j?.id || j?.job_id || j?.uuid;
  if (!jobId) throw new Error('No job id in response');
  await logEvent('uns:runWorkflow', { step: 'runWorkflow', status: 'ok', durationMs: Date.now() - t0, jobId: mask(jobId) });
  return String(jobId);
}

export async function getJobStatus(_workflowId: string, jobId: string): Promise<{ status: string; startedAt?: string; finishedAt?: string; errors?: any[]; artifacts?: any[] }>{
  const t0 = Date.now();
  // Platform: GET /jobs/{id}
  const j = await uFetch(`/jobs/${encodeURIComponent(jobId)}`, { method: 'GET' });
  const statusRaw = (j?.status || j?.state || '').toString();
  const status = statusRaw.toLowerCase();
  const startedAt = j?.created_at || j?.started_at || j?.started || undefined;
  const finishedAt = j?.finished_at || j?.ended || undefined;
  const errors = Array.isArray(j?.errors) ? j.errors : undefined;
  const artifacts = undefined; // endpoint not available; rely on destination (Qdrant)
  await logEvent('uns:getJobStatus', { step: 'getJobStatus', status, durationMs: Date.now() - t0, jobId: mask(jobId) });
  return { status, startedAt, finishedAt, errors, artifacts };
}

export async function downloadArtifact(url: string): Promise<Blob> {
  const t0 = Date.now();
  const res = await fetch(url, { headers: { 'unstructured-api-key': apiKey(), Accept: '*/*' }, cache: 'no-store' });
  const durationMs = Date.now() - t0;
  await logEvent('uns:artifact:download', { step: 'downloadArtifact', status: res.status, durationMs });
  if (!res.ok) throw new Error(`Artifact download failed: ${res.status}`);
  const ab = await res.arrayBuffer();
  return new Blob([ab], { type: res.headers.get('content-type') || 'application/octet-stream' });
}

export async function listJobs(workflowId: string, limit = 10): Promise<any[]> {
  const j = await uFetch(`/jobs/?workflow_id=${encodeURIComponent(workflowId)}`, { method: 'GET' });
  const arr = Array.isArray(j) ? j : (Array.isArray(j?.results) ? j.results : []);
  return (arr || []).slice(0, limit);
}

export default { listConnectors, upsertWorkflow, runWorkflow, getJobStatus, downloadArtifact, listJobs };
