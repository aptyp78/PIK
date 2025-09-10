/*
 * Insert mock-ingested documents and blocks without calling Adobe services.
 * Uses @prisma/client directly; safe for sandbox/offline demo.
 */
const path = require('path');
const fs = require('fs');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

function mockBlocksFor(fileName) {
  return [
    { page: 1, bbox: [10, 10, 580, 60], role: 'heading', text: fileName.replace(/\.pdf$/i, '') },
    { page: 1, bbox: [10, 80, 580, 140], role: 'paragraph', text: 'Mock paragraph derived from ' + fileName },
    { page: 1, bbox: [10, 150, 580, 220], role: 'list', text: '• item one; • item two; • item three' },
    { page: 2, bbox: [10, 20, 560, 300], role: 'table', tableJson: { rows: 2, cols: 2, data: [['A', 'B'], ['C', 'D']] } },
    { page: 2, bbox: [10, 320, 560, 380], role: 'paragraph', text: 'Second page content (mock).' },
  ];
}

async function ingestOne(absPath) {
  const base = path.basename(absPath);
  const title = base.replace(/\.pdf$/i, '');
  const blocks = mockBlocksFor(base);
  const maxPage = blocks.reduce((m, b) => (b.page > m ? b.page : m), 0);
  const doc = await prisma.sourceDoc.create({
    data: { title, type: 'pdf', path: absPath, pages: maxPage || null },
  });
  const rows = blocks.map((b) => ({
    sourceDocId: doc.id,
    page: b.page,
    bbox: JSON.stringify(b.bbox),
    role: b.role,
    text: b.text || null,
    tableJson: b.tableJson ? JSON.stringify(b.tableJson) : null,
    hash: null,
  }));
  if (rows.length) await prisma.block.createMany({ data: rows });
  return { docId: doc.id, pages: doc.pages, blocks: rows.length };
}

async function main() {
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
  const results = [];
  for (const p of existing) {
    try {
      const r = await ingestOne(p);
      results.push({ path: p, ok: true, ...r });
    } catch (e) {
      results.push({ path: p, ok: false, error: e && e.message ? e.message : String(e) });
    }
  }
  const docs = await prisma.sourceDoc.count();
  const blocks = await prisma.block.count();
  console.log(JSON.stringify({ ok: results.some((i) => i.ok), results, missing, totals: { docs, blocks } }, null, 2));
  await prisma.$disconnect();
}

main().catch((e) => {
  console.error(e && e.message ? e.message : e);
  process.exit(1);
});

