export default function BMExportPage() {
  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Export</h1>
      <p className="mb-4 text-sm">Скачать JSON‑экспорт с текущими данными зон и base64 постером.</p>
      <a className="px-4 py-2 border rounded bg-white" href="/api/bm/export">Скачать</a>
    </main>
  );
}

