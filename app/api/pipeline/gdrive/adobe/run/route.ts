import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { listFilesInFolder, copyFile, downloadFileToTemp, uploadFileBuffer, createShortcut } from '@/lib/google/drive';
import { createPdfFromImage } from '@/lib/pdf/adobeExtract';
import fs from 'fs/promises';
import path from 'path';

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const srcFolder = url.searchParams.get('src') || process.env.DRIVE_FILE_ID || '';
    const dstFolder = url.searchParams.get('dst') || process.env.GDRIVE_ADOBE_FOLDER_ID || '';
    // По умолчанию берём только верхний уровень исходной папки (без подпапок, чтобы не захватывать Adobe)
    const recursive = /^(1|true|yes)$/i.test(url.searchParams.get('recursive') || '0');
    if (!srcFolder || !dstFolder) return NextResponse.json({ ok: false, error: 'DRIVE_FILE_ID or GDRIVE_ADOBE_FOLDER_ID missing' }, { status: 400 });
    const srcFiles = await listFilesInFolder(srcFolder, recursive, ['pdf','png']);
    const dstFiles = await listFilesInFolder(dstFolder, true, ['pdf']);
    const dstNames = new Set(dstFiles.map(f => f.name));
    let copied = 0, converted = 0, skipped = 0;
    for (const f of srcFiles) {
      const ext = (f.name.split('.').pop() || '').toLowerCase();
      if (ext === 'pdf') {
        if (dstNames.has(f.name)) { skipped++; continue; }
        try {
          await copyFile(f.id, dstFolder, f.name); copied++;
        } catch (e: any) {
          if (/Service Accounts do not have storage quota/i.test(e?.message || '')) {
            await createShortcut(f.id, f.name, dstFolder); copied++;
          } else { throw e; }
        }
      } else if (ext === 'png') {
        const pdfName = f.name.replace(/\.png$/i, '.pdf');
        if (dstNames.has(pdfName)) { skipped++; continue; }
        try {
          const tmp = await downloadFileToTemp(f.id, f.name);
          const tmpPdf = path.join(path.dirname(tmp), `${path.basename(tmp, '.png')}.pdf`);
          await createPdfFromImage(tmp, tmpPdf);
          const buf = await fs.readFile(tmpPdf);
          await uploadFileBuffer(buf, pdfName, 'application/pdf', dstFolder);
          converted++;
        } catch (e: any) {
          await createShortcut(f.id, f.name, dstFolder); skipped++;
        }
      }
    }
    return NextResponse.json({ ok: true, srcCount: srcFiles.length, copied, converted, skipped, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'adobe-run failed', requestId: rid }, { status: 500 });
  }
}
