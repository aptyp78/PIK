/*
 * Generate a co-pilot style status report with current DB metrics.
 * Writes to reports/co-pilot-report-YYYY-MM-DD-HHMM.md
 */
const fs = require('fs');
const path = require('path');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

function fmtDate(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function fmtTime(d) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(d.getHours())}${pad(d.getMinutes())}`;
}

async function main() {
  const now = new Date();
  const dateStr = fmtDate(now);
  const timeStr = fmtTime(now);

  const docsCount = await prisma.sourceDoc.count();
  const blocksCount = await prisma.block.count();
  const recent = await prisma.sourceDoc.findMany({ orderBy: { id: 'desc' }, take: 6 });

  // Count blocks for each recent doc
  const recentWithCounts = [];
  for (const d of recent) {
    const cnt = await prisma.block.count({ where: { sourceDocId: d.id } });
    recentWithCounts.push({ ...d, blocks: cnt });
  }

  // Role distribution (top 10)
  let roles = [];
  try {
    roles = await prisma.block.groupBy({ by: ['role'], _count: { _all: true } });
  } catch {}
  roles.sort((a, b) => b._count._all - a._count._all);
  const rolesLines = roles.slice(0, 10).map((r) => `| ${r.role} | ${r._count._all} |`).join('\n');

  const lines = [];
  lines.push(`# co-pilot Отчёт состояния (${dateStr})`);
  lines.push('');
  lines.push('## 1. Резюме');
  lines.push('');
  lines.push(`Система в рабочем состоянии. В БД документов: ${docsCount}, блоков: ${blocksCount}.`);
  lines.push('');
  lines.push('## 2. Метрики');
  lines.push('');
  lines.push('| Показатель | Значение |');
  lines.push('|-----------|----------|');
  lines.push(`| Documents | ${docsCount} |`);
  lines.push(`| Blocks | ${blocksCount} |`);
  lines.push(`| Blocks / doc (avg) | ${docsCount ? (blocksCount / docsCount).toFixed(2) : '0'} |`);
  lines.push('');
  lines.push('## 3. Последние документы');
  lines.push('');
  if (recentWithCounts.length === 0) {
    lines.push('Нет документов.');
  } else {
    lines.push('| id | title | pages | blocks | createdAt |');
    lines.push('|----|-------|-------|--------|-----------|');
    for (const d of recentWithCounts) {
      lines.push(`| ${d.id} | ${d.title} | ${d.pages ?? ''} | ${d.blocks} | ${new Date(d.createdAt).toISOString()} |`);
    }
  }
  lines.push('');
  lines.push('## 4. Распределение по ролям (top-10)');
  lines.push('');
  if (rolesLines) {
    lines.push('| role | count |');
    lines.push('|------|-------|');
    lines.push(rolesLines);
  } else {
    lines.push('Нет данных.');
  }
  lines.push('');
  lines.push('---');
  lines.push('Сформировано автоматически.');

  const outDir = path.join(process.cwd(), 'reports');
  const outFile = path.join(outDir, `co-pilot-report-${dateStr}-${timeStr}.md`);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(outFile, lines.join('\n'), 'utf8');

  console.log(JSON.stringify({ ok: true, outFile }, null, 2));
}

main().catch((e) => {
  console.error(e && e.message ? e.message : e);
  process.exit(1);
});

