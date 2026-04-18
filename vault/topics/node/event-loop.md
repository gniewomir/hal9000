---
id: 019da1b7-1e65-7098-af89-e2e25f1ea935
references: []
---

# Node.js event loop

## Short explanation (layman terms)

Node runs your JavaScript on a **single thread** for ordinary application code, yet it can serve many concurrent connections and overlap slow work (disk, network, timers) without dedicating one OS thread per request. The mechanism is an **event loop**: a repeating cycle that asks, in effect, “what is ready now?”—completed I/O, expired timers, scheduled callbacks—and then runs the matching JavaScript in **short turns**, one callback batch at a time.

Picture a **restaurant with one waiter** on the floor. The waiter does not stand at table A until the kitchen finishes table A’s dish. They take orders, hand tickets to the kitchen, visit other tables, and return when food is **ready**. Here the “kitchen” is largely **the operating system and native code** (surfaced through **libuv**), and the waiter is the loop **dispatching your callbacks** when work completes or timers fire. Your JS never “waits” inside the CPU in the same way a blocking `read()` would; instead, you **register continuations** and the loop invokes them when the world has moved forward.

That model trades away **easy parallelism on one thread** for **cheap concurrency**: many operations in flight, little per-connection thread overhead. The flip side is anything that **keeps the waiter busy**—long synchronous CPU work, accidental tight `nextTick` loops—delays **every** other table: timers slip, sockets backlog, health checks fail. Understanding the loop is how you decide **where to defer**, **what to move off-thread**, and **why ordering of `setImmediate` vs `setTimeout(0)` vs microtasks** sometimes matters.

## Theory (precise)

**Runtime model.** Node embeds **V8** for JavaScript execution and **libuv** for a cross-platform **event loop**, async I/O, and a **thread pool** used for some APIs (notably parts of `fs`, DNS, and CPU work offloaded by native addons). User JS for a given Node process runs on the **main thread** unless you use **worker threads** or **child processes**.

**Phases (Node’s ordering).** The main loop advances through **phases**, each draining a queue of callbacks tied to that phase (see Node’s docs for the authoritative list):

1. **Timers** — `setTimeout` / `setInterval` callbacks whose targets have been reached. Delays are **minimum**; exact ordering between competing timers is not a hard real-time guarantee.
2. **Pending callbacks** — certain I/O callbacks deferred from the prior iteration.
3. **Idle, prepare** — internal libuv hooks.
4. **Poll** — wait for I/O (when appropriate), retrieve events, run I/O-related callbacks. This phase is where much network/disk completion work surfaces.
5. **Check** — `setImmediate` callbacks.
6. **Close callbacks** — e.g. `socket.on('close', ...)`.

**Microtasks between phases.** After a phase runs its **macrotask** callbacks, Node drains **microtasks** in a strict order: the **`process.nextTick`** queue runs **before** **promise microtasks** (`queueMicrotask`, `Promise` reactions). Recursive `nextTick` scheduling can run **before the event loop continues to the next phase**, which is why **`nextTick` can starve I/O** if misused.

**Blocking.** Any **long synchronous** CPU work on the main thread prevents the loop from advancing: pending I/O may sit undrained, timers fire late, and `setImmediate` waits. The thread pool can complete background tasks, but **their JavaScript callbacks still run on the main thread** unless you structured work otherwise.

**Process lifetime.** The process exits when there is **no remaining work** keeping the event system alive: no active handles, timers, etc., modulo how specific APIs **ref** or **unref** handles. This ties to libuv’s notion of active handles (see in-repo notes on handles).

**Limits and assumptions.** Docs describe the **model**; wall-clock behavior depends on OS scheduler load, timer resolution, GC pauses, and V8. Do not assume **real-time** semantics from timers or phase ordering without reading the rules for your exact call site (e.g. top-level vs inside an I/O callback).

**In practice:** Operators and library authors use this theory to choose **scheduling primitives** (`setImmediate` after I/O vs `setTimeout(0)` vs microtasks), to interpret **latency histograms** (p99 spikes often correlate with long synchronous sections or GC), and to configure **observability** (loop delay metrics, `async_hooks` / `diagnostics_channel`, CPU profiles). When debugging “mysterious” ordering, you verify **which phase** and **microtask queues** ran between two log lines. When tuning servers, you watch **event-loop lag**, accept queue depth, and **thread-pool** saturation (e.g. `UV_THREADPOOL_SIZE`) as signals that the **model** is fighting your workload.

## Where it applies (examples)

- **Context:** HTTP/TCP server with many idle connections and occasional bursts. **What you do:** Use async APIs (`http.createServer`, `stream`/`pipeline`, `await` on promises) so each completion is a **callback turn**; add backpressure (`pause`/`resume`, `highWaterMark`) so you do not allocate unbounded buffers. **Why this concept:** The loop multiplexes readiness for many FDs on one thread; blocking reads would collapse throughput. **Tradeoffs / alternatives:** For CPU-heavy per-request work, use **worker threads** or a queue + pool; for isolation, separate processes.

- **Context:** You need “run after current stack, before paint/browser analog / before I/O” in a **library** that interoperates with promises. **What you do:** Use `queueMicrotask` or `Promise.resolve().then(...)` for promise-chained ordering; reserve `process.nextTick` for rare Node-specific edge cases where you must preempt the promise microtask queue (and document starvation risk). **Why this concept:** Microtasks run in a defined order relative to the macrotask phases. **Tradeoffs / alternatives:** Overuse of `nextTick` starves the loop; prefer `setImmediate` to **yield** a full iteration when batching work.

- **Context:** Deferring work to the **next iteration** after I/O (e.g. split large JSON parsing, batch DB writes). **What you do:** Schedule chunks with `setImmediate` (or `setTimeout` with a small delay if you need timer-phase behavior); keep each chunk’s synchronous work small enough to meet SLO. **Why this concept:** `setImmediate` runs in the **check** phase, after **poll**, which matches “after this I/O callback” in many server handlers. **Tradeoffs / alternatives:** If you only need microtask ordering inside one promise chain, microtasks may suffice; if you need wall-clock spacing, timers.

- **Context:** Writing a CLI tool that should exit when work finishes. **What you do:** Ensure timers and sockets are cleared/closed; use `unref()` on long-lived timers/sockets when they should not keep the process alive (if appropriate). **Why this concept:** Exit is tied to **active handles** and scheduled work, not merely “no user code running.” **Tradeoffs / alternatives:** Explicit `process.exit` skips normal cleanup—prefer draining work and closing handles.

- **Context:** Using `fs` or `dns` APIs that go through the **libuv thread pool**. **What you do:** Avoid blocking the main thread while many pool tasks queue; consider raising `UV_THREADPOOL_SIZE` for heavy synchronous-ish disk patterns (within reason) or restructuring. **Why this concept:** Pool threads complete work, but **callbacks still run on the main thread** in loop turns. **Tradeoffs / alternatives:** `fs.promises` vs sync `fs.*Sync` (never on request paths); for CPU-bound transforms, workers.

- **Context:** Testing timing-sensitive code (`setImmediate` vs `setTimeout(0)`). **What you do:** Write tests against **observable outcomes**, not internal phase order; if you must assert ordering, set up the **same entry context** Node documents (e.g. inside an I/O callback). **Why this concept:** Order between `setImmediate` and `setTimeout(fn,0)` **differs** between top-level and I/O contexts. **Tradeoffs / alternatives:** Fake timers (`@sinonjs/fake-timers`) for deterministic tests; avoid baking fragile phase assumptions into production logic.

- **Context:** Aggregating metrics and logs for “stalls.” **What you do:** Track **event loop delay** (e.g. `perf_hooks.monitorEventLoopDelay`), process CPU time, and GC; correlate spikes with deploys or specific routes. **Why this concept:** The loop is the shared choke point for **all** main-thread JS. **Tradeoffs / alternatives:** Sampling profilers vs continuous instrumentation (cost vs fidelity).

- **Context:** Graceful shutdown on SIGTERM. **What you do:** Stop accepting (`server.close`), drain in-flight requests with timeouts, close DB pools, then exit; optionally schedule final flushes with `setImmediate` after closing listeners. **Why this concept:** Close callbacks and remaining I/O tie to specific **phases** and handle lifetime; rushing `process.exit` drops work. **Tradeoffs / alternatives:** Orchestrators may kill before drain completes—design timeouts and idempotency.

## Common gotchas (examples)

- **Gotcha:** Relying on **`setTimeout(fn, 0)` vs `setImmediate(fn)`** order everywhere. **What goes wrong:** At **top level**, timers can run before `setImmediate`; **inside an I/O callback**, `setImmediate` often runs first. Tests pass in one context and fail in another. **What to do instead / how to verify:** Pick one mechanism for a given invariant; read Node’s ordering rules for your entry context; add logging of `performance.now()` ordering in both contexts if you must prove behavior.

- **Gotcha:** **Recursive `process.nextTick`.** **What goes wrong:** The `nextTick` queue empties before other phases proceed—**I/O and timers starve**, watchdogs fire, connections appear hung. **What to do instead / how to verify:** Replace with `setImmediate` for cooperative scheduling; if using `nextTick`, cap iterations per turn; reproduce with a tight `nextTick` loop and watch loop delay metrics explode.

- **Gotcha:** **CPU-heavy synchronous work** in request handlers (JSON parse huge payloads, image resize, regex catastrophes). **What goes wrong:** Single-digit-second stalls delay **all** clients; health endpoints fail; backlog grows. **What to do instead / how to verify:** Profile the handler (CPU flame graph); chunk work (`setImmediate`), stream, or move to **workers**; confirm with loop delay + request latency correlation.

- **Gotcha:** Treating **`setInterval`** as a **steady metronome**. **What goes wrong:** Intervals are **minimum** spacing; if a tick’s synchronous work exceeds the interval, ticks **pile up** or effectively serialize with drift. **What to do instead / how to verify:** Track **intended** vs **actual** elapsed (`Date.now()` / `performance.now()`); use a single timer that schedules the next after work completes for adaptive workloads.

- **Gotcha:** Assuming **microtasks always “run after the current callback”** in the way you expect across mixed APIs. **What goes wrong:** `nextTick` runs **before** promise microtasks; mixing `nextTick`, `queueMicrotask`, and `await` in one flow produces subtle orderings. **What to do instead / how to verify:** For a disputed sequence, write a minimal script that logs `nextTick`, `queueMicrotask`, and `Promise.resolve().then` in one turn; align library code with **one** deferral strategy.

- **Gotcha:** **Blocking the loop while waiting** on a **thread-pool** callback flood. **What goes wrong:** Pool tasks finish, but the main thread is busy, so **completion callbacks queue** and latency tails grow. **What to do instead / how to verify:** Watch queue depth / latency together; reduce per-callback synchronous work; consider fewer, larger batched operations.

## Related concepts

- **libuv** — The C library behind the loop, handles, and thread pool; reading its docs clarifies **poll**, **handles**, and why some `fs`/`dns` work behaves differently from pure sockets.
- **Microtasks vs macrotasks** — Promises/`queueMicrotask` vs timers/I/O/`setImmediate`; order determines observable sequencing and starvation risks with `nextTick`.
- **Worker threads** — Run JS in parallel **without** blocking the main loop; different isolation and messaging model than async I/O alone.
- **Child processes** — Offload work to another address space; useful when CPU isolation matters more than shared memory.
- **Streams and backpressure** — The loop delivers readiness, but streams enforce **how fast** you pull/push data; ignoring backpressure blows memory.
- **EventEmitter** — Callbacks for object-level events (e.g. `'data'`); orthogonal to the loop, but handlers run in normal JS turns.
- **`async_hooks` / `AsyncLocalStorage`** — Correlate async work across the loop; helps trace context loss bugs, with runtime cost.
- **Promise semantics and `await`** — Syntax sugar over microtasks and executor timing; pairs with loop behavior in `try/catch/finally` patterns.
- **File descriptors and handles** — What keeps the process alive and how closing interacts with shutdown; complements “why doesn’t Node exit?”

## References

- [The Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/the-node-js-event-loop) — official overview of phases and behavior.
- [Event loop timers and `process.nextTick`](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick) — timers, `setImmediate`, `nextTick`, microtasks.
- [Don’t Block the Event Loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop) — blocking patterns and mitigations.
- [libuv documentation](http://docs.libuv.org/en/latest/) — event loop, handles, thread pool.
- [`vault/topics/node/file-handles.md`](file-handles.md) — FDs, libuv handles, and process lifetime.
- [`vault/topics/node/events.md`](events.md) — `EventEmitter` patterns next to async code.
- [`vault/topics/node/try-catch-finally-await.md`](try-catch-finally-await.md) — how errors and `await` interact across turns.
- [`vault/topics/node/memory-managment.md`](memory-managment.md) — GC and retention with many concurrent operations.
