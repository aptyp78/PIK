"use client";

import Link from 'next/link';
import { useEffect, useState, useTransition } from 'react';

type DemoIngestResult = import('@/lib/demo/ingestSamples').DemoIngestResult;

async function getDocsSummary(): Promise<{
  count: number;
  last?: { id: number; pages: number | null };
  lastBlocks?: number;
}> {
  try {
    const res = await fetch('/api/docs', { cache: 'no-store' });
    if (!res.ok) return { count: 0 };
    const json = (await res.json()) as { documents: { id: number; pages: number | null }[] };
    const docs = json.documents || [];
    const count = docs.length;
    const last = docs.sort((a, b) => b.id - a.id)[0];
    let lastBlocks: number | undefined;
    if (last) {
      const dres = await fetch(`/api/docs/${last.id}`, { cache: 'no-store' });
      if (dres.ok) {
        const dj = (await dres.json()) as { blocks: unknown[]; pages: number | null };
        lastBlocks = Array.isArray(dj.blocks) ? dj.blocks.length : undefined;
      }
    }
    return { count, last: last ? { id: last.id, pages: last.pages ?? null } : undefined, lastBlocks };
  } catch {
    return { count: 0 };
  }
}

function Tile({ title, value, hint }: { title: string; value: string; hint?: string }) {
  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
      {hint && <div className="text-xs text-gray-400 mt-1">{hint}</div>}
    </div>
  );
}

export default function DemoClient({ ingest }: { ingest: () => Promise<DemoIngestResult> }) {
  const [tiles, setTiles] = useState<{ docs: number; last?: { id: number; pages: number | null }; lastBlocks?: number }>({ docs: 0 });
  const [message, setMessage] = useState<string | null>(null);
  const [lastDocId, setLastDocId] = useState<number | undefined>(undefined);
  const [searchSnippets, setSearchSnippets] = useState<{ id: number; docId: number; page: number; role: string; snippet: string | null }[]>([]);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    (async () => {
      const sum = await getDocsSummary();
      setTiles({ docs: sum.count, last: sum.last, lastBlocks: sum.lastBlocks });
      setLastDocId(sum.last?.id);
    })();
  }, []);

  const runIngest = () => {
    setMessage(null);
    startTransition(async () => {
      const r = await ingest();
      const okDocs = r.totalDocs;
      const blocks = r.totalBlocks;
      const pages = r.pagesMin != null && r.pagesMax != null ? `pages ${r.pagesMin}–${r.pagesMax}` : 'pages unknown';
      setMessage(`OK: ${okDocs} documents, ${blocks} blocks, ${pages}`);
      setLastDocId(r.lastDocId);
      const sum = await getDocsSummary();
      setTiles({ docs: sum.count, last: sum.last, lastBlocks: sum.lastBlocks });
    });
  };

  const runQuickSearch = async () => {
    try {
      const res = await fetch('/api/search?q=platform', { cache: 'no-store' });
      if (!res.ok) return;
      const json = await res.json();
      const results = (json?.results ?? []).slice(0, 5);
      setSearchSnippets(results);
    } catch {}
  };

  return (
    <main className="max-w-5xl mx-auto py-8 space-y-6">
      <h1 className="text-3xl font-bold">Demo</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Tile title="Documents" value={String(tiles.docs)} />
        <Tile
          title="Last Doc"
          value={tiles.last ? `#${tiles.last.id}` : '—'}
          hint={tiles.last ? `pages ${tiles.last.pages ?? 'unknown'}` : undefined}
        />
        <Tile title="Blocks in Last Doc" value={tiles.lastBlocks != null ? String(tiles.lastBlocks) : '—'} />
      </div>

      <div className="space-y-3">
        <button
          onClick={runIngest}
          disabled={isPending}
          className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
        >
          {isPending ? 'Ingesting…' : 'Ingest PIK Samples'}
        </button>
        {message && (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-green-800 text-sm">
            {message}{' '}
            <Link href="/docs" className="underline">Open Documents</Link>
            {lastDocId ? (
              <>
                {' · '}
                <Link href={`/docs/${lastDocId}`} className="underline">Last Doc #{lastDocId}</Link>
              </>
            ) : null}
          </div>
        )}
      </div>

      <div className="space-x-3">
        <Link href="/docs" className="px-4 py-2 rounded bg-gray-100 border">Open Documents</Link>
        <button onClick={runQuickSearch} className="px-4 py-2 rounded bg-gray-100 border">Quick Search: platform</button>
      </div>

      {searchSnippets.length > 0 && (
        <div className="border rounded p-4">
          <div className="font-semibold mb-2">Quick Search results (top 5)</div>
          <ul className="space-y-1 text-sm">
            {searchSnippets.map((s) => (
              <li key={s.id}>
                <span className="text-gray-500 mr-2">#{s.docId}/p{s.page}</span>
                <span className="uppercase bg-gray-100 rounded px-1 py-0.5 text-xs mr-2">{s.role}</span>
                <Link href={`/docs/${s.docId}`} className="underline">
                  {s.snippet || '(no text)'}
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-2 text-sm">
            <Link href="/api/search?q=platform" className="underline">all results</Link>
          </div>
        </div>
      )}

      <div className="text-sm text-gray-500">
        Diagnostics: {' '}
        <Link href="/api/health" className="underline">/api/health</Link>
        {' · '}
        <Link href="/api/diagnostics/pdfservices" className="underline">/api/diagnostics/pdfservices</Link>
      </div>
    </main>
  );
}
