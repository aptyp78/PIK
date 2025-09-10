"use client";
import { useEffect, useState } from 'react';

type Doc = { id: number; title: string; pages: number | null };
type Evidence = { blockId: number; page: number; bbox: [number,number,number,number]; textSnippet: string };
type Field = { name: string; value: string | null; evidence: Evidence[] };
type Frame = { slug: string; name: string; fields: Field[] };

export default function AutoAssignClient() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [docId, setDocId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [frames, setFrames] = useState<Frame[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/docs', { cache: 'no-store' });
        const json = await res.json();
        const arr = (json.documents || []) as Doc[];
        setDocs(arr);
        if (arr[0]) setDocId(arr[0].id);
      } catch {}
    })();
  }, []);

  async function run() {
    if (!docId) return;
    setLoading(true); setError(null);
    try {
      const res = await fetch(`/api/frames/autoassign?docId=${docId}`, { method: 'POST', cache: 'no-store' });
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error || `HTTP ${res.status}`);
      setFrames(json.frames as Frame[]);
    } catch (e: any) {
      setError(e?.message || 'Failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mb-6 border rounded p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="font-semibold">Auto-assign from document</div>
        <select className="border rounded px-2 py-1" value={docId ?? ''} onChange={(e)=>setDocId(Number(e.target.value))}>
          {docs.map(d => (<option key={d.id} value={d.id}>{d.id}: {d.title}</option>))}
        </select>
        <button className="px-3 py-1 border rounded" onClick={run} disabled={loading || !docId}>{loading ? 'Assigning…' : 'Run'}</button>
        {error && <span className="text-red-600">{error}</span>}
      </div>
      {frames && (
        <div className="space-y-6 text-sm">
          {frames.map(fr => (
            <div key={fr.slug} className="border rounded p-3">
              <div className="font-semibold mb-2">{fr.name}</div>
              <ul className="space-y-1">
                {fr.fields.map((f, idx) => (
                  <li key={`${fr.slug}-${idx}`} className="flex flex-col">
                    <div><span className="text-gray-600">{f.name}:</span> {f.value ? <span>{f.value}</span> : <span className="italic text-gray-500">—</span>}</div>
                    {f.evidence && f.evidence.length > 0 && (
                      <div className="text-xs text-gray-600">
                        Evidence: {f.evidence.map((ev, i) => (
                          <a key={i} className="underline mr-2" href={`/docs/${docId}#b-${ev.blockId}`}>b#{ev.blockId} p{ev.page}</a>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

