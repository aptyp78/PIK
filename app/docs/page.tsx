"use client";
import Link from 'next/link';
import { useEffect, useState } from 'react';

interface SourceDoc {
  id: number;
  title: string;
  type: string | null;
  path: string;
  pages: number | null;
}

export default function DocsIndex() {
  const [docs, setDocs] = useState<SourceDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [results, setResults] = useState<
    { id: number; docId: number; page: number; role: string; snippet: string | null }[]
  >([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/docs');
        if (res.ok) {
          const json = await res.json();
          const arr = (json.documents ?? []) as SourceDoc[];
          setDocs(arr.sort((a, b) => b.id - a.id));
        } else {
          setError(`Error loading documents: ${res.status}`);
        }
      } catch (err: any) {
        setError(err?.message ?? 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <main className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4">Uploaded Documents</h1>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          if (res.ok) {
            const json = await res.json();
            setResults((json?.results ?? []).slice(0, 10));
          }
        }}
        className="mb-6 flex gap-2"
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search…"
          className="border rounded px-3 py-2 w-full"
        />
        <button type="submit" className="px-4 py-2 rounded bg-gray-100 border">Search</button>
      </form>
      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && docs.length === 0 && (
        <div className="p-6 border rounded bg-gray-50">
          <div className="mb-2">No documents uploaded yet.</div>
          <a href="/upload" className="inline-block px-4 py-2 rounded bg-blue-600 text-white">Upload file</a>
        </div>
      )}
      {!loading && docs.length > 0 && (
        <ul className="divide-y divide-gray-200">
          {docs.map((doc) => (
            <li key={doc.id} className="py-2">
              <Link href={`/docs/${doc.id}`}>{doc.title}</Link>
              <span className="text-sm text-gray-500 ml-2">
                {doc.pages ? `${doc.pages} pages` : 'Unknown pages'}
              </span>
              <span className="ml-3 text-sm">
                <Link href={`/api/ingest/${doc.id}/report`} className="underline" target="_blank">Report</Link>
              </span>
            </li>
          ))}
        </ul>
      )}
      {results.length > 0 && (
        <div className="mt-6 border rounded p-4">
          <div className="font-semibold mb-2">Search results</div>
          <ul className="space-y-1 text-sm">
            {results.map((r) => (
              <li key={r.id}>
                <span className="text-gray-500 mr-2">#{r.docId}/p{r.page}</span>
                <span className="uppercase bg-gray-100 rounded px-1 py-0.5 text-xs mr-2">{r.role}</span>
                <Link href={`/docs/${r.docId}`} className="underline">{r.snippet || '(no text)'}</Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
