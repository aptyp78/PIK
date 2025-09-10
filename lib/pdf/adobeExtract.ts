/*
 * Adobe PDF Extract API client.
 *
 * This module defines a single function `extractWithRaw` which accepts a path to a PDF
 * file and returns a Promise resolving to the raw JSON response and an array of
 * normalized blocks.  Each block has page, bounding box, role, text and optional
 * table JSON.  See the README for details.
 */

import fs from 'fs/promises';
import JSZip from 'jszip';
import getPdfServicesToken, { PdfTokenConfigError } from '../adobe/pdfToken';

function resolvePdfHost(): string {
  const explicit = (process.env.ADOBE_PDF_HOST || '').trim();
  if (explicit) return explicit;
  const region = (process.env.ADOBE_REGION || '').trim().toLowerCase();
  return region ? `pdf-services-${region}.adobe.io` : 'pdf-services.adobe.io';
}

// REST endpoints
const EXTRACT_ENDPOINT = `https://${resolvePdfHost()}/operation/extractpdf`;
const CREATEPDF_ENDPOINT = `https://${resolvePdfHost()}/operation/createpdf`;

export class ConfigError extends Error {}
export class ExtractError extends Error {
  constructor(message: string, public code: 'failed' | 'timeout' = 'failed') {
    super(message);
  }
}

export interface Block {
  page: number;
  bbox: [number, number, number, number];
  role: string;
  text?: string;
  tableJson?: any;
}

// Legacy sync endpoint removed – product token + async jobs only

export async function extractBlocks(pdfPath: string): Promise<Block[]> {
  const { blocks } = await extractWithRawJob(pdfPath);
  return blocks;
}

async function createUploadAsset(headers: Record<string, string>, mediaType: string): Promise<{ assetID: string; uploadUri: string }> {
  const url = `https://${resolvePdfHost()}/assets`;
  let lastStatus = 0;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { ...headers, Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ mediaType }),
    });
    lastStatus = res.status;
    if (res.ok) {
      const json = await res.json();
      const assetID = json?.assetID || json?.id;
      const uploadUri = json?.uploadUri || json?.uploadURL || json?.uploadUriSigned;
      if (!assetID || !uploadUri) throw new ExtractError('Invalid asset response');
      return { assetID, uploadUri };
    }
    if (res.status >= 500) {
      await new Promise((r) => setTimeout(r, attempt * 500));
      continue;
    }
    const txt = await res.text().catch(() => '');
    throw new ExtractError(`Failed to create upload asset: ${res.status} ${txt.slice(0, 200)}`);
  }
  throw new ExtractError(`Failed to create upload asset: ${lastStatus}`);
}

async function getDownloadUriForAsset(assetID: string, headers: Record<string, string>): Promise<string> {
  const res = await fetch(`https://${resolvePdfHost()}/assets/${encodeURIComponent(assetID)}`, {
    method: 'GET',
    headers: { ...headers, Accept: 'application/json' },
  });
  if (!res.ok) {
    const xr = res.headers.get('x-request-id') || '';
    const t = await res.text().catch(() => '');
    try { console.warn('[adobe:assets:id] failed', res.status, xr, t.slice(0, 120)); } catch {}
    throw new ExtractError(`Failed to get download uri for asset: ${res.status}${xr ? ` xrid=${xr}` : ''}`);
  }
  const json = await res.json();
  const uri = json?.downloadUri || json?.downloadURL;
  if (!uri) throw new ExtractError('No downloadUri in asset response');
  return uri;
}

async function startExtractJob(assetID: string, headers: Record<string, string>): Promise<string> {
  // REST contract: top-level fields (no input/inputs/options wrappers)
  const body = {
    assetID,
    elementsToExtract: ['text', 'tables'],
  } as const;
  const res = await fetch(`https://${resolvePdfHost()}/operation/extractpdf`, {
    method: 'POST',
    headers: { ...headers, Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!(res.status === 201 || res.status === 202)) {
    const xr = res.headers.get('x-request-id') || '';
    const t = await res.text().catch(() => '');
    try { console.warn('[adobe:job] start failed', res.status, xr, t.slice(0, 120)); } catch {}
    throw new ExtractError(`Failed to start extract job: ${res.status} ${t.slice(0, 200)}${xr ? ` xrid=${xr}` : ''}`);
  }
  const loc = res.headers.get('location') || res.headers.get('Location');
  if (!loc) throw new ExtractError('No job location header');
  const url = loc.startsWith('http') ? loc : `https://${resolvePdfHost()}${loc}`;
  return url;
}

async function pollJob(locationUrl: string, headers: Record<string, string>): Promise<any> {
  const max = 12;
  for (let attempt = 1; attempt <= max; attempt++) {
    const res = await fetch(locationUrl, { headers: { ...headers, Accept: 'application/json' } });
    if (!res.ok) throw new ExtractError(`Job status error: ${res.status}`);
    const json = await res.json();
    const status = (json?.status || json?.state || '').toString().toLowerCase();
    console.debug(`[adobe:extract] job status attempt ${attempt}: ${status || 'unknown'}`);
    if (status === 'done' || status === 'succeeded' || status === 'success' || status === 'finished' || status === 'ok') {
      return json;
    }
    if (status === 'failed' || status === 'error') {
      throw new ExtractError('Job failed', 'failed');
    }
    await new Promise((r) => setTimeout(r, attempt * 1000));
  }
  throw new ExtractError('Job timeout', 'timeout');
}

function firstStringMatch(obj: any, pred: (s: string, k?: string) => boolean): string | undefined {
  const seen = new Set<any>();
  const stack = [obj];
  while (stack.length) {
    const cur = stack.pop();
    if (!cur || typeof cur !== 'object' || seen.has(cur)) continue;
    seen.add(cur);
    for (const [k, v] of Object.entries(cur)) {
      if (typeof v === 'string') { if (pred(v, k)) return v; }
      else if (Array.isArray(v)) {
        for (const it of v) {
          if (typeof it === 'string') { if (pred(it, k)) return it; }
          else if (it && typeof it === 'object') stack.push(it);
        }
      } else if (v && typeof v === 'object') stack.push(v);
    }
  }
  return undefined;
}

async function resolveResultDownload(job: any, headers: Record<string, string>): Promise<string | undefined> {
  // Direct downloadUri if present
  const dl = firstStringMatch(job, (s, k) => (k?.toLowerCase() || '').includes('download') && /^https?:\/\//.test(s));
  if (dl) return dl;
  // Try to find an assetID (URN)
  const urn = firstStringMatch(job, (s, k) => (k?.toLowerCase() || '').includes('asset') && /urn:aaid:/.test(s))
    || firstStringMatch(job, (s) => /urn:aaid:/.test(s));
  if (urn) {
    try {
      const uri = await getDownloadUriForAsset(urn, headers);
      return uri;
    } catch {}
  }
  return undefined;
}
function toBlocksFromJson(json: any): Block[] {
  const out: Block[] = [];
  const items = Array.isArray(json?.content)
    ? json.content
    : Array.isArray(json?.elements)
    ? json.elements
    : [];
  for (const elem of items) {
    const page = typeof elem.page === 'number' ? elem.page : typeof elem.Page === 'number' ? elem.Page : 0;
    const bounds = elem.bounds || elem.Bounds || elem.bound || elem.Boundary;
    const bbox: [number, number, number, number] =
      Array.isArray(bounds) && bounds.length >= 4
        ? [Number(bounds[0]) || 0, Number(bounds[1]) || 0, Number(bounds[2]) || 0, Number(bounds[3]) || 0]
        : [0, 0, 0, 0];
    const role = (elem.type || elem.Type || 'unknown').toString();
    const block: Block = { page, bbox, role };
    if (typeof elem.text === 'string') block.text = elem.text;
    else if (typeof elem.Text === 'string') block.text = elem.Text;
    if (role.toLowerCase() === 'table' && (elem.table || elem.Table)) block.tableJson = elem.table || elem.Table;
    out.push(block);
  }
  return out;
}

export async function extractWithRawJob(pdfPath: string): Promise<{ raw: any; blocks: Block[] }> {
  // Validate OAuth config (product token only)
  try {
    // Obtain product token from PDF Services token endpoint (no IMS fallback)
    const token = await getPdfServicesToken();
    // Prefer explicit PDF Services API key for x-api-key; fallback to IMS client id
    const clientId = process.env.ADOBE_API_KEY || process.env.ADOBE_CLIENT_ID;
    if (!clientId) throw new PdfTokenConfigError('Missing ADOBE_API_KEY or ADOBE_CLIENT_ID');
    const headers: Record<string, string> = {
      Authorization: `Bearer ${token.access_token}`,
      'x-api-key': clientId,
    };
    // Intentionally omit x-gw-ims-org-id to avoid conflicts per guidance

    // 1) Create asset and upload PDF
    let assetID: string, uploadUri: string;
    try {
      const ext = (pdfPath.split('.').pop() || '').toLowerCase();
      const mediaType = ext === 'png' ? 'image/png' : 'application/pdf';
      ({ assetID, uploadUri } = await createUploadAsset(headers, mediaType));
    } catch (errFirst: any) {
      // If we initially used ADOBE_API_KEY and also have ADOBE_CLIENT_ID, retry swapping keys (some setups require client_id)
      const key1 = process.env.ADOBE_API_KEY;
      const key2 = process.env.ADOBE_CLIENT_ID;
      if (key1 && key2 && key1 !== key2) {
        try {
          const altHeaders = { ...headers, 'x-api-key': key2 };
          const ext2 = (pdfPath.split('.').pop() || '').toLowerCase();
          const mediaType2 = ext2 === 'png' ? 'image/png' : 'application/pdf';
          ({ assetID, uploadUri } = await createUploadAsset(altHeaders, mediaType2));
        } catch (errSecond) {
          throw errFirst;
        }
      } else {
        throw errFirst;
      }
    }
  const pdfData = await fs.readFile(pdfPath);
  const upExt = (pdfPath.split('.').pop() || '').toLowerCase();
  const upType = upExt === 'png' ? 'image/png' : 'application/pdf';
  const putRes = await fetch(uploadUri, { method: 'PUT', body: new Uint8Array(pdfData), headers: { 'Content-Type': upType } });
    if (!(putRes.ok || putRes.status === 200)) throw new ExtractError(`Upload failed: ${putRes.status}`);

    // 2) Start job
    const jobLocation = await startExtractJob(assetID, headers);

    // 3) Poll
    const job = await pollJob(jobLocation, headers);

    // 4) Resolve result asset + download (ZIP expected)
    const resultAssetId = job?.result?.assetID || job?.output?.assetID || job?.result?.assetId || job?.output?.assetId
      || firstStringMatch(job?.result || job?.output || job, (s, k) => (k?.toLowerCase() || '').includes('asset') && /urn:aaid:/.test(s));
    if (!resultAssetId || typeof resultAssetId !== 'string') throw new ExtractError('No result asset id');

    // Fetch signed download URL via authorized /assets/{assetID}
    let downloadUri = await getDownloadUriForAsset(resultAssetId, headers);

    // Download the ZIP (no auth required for signed URL)
    let dlRes = await fetch(downloadUri, { headers: { Accept: '*/*' } });
    if (!(dlRes.ok && (dlRes.status === 200))) {
      // Refresh signed URL and retry once
      try { downloadUri = await getDownloadUriForAsset(resultAssetId, headers); } catch {}
      dlRes = await fetch(downloadUri, { headers: { Accept: '*/*' } });
      if (!(dlRes.ok && (dlRes.status === 200))) {
        const ct = dlRes.headers.get('content-type') || '';
        const xr = dlRes.headers.get('x-ms-request-id') || dlRes.headers.get('x-request-id') || '';
        const txt = await dlRes.text().catch(() => '');
        try { console.warn('[adobe:download] failed', dlRes.status, ct, xr, txt.slice(0, 120)); } catch {}
        throw new ExtractError(`Failed to download result: ${dlRes.status}`);
      }
    }
    const ab = await dlRes.arrayBuffer();
    const zip = await JSZip.loadAsync(ab);
    // Find structuredData.json somewhere in the archive
    const entry = Object.keys(zip.files).find((n) => n.toLowerCase().endsWith('structureddata.json'));
    if (!entry) throw new ExtractError('No structuredData.json in result');
    const jsonText = await zip.file(entry)!.async('string');
    const json = JSON.parse(jsonText);
    const blocks = toBlocksFromJson(json);
    return { raw: json, blocks };
  } catch (e: any) {
    if (e instanceof PdfTokenConfigError) {
      // propagate as ConfigError for API route to map to 400
      throw new ConfigError(e.message);
    }
    if (e instanceof ExtractError) throw e;
    throw new ExtractError(e?.message || 'Extract failed');
  }
}

export async function createPdfFromImage(imagePath: string, outputPdfPath: string): Promise<void> {
  const token = await getPdfServicesToken();
  const clientId = process.env.ADOBE_API_KEY || process.env.ADOBE_CLIENT_ID;
  if (!clientId) throw new PdfTokenConfigError('Missing ADOBE_CLIENT_ID');
  const headers: Record<string, string> = { Authorization: `Bearer ${token.access_token}`, 'x-api-key': clientId };
  // 1) Create asset + upload image
  const { assetID, uploadUri } = await createUploadAsset(headers, 'image/png');
  const data = await fs.readFile(imagePath);
  const put = await fetch(uploadUri, { method: 'PUT', body: new Uint8Array(data), headers: { 'Content-Type': 'image/png' } });
  if (!(put.ok || put.status === 200)) throw new ExtractError(`Upload (createpdf) failed: ${put.status}`);
  // 2) Start createpdf job
  const res = await fetch(CREATEPDF_ENDPOINT, { method: 'POST', headers: { ...headers, Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ assetID }) });
  if (!(res.status === 201 || res.status === 202)) {
    const xr = res.headers.get('x-request-id') || '';
    const t = await res.text().catch(() => '');
    throw new ExtractError(`Failed to start createpdf job: ${res.status} ${t.slice(0, 120)}${xr ? ` xrid=${xr}` : ''}`);
  }
  const loc = res.headers.get('location') || res.headers.get('Location');
  if (!loc) throw new ExtractError('No job location (createpdf)');
  const jobUrl = loc.startsWith('http') ? loc : `https://${resolvePdfHost()}${loc}`;
  const job = await pollJob(jobUrl, headers);
  const outAsset = job?.result?.assetID || job?.output?.assetID || firstStringMatch(job, (s) => /urn:aaid:/.test(s));
  if (!outAsset) throw new ExtractError('No output asset from createpdf');
  const dl = await getDownloadUriForAsset(String(outAsset), headers);
  const dlRes = await fetch(dl);
  if (!(dlRes.ok && dlRes.status === 200)) throw new ExtractError(`Failed to download created PDF: ${dlRes.status}`);
  const buf = Buffer.from(await dlRes.arrayBuffer());
  await fs.writeFile(outputPdfPath, buf);
}

// Deprecated: extractWithRaw removed in uploads-only mode; use extractWithRawJob
