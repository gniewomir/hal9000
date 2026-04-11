---
id: 019d7a75-0ae4-7105-a861-4186ba34003c
references: []
---

# Directed graphs and DAGs

Two closely related ways to model objects and relationships when **direction matters**: a **directed graph** is the general case; a **DAG** (directed acyclic graph) adds one global rule—no directed cycles.

## Directed graph (general digraph)

A **directed graph** consists of **vertices** (nodes) and **directed edges**. Each edge goes from one vertex to another and has a direction—think of an arrow from A to B. The pair (A → B) is not the same as (B → A) unless both edges exist.

**“General”** means you assume **no extra structure** unless stated: cycles may exist, not every vertex must be reachable from every other, and graphs may be sparse or dense depending on the application.

## DAG (directed acyclic graph)

A **DAG** is a directed graph with one restriction: there is **no directed cycle**. You cannot start at a vertex, follow edges forward, and return to the same vertex.

Equivalently: the edge relation does not admit infinite “walks” that loop.

## How they relate

Every DAG is a directed graph. A directed graph is a DAG **if and only if** it has no directed cycles.

| | Directed graph | DAG |
|---|----------------|-----|
| Direction on edges | Yes | Yes |
| Directed cycles allowed | Yes | No |
| Topological ordering of all vertices | Only if acyclic | Always (if non-empty and you handle isolated nodes) |

## Related concepts

- **Undirected graph** — edges have no direction; {A, B} is one relationship. Useful when symmetry is natural (mutual friendship, single road segment usable both ways).
- **Multigraph** — multiple edges between the same vertices (e.g. parallel roads). Often combined with directed or undirected graphs.
- **Weighted graph** — edges carry numbers (cost, distance, capacity, probability). **Shortest-path** and **max-flow** algorithms typically assume directed or undirected graphs with weights.
- **Path** — sequence of vertices connected by edges following direction (in digraphs). A **cycle** is a path that starts and ends at the same vertex.
- **Topological sort** — linear ordering of vertices so every edge goes from earlier to later. **Exists if and only if** the graph is a DAG (ignoring isolated vertices).
- **Strongly connected component (SCC)** — maximal set of vertices where each can reach each other along directed edges. In a DAG, each SCC is a single vertex (unless you allow self-loops, which most “DAG” definitions forbid).
- **Tree** — connected acyclic **undirected** graph; a **rooted tree** can be seen as a DAG with edges pointing parent → child.
- **Bipartite graph** — vertices split into two groups with edges only between groups; often used for matching (can be directed or undirected).

## Where a general directed graph is useful

- **The web** — pages link to pages; links are asymmetric (A → B does not imply B → A).
- **Social “follows”** — directed; mutual follow is two edges, not one undirected edge.
- **State machines** — states as vertices, transitions as labeled directed edges; cycles are normal (e.g. loops in protocols).
- **Citation networks** — paper A cites paper B (A → B); citation graphs often have rich structure and cycles are possible in theory depending on modeling.
- **Game graphs** — positions or states with moves as directed edges; may contain cycles (repeated positions).
- **Call graphs / module imports** — “A imports B” is directed; cycles may exist and are sometimes errors, sometimes allowed.

## Where a DAG is especially useful

- **Task dependencies** — “task A must finish before B”; a cycle means an impossible schedule. Build systems (Make, npm scripts), CI pipelines, and project plans often model **dependencies as a DAG**.
- **Instruction / topic ordering** — “understand B before A” if edges mean prerequisite; topological order gives a valid study sequence.
- **Supersession** — “version 2 replaces version 1” in one direction only; chains stay acyclic if you don’t encode rollback as the same relation type.
- **Compiler IR** — basic blocks and control flow within a **single function** are often modeled as a CFG; the **DOM** in many static analyses uses DAGs; **SSA** forms use DAG-like value graphs.
- **Version control (Git)** — history of commits is often described as a DAG (merge commits have multiple parents; no commit is its own ancestor).
- **Bayesian networks** — variables as nodes, directed edges as conditional dependencies; structure is required to be acyclic.
- **Data processing pipelines** — stages with explicit upstream/downstream ordering; acyclicity ensures a clear execution order.

## Practical note for knowledge bases

A vault of notes with links can be seen as a **directed graph** (note A links to note B). Bidirectional “see also” links often create **cycles**. If you tag some links as **strict prerequisites** or **build order** only, that subgraph can be kept a **DAG** for algorithms that need a linear order (reading path, static site generation order). The same notes can participate in more than one graph if you separate **relation types**.

## See also

- [Data Structures Reference](reference.md) — broader complexity and structure catalog for this topic area.
