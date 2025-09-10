#!/usr/bin/env tsx
/*
 * Simple health smoke script: checks /api/health and /api/health/adobe
 * on localhost ports 3000 and 3001. Prints colored summary.
 */

type Result = { port: number; path: string; ok: boolean; status?: number; error?: string; contentType?: string };

const ports = [3000, 3001];
const paths = ['/api/health', '/api/health/adobe'];

function color(txt: string, c: 'red'|'green'|'yellow'|'gray'|'cyan') {
  const map: Record<typeof c, string> = {
    red: '\u001b[31m', green: '\u001b[32m', yellow: '\u001b[33m', gray: '\u001b[90m', cyan: '\u001b[36m'
  } as const;
  return `${map[c]}${txt}\u001b[0m`;
}

async function check(port: number, path: string): Promise<Result> {
  const url = `http://localhost:${port}${path}`;
  try {
    const res = await fetch(url, { method: 'GET' });
    const ct = res.headers.get('content-type') || '';
    const isJson = ct.includes('application/json');
    if (!isJson) return { port, path, ok: false, status: res.status, contentType: ct, error: 'Non-JSON response' };
    // Read body to ensure it is valid JSON
    await res.json().catch(() => { throw new Error('Invalid JSON body'); });
    return { port, path, ok: res.ok, status: res.status, contentType: ct };
  } catch (e: any) {
    return { port, path, ok: false, error: e?.message || String(e) };
  }
}

async function main() {
  const results: Result[] = [];
  for (const port of ports) {
    for (const p of paths) results.push(await check(port, p));
  }
  const byPort: Record<number, Result[]> = {};
  for (const r of results) (byPort[r.port] ||= []).push(r);
  for (const port of ports) {
    console.log(`\nPort ${port}:`);
    for (const r of byPort[port] || []) {
      const label = `${r.path}`.padEnd(20);
      if (r.ok) console.log(`  ${label} ${color('OK', 'green')} ${color(String(r.status), 'gray')}`);
      else console.log(`  ${label} ${color('FAIL', 'red')} ${color(String(r.status ?? ''), 'gray')} ${r.error ? color(`– ${r.error}`, 'yellow') : ''}${r.contentType ? color(` [ct:${r.contentType}]`, 'cyan') : ''}`);
    }
  }
  const allOk = results.every((r) => r.ok);
  process.exit(allOk ? 0 : 1);
}

main();

