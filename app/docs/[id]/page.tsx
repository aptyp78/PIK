import { notFound } from 'next/navigation';
import prisma from '@/lib/prisma';
// @ts-ignore - local client component
import DocClient from './reportClient'; // .tsx file co-located
// @ts-ignore - client component
import OverlayPdf from './OverlayPdf';

interface Props { params: { id: string }; }

export default async function DocPage({ params }: Props) {
  const docId = Number(params.id);
  if (Number.isNaN(docId)) notFound();
  const doc = await prisma.sourceDoc.findUnique({
    where: { id: docId },
    select: {
      id: true, title: true, type: true, pages: true,
      blocks: { orderBy: [{ page: 'asc' }, { id: 'asc' }], select: { id: true, page: true, bbox: true, role: true, text: true } }
    }
  });
  if (!doc) notFound();

  const grouped = Array.from(
    doc.blocks.reduce((m, b) => {
      const arr = m.get(b.page) || [];
      arr.push(b);
      m.set(b.page, arr);
      return m;
    }, new Map<number, typeof doc.blocks>())
  );

  return (
    <main className="max-w-5xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-2">{doc.title}</h1>
      <p className="text-sm text-gray-500 mb-4">{doc.pages ? `${doc.pages} pages` : 'Unknown pages'}</p>
      <OverlayPdf docId={doc.id} pages={doc.pages ?? undefined} />
      <DocClient docId={doc.id} blockCount={doc.blocks.length} pages={doc.pages ?? undefined} />
      <div className="space-y-6">
        {grouped.map(([page, blocks]) => (
          <div key={page} className="border rounded p-4">
            <h2 className="font-semibold text-lg mb-2">Page {page}</h2>
            <ul className="space-y-2">
              {blocks.map((b) => (
                <li key={b.id} id={`b-${b.id}`} className="border-b pb-2 target-highlight">
                  <span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded mr-2 uppercase">{b.role}</span>
                  {b.text ? (
                    <span className="text-sm">{b.text.length > 150 ? b.text.slice(0, 147) + '…' : b.text}</span>
                  ) : (
                    <span className="text-sm text-gray-500 italic">(no text)</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </main>
  );
}
