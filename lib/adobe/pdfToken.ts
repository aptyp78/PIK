import { z } from 'zod';

/**
 * Obtain an access token from PDF Services token endpoint.
 * Endpoint: POST https://<host>/token (form-encoded client_credentials)
 * Region host resolution:
 *  1) ADOBE_PDF_HOST (explicit override)
 *  2) ADOBE_REGION=ew1|ue1|<custom> -> pdf-services-<region>.adobe.io
 *  3) default pdf-services.adobe.io
 */

export class PdfTokenConfigError extends Error {}
export class PdfTokenError extends Error {}

const EnvSchema = z.object({
  ADOBE_CLIENT_ID: z.string().min(1),
  ADOBE_CLIENT_SECRET: z.string().min(1),
}).passthrough();

export interface PdfTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

let cached: { token: string; tokenType: string; exp: number; host: string } | null = null;

function now() { return Math.floor(Date.now() / 1000); }

export function resolvePdfServicesHost(): string {
  if (process.env.ADOBE_PDF_HOST) return process.env.ADOBE_PDF_HOST.trim();
  const region = (process.env.ADOBE_REGION || '').trim().toLowerCase();
  if (region) {
    // Conservative pattern: pdf-services-<region>.adobe.io
    return `pdf-services-${region}.adobe.io`;
  }
  return 'pdf-services.adobe.io';
}

export async function getPdfServicesToken(force = false): Promise<PdfTokenResponse> {
  const parsed = EnvSchema.safeParse(process.env);
  if (!parsed.success) {
    const missing = parsed.error.issues.map(i => i.path.join('.')).join(', ');
    throw new PdfTokenConfigError(`PDF token config invalid: ${missing}`);
  }
  const { ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET } = parsed.data as any;
  const host = resolvePdfServicesHost();
  if (!force && cached && cached.host === host && cached.exp - 60 > now()) {
    return { access_token: cached.token, token_type: cached.tokenType, expires_in: cached.exp - now() };
  }
  // Product token: only client_id and client_secret per Adobe docs
  const body = new URLSearchParams();
  body.set('client_id', ADOBE_CLIENT_ID);
  body.set('client_secret', ADOBE_CLIENT_SECRET);

  const url = `https://${host}/token`;
  let res: Response;
  try {
    res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json' }, body });
  } catch (e: any) {
    throw new PdfTokenError(`Network error requesting token: ${e?.message || e}`);
  }
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new PdfTokenError(`Token endpoint error ${res.status}: ${txt.slice(0,200)}`);
  }
  const json: any = await res.json();
  const schema = z.object({ access_token: z.string().min(10), token_type: z.string().min(3), expires_in: z.number().int().positive() });
  const token = schema.parse(json);
  cached = { token: token.access_token, tokenType: token.token_type, exp: now() + token.expires_in, host };
  try {
    const prefix = token.access_token.slice(0, 8);
    // eslint-disable-next-line no-console
    console.log(`[pdf-token] ok prefix=${prefix} expires_in=${token.expires_in}`);
  } catch {}
  return token;
}

export default getPdfServicesToken;
