https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/await_using

```
G. using / Symbol.asyncDispose (modern TS approach)
If you're on Node 22+ and TypeScript 5.2+, you could make browserContext implement AsyncDisposable. Then await using ctx = await browserContext(logger) guarantees cleanup even on exceptions — the language does the finally for you:

export async function browserContext(logger: ILogger): Promise<BrowserContext & AsyncDisposable> {
  // ...
  return {
    withBrowser,
    closeBrowser: cleanup,
    [Symbol.asyncDispose]: cleanup,
  };
}
```

tsconfig.json
```
    "lib": ["ES2022", "esnext.disposable"],
```

In other words, all of the following four combinations are valid and do different things:

for (using x of y): y is synchronously iterated, yielding one result at a time, which can be disposed synchronously.
for await (using x of y): y is asynchronously iterated, yielding one result at a time after awaiting, but the result value can be disposed synchronously.
for (await using x of y): y is synchronously iterated, yielding one result at a time, but the result value can only be disposed asynchronously.
for await (await using x of y): y is asynchronously iterated, yielding one result at a time after awaiting, and the result value can only be disposed asynchronously.

# Insight 
* object goes out of scope, dispose function is called 
* dispose can be sync or async 