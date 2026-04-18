
# Node.js: memory (heap, RSS) and runtime tracking

## Core concepts (what the numbers mean)

Node’s `process.memoryUsage()` exposes several buckets. The two most important are **heap** and **RSS**.

### Heap (V8 heap)

**Heap** is memory managed by **V8** where **JavaScript objects** live.

- **`heapUsed`**: memory currently used by *live* JS objects (plus overhead).
- **`heapTotal`**: memory V8 has currently allocated/committed for the heap (capacity, not usage).

Typical behavior is **sawtooth**: `heapUsed` climbs with allocations, then drops after GC.

### RSS (resident set size)

**RSS** is the OS view of “how much RAM this process is currently occupying”.

`rss` includes **everything** mapped/resident for the process, not just JS objects:

- V8 heap (the heap buckets above)
- **native allocations** (C/C++ addons, OpenSSL, libc, etc.)
- **Buffers / ArrayBuffers** (often allocated “externally” to the JS heap)
- JIT code space, stacks, allocator arenas, fragmentation, memory maps

Important: `rss` often **does not drop** quickly even after GC, because memory can be retained for reuse by V8 / malloc (and the OS can keep pages resident).

### External / ArrayBuffers (common “RSS grows but heap doesn’t” culprit)

- **`external`**: memory used by V8 “external” allocations (e.g. many `Buffer`s).
- **`arrayBuffers`**: subset related to `ArrayBuffer` backing stores (can overlap with `external` depending on version).

If **`heapUsed` is stable** but **`rss` grows**, look at `external` / `arrayBuffers`, native modules, and allocator fragmentation.

---

## Quick runtime instrumentation (copy/paste)

### 1) Periodically log memory usage (human-friendly MB)

```js
// memory-log.js
const MB = 1024 * 1024;

function snapshot() {
  const m = process.memoryUsage();
  return {
    rssMB: +(m.rss / MB).toFixed(1),
    heapUsedMB: +(m.heapUsed / MB).toFixed(1),
    heapTotalMB: +(m.heapTotal / MB).toFixed(1),
    externalMB: +(m.external / MB).toFixed(1),
    arrayBuffersMB: +(m.arrayBuffers / MB).toFixed(1),
  };
}

setInterval(() => {
  console.log(new Date().toISOString(), snapshot());
}, 5000);
```

**How to use**: import it in your service entrypoint early, or gate it behind an env var.

### 2) Track “trend” (delta) instead of raw numbers

Raw values are noisy. A delta helps spot monotonic growth.

```js
// memory-trend.js
const MB = 1024 * 1024;
let prev = process.memoryUsage();

setInterval(() => {
  const cur = process.memoryUsage();
  const delta = Object.fromEntries(
    Object.entries(cur).map(([k, v]) => [k, (v - prev[k]) / MB])
  );
  console.log("ΔMB/interval", {
    rss: +delta.rss.toFixed(2),
    heapUsed: +delta.heapUsed.toFixed(2),
    external: +delta.external.toFixed(2),
    arrayBuffers: +delta.arrayBuffers.toFixed(2),
  });
  prev = cur;
}, 5000);
```

### 3) Sample after GC (reduce “temporary allocation” noise)

Run Node with `--expose-gc`, then:

```js
// memory-after-gc.js
const MB = 1024 * 1024;

setInterval(() => {
  if (global.gc) global.gc();
  const { rss, heapUsed, external } = process.memoryUsage();
  console.log("post-GC", {
    rssMB: +(rss / MB).toFixed(1),
    heapUsedMB: +(heapUsed / MB).toFixed(1),
    externalMB: +(external / MB).toFixed(1),
  });
}, 10000);
```

If **post-GC `heapUsed` grows steadily**, suspect a JS heap leak.

---

## CLI workflows (what to run in practice)

### 1) “Is GC happening?”: trace GC

Run:

```bash
node --trace-gc app.js
```

If you see frequent GC but memory still trends up, you likely have:

- a leak (objects strongly referenced), or
- growth outside the JS heap (Buffers/native), or
- fragmentation / retained capacity.

### 2) “What’s allocating?”: attach inspector and take heap snapshots

Run:

```bash
node --inspect app.js
```

Then open Chrome DevTools for Node (`chrome://inspect`) and:

- **Memory → Heap snapshot**: compare snapshots over time and look for growing object graphs.
- **Memory → Allocation sampling / instrumentation**: find allocation hot spots.

### 3) Write a heap snapshot from code (offline analysis)

```js
import v8 from "node:v8";

// Writes something like Heap.2026-04-13T12-34-56.789Z.heapsnapshot
const file = v8.writeHeapSnapshot();
console.log("heap snapshot:", file);
```

Open the `.heapsnapshot` in Chrome DevTools (Memory tab).

---

## OS / container perspective (RSS is what kills containers)

### 1) Check RSS from the OS

On macOS / Linux:

```bash
ps -o pid,rss,command -p <pid>
```

`rss` there is typically in **KB**.

### 2) In containers / Kubernetes

The process can be OOM-killed because **container memory** exceeds limits even if `heapUsed` looks fine.

- Watch **RSS / working set** metrics at the container level.
- If your app uses many `Buffer`s (streams, HTTP bodies, compression), monitor **`external`** and not only heap.

---

## Interpreting patterns (common cases)

### Case A: `heapUsed` sawtooths, `rss` slowly climbs and plateaus

Often **normal**: V8 and malloc keep memory for reuse; RSS might not return to baseline.

### Case B: `heapUsed` rises after each GC (post-GC baseline increases)

Usually a **JS heap leak** (something keeps references alive):

- caches without eviction
- global maps/arrays that only grow
- event listeners / timers not removed
- request-scoped objects stored in long-lived structures

### Case C: `heapUsed` stable, `external` + `rss` rise

Often **Buffer / native** pressure:

- accumulating `Buffer`s (e.g. storing request bodies, large responses)
- streams not drained / backpressure ignored
- native module allocations

### Case D: `rss` rises, everything else flat

Consider:

- allocator fragmentation
- mmap / file-backed mappings becoming resident
- many threads (worker threads) increasing stacks

---

## “Good enough” approach for production

- Log `process.memoryUsage()` periodically (RSS + heap + external).
- Add tags for load context (RPS, queue depth, active requests) so graphs are interpretable.
- When you see sustained growth, take **two heap snapshots** (before/after) and compare.

