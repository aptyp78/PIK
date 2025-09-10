/*
 * Seed script for populating the PIK methodology definitions.
 *
 * To run this script, first run `npx prisma migrate dev` to create
 * the SQLite database, then execute `npm run prisma:generate` to
 * generate the Prisma client.  Finally, run:
 *
 *   npx ts-node prisma/seed.ts
 *
 * This script inserts a single methodology and its frames/fields
 * corresponding to the PIK v5.0 definitions.
 */

import { PrismaClient } from '@prisma/client';
import { frames } from '../lib/data/frames';

async function main() {
  const prisma = new PrismaClient();
  // Create or find the methodology using the compound unique key (title, version)
  const methodology = await prisma.methodology.upsert({
    where: {
      title_version: {
        title: 'PIK v5.0',
        version: '5.0'
      }
    },
    update: {},
    create: { title: 'PIK v5.0', version: '5.0' }
  });
  // Insert frames and fields
  for (const [order, frame] of frames.entries()) {
    const createdFrame = await prisma.frame.upsert({
      where: { slug: frame.slug },
      update: {},
      create: {
        methodologyId: methodology.id,
        name: frame.name,
        slug: frame.slug,
        order
      }
    });
    for (const [fOrder, fieldName] of frame.fields.entries()) {
      const slug = `${frame.slug}-${fieldName.toLowerCase().replace(/\s+/g, '-')}`;
      await prisma.field.upsert({
        where: { slug },
        update: {},
        create: {
          frameId: createdFrame.id,
          name: fieldName,
          slug,
          order: fOrder
        }
      });
    }
  }
  await prisma.$disconnect();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
