import fs from 'fs';
import path from 'path';
import { getPdfServicesToken, resolvePdfServicesHost } from '../lib/adobe/pdfToken';

function loadEnvLocal() {
  try {
    const p = path.join(process.cwd(), '.env.local');
    if (!fs.existsSync(p)) return;
    const txt = fs.readFileSync(p, 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      const key = m[1];
      let val = m[2];
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

(async () => {
  loadEnvLocal();
  try {
    const host = resolvePdfServicesHost();
    const t = await getPdfServicesToken();
    // eslint-disable-next-line no-console
    console.log(`pdf-services token ok (host=${host}) expires_in`, t.expires_in);
  } catch (e: any) {
    throw new Error(e?.message || 'Failed to obtain product token');
  }
})().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});
