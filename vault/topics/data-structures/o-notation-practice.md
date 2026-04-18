
# Assessing Big O in Practice

A pragmatic guide for working software engineers. No proofs — just patterns you'll see in real codebases and how to reason about their complexity.

---

## The Mental Framework

When looking at any piece of code, ask three questions:

1. **What is n?** Identify the input that grows. It might be rows in a database, elements in a list, characters in a string, nodes in a tree, or pixels in an image.
2. **How many times does the code touch each element?** Count the layers of iteration.
3. **What hidden work happens inside each step?** Built-in functions, library calls, and data structure operations all have their own complexity.

---

## Pattern 1: Simple Loops

```python
total = 0
for item in items:
    total += item.price
```

One loop over n items, constant work per iteration → **O(n)**.

### Watch for hidden linear work inside the loop

```python
for user in users:
    if user.email in blocked_emails:   # list lookup is O(m)
        skip(user)
```

If `blocked_emails` is a **list** of m elements, `in` is O(m) → total is **O(n · m)**. Switch to a **set** and the inner check drops to O(1) → total becomes **O(n)**.

This is one of the most common performance mistakes in production code.

---

## Pattern 2: Nested Loops

```python
for i in range(n):
    for j in range(n):
        matrix[i][j] = 0
```

Two nested loops over the same input → **O(n²)**.

```python
for i in range(n):
    for j in range(i, n):
        process(i, j)
```

The inner loop runs n, n-1, n-2, ... 1 times. Total iterations = n(n-1)/2 → still **O(n²)**. The halving is just a constant factor.

### Nested loops over different inputs

```python
for order in orders:           # n orders
    for item in order.items:   # m items per order
        ship(item)
```

This is **O(n · m)**, not O(n²). Keep separate variables when inputs are independent.

---

## Pattern 3: Divide and Conquer / Halving

Any time the problem size is **cut in half** at each step, you get a logarithm.

```python
while lo <= hi:
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
```

n → n/2 → n/4 → ... → 1 takes log₂(n) steps → **O(log n)**.

### Recognizing log n in disguise

- Binary search: O(log n)
- Balanced BST lookup: O(log n)
- B-tree operations (database indexes): O(log n)
- Repeatedly doubling a capacity (amortized resize): O(log n) doublings for n elements
- Exponentiation by squaring: O(log n)
- Any "discard half the remaining candidates" pattern: O(log n)

---

## Pattern 4: Sorting as a Baseline

Comparison-based sorting is O(n log n). If your algorithm sorts first and then does linear work, the bottleneck is the sort.

```python
def find_duplicates(items):
    items.sort()                      # O(n log n)
    dupes = []
    for i in range(1, len(items)):    # O(n)
        if items[i] == items[i - 1]:
            dupes.append(items[i])
    return dupes
```

Total: O(n log n) + O(n) = **O(n log n)**.

Many practical algorithms hit this floor: "sort, then scan" is a reliable O(n log n) approach to deduplication, closest-pair, interval merging, and similar problems.

---

## Pattern 5: Hash Maps Change Everything

Hash map insert/lookup/delete are O(1) average. Reaching for a hash map often drops a factor of n from your complexity.

| Task | Without hash map | With hash map |
|------|-----------------|---------------|
| Check for duplicates | O(n²) nested comparison | O(n) insert-and-check |
| Two-sum | O(n²) brute force | O(n) complement lookup |
| Frequency counting | O(n²) or O(n log n) sort | O(n) counter dict |
| Group by key | O(n²) | O(n) |

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:        # O(1) average
            return [seen[complement], i]
        seen[num] = i
```

**Caveat:** Hash map worst case is O(n) per operation (hash collisions). In practice this almost never happens with good hash functions, but be aware when analyzing adversarial inputs.

---

## Pattern 6: String Operations

Strings are arrays of characters. Operations that look cheap are often linear in string length.

```python
result = ""
for word in words:
    result += word      # copies entire result string each time
```

If there are n words of average length k, each concatenation copies the growing string. Total work: k + 2k + 3k + ... + nk = O(n²k). Use `"".join(words)` for **O(nk)** instead.

### Common string operation costs

| Operation | Complexity |
|-----------|-----------|
| `s[i]` index access | O(1) |
| `len(s)` | O(1) in Python |
| `s + t` concatenation | O(len(s) + len(t)) |
| `s.find(t)` / `t in s` | O(len(s) · len(t)) worst case |
| `s.replace(old, new)` | O(len(s) · len(old)) |
| `s.split(sep)` | O(len(s)) |
| `"".join(parts)` | O(total length) |

---

## Pattern 7: Database and SQL Thinking

### Table scan vs. index lookup

- `SELECT * FROM users WHERE email = ?` without an index: **O(n)** — full table scan.
- Same query with a B-tree index on `email`: **O(log n)**.

### Joins

- Nested loop join (no indexes): **O(n · m)** where n and m are table sizes.
- Hash join: **O(n + m)** — builds a hash table on the smaller table, probes with the larger.
- Merge join (pre-sorted inputs): **O(n + m)**.

### N+1 query problem

```python
orders = db.query("SELECT * FROM orders")          # 1 query
for order in orders:                                # n iterations
    items = db.query(f"SELECT * FROM items WHERE order_id = {order.id}")  # 1 query each
```

This makes **n + 1** database round-trips. Each round-trip has network latency (often milliseconds). For 1000 orders, that's 1001 queries. Fix with a JOIN or an IN clause:

```python
order_ids = [o.id for o in orders]
items = db.query(f"SELECT * FROM items WHERE order_id IN ({','.join(order_ids)})")
```

Now it's 2 queries regardless of n. The complexity of the SQL execution itself depends on indexes, but the number of network round-trips drops from O(n) to O(1).

---

## Pattern 8: Tree and Graph Traversal

### Tree traversal (BFS/DFS)

Visiting every node in a tree with n nodes: **O(n)**. Each node is visited exactly once.

### Graph traversal

BFS/DFS on a graph with V vertices and E edges: **O(V + E)**. You visit each vertex once and examine each edge once.

### Why O(V + E) and not O(V · E)?

Because you don't re-examine edges for vertices you've already visited. The adjacency list representation lets you iterate only over a node's actual neighbors, not all possible edges.

### Shortest path algorithms

| Algorithm | Complexity | Use case |
|-----------|-----------|----------|
| BFS | O(V + E) | Unweighted graphs |
| Dijkstra (binary heap) | O((V + E) log V) | Non-negative weights |
| Bellman-Ford | O(V · E) | Negative weights |
| Floyd-Warshall | O(V³) | All-pairs shortest path |

---

## Pattern 9: Recursion

Map the recursion to a recurrence relation, then estimate.

### Linear recursion

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

One recursive call, reduces n by 1 each time → n calls → **O(n)**.

### Binary recursion (branching)

```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```

Two recursive calls per level, depth n → roughly 2ⁿ calls → **O(2ⁿ)**. This is why naive recursive Fibonacci is catastrophically slow. Use memoization or bottom-up DP to drop it to **O(n)**.

### Quick rule of thumb for recursion

- **How many branches** at each call? → base of the exponential
- **How deep** is the recursion? → exponent (or multiplier if linear branching)
- **How much work** at each call? → multiplied by the above

---

## Pattern 10: API and Network Calls

Network I/O has constant overhead (latency) per call, but the algorithmic pattern determines how many calls you make.

| Pattern | Calls | Total latency |
|---------|-------|--------------|
| Single batch request | 1 | O(1) round-trips |
| Paginated fetch (p pages) | p | O(p) round-trips |
| One request per item | n | O(n) round-trips |
| Polling until ready | t | O(t) where t is wait time |

**Pagination example:**

```python
results = []
page = 1
while True:
    response = api.get(f"/items?page={page}&per_page=100")
    results.extend(response.items)
    if not response.has_next:
        break
    page += 1
```

If there are n total items and each page has 100, you make n/100 requests → **O(n/100) = O(n)** round-trips, but the constant factor (100x fewer calls) matters enormously in practice.

---

## Pattern 11: Caching and Memoization

Caching trades space for time by avoiding recomputation.

```python
@lru_cache(maxsize=None)
def expensive(key):
    return db.query(f"SELECT * FROM data WHERE key = {key}")
```

- **First call** for each unique key: O(cost of computation)
- **Subsequent calls** for the same key: O(1) lookup
- **Space:** O(k) where k is the number of unique keys

If you call `expensive()` n times with k unique keys (k ≤ n), total work is O(k · cost + n) instead of O(n · cost).

---

## Pattern 12: Middleware and Request Pipelines

Web frameworks execute middleware/interceptors for every request. If you have m middleware functions and each does O(1) work, per-request cost is O(m). Since m is usually fixed and small, this is effectively O(1) per request.

But watch out for middleware that does linear work:

```python
class AuthMiddleware:
    def process(self, request):
        user = get_user(request.token)          # O(1) with cache/index
        permissions = get_permissions(user)      # O(1) with cache/index
        for perm in permissions:                 # O(p) where p = number of permissions
            if perm.resource == request.path:
                return True
        return False
```

If permissions grow large and this runs on every request, it matters. Use a set or hash map for permission lookups.

---

## Pattern 13: File and Stream Processing

### Line-by-line processing

```python
with open("huge.csv") as f:
    for line in f:
        process(line)
```

Reads n lines, constant work per line → **O(n)**. Memory is O(1) because only one line is in memory at a time — this is the right way to handle large files.

### Loading everything into memory first

```python
data = open("huge.csv").read()   # O(n) memory
lines = data.split("\n")         # O(n) again
```

Same O(n) time but O(n) space. For multi-gigabyte files, this will crash.

---

## Pattern 14: Regex

Regex complexity depends on the pattern and the engine.

- Simple patterns (literal match, character class): **O(n)** where n is string length.
- Patterns with backreferences or catastrophic backtracking (e.g., `(a+)+b`): can be **O(2ⁿ)** in pathological cases.

**Practical rule:** Avoid nested quantifiers on overlapping character classes. If your regex hangs on certain inputs, suspect catastrophic backtracking.

---

## Decision Framework: Choosing the Right Approach

Given n items and a time budget, what complexity can you afford?

| n | Max affordable complexity | Typical scenario |
|---|--------------------------|------------------|
| ≤ 20 | O(2ⁿ), O(n!) | Permutation/subset brute force |
| ≤ 500 | O(n³) | Small matrix operations |
| ≤ 10,000 | O(n²) | Moderate datasets, quadratic OK |
| ≤ 1,000,000 | O(n log n) | Sorting, divide-and-conquer |
| ≤ 100,000,000 | O(n) | Single pass, streaming |
| > 100,000,000 | O(log n), O(1) | Index lookups, constant-time ops |

These assume roughly 10⁸ operations per second and a ~1 second time budget.

---

## Checklist: Reviewing Code for Complexity

1. **Identify the hot path.** What runs on every request / every row / every frame?
2. **Count nesting depth.** Each nested loop multiplies: 1 loop = O(n), 2 nested = O(n²), 3 nested = O(n³).
3. **Check data structure operations.** Is that lookup O(1) (hash map) or O(n) (list scan)?
4. **Watch for hidden iteration.** `in` on a list, string concatenation in loops, `filter()` inside `map()`.
5. **Count network round-trips.** Each one adds latency. Batch where possible.
6. **Check for the N+1 problem.** One query per item in a loop = O(n) queries.
7. **Verify index usage.** No index on a WHERE clause = full table scan = O(n).
8. **Test with realistic data sizes.** Something that works on 100 items may fail on 100,000.
