import AdobeViewerClient from './Client';

export default async function Page() {
  return (
    <main className="max-w-6xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Adobe Viewer (GCS JSON)</h1>
      <div className="mb-3 text-sm text-gray-600">Отобразите прямоугольники (bbox) по выбранному артефакту Adobe из GCS.</div>
      <AdobeViewerClient />
    </main>
  );
}

