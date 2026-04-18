---
id: 019d8c19-5313-71fb-8148-3b895a332dfa
references: []
---

# `await` in `try` / `catch` / `finally` (JavaScript / Node.js)

## The big rule

`finally` runs *before* the async function settles (resolves/rejects), even if the `try`/`catch` path did `return` or `throw`. If `finally` contains an `await`, it delays settlement.

### Key quirks of `await` inside `try / catch / finally`

- **`finally` always runs (even after `return`, `throw`, `break`, `continue`)**  
  If your `try` or `catch` returns/throws, JS *still* executes `finally` first.

- **If `finally` has `await`, it *delays* completion of the whole operation**  
  The function won’t resolve/reject until the awaited work in `finally` finishes.

- **A `throw` (or rejection) in `finally` overrides earlier results**  
  If `try` returned a value, but `finally` throws, the function rejects with the `finally` error (the return value is lost). Same if `catch` was about to rethrow—`finally` can replace that error.

- **A `return` in `finally` overrides earlier `return`/`throw`** (usually a footgun)  
  If you `return` from `finally`, it replaces whatever `try`/`catch` was going to do, including swallowing errors.

- **An `await` in `finally` can surface “cleanup failed” instead of the “real” error**  
  Example: `try` throws `E1`, `finally` awaits cleanup that rejects `E2` → caller typically sees `E2`. If you care about `E1`, you must preserve it intentionally.

- **Cancellation/abort semantics still run `finally`, but your cleanup must be abort-safe**  
  In browser/Node there’s no general promise cancellation; using `AbortController` doesn’t magically stop `finally`. Cleanup that awaits network/file ops can hang unless you time out / pass abort signals.

- **Unhandled rejection traps**  
  If you start async work in `finally` without awaiting it, and it rejects, you can get unhandled rejections. If you *do* await it, its failure can mask the original error (see above).

- **`catch` without rethrow changes control flow; `finally` doesn’t “restore” it**  
  If `catch` handles and returns, the error is gone; `finally` runs either way.

### Practical rules of thumb

- **Avoid `return` in `finally`.**
- **If cleanup failure shouldn’t mask the main failure, wrap cleanup in its own `try/catch` inside `finally`** and decide how to report it (log, attach as `cause`, etc.).
- **If you must preserve the original error**, store it and rethrow it after cleanup (or throw an aggregated error).

If you tell me whether you mean **JavaScript/TypeScript** (Node, browser, Deno) or another language, I can call out the language-specific edge cases (e.g., Python’s `try/finally` with `await`, C# `async`/`finally`, etc.).

## Footguns to remember

### 1) `await` in `finally` delays everything

```ts
async function f() {
  try {
    return 123;
  } finally {
    await new Promise((r) => setTimeout(r, 1000));
  }
}

await f(); // resolves ~1s later
```

### 2) A throw/rejection in `finally` overrides earlier return/throw

```ts
async function f() {
  try {
    throw new Error("original");
  } finally {
    await cleanup(); // if this rejects with "cleanup failed"...
  }
}

// Caller typically observes "cleanup failed", not "original".
```

### 3) `return` in `finally` overrides everything (swallows errors)

Avoid this pattern unless you *explicitly* want to swallow errors.

```ts
async function f() {
  try {
    throw new Error("boom");
  } finally {
    return "ok"; // swallows "boom"
  }
}
```

### 4) “Fire-and-forget” cleanup in `finally` risks unhandled rejections

```ts
async function f() {
  try {
    return await doWork();
  } finally {
    cleanupAsync(); // if it rejects => can become an unhandled rejection
  }
}
```

If you don’t want cleanup failure to affect the caller, still handle its errors explicitly.

## Safer patterns

### Pattern A: cleanup failure should NOT mask the original outcome

```ts
async function f() {
  try {
    return await doWork();
  } finally {
    try {
      await cleanupAsync();
    } catch (e) {
      // log/metric, but don't mask the original return/throw
      console.error("cleanup failed", e);
    }
  }
}
```

### Pattern B: preserve original error, but still fail if cleanup fails

If you want “either can fail” while still retaining the original error, use `Error` causes (or an aggregate-like error strategy).

```ts
async function f() {
  let original: unknown;
  try {
    return await doWork();
  } catch (e) {
    original = e;
    throw e;
  } finally {
    try {
      await cleanupAsync();
    } catch (cleanupErr) {
      if (original instanceof Error) {
        throw new Error("cleanup failed (original error preserved)", { cause: original });
      }
      throw cleanupErr;
    }
  }
}
```

## Operational notes (Node)

- `finally` + `await` can extend lifetimes of resources (locks, db conns) longer than you expect.
- If cleanup can hang (network/file), consider timeouts / abort signals so `finally` can’t stall the whole request forever.

