import Link from 'next/link';

export default function Home() {
  return (
    <main className="max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-3">PIK‑AI</h1>
      <p className="mb-4">Uploads‑only: загрузите свой PDF или PNG на странице Upload. Система выполнит извлечение и откроет документ.</p>
      <ul className="list-disc pl-5 space-y-2">
        <li><Link href="/upload">/upload</Link> — загрузка файла (до 30 МБ).</li>
        <li><Link href="/docs">/docs</Link> — список документов.</li>
        <li><Link href="/api/search?q=platform">/api/search</Link> — простая текстовая поисковая выдача.</li>
        <li><Link href="/frames">/frames</Link> — фреймы PIK.</li>
        <li><Link href="/api/health">/api/health</Link> — здоровье сервиса.</li>
        <li><Link href="/api/diagnostics/pdfservices">/api/diagnostics/pdfservices</Link> — проверка соединения c Adobe PDF Services.</li>
      </ul>
    </main>
  );
}
