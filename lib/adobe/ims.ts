import { z } from 'zod';

export class ConfigError extends Error {}

const EnvSchema = z.object({
  ADOBE_IMS_HOST: z.string().url(),
  ADOBE_CLIENT_ID: z.string().min(1),
  ADOBE_CLIENT_SECRET: z.string().min(1),
  ADOBE_SCOPES: z.string().min(1),
});

type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number; // seconds
};

let cached: { token: string; expiresAt: number; tokenType: string } | null = null;

function nowSec(): number {
  return Math.floor(Date.now() / 1000);
}

export async function getAdobeAccessToken(): Promise<TokenResponse> {
  const parsed = EnvSchema.safeParse(process.env);
  if (!parsed.success) {
    const missing = parsed.error.issues.map((i) => i.path.join('.')).join(', ');
    throw new ConfigError(`Adobe IMS config missing or invalid: ${missing}`);
  }
  if (process.env.DEBUG_ADOBE_IMS === '1') {
    // eslint-disable-next-line no-console
    console.log('[adobe:ims] env OK (host,id,secret,scopes)');
  }
  const { ADOBE_IMS_HOST, ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET, ADOBE_SCOPES } = parsed.data;

  if (cached && cached.expiresAt - 60 > nowSec()) {
    return { access_token: cached.token, token_type: cached.tokenType, expires_in: cached.expiresAt - nowSec() };
  }

  const body = new URLSearchParams();
  body.set('grant_type', 'client_credentials');
  body.set('client_id', ADOBE_CLIENT_ID);
  body.set('client_secret', ADOBE_CLIENT_SECRET);
  body.set('scope', ADOBE_SCOPES);

  const url = new URL('/ims/token/v3', ADOBE_IMS_HOST).toString();
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to obtain Adobe token: ${res.status} ${text.slice(0, 200)}`);
  }
  const json = (await res.json()) as unknown;
  const schema = z.object({
    access_token: z.string().min(10),
    token_type: z.string().min(3),
    expires_in: z.number().int().positive(),
  });
  const parsedToken = schema.parse(json);

  cached = {
    token: parsedToken.access_token,
    tokenType: parsedToken.token_type,
    expiresAt: nowSec() + parsedToken.expires_in,
  };
  // Optional debug log (disabled by default to avoid leaking token details)
  try {
    if (process.env.DEBUG_ADOBE_IMS === '1') {
      const prefix = parsedToken.access_token.slice(0, 8);
      console.debug(`[adobe:ims] token fetched, expires_in=${parsedToken.expires_in}, token_prefix=${prefix}…`);
    }
  } catch {}

  return parsedToken;
}

export default getAdobeAccessToken;
