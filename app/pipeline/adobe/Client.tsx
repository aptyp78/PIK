"use client";
import { useEffect, useState } from 'react';

type Item = { name: string; size: number; updated?: string };

export default function AdobeGcsClient() {
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<Item | null>(null);
  const [preview, setPreview] = useState<any>(null);

  async function loadList() {
    setBusy(true); setError(null);
    try {
      const r = await fetch('/api/pipeline/gcs/adobe/status', { cache: 'no-store' });
      const j = await r.json();
      if (!j?.ok) throw new Error(j?.error || `HTTP ${r.status}`);
      setItems(j.files || []);
    } catch (e: any) { setError(e?.message || 'failed'); }
    finally { setBusy(false); }
  }

  async function openItem(it: Item) {
    setActive(it); setPreview(null); setBusy(true); setError(null);
    try {
      const r = await fetch(`/api/pipeline/gcs/adobe/get?name=${encodeURIComponent(it.name)}`, { cache: 'no-store' });
      const j = await r.json();
      if (!j?.ok) throw new Error(j?.error || `HTTP ${r.status}`);
      setPreview(j.json ?? j.raw ?? null);
    } catch (e: any) { setError(e?.message || 'failed'); }
    finally { setBusy(false); }
  }

  useEffect(() => { loadList(); }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="border rounded p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">Файлы</div>
          <button className="px-2 py-1 border rounded text-sm" onClick={loadList} disabled={busy}>Обновить</button>
        </div>
        {error && <div className="text-sm text-red-700 mb-2">{error}</div>}
        <ul className="space-y-1 max-h-[65vh] overflow-auto">
          {items.map((it) => (
            <li key={it.name} className={`px-2 py-1 border rounded cursor-pointer ${active?.name===it.name?'bg-blue-50':''}`}
                title={it.name}
                onClick={() => openItem(it)}>
              <div className="truncate">{it.name}</div>
              <div className="text-xs text-gray-500">{Math.round((it.size||0)/1024)} KB{it.updated?` • ${new Date(it.updated).toLocaleString()}`:''}</div>
            </li>
          ))}
        </ul>
      </div>
      <div className="border rounded p-3">
        <div className="font-semibold mb-2">Предпросмотр</div>
        {!active ? (
          <div className="text-sm text-gray-600">Выберите файл слева</div>
        ) : busy ? (
          <div className="text-sm text-gray-600">Загрузка…</div>
        ) : preview ? (
          <pre className="text-xs whitespace-pre-wrap break-all max-h-[65vh] overflow-auto">{JSON.stringify(preview, null, 2)}</pre>
        ) : (
          <div className="text-sm text-gray-600">Нет данных</div>
        )}
      </div>
    </div>
  );
}

