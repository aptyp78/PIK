"use client";
import { useEffect, useState } from 'react';

type Doc = { key: string; filename: string|null; fileId: string|null; count: number };

export default function ResultsClient() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [active, setActive] = useState<Doc | null>(null);
  const [entities, setEntities] = useState<any>(null);
  const [blocks, setBlocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const r = await fetch('/api/results/docs');
      const j = await r.json();
      if (j?.ok) setDocs(j.items || []);
    })();
  }, []);

  async function openDoc(d: Doc) {
    setActive(d); setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (d.fileId) qs.set('fileId', d.fileId);
      else if (d.filename) qs.set('filename', d.filename);
      const [e, b] = await Promise.all([
        fetch(`/api/results/entities?${qs.toString()}`).then(r=>r.json()),
        fetch(`/api/results/blocks?limit=200&${qs.toString()}`).then(r=>r.json()),
      ]);
      setEntities(e?.ok ? e : null);
      setBlocks(b?.ok ? (b.items || []) : []);
    } finally { setLoading(false); }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-1 border rounded p-3 max-h-[75vh] overflow-auto">
        <div className="font-semibold mb-2">Документы</div>
        <ul className="space-y-1 text-sm">
          {docs.map((d)=> (
            <li key={d.key} className={`px-2 py-1 rounded cursor-pointer ${active?.key===d.key?'bg-blue-50':''}`} onClick={()=>openDoc(d)}>
              <div className="truncate" title={d.filename || d.fileId || d.key}>{d.filename || d.fileId || d.key}</div>
              <div className="text-xs text-gray-500">points: {d.count}</div>
            </li>
          ))}
        </ul>
      </div>
      <div className="md:col-span-2 space-y-4">
        <div className="border rounded p-3">
          <div className="font-semibold mb-2">Сущности</div>
          {!entities ? (
            <div className="text-sm text-gray-500">{loading ? 'Загрузка…' : 'Выберите документ'}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              {entities.entities?.map((g:any,i:number)=> (
                <div key={i} className="border rounded p-2">
                  <div className="font-medium mb-1">{g.type} · {g.total}</div>
                  <ul className="text-xs space-y-0.5 max-h-40 overflow-auto">
                    {g.top.map((t:any,j:number)=> (<li key={j} className="flex justify-between"><span className="truncate pr-2" title={t.text}>{t.text}</span><span>{t.count}</span></li>))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="border rounded p-3">
          <div className="font-semibold mb-2">Блоки</div>
          <ul className="space-y-1 text-sm max-h-[45vh] overflow-auto">
            {blocks.map((b:any)=> (
              <li key={b.id} className="border rounded px-2 py-1"><span className="text-xs text-gray-500 mr-2">p{String(b.page)}</span>{String(b.text||'').slice(0,300)}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

