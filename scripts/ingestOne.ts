import fs from 'fs';
import fsp from 'fs/promises';
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
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

async function main() {
  loadEnvLocal();
  const { extractWithRawJob } = await import('../lib/pdf/adobeExtract');
  const input = process.argv[2] || path.join(process.cwd(), 'data', 'PIK 5-0 - Platform Experience - ENG.pdf');
  if (!fs.existsSync(input)) throw new Error(`PDF not found: ${input}`);
  // 1) Extract
  const { raw, blocks } = await extractWithRawJob(input);
  // 2) Persist raw and normalized
  const fileName = path.basename(input, path.extname(input));
  const rawOut = path.join(process.cwd(), 'data', 'raw', `${fileName}.json`);
  const normOut = path.join(process.cwd(), 'data', 'normalized', `${fileName}.json`);
  await fsp.mkdir(path.dirname(rawOut), { recursive: true });
  await fsp.mkdir(path.dirname(normOut), { recursive: true });
  await fsp.writeFile(rawOut, JSON.stringify(raw, null, 2), 'utf8');
  await fsp.writeFile(normOut, JSON.stringify(blocks, null, 2), 'utf8');
  // 3) Insert into DB
  const maxPage = blocks.reduce((m, b) => (b.page > m ? b.page : m), 0);
  const doc = await prisma.sourceDoc.create({
    data: { title: fileName, type: path.extname(input).replace('.', ''), path: input, pages: maxPage || null },
  });
  const data = blocks.map((b) => ({
    sourceDocId: doc.id,
    page: b.page,
    bbox: JSON.stringify(b.bbox),
    role: b.role,
    text: b.text ?? null,
    tableJson: b.tableJson ? JSON.stringify(b.tableJson) : null,
    hash: null,
  }));
  if (data.length > 0) {
    const CHUNK = 2000;
    for (let i = 0; i < data.length; i += CHUNK) {
      await prisma.block.createMany({ data: data.slice(i, i + CHUNK) });
    }
  }
  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ message: 'Ingestion complete', docId: doc.id, pages: maxPage, blocks: blocks.length }, null, 2));
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});
