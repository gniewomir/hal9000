
# Redis: memory and disk

## Theory

**Memory** — Normal reads and writes operate on data held in RAM. That is Redis’s primary model; latency and capacity are dominated by RAM.

**Disk** — Redis does not persist every operation to disk unless persistence is enabled. Disk use is for **durability** and **recovery**, not for serving hot data.

**Persistence modes**

- **None** — No routine data writes for recovery. Minimal disk I/O from persistence (aside from logs or other stack components).
- **RDB** — Point-in-time **snapshots** of the full dataset (`BGSAVE` forks a child; writes a binary dump). Frequency is **rule-based** (`save` seconds/changes), **manual** (`SAVE` / `BGSAVE`), or tied to shutdown/replication behavior—not a fixed global “every N ms.” On **restart**, Redis **loads** the last good RDB into RAM (full restore of that snapshot’s keys), so the instance can be **warmer** than empty—but only **as stale as** the time since that snapshot (plus anything that never reached disk).
- **AOF** — **Append-only log of write commands**. Appends happen as writes occur; **durability of what hits stable storage** depends on `appendfsync`. **AOF rewrite** periodically compacts the file (bursty extra I/O).

**Write frequency (disk)** — Not one number: it is **RDB schedule + workload**, or **AOF append rate + `appendfsync` + rewrite policy**, plus temporary files during `BGSAVE` / AOF rewrite.

**Bounding RAM** — Use `maxmemory` to cap the dataset Redis will hold under eviction rules; some overhead (clients, buffers) exists beyond strict “key bytes.” Replication adds nuances for eviction on replicas.

---

## Configuration (related options)

### Memory

| Option | Role |
|--------|------|
| `maxmemory` | Upper bound for the managed dataset (`0` = no limit on many installs). |
| `maxmemory-policy` | At limit: `noeviction` (reject writes) vs eviction (`allkeys-*`, `volatile-*`, LRU/LFU/random/TTL). |
| `replica-ignore-maxmemory` | Whether replica honors `maxmemory` for eviction (replication consistency vs local cap). |

### RDB

| Option | Role |
|--------|------|
| `save <seconds> <changes>` | Auto snapshot when **both** conditions for that line match (time window and write count—see `redis.conf` on your version); multiple lines allowed. |
| `save ""` | Disable automatic RDB saves (no schedule; snapshots only via manual `SAVE`/`BGSAVE` or other triggers). |
| `dir` | Directory for RDB (and AOF). |
| `dbfilename` | RDB filename (e.g. `dump.rdb`). |
| `rdbcompression` | Compress strings in dump (smaller file, more CPU). |
| `rdbchecksum` | Checksum on load for corruption detection. |
| `stop-writes-on-bgsave-error` | Stop writes if background save failed (avoid silent loss of snapshots). |
| `rdb-save-incremental-fsync` | Spread fsync during RDB write to reduce latency spikes. |

**Longest interval between automatic RDB snapshots** — Use a single `save` line with a **very large** `seconds` and the **smallest** `changes` you can accept (often `1`). The upper bound is whatever integer the server allows for `seconds` (often on the order of `2^31 - 1` seconds in typical builds). For **no** automatic RDB at all, use `save ""`.

### AOF

| Option | Role |
|--------|------|
| `appendonly` | Enable AOF. |
| `appendfsync` | `always` (fsync per write), `everysec` (~1s window), `no` (OS buffers). |
| `auto-aof-rewrite-percentage` / `auto-aof-rewrite-min-size` | When to trigger AOF rewrite. |

RDB and AOF can be combined; startup recovery follows Redis’s documented order for your version.

---

## Containers and process death

**Warm restart** — If a **completed** RDB (or AOF, per your setup) exists on disk when Redis starts, the dataset is **loaded into memory**; you get a **partially warm** cache compared to a blank instance, but values are **only as fresh as** the last successful persistence.

**Docker / orchestration** — The file must **survive** container replacement: map or mount a **volume** (or otherwise persistent storage) for `dir`. An ephemeral container filesystem alone often **loses** `dump.rdb` → next start is **cold**.

**SIGKILL / crash** — Does not flush RAM to disk; recovery uses the **last good** RDB/AOF already on disk (Redis normally writes snapshots atomically via rename).

**TTLs and loading RDB** — Expiry is stored as **absolute** expire time (not merely “TTL seconds at save”). After load, Redis compares **current time** to each key’s expiry:

- If expiry is **already in the past** at startup, the key is **not** kept as live data — it is treated as **expired** and removed (this is **expiration**, not `maxmemory` **eviction**, which is a separate mechanism).
- Keys that **would have expired while Redis was down** therefore do not reappear as valid entries if their timestamp is before `now`.
- Keys that were **already expired before the snapshot** was taken are usually **absent from the RDB** (they were no longer in the keyspace when the dump was produced).

Large **clock jumps** after restart can change which keys appear expired relative to wall time.
