"use client";
import { useEffect, useState } from 'react';

type Doc = { id: number; title: string; pages: number | null };
type Report = {
  docId: number;
  engine: string | null;
  totalBlocks: number;
  tablesCount: number;
  avgBlockLen: number;
  emptyPagesShare: number;
};

export default function ComparePage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [a, setA] = useState<number | ''>('');
  const [b, setB] = useState<number | ''>('');
  const [ra, setRa] = useState<Report | null>(null);
  const [rb, setRb] = useState<Report | null>(null);

  useEffect(() => {
    (async () => {
      const res = await fetch('/api/docs', { cache: 'no-store' });
      const json = await res.json();
      setDocs((json.documents || []) as Doc[]);
    })();
  }, []);

  async function loadReport(id: number) {
    const r = await fetch(`/api/ingest/${id}/report`, { cache: 'no-store' });
    if (!r.ok) return null;
    return (await r.json()) as Report;
  }

  async function run() {
    setRa(null); setRb(null);
    if (typeof a === 'number') setRa(await loadReport(a));
    if (typeof b === 'number') setRb(await loadReport(b));
  }

  return (
    <main className="max-w-5xl mx-auto py-8 space-y-4">
      <h1 className="text-3xl font-bold">Compare</h1>
      <div className="flex flex-wrap items-center gap-3">
        <select className="border rounded px-2 py-1" value={a} onChange={(e)=>setA(Number(e.target.value)||'')}>
          <option value="">Select A</option>
          {docs.map(d => (<option key={d.id} value={d.id}>#{d.id} {d.title}</option>))}
        </select>
        <span className="text-gray-500">vs</span>
        <select className="border rounded px-2 py-1" value={b} onChange={(e)=>setB(Number(e.target.value)||'')}>
          <option value="">Select B</option>
          {docs.map(d => (<option key={d.id} value={d.id}>#{d.id} {d.title}</option>))}
        </select>
        <button className="px-3 py-1 border rounded" onClick={run}>Compare</button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[ra, rb].map((r, idx) => (
          <div key={idx} className="border rounded p-4 text-sm">
            {!r ? <div className="text-gray-500">No report</div> : (
              <ul className="space-y-1">
                <li><b>Doc:</b> #{r.docId}</li>
                <li><b>Engine:</b> {r.engine || 'n/a'}</li>
                <li><b>Blocks:</b> {r.totalBlocks}</li>
                <li><b>Tables:</b> {r.tablesCount}</li>
                <li><b>Avg block len:</b> {r.avgBlockLen}</li>
                <li><b>Empty pages share:</b> {(r.emptyPagesShare*100).toFixed(1)}%</li>
              </ul>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}

