---
id: 019d7a35-4574-73e5-a9ba-83d88cb92a57
references: []
---

# Data Structures Reference

Comprehensive reference of data structures with descriptions and time complexity.

**Legend:** `n` = number of elements, `k` = key length, `m` = pattern length, `h` = height of tree

---

## Arrays & Lists

### Array (Static)

Fixed-size contiguous block of memory. Elements accessed by index.

| Operation      | Average | Worst |
|----------------|---------|-------|
| Access         | O(1)    | O(1)  |
| Search         | O(n)    | O(n)  |
| Insert         | O(n)    | O(n)  |
| Delete         | O(n)    | O(n)  |

**Space:** O(n)

### Dynamic Array (ArrayList / Vector)

Resizable array that doubles capacity when full. Amortized O(1) append.

| Operation      | Average | Worst |
|----------------|---------|-------|
| Access         | O(1)    | O(1)  |
| Search         | O(n)    | O(n)  |
| Insert (end)   | O(1)*   | O(n)  |
| Insert (middle)| O(n)    | O(n)  |
| Delete         | O(n)    | O(n)  |

*amortized

**Space:** O(n)

### Singly Linked List

Linear sequence of nodes, each pointing to the next. No random access.

| Operation         | Average | Worst |
|-------------------|---------|-------|
| Access            | O(n)    | O(n)  |
| Search            | O(n)    | O(n)  |
| Insert (head)     | O(1)    | O(1)  |
| Insert (tail w/ pointer) | O(1) | O(1) |
| Insert (middle)   | O(n)    | O(n)  |
| Delete (head)     | O(1)    | O(1)  |
| Delete (middle)   | O(n)    | O(n)  |

**Space:** O(n)

### Doubly Linked List

Each node has pointers to both next and previous. Traversal in both directions.

| Operation         | Average | Worst |
|-------------------|---------|-------|
| Access            | O(n)    | O(n)  |
| Search            | O(n)    | O(n)  |
| Insert (head/tail)| O(1)    | O(1)  |
| Insert (middle)   | O(n)    | O(n)  |
| Delete (known node)| O(1)   | O(1)  |
| Delete (by value) | O(n)    | O(n)  |

**Space:** O(n)

### Circular Linked List

Last node points back to the head. Useful for round-robin scheduling and circular buffers.

Same complexity as Singly Linked List, but traversal wraps around.

**Space:** O(n)

### Skip List

Layered linked list with express lanes for faster search. Probabilistic alternative to balanced BSTs.

| Operation | Average    | Worst  |
|-----------|------------|--------|
| Access    | O(log n)   | O(n)   |
| Search    | O(log n)   | O(n)   |
| Insert    | O(log n)   | O(n)   |
| Delete    | O(log n)   | O(n)   |

**Space:** O(n log n)

---

## Stacks & Queues

### Stack (LIFO)

Last-In-First-Out. Push/pop from one end only. Used for recursion, undo, parsing.

| Operation | Average | Worst |
|-----------|---------|-------|
| Push      | O(1)    | O(1)  |
| Pop       | O(1)    | O(1)  |
| Peek      | O(1)    | O(1)  |
| Search    | O(n)    | O(n)  |

**Space:** O(n)

### Queue (FIFO)

First-In-First-Out. Enqueue at back, dequeue from front. Used for BFS, task scheduling.

| Operation | Average | Worst |
|-----------|---------|-------|
| Enqueue   | O(1)    | O(1)  |
| Dequeue   | O(1)    | O(1)  |
| Peek      | O(1)    | O(1)  |
| Search    | O(n)    | O(n)  |

**Space:** O(n)

### Deque (Double-Ended Queue)

Insert and remove from both ends. Generalizes both stack and queue.

| Operation          | Average | Worst |
|--------------------|---------|-------|
| Insert (front/back)| O(1)    | O(1)  |
| Remove (front/back)| O(1)    | O(1)  |
| Peek (front/back)  | O(1)    | O(1)  |
| Search             | O(n)    | O(n)  |

**Space:** O(n)

### Priority Queue (via Binary Heap)

Elements dequeued by priority, not insertion order. Backed by a heap.

| Operation    | Average    | Worst    |
|--------------|------------|----------|
| Insert       | O(log n)   | O(log n) |
| Extract-Min/Max | O(log n) | O(log n)|
| Peek Min/Max | O(1)       | O(1)     |
| Search       | O(n)       | O(n)     |

**Space:** O(n)

### Monotonic Stack / Queue

Stack/queue that maintains elements in sorted order. Used for next-greater-element problems, sliding window max/min.

| Operation | Amortized |
|-----------|-----------|
| Push      | O(1)      |
| Pop       | O(1)      |

**Space:** O(n)

---

## Hash-Based Structures

### Hash Table (HashMap / Dictionary)

Key-value store using a hash function to map keys to buckets. Average O(1) for most operations, degrades with collisions.

| Operation | Average | Worst |
|-----------|---------|-------|
| Search    | O(1)    | O(n)  |
| Insert    | O(1)    | O(n)  |
| Delete    | O(1)    | O(n)  |

**Space:** O(n)

Worst case occurs with pathological hash collisions. Resizing is amortized O(1).

### Hash Set

Stores unique values (no key-value pairs). Same mechanics as hash table.

| Operation | Average | Worst |
|-----------|---------|-------|
| Contains  | O(1)    | O(n)  |
| Add       | O(1)    | O(n)  |
| Remove    | O(1)    | O(n)  |

**Space:** O(n)

### Linked Hash Map / LinkedHashSet

Hash table that also maintains insertion order via a doubly linked list. Same O as hash table, but ordered iteration.

**Space:** O(n)

### Bloom Filter

Probabilistic set membership test. Can say "definitely not in set" or "probably in set." No false negatives, possible false positives. Cannot delete.

| Operation | Time |
|-----------|------|
| Add       | O(k) |
| Query     | O(k) |

k = number of hash functions. **Space:** O(m) where m = bit array size (much smaller than storing elements).

### Count-Min Sketch

Probabilistic frequency counter. Estimates how many times an element has been seen. Can overcount, never undercounts.

| Operation | Time |
|-----------|------|
| Add       | O(k) |
| Query     | O(k) |

**Space:** O(k × w) where w = width of each row.

### Cuckoo Filter

Similar to Bloom filter but supports deletion. Better space efficiency for low false-positive rates.

| Operation | Time |
|-----------|------|
| Add       | O(1) amortized |
| Query     | O(1) |
| Delete    | O(1) |

**Space:** O(n)

---

## Trees

### Binary Tree

Each node has at most two children. Foundation for many tree variants.

| Operation | Average | Worst |
|-----------|---------|-------|
| Search    | O(n)    | O(n)  |
| Insert    | O(n)    | O(n)  |
| Delete    | O(n)    | O(n)  |

**Space:** O(n)

### Binary Search Tree (BST)

Binary tree where left child < parent < right child. Efficient search when balanced.

| Operation | Average    | Worst |
|-----------|------------|-------|
| Search    | O(log n)   | O(n)  |
| Insert    | O(log n)   | O(n)  |
| Delete    | O(log n)   | O(n)  |

Worst case when tree degenerates into a linked list (sorted insertions).

**Space:** O(n)

### AVL Tree

Self-balancing BST. Heights of subtrees differ by at most 1. Stricter balance than Red-Black.

| Operation | Average    | Worst      |
|-----------|------------|------------|
| Search    | O(log n)   | O(log n)   |
| Insert    | O(log n)   | O(log n)   |
| Delete    | O(log n)   | O(log n)   |

More rotations on insert/delete than Red-Black, but faster lookups due to stricter balancing.

**Space:** O(n)

### Red-Black Tree

Self-balancing BST with color invariants. Used by `TreeMap` (Java), `std::map` (C++).

| Operation | Average    | Worst      |
|-----------|------------|------------|
| Search    | O(log n)   | O(log n)   |
| Insert    | O(log n)   | O(log n)   |
| Delete    | O(log n)   | O(log n)   |

Fewer rotations than AVL on insert/delete (at most 2-3 rotations). Slightly less balanced.

**Space:** O(n)

### Splay Tree

Self-adjusting BST that moves recently accessed elements to the root. Good when access patterns are non-uniform.

| Operation | Amortized  | Worst |
|-----------|------------|-------|
| Search    | O(log n)   | O(n)  |
| Insert    | O(log n)   | O(n)  |
| Delete    | O(log n)   | O(n)  |

**Space:** O(n)

### Treap

Combines BST ordering with heap-priority randomization. Probabilistically balanced.

| Operation | Expected   | Worst |
|-----------|------------|-------|
| Search    | O(log n)   | O(n)  |
| Insert    | O(log n)   | O(n)  |
| Delete    | O(log n)   | O(n)  |

**Space:** O(n)

### B-Tree

Self-balancing tree optimized for disk I/O. Nodes contain multiple keys. Used in databases and filesystems.

| Operation | Average    | Worst      |
|-----------|------------|------------|
| Search    | O(log n)   | O(log n)   |
| Insert    | O(log n)   | O(log n)   |
| Delete    | O(log n)   | O(log n)   |

Branching factor `b` makes height O(log_b n), minimizing disk reads.

**Space:** O(n)

### B+ Tree

Variant of B-Tree where all values live in leaf nodes, and leaves are linked. Range queries are efficient. Standard in RDBMS indexes.

| Operation    | Average    | Worst      |
|--------------|------------|------------|
| Search       | O(log n)   | O(log n)   |
| Insert       | O(log n)   | O(log n)   |
| Delete       | O(log n)   | O(log n)   |
| Range query  | O(log n + k) | O(log n + k) |

k = number of elements in range.

**Space:** O(n)

### Segment Tree

Stores intervals/segments. Answers range queries (sum, min, max) and supports point/range updates.

| Operation      | Time       |
|----------------|------------|
| Build          | O(n)       |
| Query (range)  | O(log n)   |
| Update (point) | O(log n)   |
| Update (range, lazy) | O(log n) |

**Space:** O(n) (2n or 4n nodes)

### Fenwick Tree (Binary Indexed Tree)

Compact structure for prefix sums and point updates. Simpler and lower constant factor than segment tree, but less flexible.

| Operation       | Time     |
|-----------------|----------|
| Build           | O(n)     |
| Prefix sum      | O(log n) |
| Point update    | O(log n) |
| Range sum query | O(log n) |

**Space:** O(n)

### Interval Tree

Stores intervals and efficiently finds all intervals overlapping a given point or interval.

| Operation                   | Time       |
|-----------------------------|------------|
| Insert                      | O(log n)   |
| Delete                      | O(log n)   |
| Find all overlapping        | O(log n + k) |

k = number of overlapping intervals.

**Space:** O(n)

### K-D Tree (K-Dimensional Tree)

Partitions k-dimensional space. Used for nearest neighbor search, range search in spatial data.

| Operation          | Average    | Worst |
|--------------------|------------|-------|
| Search             | O(log n)   | O(n)  |
| Insert             | O(log n)   | O(n)  |
| Nearest neighbor   | O(log n)   | O(n)  |
| Range search       | O(√n + k)  | O(n)  |

**Space:** O(n)

### R-Tree

Spatial index for multi-dimensional objects (bounding boxes). Used in GIS, spatial databases.

| Operation      | Average    | Worst |
|----------------|------------|-------|
| Search         | O(log n)   | O(n)  |
| Insert         | O(log n)   | O(n)  |
| Delete         | O(log n)   | O(n)  |

**Space:** O(n)

### Quad Tree / Oct Tree

Recursively subdivides 2D (quad) or 3D (oct) space into 4 or 8 children. Used in collision detection, image compression.

| Operation | Average    | Worst |
|-----------|------------|-------|
| Search    | O(log n)   | O(n)  |
| Insert    | O(log n)   | O(n)  |
| Delete    | O(log n)   | O(n)  |

**Space:** O(n) to O(n log n)

### Merkle Tree

Binary tree of hashes. Each leaf is a hash of a data block; each internal node is a hash of its children. Used for data integrity verification (Git, blockchain, file sync).

| Operation        | Time     |
|------------------|----------|
| Build            | O(n)     |
| Verify leaf      | O(log n) |
| Compare two trees| O(log n) |

**Space:** O(n)

---

## Heaps

### Binary Heap (Min/Max)

Complete binary tree stored as an array. Parent is smaller (min-heap) or larger (max-heap) than children.

| Operation     | Average    | Worst      |
|---------------|------------|------------|
| Find min/max  | O(1)       | O(1)       |
| Insert        | O(log n)   | O(log n)   |
| Extract min/max| O(log n)  | O(log n)   |
| Build heap    | O(n)       | O(n)       |

**Space:** O(n)

### Fibonacci Heap

Lazy mergeable heap with excellent amortized bounds. Powers optimal Dijkstra and Prim's algorithms.

| Operation       | Amortized  | Worst      |
|-----------------|------------|------------|
| Find min        | O(1)       | O(1)       |
| Insert          | O(1)       | O(1)       |
| Decrease key    | O(1)       | O(log n)   |
| Extract min     | O(log n)   | O(n)       |
| Merge           | O(1)       | O(1)       |

**Space:** O(n)

### Binomial Heap

Collection of binomial trees. Efficient merge. Simpler than Fibonacci heap.

| Operation     | Average    | Worst      |
|---------------|------------|------------|
| Find min      | O(1)       | O(log n)   |
| Insert        | O(1)*      | O(log n)   |
| Extract min   | O(log n)   | O(log n)   |
| Merge         | O(log n)   | O(log n)   |
| Decrease key  | O(log n)   | O(log n)   |

*amortized

**Space:** O(n)

### Pairing Heap

Simpler alternative to Fibonacci heap with good practical performance. Theoretically O(log n) amortized decrease-key.

| Operation     | Amortized  |
|---------------|------------|
| Find min      | O(1)       |
| Insert        | O(1)       |
| Extract min   | O(log n)   |
| Merge         | O(1)       |
| Decrease key  | O(log n)   |

**Space:** O(n)

### D-ary Heap

Generalization of binary heap where each node has up to d children. Shallower tree = faster decrease-key, slower extract.

| Operation     | Time              |
|---------------|-------------------|
| Find min      | O(1)              |
| Insert        | O(log_d n)        |
| Extract min   | O(d × log_d n)    |
| Decrease key  | O(log_d n)        |

**Space:** O(n)

---

## Graphs

### Adjacency Matrix

2D matrix where `matrix[i][j]` indicates edge between vertex i and j.

| Operation         | Time |
|-------------------|------|
| Check edge exists | O(1) |
| List neighbors    | O(V) |
| Add edge          | O(1) |
| Remove edge       | O(1) |
| Add vertex        | O(V²)|

**Space:** O(V²) — good for dense graphs

### Adjacency List

Array of lists, each storing neighbors of a vertex.

| Operation         | Time   |
|-------------------|--------|
| Check edge exists | O(deg) |
| List neighbors    | O(deg) |
| Add edge          | O(1)   |
| Remove edge       | O(deg) |
| Add vertex        | O(1)   |

deg = degree of vertex. **Space:** O(V + E) — good for sparse graphs

### Edge List

Simple list of all edges as (u, v, weight) tuples.

| Operation         | Time |
|-------------------|------|
| Check edge exists | O(E) |
| List neighbors    | O(E) |
| Add edge          | O(1) |
| Remove edge       | O(E) |

**Space:** O(E)

### Incidence Matrix

Matrix of V × E. `matrix[v][e] = 1` if vertex v is incident to edge e.

| Operation         | Time |
|-------------------|------|
| Check edge exists | O(E) |
| List neighbors    | O(E) |

**Space:** O(V × E) — rarely used in practice

---

## Trie & String Structures

### Trie (Prefix Tree)

Tree where each edge represents a character. Shared prefixes share paths. Used for autocomplete, spell check, IP routing.

| Operation | Time |
|-----------|------|
| Search    | O(k) |
| Insert    | O(k) |
| Delete    | O(k) |
| Prefix search | O(k + results) |

k = length of key. **Space:** O(n × k) worst case, but shared prefixes reduce it in practice.

### Radix Tree (Compressed Trie / Patricia Tree)

Compressed trie where single-child chains are merged into one edge. Saves space while keeping the same time complexity.

| Operation | Time |
|-----------|------|
| Search    | O(k) |
| Insert    | O(k) |
| Delete    | O(k) |

**Space:** O(n × k) worst case, significantly less in practice.

### Suffix Tree

Stores all suffixes of a string in a compressed trie. Powerful for substring search, longest common substring, repeat finding.

| Operation              | Time |
|------------------------|------|
| Build (Ukkonen's)      | O(n) |
| Substring search       | O(m) |
| Longest repeated substr| O(n) |

m = pattern length. **Space:** O(n) (with compression, but large constant).

### Suffix Array

Sorted array of all suffixes of a string. Space-efficient alternative to suffix tree.

| Operation         | Time           |
|-------------------|----------------|
| Build             | O(n log n) or O(n) |
| Substring search  | O(m log n)     |

Pair with LCP array for O(m + log n) search.

**Space:** O(n)

---

## Disjoint Set / Union-Find

Tracks a partition of elements into disjoint sets. Used in Kruskal's MST, connected components, percolation.

| Operation | Amortized (with path compression + union by rank) |
|-----------|---------------------------------------------------|
| Find      | O(α(n)) ≈ O(1)                                    |
| Union     | O(α(n)) ≈ O(1)                                    |

α = inverse Ackermann function (effectively constant for all practical input sizes).

**Space:** O(n)

---

## Specialized & Advanced Structures

### LRU Cache

Combines hash map + doubly linked list. Evicts least recently used item when full. Used in caching layers.

| Operation | Time |
|-----------|------|
| Get       | O(1) |
| Put       | O(1) |
| Evict     | O(1) |

**Space:** O(capacity)

### Ring Buffer (Circular Buffer)

Fixed-size buffer that wraps around. Used in streaming, I/O buffers, producer-consumer patterns.

| Operation        | Time |
|------------------|------|
| Read/Write (end) | O(1) |
| Access by index  | O(1) |

**Space:** O(n)

### Sparse Table

Precomputes answers for range queries on static data. Best for idempotent operations (min, max, gcd).

| Operation    | Time     |
|--------------|----------|
| Build        | O(n log n) |
| Range query  | O(1)     |

No updates supported (static only).

**Space:** O(n log n)

### Persistent Data Structures

Immutable versions that preserve all previous states. Each "modification" returns a new version sharing structure with the old.

Persistent BST/Treap:

| Operation | Time     |
|-----------|----------|
| Access    | O(log n) |
| "Update"  | O(log n) |

**Space:** O(log n) per version (path copying).

### Rope

Balanced binary tree of strings. Efficient for large text editing (used in text editors).

| Operation      | Time     |
|----------------|----------|
| Index           | O(log n) |
| Concat          | O(log n) |
| Split           | O(log n) |
| Insert          | O(log n) |
| Delete          | O(log n) |

**Space:** O(n)

### Bitset / Bit Array

Compact array of bits. Supports fast set operations (AND, OR, XOR) on large sets.

| Operation       | Time      |
|-----------------|-----------|
| Get/Set bit     | O(1)      |
| AND/OR/XOR      | O(n/w)    |
| Count set bits  | O(n/w)    |

w = word size (64). **Space:** O(n/8) bytes.

---

## Summary Comparison Table

| Data Structure       | Access   | Search   | Insert   | Delete   | Space      |
|----------------------|----------|----------|----------|----------|------------|
| Array                | O(1)     | O(n)     | O(n)     | O(n)     | O(n)       |
| Dynamic Array        | O(1)     | O(n)     | O(1)*    | O(n)     | O(n)       |
| Singly Linked List   | O(n)     | O(n)     | O(1)†    | O(1)†    | O(n)       |
| Doubly Linked List   | O(n)     | O(n)     | O(1)†    | O(1)†    | O(n)       |
| Skip List            | O(log n) | O(log n) | O(log n) | O(log n) | O(n log n) |
| Hash Table           | —        | O(1)     | O(1)     | O(1)     | O(n)       |
| BST (unbalanced)     | O(log n) | O(log n) | O(log n) | O(log n) | O(n)       |
| AVL / Red-Black Tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n)       |
| B-Tree / B+ Tree     | O(log n) | O(log n) | O(log n) | O(log n) | O(n)       |
| Binary Heap          | —        | O(n)     | O(log n) | O(log n) | O(n)       |
| Fibonacci Heap       | —        | O(n)     | O(1)     | O(log n) | O(n)       |
| Trie                 | —        | O(k)     | O(k)     | O(k)     | O(n×k)     |
| Segment Tree         | —        | O(log n) | —        | O(log n) | O(n)       |
| Fenwick Tree         | —        | O(log n) | —        | O(log n) | O(n)       |
| Union-Find           | —        | O(α(n))  | —        | —        | O(n)       |
| Bloom Filter         | —        | O(k)     | O(k)     | —        | O(m)       |

*amortized, at end  
†at known position (head/tail)  
k = key/string length  
α(n) ≈ O(1) in practice
