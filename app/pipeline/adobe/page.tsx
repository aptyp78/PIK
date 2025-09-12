import AdobeGcsClient from './Client';

export default async function Page() {
  return (
    <main className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Adobe Results (GCS)</h1>
      <div className="mb-3 text-sm text-gray-600">Выберите файл для предпросмотра</div>
      <AdobeGcsClient />
    </main>
  );
}
