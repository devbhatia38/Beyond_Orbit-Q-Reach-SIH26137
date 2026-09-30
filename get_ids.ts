import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
async function main() {
  const batch = await prisma.routeBatch.findFirst({ include: { stops: true } });
  if (batch) {
    console.log('Batch ID:', batch.id);
    console.log('Tracking Token (Stop ID):', batch.stops[0].id);
  }
}
main().finally(() => prisma.$disconnect());
