import { NextRequest, NextResponse } from 'next/server';

// Ensure this route runs on the Node.js runtime rather than the Edge runtime.
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

/*
 * API route: GET /api/docs/:id
 * Returns document metadata and its blocks ordered by page/id.
 */
export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = parseInt(params.id, 10);
  if (isNaN(id)) return NextResponse.json({ error: 'Invalid document id' }, { status: 400 });
  try {
    const doc = await prisma.sourceDoc.findUnique({
      where: { id },
      select: {
        id: true, title: true, type: true, pages: true,
        engine: true, canvasProfileId: true, canvasTransform: true, canvasMatchScore: true,
        blocks: {
          orderBy: [{ page: 'asc' }, { id: 'asc' }],
          select: { id: true, page: true, bbox: true, role: true, text: true }
        }
      }
    });
    if (!doc) return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    const blockCount = doc.blocks.length;
    const hasTables = doc.blocks.some((b) => b.role.toLowerCase() === 'table');
    const firstPageWithContent = blockCount ? Math.min(...doc.blocks.map((b) => b.page)) : null;
    const lastPage = blockCount ? Math.max(...doc.blocks.map((b) => b.page)) : null;
    return NextResponse.json({
      id: doc.id,
      title: doc.title,
      type: doc.type,
      pages: doc.pages,
      blockCount,
      hasTables,
      firstPageWithContent,
      lastPage,
      blocks: doc.blocks,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'Unknown error' }, { status: 500 });
  }
}
