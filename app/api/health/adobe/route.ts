import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { getPdfServicesToken, resolvePdfServicesHost, PdfTokenConfigError, PdfTokenError } from '@/lib/adobe/pdfToken';

type StepResult = { ok: boolean; status?: number; error?: string; advice?: string };

async function fetchJson(url: string, init: RequestInit): Promise<{ status: number; ok: boolean; body?: any; text?: string }> {
  try {
    const res = await fetch(url, init);
    let body: any; let txt: string | undefined;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) body = await res.json().catch(() => undefined);
    else txt = await res.text().catch(() => '');
    return { status: res.status, ok: res.ok, body, text: txt };
  } catch (e: any) {
    return { status: 0, ok: false, text: e?.message || 'network error' };
  }
}

function adviceFor(step: 'token'|'assets'|'extract', status: number, error?: string): string {
  if (status === 0) return 'Network / DNS issue – verify connectivity & host resolution';
  if (step === 'token') {
    if (status === 401 || status === 403) return 'Check client id/secret and project entitlements';
    if (status >= 500) return 'Service error – retry later';
  }
  if (step === 'assets') {
    if (status === 401) return 'Token invalid/expired – refresh credentials';
    if (status === 403) return 'Insufficient permissions for assets scope';
    if (status === 404) return 'Endpoint not found – confirm host/region';
  }
  if (step === 'extract') {
    if (status === 404) return 'Auth OK (invalid fake asset is expected)';
    if (status === 400) return 'Auth OK (payload invalid – expected with dry run)';
    if (status === 401) return 'Token rejected for extract operation';
    if (status === 403) return 'Entitlement missing for extract operation';
  }
  if (error && /timeout/i.test(error)) return 'Timeout – check network latency / firewall';
  return 'Inspect status and logs';
}

export async function GET(_req: NextRequest) {
  const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
  const started = Date.now();
  const host = resolvePdfServicesHost();
  const base = `https://${host}`;
  const steps: Record<string, StepResult> = {};
  let token: string | undefined;
  try {
    const t0 = Date.now();
    const t = await getPdfServicesToken();
    token = t.access_token;
    steps.token = { ok: true, status: 200, advice: 'Product token acquired' };
    try { console.log(JSON.stringify({ level: 'info', step: 'productToken', durationMs: Date.now() - t0, requestId: rid })); } catch {}
  } catch (e: any) {
    if (e instanceof PdfTokenConfigError) {
      steps.token = { ok: false, error: e.message, advice: 'Set required env vars (client id/secret)' };
    } else if (e instanceof PdfTokenError) {
      steps.token = { ok: false, error: e.message, advice: 'Verify credentials / region host' };
    } else {
      steps.token = { ok: false, error: e?.message || 'token error', advice: 'Unexpected error' };
    }
    try { console.log(JSON.stringify({ level: 'error', step: 'productToken', durationMs: Date.now() - started, requestId: rid })); } catch {}
  }

  if (token) {
    const commonHeaders: Record<string,string> = { 'Authorization': `Bearer ${token}`, 'x-api-key': process.env.ADOBE_API_KEY || process.env.ADOBE_CLIENT_ID || '' };
    // Assets GET (listing)
    const ag0 = Date.now();
    const assetsRes = await fetchJson(`${base}/assets`, { method: 'GET', headers: commonHeaders, cache: 'no-store' });
    steps.assets = { ok: assetsRes.ok, status: assetsRes.status, error: assetsRes.ok ? undefined : assetsRes.text, advice: adviceFor('assets', assetsRes.status, assetsRes.text) };
    try { console.log(JSON.stringify({ level: assetsRes.ok ? 'info' : 'warn', step: 'assets', durationMs: Date.now() - ag0, requestId: rid })); } catch {}
    // Assets POST with body (mediaType)
    const body = JSON.stringify({ mediaType: 'application/pdf' });
    const postHeaders = { ...commonHeaders, 'Content-Type': 'application/json' };
    const ap0 = Date.now();
    const assetsPost = await fetchJson(`${base}/assets`, { method: 'POST', headers: postHeaders, body, cache: 'no-store' });
    steps['assetsBody'] = { ok: assetsPost.ok, status: assetsPost.status, error: assetsPost.ok ? undefined : assetsPost.text, advice: adviceFor('assets', assetsPost.status, assetsPost.text) };
    try { console.log(JSON.stringify({ level: assetsPost.ok ? 'info' : 'warn', step: 'assetsBody', durationMs: Date.now() - ap0, requestId: rid })); } catch {}
    // Dry-run extract with fake asset id (expect 400/404 for auth OK)
    const fakeBody = JSON.stringify({ input: { assetID: 'fake-asset-id' }, options: { elementsToExtract: ['text'] } });
    const extractHeaders = { ...commonHeaders, 'Content-Type': 'application/json' };
    const ex0 = Date.now();
    const extractRes = await fetchJson(`${base}/operation/extractpdf`, { method: 'POST', headers: extractHeaders, body: fakeBody, cache: 'no-store' });
    steps.extract = { ok: extractRes.status === 400 || extractRes.status === 404, status: extractRes.status, error: extractRes.ok ? undefined : extractRes.text, advice: adviceFor('extract', extractRes.status, extractRes.text) };
    try { console.log(JSON.stringify({ level: steps.extract.ok ? 'info' : 'warn', step: 'extractDryRun', durationMs: Date.now() - ex0, requestId: rid })); } catch {}
  }
  const ok = steps.token?.ok && steps.assets?.ok !== false && steps.extract?.ok !== false;
  const res = NextResponse.json({ ok, host, region: process.env.ADOBE_REGION || null, steps, requestId: rid, durationMs: Date.now() - started });
  res.headers.set('x-request-id', rid);
  return res;
}
