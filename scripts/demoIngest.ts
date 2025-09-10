import { demoIngest } from '../lib/demo/ingestSamples';

(async () => {
  const r = await demoIngest();
  // eslint-disable-next-line no-console
  console.log(JSON.stringify(r, null, 2));
})().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});

