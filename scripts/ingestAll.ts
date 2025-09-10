import fs from 'fs';
import path from 'path';
import prisma from '../lib/prisma';
import '../lib/runtime/net';

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
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

async function ingestOne(absPath: string) {
  const { extractWithRawJob } = await import('../lib/pdf/adobeExtract');
  const { raw, blocks } = await extractWithRawJob(absPath);
  const basename = path.basename(absPath, path.extname(absPath));
  const fsPromises = await import('fs/promises');
  const rawOut = path.join(process.cwd(), 'data', 'raw', `${basename}.json`);
  const normOut = path.join(process.cwd(), 'data', 'normalized', `${basename}.json`);
  await fsPromises.mkdir(path.dirname(rawOut), { recursive: true });
  await fsPromises.mkdir(path.dirname(normOut), { recursive: true });
  await fsPromises.writeFile(rawOut, JSON.stringify(raw, null, 2), 'utf8');
  await fsPromises.writeFile(normOut, JSON.stringify(blocks, null, 2), 'utf8');
  const maxPage = blocks.reduce((m, b: any) => (b.page > m ? b.page : m), 0);
  const doc = await prisma.sourceDoc.create({
    data: { title: basename, type: path.extname(absPath).replace('.', ''), path: absPath, pages: maxPage || null },
  });
  if (blocks.length) {
    const data = blocks.map((b: any) => ({
      sourceDocId: doc.id,
      page: b.page,
      bbox: JSON.stringify(b.bbox),
      role: b.role,
      text: b.text ?? null,
      tableJson: b.tableJson ? JSON.stringify(b.tableJson) : null,
      hash: null,
    }));
    const CHUNK = 2000;
    for (let i = 0; i < data.length; i += CHUNK) {
      await prisma.block.createMany({ data: data.slice(i, i + CHUNK) });
    }
  }
  return { docId: doc.id, pages: maxPage || null, blocks: blocks.length };
}

async function main() {
  loadEnvLocal();
  // Ensure mock is disabled for real run unless user overrides
  if (!('MOCK_ADOBE' in process.env)) process.env.MOCK_ADOBE = '0';
  if (!('MOCK_ADOBE_AUTO' in process.env)) process.env.MOCK_ADOBE_AUTO = '0';

  const baseDir = path.join(process.cwd(), 'data');
  const files = [
    'PIK 5-0 - Platform Experience - ENG.pdf',
    'PIK 5-0 - Ecosystem Forces Scan - ENG.pdf',
    'PIK 5-0 - Platform Business Model - ENG.pdf',
    'PIK 5-0 - NFX Reinforcement Engines - ENG.pdf',
    'PIK 5-0 - Platform Value Network Canvas - ENG.pdf',
    'PIK 5-0 - Introduction - English.pdf',
  ].map((n) => path.join(baseDir, n));

  const existing = files.filter((p) => fs.existsSync(p));
  const missing = files.filter((p) => !fs.existsSync(p));
  const results: any[] = [];
  let totalBlocks = 0;
  let firstDocId: number | undefined;
  let lastDocId: number | undefined;
  for (const p of existing) {
    try {
      const r = await ingestOne(p);
      results.push({ path: p, ok: true, ...r });
      totalBlocks += r.blocks;
      if (!firstDocId) firstDocId = r.docId;
      lastDocId = r.docId;
    } catch (e: any) {
      results.push({ path: p, ok: false, error: e?.message || String(e) });
    }
  }
  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ ok: results.some((i) => i.ok), results, missing, totalBlocks, firstDocId, lastDocId }, null, 2));
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});
