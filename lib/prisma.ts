import { PrismaClient } from '@prisma/client';

/**
 * Singleton Prisma client for use in API routes and server components.
 *
 * Next.js' hot-reloading can create multiple instances of PrismaClient if
 * instantiated in each request.  To avoid exhausting database connections
 * or re-creating clients in development, this module exports a single
 * instance.  See https://www.prisma.io/docs/orm/prisma-client/setup-and-usage
 * for more details.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const globalForPrisma: any = globalThis as unknown as { prisma?: PrismaClient };

export const prisma: PrismaClient =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'info', 'warn', 'error'] : ['error']
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
