
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