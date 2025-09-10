/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { domains: [] },
  reactStrictMode: true,
  // Ensure Prisma engines are included in production output file tracing
  experimental: {
    outputFileTracingIncludes: {
      '/**/*': [
        './node_modules/@prisma/client/**/*',
        './node_modules/.prisma/**/*',
      ],
    },
  },
};

// Debug helpers: log unhandled errors when server exits unexpectedly.
if (!process.env.SUPPRESS_UNHANDLED_LOG) {
  process.on('unhandledRejection', (e) => {
    // eslint-disable-next-line no-console
    console.error('[unhandledRejection]', e);
  });
  process.on('uncaughtException', (e) => {
    // eslint-disable-next-line no-console
    console.error('[uncaughtException]', e);
  });
  process.on('exit', (code) => {
    // eslint-disable-next-line no-console
    console.error('[process:exit]', code);
  });
}

module.exports = nextConfig;
