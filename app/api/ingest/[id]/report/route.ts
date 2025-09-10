import { NextRequest, NextResponse } from 'next/server';

// Ensure this route runs on the Node.js runtime rather than the Edge runtime.
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

/*
 * API route: GET /api/ingest/:id/report
 * Returns aggregates for a document.
 */
export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const docId = parseInt(params.id, 10);
  if (isNaN(docId)) return NextResponse.json({ error: 'Invalid document id' }, { status: 400 });

  try {
    const doc = await prisma.sourceDoc.findUnique({ where: { id: docId }, select: { id: true, pages: true, engine: true } });
    const blocks = await prisma.block.findMany({ where: { sourceDocId: docId } });
    if (!doc || blocks.length === 0) return NextResponse.json({ error: 'Document not found or no blocks' }, { status: 404 });

    const total = blocks.length;
    const byRole: Record<string, number> = {};
    let tables = 0, emptyText = 0, maxPage = 0;

    for (const b of blocks) {
      byRole[b.role] = (byRole[b.role] ?? 0) + 1;
      if (b.role === 'table') tables++;
      if (!b.text || b.text.trim() === '') emptyText++;
      if (b.page > maxPage) maxPage = b.page;
    }
    const pagesWithBlocks = new Set(blocks.map(b => b.page));
    const totalPages = (typeof doc.pages === 'number' && doc.pages > 0) ? doc.pages : (maxPage + 1);
    const emptyPages: number[] = [];
    for (let p = 0; p < totalPages; p++) if (!pagesWithBlocks.has(p)) emptyPages.push(p);
    const emptyPagesShare = totalPages > 0 ? emptyPages.length / totalPages : 0;
    const avgBlockLen = total > 0 ? Math.round(blocks.reduce((s, b) => s + (b.text ? b.text.length : 0), 0) / total) : 0;

    return NextResponse.json({
      docId,
      engine: doc.engine || null,
      totalBlocks: total,
      byRole,
      tablesCount: tables,
      emptyTextBlocks: emptyText,
      emptyPages,
      emptyPagesShare,
      avgBlockLen,
      pages: totalPages,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'Unknown error' }, { status: 500 });
  }
}
