export default function DemoPage() {
  async function ingestAction() {
    'use server';
    const { demoIngest } = await import('@/lib/demo/ingestSamples');
    const r = await demoIngest();
    return r;
  }

  const DemoClient = require('./DemoClient').default as (props: { ingest: () => Promise<any> }) => JSX.Element;
  return <DemoClient ingest={ingestAction} />;
}

