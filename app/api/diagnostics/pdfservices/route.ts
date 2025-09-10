import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import dns from 'node:dns/promises';
import '@/lib/runtime/net';

async function tryResolve(host: string) {
  const out: { host: string; v4?: string[]; v6?: string[]; error?: string } = { host };
  try { out.v4 = await dns.resolve4(host); } catch (e: any) { out.v4 = []; out.error = (out.error || '') + ` v4:${e?.code || e?.message || 'err'}`; }
  try { out.v6 = await dns.resolve6(host); } catch (e: any) { out.v6 = []; out.error = (out.error || '') + ` v6:${e?.code || e?.message || 'err'}`; }
  return out;
}

async function tryFetch(url: string, init: RequestInit): Promise<{ url: string; ok: boolean; status?: number; error?: string }> {
  try {
    const res = await fetch(url, init);
    return { url, ok: res.ok, status: res.status };
  } catch (e: any) {
    return { url, ok: false, error: e?.message || 'fetch failed' };
  }
}

export async function GET(_req: NextRequest) {
  const imsHost = 'ims-na1.adobelogin.com';
  const pdfHost = 'pdf-services.adobe.io';
  const ims = await tryResolve(imsHost);
  const pdf = await tryResolve(pdfHost);

  const imsPing = await tryFetch(`https://${imsHost}/ims/token/v3`, { method: 'POST' });
  const pdfGet = await tryFetch(`https://${pdfHost}/assets`, { method: 'GET' });

  // Optionally attempt POST /assets with x-api-key if present (no Bearer token)
  const clientId = process.env.ADOBE_CLIENT_ID || process.env.ADOBE_API_KEY;
  let pdfPost: { url: string; ok: boolean; status?: number; error?: string } | undefined;
  let pdfPostAuth: { url: string; ok: boolean; status?: number; error?: string } | undefined;
  if (clientId) {
    pdfPost = await tryFetch(`https://${pdfHost}/assets`, {
      method: 'POST',
      headers: { 'Accept': 'application/json', 'x-api-key': clientId },
    });
    const org = process.env.ADOBE_ORG_ID || '';
    // Attempt authorized POST if token can be fetched
    try {
      const { getPdfServicesToken } = await import('@/lib/adobe/pdfToken');
      const t = await getPdfServicesToken();
      const headers: Record<string,string> = { 'Accept': 'application/json', 'x-api-key': clientId, 'Authorization': `Bearer ${t.access_token}` };
      if (org) headers['x-gw-ims-org-id'] = org;
      pdfPostAuth = await tryFetch(`https://${pdfHost}/assets`, { method: 'POST', headers });
    } catch {}
  }

  const env = {
    hasClientId: Boolean(process.env.ADOBE_CLIENT_ID || process.env.ADOBE_API_KEY),
    hasSecret: Boolean(process.env.ADOBE_CLIENT_SECRET),
    imsHost: process.env.ADOBE_IMS_HOST || null,
  };

  const ok = (imsPing.ok || imsPing.status === 400) && (pdfGet.ok || pdfGet.status === 401 || pdfGet.status === 404 || pdfGet.status === 405);

  return NextResponse.json({ ok, ims: { resolve: ims, ping: imsPing }, pdfservices: { resolve: pdf, getAssets: pdfGet, postAssets: pdfPost, postAssetsAuth: pdfPostAuth }, env });
}
