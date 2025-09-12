import FramesClient from './Client';

export default async function Page() {
  return (
    <main className="max-w-7xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Frames Overview</h1>
      <FramesClient />
    </main>
  );
}

