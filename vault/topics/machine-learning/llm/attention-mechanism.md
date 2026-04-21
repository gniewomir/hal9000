# Attention mechanism in modern LLMs

## Short explanation (layman terms)

An **attention mechanism** is how modern language models decide *what to focus on* in the text they’re reading or generating.

When an LLM processes a sentence, it doesn’t just read left-to-right like a human. Instead, for each word (token), it looks back over the tokens it has available and asks: **which parts are most relevant right now?** It then mixes information from those relevant tokens to build a better understanding of the current token and what should come next.

A useful mental model: attention is like having a **searchlight** that sweeps over the recent conversation and shines brightest on the pieces that matter for the current step. The model does this *every layer*, and often with *many searchlights in parallel* (attention “heads”), so it can track different relationships at once (e.g. grammar agreement, topic, names, code symbols).

## Theory (precise)

**Setting:** A Transformer LLM operates on a sequence of token representations \(X \in \mathbb{R}^{T \times d}\) (length \(T\), hidden size \(d\)). Attention is the core operation that lets each position combine information from other positions.

### Scaled dot-product attention (single head)

The model forms three projected views of the same tokens:

- \(Q = XW_Q\) (**queries**)
- \(K = XW_K\) (**keys**)
- \(V = XW_V\) (**values**)

For each position \(t\), attention weights over all positions \(s\) are:

\[
A = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)
\]

- \(d_k\): key/query head dimension.
- \(M\): **mask** (e.g. causal mask sets future positions to \(-\infty\)).

The output is a weighted sum of values:

\[
O = AV
\]

Intuition in precise terms:
- **Keys** identify “what’s at position \(s\)”.
- **Queries** express “what position \(t\) is looking for”.
- **Values** carry the content to be aggregated if a key is selected.

### Multi-head attention (MHA)

Instead of one attention, compute \(h\) heads with smaller dimensions, then concatenate and project:

\[
\text{MHA}(X) = \text{Concat}(O_1,\dots,O_h)W_O
\]

Heads let the model represent different relations simultaneously.

### Self-attention vs cross-attention

- **Self-attention:** \(Q,K,V\) come from the same sequence \(X\). Used in decoder-only LLMs (GPT/LLaMA-style) and in encoders.
- **Cross-attention:** \(Q\) comes from one sequence (e.g. decoder states), while \(K,V\) come from another (e.g. encoder outputs). Common in encoder-decoder models and some retrieval/tool architectures.

### Causal masking for next-token prediction

Decoder-only LLMs apply a **causal mask** so token \(t\) can only attend to tokens \(\le t\). This makes the model a valid autoregressive next-token predictor.

### Complexity + the KV cache

Naively, attention is \(O(T^2)\) in time and memory for the attention matrix \(A\). In generation, LLMs use a **KV cache**: they store previous \(K,V\) for each layer so that when generating one new token, they only compute the new query and attend over cached keys/values.

**In practice:** attention shows up as:
- **Speed and memory scaling with context length** (longer prompts cost more).
- **The KV cache** often becoming the real memory limiter during long chats, independent of model weights (see also `vault/topics/machine-learning/llm/moe-models-and-older-hardware.md` for the “KV cache dominates” pattern).
- **Quality issues** when relevant info is far back or buried among irrelevant tokens (“lost in the middle”), which is why RAG pipelines obsess over feeding fewer, more relevant chunks and often add reranking (`vault/topics/machine-learning/vectorization/reranker.md`).

## Where it applies (examples)

- **Context:** You’re estimating why latency spikes when users paste long conversations. **What you do:** Treat attention as roughly quadratic in prompt length for prefill; measure prompt token counts and cap context; consider chunking/summarizing earlier turns; watch KV cache growth in long generations. **Why this concept:** attention cost is the main reason “longer context = slower & heavier.” **Tradeoffs / alternatives:** bigger context helps recall; mitigation is better context management (summaries/RAG) rather than just raising the limit.

- **Context:** You’re implementing a local LLM service and keep hitting OOM at long context. **What you do:** Separate **weights memory** vs **KV cache**; reduce context length first; lower batch size; use quantization for weights; monitor RAM/VRAM while generating, not just at model load. **Why this concept:** attention’s KV cache scales with \(T\) and layers. **Tradeoffs / alternatives:** if you truly need long context, you may need higher-memory hardware or architectures/engines optimized for long context.

- **Context:** You’re building RAG and answers ignore a key fact that *is* in retrieved text. **What you do:** Improve *ordering* and *precision* of context: smaller chunks, put most relevant near the ends, add reranking (cross-encoder), limit total context size, and test “lost in the middle” sensitivity. **Why this concept:** attention is a finite budget; noisy or badly-ordered context dilutes focus. **Tradeoffs / alternatives:** more context can hurt; fewer higher-quality chunks often wins.

- **Context:** You want to understand why LLMs can do coreference (“it”, “they”, variable names) and long-range dependencies. **What you do:** Inspect attention maps in a small model; relate heads to patterns (induction heads, delimiter tracking, matching braces in code); test with controlled prompts. **Why this concept:** attention is the mechanism that directly connects distant tokens. **Tradeoffs / alternatives:** not all “reasoning” is attention; MLPs store and transform features too.

- **Context:** You’re fine-tuning and the model becomes “forgetful” or style-biased. **What you do:** Check if you’re changing the model’s internal routing of information: prompts become dominated by recent tokens; monitor training data formatting; consider LoRA rank/target modules (often includes attention projections). **Why this concept:** attention projections \(W_Q,W_K,W_V,W_O\) are a large, sensitive part of model parameters. **Tradeoffs / alternatives:** sometimes tuning only MLPs or using prompt/prefix-tuning is safer.

- **Context:** You’re comparing architectures (MHA vs grouped-query attention, multi-query attention) for serving. **What you do:** Choose attention variants that reduce KV cache size by sharing keys/values across heads; benchmark throughput and quality at your target context. **Why this concept:** attention storage and bandwidth dominate inference costs at long context. **Tradeoffs / alternatives:** aggressive sharing can reduce quality; pick based on your workload.

## Common gotchas (examples)

- **Gotcha: Confusing “attention is like retrieval” with “the model can search arbitrarily far.”** **What goes wrong:** You expect perfect recall from huge context; the answer misses details or fixates on recent text. **Likely cause:** attention is *soft* and budget-limited; signals compete; position/ordering effects matter. **Fix / verify:** reorder context (most relevant near ends), reduce noise, add reranking, and test with targeted probes (place the same fact at different positions).

- **Gotcha: Treating OOM as only “model too big.”** **What goes wrong:** Model loads fine, but crashes or slows drastically during long responses. **Likely cause:** KV cache growth with context length and generated tokens. **Fix / verify:** reduce context (`num_ctx`), reduce max tokens, lower batch size; monitor VRAM/RAM during generation; distinguish prefill vs decode.

- **Gotcha: Assuming more retrieved chunks always helps RAG.** **What goes wrong:** As you increase \(k\), answer quality gets worse. **Likely cause:** attention gets diluted; irrelevant chunks steal probability mass; “lost in the middle.” **Fix / verify:** cap context size, rerank top-k, drop near-duplicates, and evaluate accuracy vs chunk count.

- **Gotcha: Over-interpreting attention visualizations.** **What goes wrong:** You conclude “the model used token X” because a head attended to it. **Likely cause:** attention is one pathway; multiple heads/layers interact; causal attribution is non-trivial. **Fix / verify:** use controlled ablations (remove/alter the token and re-run), compare across layers/heads, and rely on behavioral tests more than single-head maps.

## Related concepts

- **Transformer blocks (residual + MLP + norms)** — Attention is one sublayer; the MLPs and residual pathways do much of the feature computation and storage too.
- **KV cache** — Practical memory/time consequence of attention during generation; often the bottleneck in long chats.
- **Positional encoding (RoPE, ALiBi, etc.)** — How the model knows token order; strongly affects long-context behavior.
- **Multi-query / grouped-query attention (MQA/GQA)** — Attention variants that reduce KV cache size for faster serving.
- **FlashAttention / fused attention kernels** — Implementation tricks that make attention faster and more memory-efficient.
- **RAG + reranking (cross-encoders)** — Systems approach to give attention cleaner, higher-signal context (`vault/topics/machine-learning/vectorization/reranker.md`).
- **“Lost in the middle”** — Empirical phenomenon: models underweight info in the middle of long contexts; impacts prompt/RAG design.
- **MoE vs dense** — Orthogonal to attention, but both interact with real memory limits; KV cache remains even with MoE (`vault/topics/machine-learning/llm/moe-models-and-older-hardware.md`).

## References

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) — Original Transformer paper; defines scaled dot-product attention and multi-head attention.
- [The Annotated Transformer](https://nlp.seas.harvard.edu/annotated-transformer/) — Clear walk-through with equations and code.
- [FlashAttention](https://arxiv.org/abs/2205.14135) — Practical attention implementation optimized for memory and speed.
- [Parameters in Large Language Models](vault/topics/machine-learning/llm/parameters.md) — In-repo note listing attention projection matrices (Q/K/V/O) as key parameter groups.
- [Mixture-of-Experts (MoE) models and older hardware](vault/topics/machine-learning/llm/moe-models-and-older-hardware.md) — In-repo discussion highlighting KV cache and context-length memory constraints in real serving setups.
- [Reranker](vault/topics/machine-learning/vectorization/reranker.md) — In-repo note on cross-encoders, relevant to “token-level interaction” and improving context quality for attention.
- [Relative links to other md files](vault/projects/hal9000/done/relative-links-to-other-md-files.md) — In-repo linking convention used above.
