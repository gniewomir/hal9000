<!-- 
tags: node, async
status: draft
-->

# Explicit Resource Management (`using` / `await using`)

## The core idea

Many resources — database connections, file handles, browser contexts, locks — need to be cleaned up after use. Traditionally you wrap them in `try/finally`:

```ts
const conn = await pool.getConnection();
try {
  await conn.query("SELECT 1");
} finally {
  await conn.release();
}
```

This works, but it's fragile. If you juggle multiple resources, the nesting explodes. If a new team member forgets the `finally`, you leak resources. The pattern can't compose — each caller has to know the cleanup details.

**Explicit Resource Management** (the TC39 proposal, now at Stage 3) introduces `using` and `await using` declarations. When the variable goes out of scope, the runtime calls its dispose method automatically — the language does the `finally` for you:

```ts
await using conn = await pool.getConnection();
await conn.query("SELECT 1");
// conn[Symbol.asyncDispose]() is called automatically when this block exits
```

No `finally`. No forgetting. Cleanup is guaranteed by the language, even when exceptions are thrown.

## How it works

### The `Disposable` and `AsyncDisposable` protocols

An object is disposable if it implements one of two well-known symbols:

| Protocol | Symbol | Method signature | Declaration |
|---|---|---|---|
| `Disposable` | `Symbol.dispose` | `[Symbol.dispose](): void` | `using x = ...` |
| `AsyncDisposable` | `Symbol.asyncDispose` | `[Symbol.asyncDispose](): Promise<void>` | `await using x = ...` |

When the block containing a `using` or `await using` declaration exits — whether normally, via `return`, or via a thrown exception — the runtime calls the dispose method. Multiple resources are disposed in **reverse declaration order** (LIFO), matching the intuition that later resources may depend on earlier ones.

### Scope rules

`using` and `await using` are block-scoped, like `const`. The dispose happens at the end of the enclosing block:

```ts
{
  await using a = getResourceA();
  await using b = getResourceB();
  // use a and b
} // b is disposed, then a is disposed
```

This also works inside `for`, `for...of`, `switch`, and any other block. Each loop iteration disposes resources acquired during that iteration.

## TypeScript and Node.js requirements

| Requirement | Minimum version |
|---|---|
| TypeScript | 5.2+ |
| Node.js | 22+ (stable), 18.x/20.x with `--harmony-dispose` flag |
| `tsconfig.json` `lib` | Must include `"esnext.disposable"` (or `"esnext"`) |

Typical `tsconfig.json` addition:

```json
{
  "compilerOptions": {
    "lib": ["ES2022", "esnext.disposable"]
  }
}
```

If you target older runtimes, you may need a polyfill for `Symbol.dispose` / `Symbol.asyncDispose` (e.g. the `disposablestack` npm package).

## Practical examples

### 1. Database connection

```ts
class PoolConnection implements AsyncDisposable {
  private conn: Connection;

  constructor(conn: Connection) {
    this.conn = conn;
  }

  async query(sql: string) {
    return this.conn.query(sql);
  }

  async [Symbol.asyncDispose]() {
    await this.conn.release();
  }
}

async function getConnection(pool: Pool): Promise<PoolConnection> {
  const conn = await pool.getConnection();
  return new PoolConnection(conn);
}

// Usage — connection is always released
async function loadUser(pool: Pool, id: string) {
  await using conn = await getConnection(pool);
  return conn.query("SELECT * FROM users WHERE id = ?", [id]);
}
```

### 2. Temporary file

```ts
import { open, unlink } from "node:fs/promises";

async function withTempFile(path: string) {
  const handle = await open(path, "w");
  return {
    handle,
    async [Symbol.asyncDispose]() {
      await handle.close();
      await unlink(path);
    },
  };
}

async function processData() {
  await using tmp = await withTempFile("/tmp/work.dat");
  await tmp.handle.write("intermediate results");
  // file is closed and deleted when the block exits
}
```

### 3. Wrapping a third-party resource (e.g. Playwright browser)

When you don't control the class, return a composite object:

```ts
export async function browserContext(logger: ILogger): Promise<BrowserContext & AsyncDisposable> {
  const browser = await chromium.launch();
  const context = await browser.newContext();

  return {
    ...context,
    async [Symbol.asyncDispose]() {
      await context.close();
      await browser.close();
      logger.info("Browser disposed");
    },
  };
}

async function scrape(url: string, logger: ILogger) {
  await using ctx = await browserContext(logger);
  const page = await ctx.newPage();
  await page.goto(url);
  return page.content();
}
```

### 4. `DisposableStack` / `AsyncDisposableStack`

When you need to compose multiple disposables into a single unit, or add cleanup callbacks ad-hoc:

```ts
async function pipeline() {
  await using stack = new AsyncDisposableStack();

  const db = stack.use(await getConnection(pool));
  const cache = stack.use(await openCache());
  stack.defer(async () => {
    await flushMetrics();
  });

  // all three cleanups run (in reverse order) when the block exits
}
```

`stack.use()` adopts an existing disposable. `stack.defer()` registers an arbitrary callback. The stack itself is `AsyncDisposable`, so `await using` handles it.

## The `for` loop combinations

Both iteration and disposal can be sync or async independently, giving four valid combinations:

| Syntax | Iteration | Disposal |
|---|---|---|
| `for (using x of y)` | sync | sync |
| `for await (using x of y)` | async | sync |
| `for (await using x of y)` | sync | async |
| `for await (await using x of y)` | async | async |

The position of `await` tells you *what* is async: `for await` means the iterator is async, `await using` means disposal is async.

## Caveats

**1. `await using` only works in async functions.**
If you try `await using` in a synchronous function, it's a syntax error. Use `using` with `Symbol.dispose` for synchronous cleanup, or restructure to an async context.

**2. Dispose errors can mask the original error.**
If the body throws and then dispose *also* throws, the behaviour follows a `SuppressedError` model. The original error becomes `SuppressedError.suppressed` and the dispose error becomes `SuppressedError.error`. This is by design, but you should make dispose methods robust — catch and log internally rather than letting them throw.

**3. `null` and `undefined` are silently skipped.**
`using x = null` and `await using x = undefined` are valid — no dispose is called. This is intentional (it lets factories return `null` to mean "nothing to clean up"), but it can hide bugs if you expected a resource.

**4. You cannot re-assign a `using` binding.**
Like `const`, the binding is read-only. You can't do `using x = a; x = b;`. If you need to swap resources, use a `DisposableStack`.

**5. The binding must be a simple identifier.**
Destructuring is not supported: `using { handle } = getResource()` is a syntax error. You must assign the whole object: `using res = getResource()` and then access `res.handle`.

**6. `Symbol.dispose` and `Symbol.asyncDispose` are not interchangeable.**
`using` only calls `Symbol.dispose`. `await using` only calls `Symbol.asyncDispose`. If your object only has `Symbol.asyncDispose`, you must use `await using`. If it has both, `await using` calls `Symbol.asyncDispose` and `using` calls `Symbol.dispose`.

**7. Polyfill landscape is still settling.**
Older Node.js versions and some bundlers don't support the symbols natively. Check your target runtimes and add polyfills if needed. TypeScript emits the syntax as-is — it does not downlevel `using`/`await using`.

**8. Top-level `await using` requires ESM.**
If you're using CommonJS modules, top-level `await using` won't work. You need ESM (`"type": "module"` in `package.json`) or wrap it in an async IIFE.

## Documentation

- [TC39 Proposal: Explicit Resource Management](https://github.com/tc39/proposal-explicit-resource-management)
- [MDN: `await using`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/await_using)
- [MDN: `using`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/using)
- [MDN: `Symbol.asyncDispose`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/asyncDispose)
- [MDN: `Symbol.dispose`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/dispose)
- [TypeScript 5.2 Release Notes — `using` Declarations](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html)
- [Node.js docs: `Symbol.asyncDispose` support](https://nodejs.org/docs/latest/api/globals.html#symbolasyncDispose)
