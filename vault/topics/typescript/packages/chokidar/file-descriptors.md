---
id: 019d8def-4088-74cc-9a4f-00ef550dbaa2
references: []
---

# Chokidar and file descriptors

Notes on **`EMFILE` / “too many open files”**, how **watching** relates to FDs and **kernel watch limits**, and **practical mitigations** with tradeoffs. For general Node FD lifecycle, see [Node.js: file descriptors and handles](../../../backend/node/file-handles.md).

---

## Concepts

### What `EMFILE` means

**`EMFILE`** means the process tried to open another **file descriptor** but hit the **per-process soft limit** on open FDs (`RLIMIT_NOFILE`, often surfaced as **`ulimit -n`**). It aggregates **files**, **sockets**, **pipes**, **watch-related handles**, and similar—not “only chokidar.”

### FD limit vs “unused headroom”

Raising **`ulimit -n`** sets a **ceiling**, not a pre-allocation. **Unused** high limits are usually **cheap**; **cost** appears when the process **actually opens** many FDs (buffers, kernel objects, sockets, etc.).

### Watchers vs “one FD per watched file”

**Chokidar** (via **`fs.watch`** / platform backends) does **not** map 1:1 to “number of leaf files” in every OS mode:

- **macOS** often uses **FSEvents**-style behavior behind **`fs.watch`**—more **aggregated** than naive “one handle per file” for huge trees.
- **Linux** often involves **inotify**; limits frequently track **watches** (often **per directory** in recursive setups), sometimes surfacing as **`ENOSPC`** (“no space left on device”) for the **inotify** subsystem—not the same errno as **`EMFILE`**, but the same class of “too much watching.”
- **`usePolling: true`** avoids relying on native event watches for those paths; it **polls** (e.g. periodic **`stat`** / directory reads). That changes **which** subsystem is stressed (see below).

So: **FD / watch pressure scales with backend, tree shape, and options**—not strictly “file count” alone.

### `usePolling` and FD / watch pressure

| Aspect | Theory | Tradeoff |
|--------|--------|----------|
| **Linux inotify** | Polling avoids consuming **inotify watches** the same way native **`fs.watch`** does. | **Mitigates** “too many watches” / inotify exhaustion. |
| **`EMFILE` from native watchers** | Polling can **reduce** persistent watch-related handles in some workloads. | **Not** a universal fix if **`EMFILE`** is dominated by **sockets**, **leaked streams**, or **mass concurrent `open`**. |
| **Cost** | Work moves to **periodic scanning** (`stat` / readdir-style work). | **Higher CPU**, **slower** change detection, worse **battery** on laptops—classic **space vs time** tradeoff. |

### Moving files out of the watched tree

**`fs.watch`** returns an **`fs.FSWatcher`**; resources are **released when the watcher is `close()`d** (or the process exits). **Do not assume** that moving/renaming a path **automatically** tears down every kernel/libuv resource without a **close**.

**Chokidar** updates its internal tree when it **sees** unlink/rename events and **should** drop subsidiary watchers—but **edge cases** (racy moves, symlinks, missed events) exist. Treat **explicit close** (Chokidar’s teardown / `close()`) as the reliable contract.

### Raising the FD limit: “cost”

| Effect | Notes |
|--------|--------|
| **Higher ceiling** | Lets legitimate workloads (dev servers, tests, many parallel connections) proceed. |
| **Delayed failure on leaks** | Leaks hit **`EMFILE`** later; symptoms may become **memory** / **slowness** instead. |
| **Wider blast radius** | A runaway process can open **more** FDs before failing—**stability** tradeoff, not a per-slot RAM bill for unused limit. |
| **System-wide** | Many processes each opening **lots** of FDs can stress **global** kernel limits—relevant at **scale**, rarely for a single local Node dev process. |

---

## Practical recommendations

### 1. Confirm what failed

- **`EMFILE` / “too many open files”** → per-process FD cap or true exhaustion.
- **Linux `ENOSPC` on watch** → often **inotify max watches** (`fs.inotify.max_user_watches`)—**polling** or **fewer watch roots** address a different layer than **`ulimit`**.

### 2. See who holds FDs

Use **`lsof -p <pid>`** (or Activity Monitor / Instruments) and group by **type**: regular files, **TCP**, **pipe**, etc. If **sockets** dominate, **chokidar isn’t the main story**.

### 3. Reduce watch surface (best bang for buck)

- **`ignored`**: exclude **`node_modules`**, build output, `.git`, huge assets, generated trees.
- **Narrow `cwd` / roots**: watch **one package** or **src/** instead of the whole monorepo root when possible.
- **Fewer parallel tools** each running their own watcher (multiple dev servers, duplicate tooling).

**Why it works:** fewer paths imply fewer native watches / less traversal and less concurrent short-lived opens during scans.

**Tradeoff:** more config and occasional “why didn’t it reload?” when something ignored changes.

### 4. Polling (`usePolling: true`)

**When:** Linux **inotify** pressure, or native watch FD pressure you **measure** as watcher-related.

**Why:** shifts work from **kernel watch tables** to **periodic filesystem checks** (see table above).

**Tradeoff:** **CPU**, **latency**, **battery**; use only where needed or for specific paths.

### 5. Raise `ulimit -n` (especially on macOS dev)

**When:** legitimate concurrency (tests, dev server, many files briefly open) hits **`EMFILE`**.

**Why:** raises the **soft limit** so the process may open more FDs **without** changing app code.

**Tradeoff:** masks **leaks** longer; ensure **launch environment** (Terminal vs IDE vs `launchd`) actually inherits the limit you think—**same** binary can see **different** limits.

### 6. Fix leaks and cap concurrency

- **Streams / `FileHandle` / raw `fd`**: ensure **`close()`** / **`destroy()`** on long-lived paths; see [file-handles.md](../../../backend/node/file-handles.md).
- **Parallel `readFile` / glob / copy**: many overlapping ops ⇒ many **short-lived** FDs at once—**throttle** or reduce parallelism.

### 7. Don’t rely on `mv` to free watchers

After large tree renames, prefer **restarting** the watcher or ensuring your tool **closes** old watchers; don’t assume **`mv`** alone guarantees cleanup.

---

## Short checklist

1. **Identify** errno (`EMFILE` vs Linux inotify `ENOSPC`).
2. **Measure** with **`lsof`**—watchers vs sockets vs files.
3. **Shrink** watch roots and **`ignore`** heavy directories.
4. **Consider** **`usePolling`** for inotify/native watch pressure; accept **CPU** cost.
5. **Raise** **`ulimit -n`** for dev if appropriate; **don’t** use it as the only fix for leaks.
6. **Close** long-lived handles explicitly; **cap** concurrent file-heavy work.
