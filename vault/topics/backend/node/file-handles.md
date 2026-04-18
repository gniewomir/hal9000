
## When FDs are acquired

Roughly: **whenever something in Node opens a resource** that maps to an OS object.


| Area                   | Typical acquisition                                                                                                                                            |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `**fs`**               | `fs.open` / `fs.openSync` → you get a numeric `fd`. `fs.promises.open()` → a `**FileHandle**` (wraps an `fd` internally).                                      |
| **Streams from paths** | `fs.createReadStream` / `createWriteStream` open the file (unless you pass an existing `fd`).                                                                  |
| **Network**            | `net.createServer`, `net.connect`, `dgram.createSocket`, `tls`, `http`/`https` servers and requests — sockets get FDs.                                         |
| **Child processes**    | `child_process` spawns processes and often **pipes** for `stdio`; those pipes are FDs.                                                                         |
| **Standard I/O**       | `process.stdin`, `process.stdout`, `process.stderr` are normal FDs (usually 0, 1, 2). The process does not “create” them in the Node sense; they’re inherited. |
| **Watching**           | `fs.watch` / `fs.watchFile` use OS-specific mechanisms; they hold resources (sometimes extra FDs or kernel watches).                                           |
| **Misc**               | IPC, some cluster/worker setups, TTYs, etc.                                                                                                                    |


Acquisition happens at `open`, `connect`, `listen`, `spawn` (with pipes), and similar — not in some mysterious lazy way: the syscall (or libuv equivalent) runs when that API runs (modulo connection state for TCP: you may get an FD at connect/listen time depending on path).

---

## When FDs are released

**Rule of thumb:** the FD is freed when the **owning API is closed** and **nothing else duplicates the FD**.

### Explicit close (preferred and clearest)

- `**fs.close(fd, cb)`** / `**fs.closeSync(fd)**` — releases that numeric `fd`.
- `**FileHandle.close()**` — closes the underlying `fd` (and invalidates the handle).
- **Streams:** `ReadStream` / `WriteStream` often call `fs.close` on the `fd` when:
  - the stream ends or errors, **and** `autoClose` is `true` (default for file streams opened by path), **or**
  - you call `.destroy()` / `.close()` where applicable.

If you passed an **external `fd`** into a stream, Node may **not** close it by default — you own it.

- **Sockets:** `server.close()`, `socket.destroy()`, etc., release the socket’s FD when libuv/OS cleanup completes.

### Garbage collection (only for some types — do not rely on it)

For `**fs.promises.FileHandle`**, Node treats **not calling `close()`** as a problem: it can emit **deprecation/runtime warnings** if a `FileHandle` is finalized by GC without being closed, because **GC is not a substitute for deterministic cleanup**. Always `await fileHandle.close()` (or `finally`).

Plain numeric `fd`s from `fs.open` **do not** get magically closed when variables go out of scope — **there is no automatic `close` on GC for raw numbers**.

---

## Lifecycle and the event loop

Open FDs (especially sockets and active libuv handles) participate in **keeping the process alive**: libuv **refs** active handles so the event loop does not exit while work might still happen. Closing releases that ref (for that handle). That’s why “closing the server/socket/stream” affects **shutdown**, not just kernel bookkeeping.

---

## Practical summary

1. **Acquired** when you open files, create sockets/pipes, spawn children with stdio, etc.
2. **Released** when you **close/destroy** the corresponding Node abstraction or call `**fs.close`** on a raw `fd` you own.
3. **Raw `fd`:** you must `**fs.close`** — GC won’t do it.
4. `**FileHandle`:** always `**close()`** in a `try/finally`; don’t rely on GC.
5. **Streams:** understand `**autoClose`** and whether you **passed in** an `fd` (you may still own it).

---

## One-shot `fs` APIs (`readFile`, `writeFile`, `cp`, `exists`, etc.)

For `**readFile` / `writeFile` / `cp` / `rm` / `mkdir` / `rename`** (sync and async), you almost never **see** an FD: Node opens whatever it needs **inside** the implementation, does the work, then **closes** before returning (sync) or before the completion callback / promise resolves (async). You do **not** call `close()` yourself.

So: **FDs are acquired for the duration of that single operation and released when that operation finishes** (success or failure), unless the implementation documents otherwise (it usually doesn’t for these helpers).

### Per-function behavior (conceptually)


| API                               | FDs in play                                                                                                                                                                                                                                                                                     |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `**readFile` / `readFileSync`**   | Opens the file (or uses an internal path), reads, then closes. **Short-lived FD** for that read.                                                                                                                                                                                                |
| `**writeFile` / `writeFileSync`** | Opens (and may create/truncate depending on flags), writes, closes. **Short-lived FD**.                                                                                                                                                                                                         |
| `**cp` / `cpSync`**               | Opens source (and destination as needed), copies (or uses a fast path like `copy_file` on some OSes where applicable), then closes. **Temporary FD(s)** for the copy.                                                                                                                           |
| `**rm` / `rmSync`**               | Unlinks / removes trees; uses directory iteration and `unlink` / `rmdir`-style operations. **No “keep this file open” FD** for normal files beyond what’s needed momentarily inside the implementation (e.g. while walking a directory).                                                        |
| `**mkdir` / `mkdirSync`**         | `**mkdir**`-style syscalls on paths. **Not** “open a FileHandle and return it”; no long-lived user-visible FD.                                                                                                                                                                                  |
| `**rename` / `renameSync`**       | `**rename**` syscall. **No** persistent open file FD for the data path in the typical case.                                                                                                                                                                                                     |
| `**existsSync`**                  | Implemented with a **metadata check on the path** (e.g. `stat`/`lstat`-style), not “open file for reading and leave it open.” **No** lingering FD for file content. (Same idea for async `**fs.exists`** if you use it — though the async `exists` API has been discouraged in docs for years.) |


So: **only the read/write/copy-style helpers routinely “open a file” in the sense of an FD for I/O**. The rest are mostly path operations or unlink trees.

### Sync vs async (for FD lifetime)

- `***Sync`**: FDs are held **only for the time that synchronous function runs** on the JS thread (plus any native work it does before return). When the function returns, the implementation has already closed what it opened (normal path).
- **Async** (`fs.promises.readFile`, `fs.readFile` with callback, etc.): An FD exists **from when the libuv/native layer opens the file until that one operation completes**. You still don’t manage it; Node closes it when the op finishes.

### What this means in practice

1. **No explicit acquire/release** for these APIs — unlike `fs.open()` / `FileHandle`.
2. **Leaks** from “forgetting to close” usually **don’t** apply here; leaks more often come from **streams**, **servers**, **raw `fd`s**, or **long-lived `FileHandle`s**.
3. **Concurrency** still matters: many concurrent `**readFile`** / `**writeFile**` calls means **many FDs open at once**, each until its own operation ends — you can hit `**EMFILE` “too many open files”** under load if `ulimit -n` is low. That’s “many short-lived FDs overlapping,” not “forgot to close one handle.”

### Caveats

- If you pass an **existing `fd`** or `**FileHandle**` into APIs that accept them (e.g. some `**readFile**` / stream constructors), **FD ownership rules** follow what those APIs document — you may still own the `fd` / handle.
- `**fs.watch`** / watchers are a different story: they keep a **persistent** resource (and sometimes FDs) until you **stop** the watcher.

