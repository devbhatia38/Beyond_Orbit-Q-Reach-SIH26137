import { PrismaClient } from '@prisma/client';
import { verifyOtp } from './src/actions/verifyOtp';
import crypto from 'crypto';

const prisma = new PrismaClient();

async function runTest() {
  console.log("--- Starting OTP Security Hardening Test ---");
  
  // Clean up any previous test data
  await prisma.oTPVerificationLog.deleteMany({});
  await prisma.deliveryStop.deleteMany({});
  
  const otpSecret = process.env.OTP_SECRET || "default_secret_for_hackathon";
  
  // The correct OTP for our test stops
  const correctOtp = "123456";
  const validHash = crypto.createHmac("sha256", otpSecret).update(correctOtp).digest("hex");
  
  // Future expiry for testing
  const futureDate = new Date(Date.now() + 10 * 60 * 1000); // +10 mins

  // --- Scenario 1: Failed Attempts & Lockout ---
  console.log("\n[Scenario 1] Failed Attempts & Lockout");
  const stop1 = await prisma.deliveryStop.create({
    data: {
      otpHash: validHash,
      otpExpiresAt: futureDate,
    }
  });

  // 1-4 failures
  console.log("Simulating 4 failed attempts...");
  for (let i = 1; i <= 4; i++) {
    const res = await verifyOtp(stop1.id, "000000");
    console.log(`Attempt ${i}: success=${res.success}, error='${res.error}'`);
  }
  
  let dbStop = await prisma.deliveryStop.findUnique({ where: { id: stop1.id } });
  console.log(`DB State: otpAttempts=${dbStop?.otpAttempts}, lockedUntil=${dbStop?.lockedUntil}`);

  // 5th failure -> triggers lockout
  console.log("\nSimulating 5th failed attempt (should trigger lockout)...");
  const res5 = await verifyOtp(stop1.id, "000000");
  console.log(`Attempt 5: success=${res5.success}, error='${res5.error}'`);
  
  dbStop = await prisma.deliveryStop.findUnique({ where: { id: stop1.id } });
  console.log(`DB State: otpAttempts=${dbStop?.otpAttempts}, lockedUntil=${dbStop?.lockedUntil}`);

  // 6th attempt (even if correct) -> blocked by lockout
  console.log("\nSimulating 6th attempt with CORRECT OTP (should be blocked by lockout)...");
  const res6 = await verifyOtp(stop1.id, correctOtp);
  console.log(`Attempt 6: success=${res6.success}, error='${res6.error}'`);

  
  // --- Scenario 2: Successful Verification ---
  console.log("\n[Scenario 2] Successful Verification");
  const stop2 = await prisma.deliveryStop.create({
    data: {
      otpHash: validHash,
      otpExpiresAt: futureDate,
    }
  });

  console.log("Verifying with correct OTP...");
  const successRes = await verifyOtp(stop2.id, correctOtp);
  console.log(`Attempt: success=${successRes.success}, message='${successRes.message}'`);

  dbStop = await prisma.deliveryStop.findUnique({ where: { id: stop2.id } });
  console.log(`DB State: status=${dbStop?.status}, otpAttempts=${dbStop?.otpAttempts}`);
  
  // Check logs
  const logs = await prisma.oTPVerificationLog.findMany();
  console.log(`\nTotal OTP Verification Logs in DB: ${logs.length}`);
  const successLogs = logs.filter(l => l.success).length;
  console.log(`Successful Logs: ${successLogs}, Failed Logs: ${logs.length - successLogs}`);
}

runTest()
  .catch(e => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });
