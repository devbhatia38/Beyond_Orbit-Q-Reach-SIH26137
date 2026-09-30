import { prisma } from './src/lib/db';
import crypto from 'crypto';
import { verifyOtp } from './src/actions/verifyOtp';

async function simulateReoptimizeRace(batchId: string, currentVersion: number) {
  // 1. Fetch batch
  const batch = await prisma.routeBatch.findUnique({
    where: { id: batchId },
    include: { stops: true }
  });

  if (!batch) return { success: false, error: "Batch not found." };

  const deliveredLoad = batch.stops
    .filter(s => s.status === 'DELIVERED')
    .reduce((acc, s) => acc + s.loadWeight, 0);
  
  const remainingCapacity = Math.max(0, batch.originalCapacity - deliveredLoad);
  const pendingStops = batch.stops.filter(s => s.status === 'PENDING');

  console.log(`[Re-Opt Process] Captured state: remainingCapacity=${remainingCapacity}, pendingStops=${pendingStops.length}`);

  // 2. Simulate Python API delay (3 seconds)
  console.log(`[Re-Opt Process] Calling Python API (Simulated 3s delay)...`);
  await new Promise(resolve => setTimeout(resolve, 3000));
  console.log(`[Re-Opt Process] Python API returned successfully.`);

  // 3. Atomic Write
  console.log(`[Re-Opt Process] Attempting to write with version constraint = ${currentVersion}...`);
  const updateResult = await prisma.routeBatch.updateMany({
    where: {
      id: batchId,
      version: currentVersion
    },
    data: {
      version: { increment: 1 },
      optimizedDistance: 9999,
    }
  });

  if (updateResult.count === 0) {
    return { success: false, error: "Route was modified by a driver during optimization. Please refresh and try again." };
  }
  return { success: true, message: "Successfully re-optimized route!" };
}

async function runTest() {
  console.log("--- Starting Concurrency Race Condition Test ---");
  
  const otpSecret = process.env.OTP_SECRET || "default_secret_for_hackathon";
  const dummyOtp = "123456";
  const dummyHash = crypto.createHmac("sha256", otpSecret).update(dummyOtp).digest("hex");

  // Create a new batch with 2 stops
  const batch = await prisma.routeBatch.create({
    data: {
      demoPrefix: "RACE-TEST",
      originalCapacity: 100,
      version: 1,
      stops: {
        create: [
          { status: 'PENDING', loadWeight: 30, otpHash: dummyHash, otpExpiresAt: new Date(Date.now() + 600000) },
          { status: 'PENDING', loadWeight: 40, otpHash: dummyHash, otpExpiresAt: new Date(Date.now() + 600000) }
        ]
      }
    },
    include: { stops: true }
  });

  console.log(`Initial Batch Version: ${batch.version}`);

  // Fire both processes concurrently
  // 1. Admin triggers re-opt at t=0
  const reoptPromise = simulateReoptimizeRace(batch.id, batch.version);

  // 2. Driver delivers a package at t=1s (while re-opt is inflight)
  setTimeout(async () => {
    console.log(`[Driver Process] Delivering stop ${batch.stops[0].id}...`);
    const res = await verifyOtp(batch.stops[0].id, dummyOtp);
    console.log(`[Driver Process] verifyOtp returned: success=${res.success}`);
  }, 1000);

  // Wait for re-opt to finish
  const reoptRes = await reoptPromise;
  console.log(`\n[Re-Opt Final Result]: success=${reoptRes.success}, msg='${reoptRes.error || reoptRes.message}'`);

  const finalBatch = await prisma.routeBatch.findUnique({ where: { id: batch.id } });
  console.log(`Final Batch Version: ${finalBatch?.version}`);

  // --- Happy Path Scenario ---
  console.log("\n--- Starting Happy Path Test ---");
  const happyBatch = await prisma.routeBatch.create({
    data: {
      demoPrefix: "HAPPY-TEST",
      originalCapacity: 100,
      version: 1,
      stops: {
        create: [
          { status: 'PENDING', loadWeight: 30, otpHash: dummyHash, otpExpiresAt: new Date(Date.now() + 600000) }
        ]
      }
    },
    include: { stops: true }
  });

  console.log(`Initial Batch Version: ${happyBatch.version}`);
  const happyReoptPromise = simulateReoptimizeRace(happyBatch.id, happyBatch.version);
  
  // No driver interference here!
  
  const happyReoptRes = await happyReoptPromise;
  console.log(`\n[Re-Opt Final Result]: success=${happyReoptRes.success}, msg='${happyReoptRes.error || happyReoptRes.message}'`);

  const finalHappyBatch = await prisma.routeBatch.findUnique({ where: { id: happyBatch.id } });
  console.log(`Final Batch Version: ${finalHappyBatch?.version}`);
}

runTest()
  .catch(e => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });
