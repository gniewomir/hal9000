
# Asymptotic Notation

Asymptotic notation describes how the runtime or space requirements of an algorithm grow as the input size approaches infinity. It abstracts away constants and lower-order terms to focus on the dominant factor that determines scalability.

## Big O — O(n) — Upper Bound

Big O gives the **worst-case** (or an upper bound on) growth rate. When we say an algorithm is O(f(n)), we mean its resource usage grows **no faster than** f(n) for sufficiently large n, up to a constant factor.

**Formal definition:** T(n) is O(f(n)) if there exist constants c > 0 and n₀ ≥ 0 such that for all n ≥ n₀:

    T(n) ≤ c · f(n)

**Example:** If T(n) = 3n² + 5n + 7, then T(n) is O(n²), because for large n the n² term dominates. We can pick c = 4 and n₀ = 6 to satisfy the inequality.

## Big Omega — Ω(n) — Lower Bound

Big Omega gives the **best-case** (or a lower bound on) growth rate. T(n) is Ω(f(n)) means the algorithm takes **at least** f(n) time.

**Formal definition:** T(n) is Ω(f(n)) if there exist constants c > 0 and n₀ ≥ 0 such that for all n ≥ n₀:

    T(n) ≥ c · f(n)

**Example:** Comparison-based sorting is Ω(n log n) — no comparison sort can do better than n log n in the worst case.

## Big Theta — Θ(n) — Tight Bound

Big Theta means the algorithm grows **exactly at the rate** of f(n), up to constant factors. It is both O(f(n)) and Ω(f(n)) simultaneously.

**Formal definition:** T(n) is Θ(f(n)) if there exist constants c₁, c₂ > 0 and n₀ ≥ 0 such that for all n ≥ n₀:

    c₁ · f(n) ≤ T(n) ≤ c₂ · f(n)

**Example:** Merge sort is Θ(n log n) — it always takes n log n time regardless of input ordering.

## Little o — o(n) — Strict Upper Bound

Little o means T(n) grows **strictly slower** than f(n). Unlike Big O, equality is excluded.

**Formal definition:** T(n) is o(f(n)) if for **every** constant c > 0, there exists n₀ such that for all n ≥ n₀:

    T(n) < c · f(n)

Equivalently: lim(n→∞) T(n)/f(n) = 0.

**Example:** n is o(n²), because n/n² = 1/n → 0. But n² is **not** o(n²).

## Little Omega — ω(n) — Strict Lower Bound

Little omega is the counterpart to little o. T(n) grows **strictly faster** than f(n).

**Formal definition:** lim(n→∞) T(n)/f(n) = ∞.

**Example:** n² is ω(n), because n²/n = n → ∞.

---

## Common Complexity Classes

Listed from fastest to slowest growth:

| Class | Name | Example |
|-------|------|---------|
| O(1) | Constant | Hash table lookup, array index access |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Linear search, single traversal |
| O(n log n) | Linearithmic | Merge sort, heap sort |
| O(n²) | Quadratic | Bubble sort, insertion sort (worst case) |
| O(n³) | Cubic | Naive matrix multiplication |
| O(2ⁿ) | Exponential | Brute-force subset enumeration |
| O(n!) | Factorial | Brute-force permutation generation |

### O(1) — Constant

Runtime does not depend on input size.

```python
def get_first(items):
    return items[0]
```

No matter if the list has 10 or 10 million elements, one operation is performed.

### O(log n) — Logarithmic

Each step eliminates a constant fraction of the remaining input (typically half).

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

For n = 1,000,000 elements, binary search needs at most ~20 comparisons (log₂ 1,000,000 ≈ 20).

### O(n) — Linear

Work scales directly with input size.

```python
def find_max(arr):
    maximum = arr[0]
    for val in arr:
        if val > maximum:
            maximum = val
    return maximum
```

Doubling the input doubles the work.

### O(n log n) — Linearithmic

Divide-and-conquer algorithms that split the problem and do linear work per level.

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

There are log n levels of recursion, each doing O(n) work → O(n log n) total.

### O(n²) — Quadratic

Typically nested loops where each element is compared against every other element.

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
```

Doubling the input quadruples the work.

### O(2ⁿ) — Exponential

Each additional input element doubles the total work. Common in brute-force combinatorial problems.

```python
def all_subsets(items):
    if not items:
        return [[]]
    first = items[0]
    rest_subsets = all_subsets(items[1:])
    with_first = [[first] + subset for subset in rest_subsets]
    return rest_subsets + with_first
```

For 20 items: 2²⁰ = 1,048,576 subsets. For 30 items: over a billion.

---

## Amortized Analysis

Some operations are expensive occasionally but cheap most of the time. Amortized analysis averages the cost over a sequence of operations.

**Example — Dynamic array (Python list) append:**

Most appends are O(1). When the internal buffer is full, the array doubles its capacity and copies all elements — an O(n) operation. But this doubling happens so rarely that across n appends, total work is O(n), giving an **amortized O(1)** per append.

```
Appends:     1  2  3  4  5  6  7  8  9 ...
Cost:        1  1  1  1+4  1  1  1  1+8  1 ...
                      ↑ resize          ↑ resize
```

Total cost for n appends ≈ n + n/2 + n/4 + ... ≈ 3n → amortized O(1) each.

---

## Best, Worst, and Average Case

Big O notation describes a **growth rate**, not a specific case. Any algorithm can be analyzed under different input scenarios:

- **Best case:** The input that causes the least work. Insertion sort on an already-sorted array is O(n).
- **Worst case:** The input that causes the most work. Insertion sort on a reverse-sorted array is O(n²).
- **Average case:** Expected performance over all possible inputs (often assumes uniform distribution). Quicksort averages O(n log n) even though its worst case is O(n²).

Big O is most commonly used for worst-case analysis, but it can describe any of these. Always clarify which case you mean.

---

## Space Complexity

The same notation applies to memory usage.

| Algorithm | Time | Space |
|-----------|------|-------|
| Binary search (iterative) | O(log n) | O(1) |
| Merge sort | O(n log n) | O(n) |
| Quicksort (in-place) | O(n log n) avg | O(log n) stack |
| BFS on a graph | O(V + E) | O(V) |
| Hash table | O(1) avg lookup | O(n) |

**In-place** algorithms use O(1) auxiliary space (not counting the input itself). Merge sort requires O(n) extra space for the temporary arrays, while quicksort operates in-place with only O(log n) stack frames on average.

---

## Rules for Simplifying Big O

### Drop constants

O(3n) = O(n). Constants do not affect growth rate.

### Drop lower-order terms

O(n² + n) = O(n²). For large n, the n² term dominates.

### Multiplication rule

If an outer loop runs O(n) times and an inner loop runs O(m) times, total is O(n · m).

### Addition rule

Sequential phases add: O(n) followed by O(n²) is O(n²) overall (dominated by the larger term).

### Different variables

If two inputs have different sizes, keep both variables: iterating an n×m matrix is O(n · m), not O(n²).

---

## Logarithm Bases Don't Matter

O(log₂ n) = O(log₁₀ n) = O(ln n) because logarithm base conversion is a constant factor:

    log_a(n) = log_b(n) / log_b(a)

Since 1/log_b(a) is a constant, all logarithmic bases are equivalent in Big O.

---

## Practical Intuition

For n = 1,000,000 (one million elements):

| Complexity | Approximate operations |
|------------|----------------------|
| O(1) | 1 |
| O(log n) | 20 |
| O(n) | 1,000,000 |
| O(n log n) | 20,000,000 |
| O(n²) | 1,000,000,000,000 |
| O(2ⁿ) | incomprehensibly large |

A modern computer does roughly 10⁸–10⁹ simple operations per second. This means:

- O(n log n) on a million elements: ~0.02 seconds
- O(n²) on a million elements: ~16 minutes
- O(2ⁿ) on just 50 elements: longer than the age of the universe

---

## Recurrence Relations

Many recursive algorithms have runtimes described by recurrence relations, solved to get a closed-form Big O.

### Master Theorem

For recurrences of the form T(n) = aT(n/b) + O(nᵈ):

- If d < log_b(a): T(n) = O(n^(log_b(a)))
- If d = log_b(a): T(n) = O(nᵈ log n)
- If d > log_b(a): T(n) = O(nᵈ)

**Examples:**

| Algorithm | Recurrence | a, b, d | Result |
|-----------|-----------|---------|--------|
| Binary search | T(n) = T(n/2) + O(1) | 1, 2, 0 | O(log n) |
| Merge sort | T(n) = 2T(n/2) + O(n) | 2, 2, 1 | O(n log n) |
| Strassen multiplication | T(n) = 7T(n/2) + O(n²) | 7, 2, 2 | O(n^2.81) |

---

## Common Pitfalls

**Confusing Big O with exact runtime.** O(n) doesn't mean n operations — it could be 1000n + 500. For small inputs, an O(n²) algorithm with tiny constants can outperform an O(n log n) algorithm with large constants.

**Ignoring hidden loops.** String concatenation in a loop can be O(n²) if each concatenation copies the whole string. Built-in functions like `sort()`, `in`, or `substring` have their own complexity.

**Assuming Big O = worst case.** Big O describes a growth bound, not a specific scenario. You can say "the best case is O(n)" — that's a valid statement meaning the best-case runtime grows linearly.

**Confusing time and space.** An algorithm can be fast but use enormous memory, or vice versa. Always analyze both.
