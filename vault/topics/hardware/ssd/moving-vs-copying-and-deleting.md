---
id: 019d87fd-eeee-71e9-b363-1e77875a63d5
references: []
---

# Moving vs copy + delete (typical filesystems)

On common setups—Linux with ext4 (ext3 behaves similarly for this), macOS with APFS (HFS+ was analogous)—**moving** and **copying then removing the source** differ mainly when the source and destination live on the **same mounted volume**.

## Same filesystem (same volume)

**Move (`rename`)** is usually a **metadata** operation. The kernel does not read and rewrite file contents. It updates directory entries (and inode link counts / parent pointers where needed): effectively “this name now points here” or “this directory entry moves.” For a single file that is a small number of inode and directory updates. For a directory tree, the kernel walks the tree and renames components; there is still **no bulk copy of file data blocks** for the ordinary case.

**Copy then delete** always **duplicates data** unless a tool uses a special mechanism (see below). It allocates new inodes and blocks, reads bytes from the source, writes them to the destination, then unlinks the source. Time and I/O scale with **data size**, not just path length.

So on the **same volume**, a move is normally **fast and cheap**; copy + delete is **slow and heavy** for large trees.

## Different filesystems or devices

If the destination is **another mount** (another disk, partition, or network volume), a single-filesystem **rename** cannot span devices. Tools like `mv` then **behave like** copy + unlink: same practical outcome as `cp -a` followed by `rm` for trees, modulo how each tool preserves metadata.

## Correctness and atomicity

- **Rename on one filesystem** is often **atomic** at the metadata level (one observable switch: old name gone, new name present), which matters for safe replacement patterns.
- **Copy then remove** introduces a **window**: duplicate data on disk, possible partial copy if interrupted, and ordering concerns if you care about never leaving both or neither in bad states (common pattern: copy to a temp name, then rename into place).

## Metadata and edge cases

- **Permissions, owners, timestamps, extended attributes, ACLs**: `cp` flags and `mv` / `cp -a` behavior differ; a naive copy might not match what `mv` preserves on one FS. Tools like `cp -a` or `rsync -a` aim to preserve more.
- **Hard links**: Moving within the same FS keeps one inode; copying creates a **new** file (new inode); link topology changes.
- **Symlinks**: `mv` moves the symlink entry; `cp` may copy the link or the target depending on flags.

## macOS APFS and Linux extras

**APFS** supports **file cloning** (copy-on-write): some copies can share blocks until one side is modified, so “copy” can be **faster and use less extra space** than a full duplicate—but you still get **new** files and directory entries unless you only renamed. **ext4** does not do that for ordinary `cp`; you get real duplication unless you use something like **reflinks** (`cp --reflink=auto` on a filesystem that supports it).

## SSDs

From the application’s perspective the distinction is unchanged: **rename** is mostly metadata I/O; **copy** is bulk read/write. SSDs make everything faster, but **relative** cost still differs a lot for large data.

## Short summary

- **Same volume:** move ≈ **rename** (metadata); copy + delete = **full data duplication** plus removal.
- **Across volumes:** move ≈ **copy + delete** in practice.
