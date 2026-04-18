
# Node.js memory management

## The mental model

Node.js memory is not "just the heap". A running process usually uses memory in a few distinct places:

- **Call stack**: local variables and function frames for currently executing code.
- **V8 heap**: JavaScript objects, arrays, closures, class instances.
- **External memory**: `Buffer`s, `ArrayBuffer`s, and native allocations attached to JS objects.
- **RSS**: the process's total resident memory from the OS perspective.

That distinction matters because apps often fail due to **RSS** or **external memory** growth even when normal JS heap usage looks reasonable.

## What V8 manages

V8 uses **garbage collection (GC)** to reclaim JS objects that are no longer reachable.

At a high level:

- **New space** holds short-lived objects.
- **Old space** holds objects that survive multiple GC cycles.
- Objects start young and get promoted if they live long enough.

This is why many healthy Node processes show a **sawtooth** memory pattern:

1. Requests allocate objects.
2. `heapUsed` grows.
3. GC runs.
4. `heapUsed` drops.

That pattern is normal. A problem starts when the **post-GC baseline** keeps rising.

## The numbers you will look at

`process.memoryUsage()` is the main runtime snapshot:

```js
console.log(process.memoryUsage());
```

Typical fields:

- `heapUsed`: memory currently used by live JS objects.
- `heapTotal`: heap space currently reserved by V8.
- `external`: memory attached to JS objects but allocated outside the JS heap.
- `arrayBuffers`: memory used by `ArrayBuffer`/`Buffer` backing stores.
- `rss`: total RAM currently occupied by the process.

Example formatter:

```js
const MB = 1024 * 1024;

function memorySnapshot() {
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
  console.log(new Date().toISOString(), memorySnapshot());
}, 5000);
```

## What gets reclaimed, and what does not

GC can reclaim only objects that are **no longer strongly reachable**.

That means this memory is collectible:

```js
function handleRequest() {
  const temp = new Array(100_000).fill("x");
  return temp.length;
}
```

After the function returns, `temp` can be collected because nothing keeps a reference to it.

This memory is **not** collectible:

```js
const cache = [];

function handleRequest(payload) {
  cache.push(payload);
}
```

`payload` is retained by the global `cache`, so memory will keep growing unless entries are removed.

## Common sources of memory pressure

### 1. Heap growth from retained objects

Typical causes:

- unbounded caches
- arrays/maps that only grow
- event listeners that are never removed
- timers that capture large closures
- request-scoped objects stored in global state

Leak example:

```js
const requests = new Map();

app.use((req, res, next) => {
  requests.set(req.id, { headers: req.headers, body: req.body });
  next();
});
```

If entries are never deleted, memory grows with traffic.

Safer pattern:

```js
const requests = new Map();

app.use((req, res, next) => {
  requests.set(req.id, { startedAt: Date.now() });
  res.on("finish", () => {
    requests.delete(req.id);
  });
  next();
});
```

### 2. Buffer and external memory growth

`Buffer`s are common in Node and often live **outside** the JS heap.

This can surprise people:

```js
const chunks = [];

stream.on("data", (chunk) => {
  chunks.push(chunk);
});
```

If the stream is large, `heapUsed` may stay moderate while `external`, `arrayBuffers`, and `rss` rise sharply.

Prefer streaming instead of accumulating:

```js
import { pipeline } from "node:stream/promises";
import fs from "node:fs";

await pipeline(
  incomingRequest,
  fs.createWriteStream("./upload.bin")
);
```

This keeps memory flatter because data is processed incrementally.

### 3. Large object lifetimes

Sometimes the code is not "leaking" but holds too much at once:

```js
const users = await db.loadAllUsers();
const csv = users.map(formatUser).join("\n");
await fs.promises.writeFile("users.csv", csv);
```

This creates multiple large in-memory structures at once.

A better approach is chunking or streaming:

```js
for await (const user of db.streamUsers()) {
  output.write(formatUser(user) + "\n");
}
```

### 4. Backpressure ignored

When producers are faster than consumers, memory grows because buffered data piles up.

Bad:

```js
readable.on("data", (chunk) => {
  writable.write(chunk);
});
```

Better:

```js
import { pipeline } from "node:stream/promises";

await pipeline(readable, writable);
```

`pipeline()` propagates errors and respects backpressure, which is one of the easiest ways to avoid accidental memory growth in Node.

## How garbage collection behaves in practice

A few practical truths are useful:

- GC is **automatic**, but not free.
- More live objects usually means more GC work.
- RSS often does **not** drop immediately after GC.
- V8 may keep memory reserved for future reuse instead of returning it to the OS.

So this is normal:

- `heapUsed` goes up and down.
- `rss` climbs and then plateaus above the original baseline.

This is suspicious:

- after forcing or waiting for GC, `heapUsed` keeps trending upward
- traffic is flat, but memory baseline keeps increasing
- `external` rises continuously because buffers are being retained

## Limits and tuning

Node's heap has limits. If the old-space heap cannot grow enough, the process may eventually fail with an out-of-memory error.

A common tuning flag is:

```bash
node --max-old-space-size=4096 app.js
```

That sets the old-space heap limit to roughly 4 GB.

Use it carefully:

- it can help legitimate high-memory workloads
- it does **not** fix leaks
- in containers, you must also respect container memory limits

## Debugging workflow

### Quick runtime logging

Start with periodic snapshots from `process.memoryUsage()`.

### Trace GC

```bash
node --trace-gc app.js
```

Useful when you want to see whether GC is frequent, expensive, or unable to bring usage down.

### Capture a heap snapshot

```js
import v8 from "node:v8";

const file = v8.writeHeapSnapshot();
console.log(file);
```

Then open the `.heapsnapshot` in Chrome DevTools and compare snapshots over time.

### Inspector

```bash
node --inspect app.js
```

Then use DevTools:

- **Heap snapshot** to find retained object graphs
- **Allocation sampling** to find hot allocation sites

For more detail on runtime measurement and RSS vs heap interpretation, see [Node.js: memory (heap, RSS) and runtime tracking](vault/topics/backend/node/debuging/memory.md).

## Rules of thumb

- Prefer streaming over buffering entire payloads.
- Put bounds and eviction on caches.
- Clean up listeners, timers, and request registries.
- Watch `external` and `rss`, not only `heapUsed`.
- If memory only grows under load, check buffering and backpressure first.
- If post-GC heap baseline grows, suspect retained references.

## Mini checklist

When memory grows, ask:

1. Is `heapUsed` growing, or mostly `rss` / `external`?
2. Does usage drop after GC, or does the baseline keep rising?
3. Are we buffering data that could be streamed?
4. Do we have unbounded caches, maps, arrays, or listeners?
5. Is the process inside a container with stricter memory limits than the heap size suggests?

## Documentation

- [Node.js docs: `process.memoryUsage()`](https://nodejs.org/api/process.html#processmemoryusage)
- [Node.js docs: V8 module](https://nodejs.org/api/v8.html)
- [Node.js guide: Using Heap Snapshot](https://nodejs.org/en/learn/diagnostics/memory/using-heap-snapshot)
- [Node.js guide: Understanding and Tuning Memory](https://nodejs.org/en/learn/diagnostics/memory/understanding-and-tuning-memory)
- [V8: Trash talk - the Orinoco garbage collector](https://v8.dev/blog/trash-talk)
