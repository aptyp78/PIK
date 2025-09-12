import TemplateEditorClient from './Client';

export default async function Page({ searchParams }: { searchParams: { [k: string]: string | undefined } }) {
  const template = searchParams?.template || 'PIK_PBM_v5';
  const name = searchParams?.name || '';
  return (
    <main className="max-w-7xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Template Editor</h1>
      <div className="mb-3 text-sm text-gray-600">Шаблон: {template} · Артефакт: {name ? decodeURIComponent(String(name)) : '—'}</div>
      <TemplateEditorClient name={decodeURIComponent(String(name))} templateId={String(template)} />
    </main>
  );
}
