## Commander.js and Process Signals — Summary

**Commander provides no signal handling or cleanup mechanism.** Handling it yourself was the right call.

### What Commander does

- Parses CLI arguments into options, commands, and arguments
- Manages `--help`, `--version`, parse errors (via `.exitOverride()` if you want to intercept those)
- Forwards signals to child processes **only** when using stand-alone executable subcommands (the two-argument `.command('name', 'description')` form)
- Offers `preAction`/`postAction` lifecycle hooks, but these are not signal-aware

### What Commander does not do

- Listen for `SIGINT`/`SIGTERM` on your behalf (except the narrow executable-subcommand case above)
- Provide any shutdown, cleanup, or graceful-exit abstraction
- Support async cleanup on exit (`.exitOverride()` is synchronous; async support is an [open feature request](https://github.com/tj/commander.js/issues/2446))

### The correct pattern

Two independent layers, both your responsibility:

1. **`await using` / `Symbol.asyncDispose`** — handles cleanup on normal scope exit (exceptions, early returns). The language does the `finally` for you.

2. **`process.on('SIGINT' / 'SIGTERM')` handlers** — handles cleanup when the process is killed externally. Signals bypass normal scope unwinding, so dispose blocks won't run; you need explicit handlers.

This is especially important for your Puppeteer case, where Chrome child processes aren't reliably terminated by Node's own signal propagation and you need to track and kill PIDs yourself.