async function fetchStatus() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || ''}/api/pipeline/gdrive/adobe/status`, { cache: 'no-store' });
  try { return await res.json(); } catch { return { ok:false }; }
}

export default async function Page() {
  const j = await fetchStatus();
  return (
    <main className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Adobe Results (Drive → Adobe)</h1>
      <div className="mb-3 text-sm text-gray-600">Папка: GDRIVE_ADOBE_FOLDER_ID • Файлов: {j?.count ?? 0}</div>
      {!j?.ok ? (
        <div className="p-3 border rounded bg-red-50 text-red-700">Не удалось получить статус Adobe‑папки</div>
      ) : (
        <ul className="space-y-1 text-sm">
          {(j.files || []).slice(0, 200).map((f: any) => (
            <li key={f.id} className="border rounded px-2 py-1 flex justify-between"><span>{f.name}</span><span className="text-gray-500">{f.mimeType}</span></li>
          ))}
        </ul>
      )}
    </main>
  );
}

