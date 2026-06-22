const fs = require('fs/promises');
const path = require('path');
const { performance } = require('perf_hooks');

const NUM_FILES = 10;
const READS_PER_FILE = 10; // 10 files * 10 reads = 100 total async reads

async function runBenchmark() {
  const dir = path.join(__dirname, 'test_data');
  await fs.mkdir(dir, { recursive: true });
  
  const buffer = Buffer.alloc(64 * 1024, 'gvisor-bench'); // 64KB chunks

  // ==========================================
  // SETUP PHASE: Write files before the timer
  // ==========================================
  const setupTasks = [];
  for (let i = 0; i < NUM_FILES; i++) {
    const file = path.join(dir, `test_${i}.txt`);
    setupTasks.push(fs.writeFile(file, buffer));
  }
  await Promise.all(setupTasks);

  // ==========================================
  // BENCHMARK PHASE: Only measure reads
  // ==========================================
  const start = performance.now();

  const readTasks = [];
  for (let i = 0; i < NUM_FILES; i++) {
    readTasks.push((async () => {
      const file = path.join(dir, `test_${i}.txt`);
      
      // Perform Async Reads
      for (let j = 0; j < READS_PER_FILE; j++) {
        await fs.readFile(file);
      }
    })());
  }

  await Promise.all(readTasks);
  
  const end = performance.now();
  // ==========================================

  // TEARDOWN PHASE: Clean up files
  const cleanupTasks = [];
  for (let i = 0; i < NUM_FILES; i++) {
    const file = path.join(dir, `test_${i}.txt`);
    cleanupTasks.push(fs.unlink(file));
  }
  await Promise.all(cleanupTasks);
  await fs.rmdir(dir);

  console.log(`Node Internal Run Time: ${(end - start).toFixed(2)} ms`);
}

runBenchmark().catch(console.error);

