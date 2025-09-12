async function fetchSample() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || ''}/api/qdrant/sample?limit=10`, { cache: 'no-store' });
  try { return await res.json(); } catch { return { ok:false }; }
}

export default async function Page() {
  const j = await fetchSample();
  return (
    <main className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Финальный результат</h1>
      <div className="mb-3 text-sm text-gray-600">Коллекция: {j?.collection || '—'} · Всего (оценка): {j?.count ?? '—'}</div>
      <div className="mb-4 text-sm text-gray-600">Просмотр примеров ниже. Отдельная визуализация будет позже.</div>
      {!j?.ok ? (
        <div className="p-3 border rounded bg-red-50 text-red-700">Не удалось получить sample из Qdrant</div>
      ) : (
        <div className="text-sm">
          <div className="font-medium mb-1">Примеры точек</div>
          <ul className="space-y-1">
            {(j.items || []).map((it: any, i: number) => (
              <li key={i} className="border rounded px-2 py-1"><div className="text-xs text-gray-500">{String(it.id)}</div><div className="text-xs">{String(it.payload?.text || '').slice(0, 160)}</div></li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
