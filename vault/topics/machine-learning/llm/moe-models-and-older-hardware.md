# Mixture-of-Experts (MoE) models and older hardware

## Short explanation (layman terms)

A **dense** language model uses the same big “brain chunk” for every word it processes: every layer’s main feed-forward block runs on every token. A **Mixture-of-Experts (MoE)** model is different: it keeps **several parallel “specialist” blocks (experts)** and a small **router** that picks **only one or two** of them for each token. So the model can store a lot of knowledge spread across many experts, but **each step of thinking** only pays the cost of a few experts, not all of them.

That sounds like free extra capacity on a weak PC, but there is a catch most people miss: **your disk and RAM still hold *all* the experts**, the same way a toolbox holds every wrench even if you only use two at a time. So MoE helps mainly with **quality per unit of compute during generation**, not with pretending the full model is as small as a 7B dense model in **memory**.

On **older hardware** (e.g. a few CPU cores, **8 GB VRAM**, **16–32 GB system RAM**), MoE is **not** a magic setting that turns a 47B-class model into something that “fits like 7B.” It *can* still help you **squeeze more capability** if you accept **partial GPU use**, **CPU offload**, slower tokens per second, or a **smaller MoE** whose **quantized checkpoint** actually fits your budget. What you **cannot** expect is to load an enormous MoE **fully on GPU** or to cut **VRAM needs** down to “active experts only” in typical **Ollama / llama.cpp** style serving.

## Theory (precise)

**Definitions:**

- **Expert:** In a Transformer block, the usual two-layer MLP (feed-forward network) is replaced by **N** parallel MLPs (“experts”). Each has its own weights.
- **Router / gating:** A learned function (often a small linear layer + softmax) produces a distribution over experts **per token** (sometimes per sequence prefix in variants). **Top-k routing** (commonly **k = 2**) means only **k** experts’ outputs are combined for that token’s FFN step.
- **Total vs. active parameters:** **Total** parameters count every expert and shared layers (attention, norms, embeddings). **Active** parameters per token approximate: shared stack + **k** times the per-expert FFN size (plus router), **not** the sum of all experts’ FFNs.

**Compute vs. memory asymmetry:** Routing reduces **FLOPs** for the FFN sublayer toward “roughly **k/N** of what N independent experts would cost if all ran,” but **weight storage** for standard inference still requires **all expert weights** to be available unless the runtime implements **expert offloading or on-demand loading** (uncommon in default consumer stacks).

**Quantization:** GGUF-style **INT4** weights reduce **bytes per parameter** uniformly; MoE checkpoints remain large because **parameter count** is large.

**Limits and assumptions:** Benefits assume **efficient kernels** for sparse expert execution; memory benefits require **true sparse residency** (not assumed in typical single-GPU Ollama workflows). **KV cache** and **context length** add memory **orthogonal** to MoE routing.

**In practice:** Treat **checkpoint size × quant** as the **first** feasibility filter for “will this run on my machine?” Use **`ollama ps`**, **GPU memory in `nvidia-smi`**, and **wall-clock tokens/sec** to see whether you are **GPU-bound**, **CPU-bound**, or **RAM-limited**. If VRAM is full and the process still uses lots of **system RAM**, you are likely in **partial offload** territory—MoE does not remove that pattern. Prefer **smaller total models**, **Q4-class quants**, and **shorter context** before chasing huge MoE names.

## Where it applies (examples)

- **Context:** You have **8 GB VRAM** and want **better coding quality** than a dense 7B without buying hardware. **What you do:** Pull a **MoE that fits partially on GPU** (e.g. a **lite** or **smaller** variant) with **Q4**; set expectations for **CPU offload** and test **`/api/chat`** latency on real prompts. **Why this concept:** MoE can deliver **higher effective capability** than dense models at similar **per-token compute**, which matters when the GPU is weak but CPU/RAM can absorb spillover. **Tradeoffs / alternatives:** A **dense 14B Q4** might be simpler to reason about than a **large MoE** with most layers on CPU; compare **tokens/sec** and **quality** empirically.

- **Context:** **24 GB system RAM** total, daily desktop use. **What you do:** Before committing to a big MoE, check **published GGUF size** and leave **headroom** for OS, browser, and **KV cache**; run **one model at a time** and avoid huge **context** in the client. **Why this concept:** MoE **does not shrink** resident weights; **RAM** is still the ceiling for **offloaded** layers. **Tradeoffs / alternatives:** **Smaller dense model** + better prompting or **RAG** often beats a **starved MoE** that thrashes.

- **Context:** You read marketing (“**47B** but only **~13B active**”) and expect **47B → 13B VRAM**. **What you do:** Re-read **total** vs **active**: plan for **full checkpoint** size at your quant; use **active** count only for **rough** speed vs dense-at-same-total-params comparisons. **Why this concept:** Avoid wrong mental model of **memory**. **Tradeoffs / alternatives:** Use **parameter** notes and **Ollama model cards** for **disk/VRAM** reality checks.

- **Context:** **Local LLM server** on an **older CPU** (few cores, no AVX-512). **What you do:** Any model with **heavy CPU offload**—MoE included—will be **CPU-limited**; profile **tokens/sec** and consider **smaller models** or **faster quant** tradeoffs. **Why this concept:** MoE saves **FFN compute** when sparse execution is efficient, but **CPU offload** paths may **not** feel sparse if implementation falls back to broader reads. **Tradeoffs / alternatives:** **Newer dense 8B** fully on GPU often **beats** **huge MoE** mostly on CPU for **interactive** use.

- **Context:** You want **one** “big brain” for both **chat** and **embeddings** on the same box. **What you do:** Keep **embedding model** tiny and separate (e.g. dedicated embed model); use MoE for **generation** only when it fits your **memory budget**. **Why this concept:** MoE does not remove the need for **multi-model** memory planning. **Tradeoffs / alternatives:** **Ollama** swaps models with a **cold-start** cost—plan workflows accordingly (see project server notes).

- **Context:** **Quality-first** batch jobs (rewrite, summarize overnight). **What you do:** Accept **slow** generation with a **larger MoE** using **partial offload**; tune **batch size** / **context** so you do not **OOM**. **Why this concept:** When **latency** does not matter, MoE’s **quality per FLOP** can justify **painful** throughput. **Tradeoffs / alternatives:** Cloud API or a **smaller model** + pipeline for **time-sensitive** work.

- **Context:** Comparing **Mixtral-class** vs **Llama 8B** on the same GPU. **What you do:** Benchmark **same prompt**, **same quant tier**, measure **tok/s** and subjective quality; check **VRAM** headroom for **longer context**. **Why this concept:** Empirical comparison beats **parameter marketing**. **Tradeoffs / alternatives:** **Llama 8B** may win on **simplicity and VRAM** for **short** tasks.

## Common gotchas (examples)

- **Gotcha: Confusing “active parameters” with “VRAM needed.”** **What goes wrong:** You pull a **large MoE**, Ollama loads, then **system RAM** spikes, **swap** thrashes, or the model **refuses** to run—despite “only 2 experts active.” **What to do instead / how to verify:** Check **total quantized size** before pulling; watch **`nvidia-smi`** vs **RAM** in **`htop`**; read **Ollama** output for **offload** behavior.

- **Gotcha: Expecting MoE to “switch off” unused experts in VRAM.** **What goes wrong:** You assume **7/8 experts stay on disk**; in common stacks **all experts** are **resident** in **combined** CPU/GPU memory for the loaded model. **What to do instead / how to verify:** Assume **full model resident** unless docs claim **expert paging**; if **VRAM** << **checkpoint size**, you are in **CPU/RAM** territory by design.

- **Gotcha: Ignoring router overhead and kernel efficiency.** **What goes wrong:** **Throughput** is worse than a **dense** model of similar **active** size because **routing**, **memory bandwidth**, or **partial** expert execution patterns hurt on **small GPUs**. **What to do instead / how to verify:** Benchmark **tok/s** against a **dense** baseline at similar **VRAM**; try **different quants** or **smaller** models.

- **Gotcha: Chasing MoE for **8 GB VRAM** when a **dense 8B Q4** already fits cleanly.** **What goes wrong:** You add **complexity** and **memory pressure** without beating **llama3-class 8B** on **latency** or **reliability**. **What to do instead / how to verify:** Define success metrics (**quality**, **tok/s**, **max context**); compare **side by side** on **your** tasks.

- **Gotcha: Long context + MoE + limited RAM.** **What goes wrong:** **KV cache** dominates; **OOM** or **crawl** even though “the model loaded.” **What to do instead / how to verify:** Reduce **`num_ctx`** / prompt size in client; monitor **RAM** during long generations.

## Related concepts

- **Quantization (Q4_K_M, etc.)** — Reduces weight footprint; combines with MoE math but does **not** turn total MoE size into active size; first lever on old GPUs.

- **GPU layer offload (`num_gpu` / Ollama environment)** — Controls how many layers sit on **VRAM** vs **CPU**; MoE models hit this like dense models when **checkpoint** is large.

- **KV cache** — Memory that grows with **sequence length**; independent of MoE routing, often the **real** limit in long chats.

- **Sparse training vs. sparse inference serving** — Research and some datacenter stacks exploit sparsity aggressively; **consumer Ollama** paths are often closer to **“load full weights, sparse compute where possible.”**

- **Scaling laws / Chinchilla** — Relates **parameters**, **data**, and **quality**; MoE is an **architecture** choice within that landscape, not a bypass of **memory physics.**

- **RAG and tool use** — Practical ways to **stretch** a small local model without larger checkpoints; orthogonal to MoE but often a better first step on **tight RAM.**

- **Mixtral-class architectures** — Canonical public example of **multi-expert** routing; useful reference point for **total vs. active** parameter discussions.

- **Expert parallelism (datacenter)** — How large deployments shard experts across devices; highlights why **single-GPU** stories differ from **cluster** stories.

## References

- [Ollama — documentation](https://github.com/ollama/ollama/blob/main/docs/README.md) — install, API, and runtime behavior for local models.

- [Mixtral of Experts (Mistral AI paper)](https://arxiv.org/abs/2401.04088) — routing, architecture, and the **total vs. active** parameter story at source.

- [llama.cpp](https://github.com/ggerganov/llama.cpp) — quantization and inference stack commonly behind Ollama; relevant to **memory** and **layer offload** behavior.

- [Parameters in Large Language Models](vault/topics/machine-learning/llm/parameters.md) — in-repo note on **parameter count**, **MoE example (Mixtral 8×7B)**, and **memory** tables.

- [Repurpose gaming desktop as local LLM server](vault/projects/llm-server/done/llm-server-on-desktop.md) — **8 GB VRAM** constraints, **Ollama** workflow, model picks, **MoE** example (`deepseek-coder-v2:lite`) and partial-offload reality.

- [Relative links to other md files](vault/projects/hal9000/done/relative-links-to-other-md-files.md) — how this vault expects **in-repo** markdown links.
