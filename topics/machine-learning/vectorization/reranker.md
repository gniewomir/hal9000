---
id: 019d7a35-4576-7122-92b5-47fb040523da
references: []
---
## What is a Reranker?

A **reranker** is a second-stage model that re-scores and reorders the candidate documents returned by an initial vector similarity search (the "retriever") to improve relevance before results are passed to an LLM or shown to a user.

### Why it's needed

Vector search (embedding-based retrieval) is fast because it compares pre-computed embeddings via approximate nearest neighbor (ANN) algorithms. But the bi-encoder architecture used for embeddings encodes the query and each document **independently** — they never "see" each other. This makes retrieval efficient but limits how well it can judge nuanced relevance.

A reranker fixes this by using a **cross-encoder**: it takes the query and a candidate document **together** as input, allowing full token-level interaction between them. This is far more accurate but too expensive to run against millions of documents, which is why it's only applied to the top-k results from the retriever.

### The two-stage pipeline

```
Corpus (millions of docs)
    │
    ▼
┌──────────────┐
│  Retriever   │  Bi-encoder / vector similarity (fast, approximate)
│  (Stage 1)   │  Returns top-k candidates (e.g. 100)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Reranker    │  Cross-encoder (slow, precise)
│  (Stage 2)   │  Reorders candidates by relevance score
└──────┬───────┘
       │
       ▼
  Top-n results → LLM context / user
```

### Key differences: Retriever vs. Reranker

| | Retriever (Bi-encoder) | Reranker (Cross-encoder) |
|---|---|---|
| Input | Query and docs encoded separately | Query + doc encoded together |
| Speed | Fast (ANN over pre-computed vectors) | Slow (inference per query-doc pair) |
| Accuracy | Good recall, weaker precision | High precision |
| Scale | Millions of documents | Top-k candidates only (e.g. 20–100) |

### Popular reranker models

- **Cohere Rerank** — API-based, easy to integrate, supports multilingual
- **BGE Reranker** (BAAI) — open-source, available on HuggingFace (`BAAI/bge-reranker-v2-m3`)
- **Jina Reranker** — open-source cross-encoder models
- **ColBERT** — late-interaction model, a middle ground between bi-encoder speed and cross-encoder accuracy
- **RankGPT** — uses an LLM itself (e.g. GPT-4) as the reranker via listwise prompting

### Impact on RAG

In a RAG (Retrieval-Augmented Generation) pipeline, reranking is especially valuable because:

1. **LLM context windows are limited** — even with large windows, stuffing irrelevant chunks degrades answer quality and increases cost
2. **Precision matters more than recall** — the LLM only needs the *most relevant* chunks, not all possibly-relevant ones
3. **"Lost in the middle" problem** — LLMs tend to pay less attention to information in the middle of long contexts; feeding fewer, more relevant chunks mitigates this

### Practical considerations

- Reranking adds latency (typically 50–200ms for cross-encoders on ~100 candidates)
- For local/self-hosted setups, lightweight models like `BAAI/bge-reranker-base` run well on CPU
- Most vector databases and frameworks (LangChain, LlamaIndex, Haystack) have built-in reranker integrations

### Links

- https://www.sbert.net/examples/applications/cross-encoder/README.html
- https://txt.cohere.com/rerank/
- https://huggingface.co/BAAI/bge-reranker-v2-m3
- https://arxiv.org/abs/2304.09542 (RankGPT paper)
- https://jina.ai/reranker
