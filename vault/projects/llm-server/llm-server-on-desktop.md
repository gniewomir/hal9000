
# Repurpose gaming desktop as local LLM server

Instead of selling/trashing the gaming desktop, set it up as a local LLM inference server with Ollama. Other devices on the same local WiFi network call it via HTTP API for embeddings, generation, vision, etc.

## Hardware

| Component | Spec |
|---|---|
| OS | Ubuntu |
| PSU | SilentiumPC VERO M1 600W modular [SPC117] |
| Motherboard | MSI Z170A KRAIT GAMING 3X |
| CPU | Intel Core i7-6700 — 3.4/4.0 GHz (4 cores / 8 threads, 8 MB cache, 65W) |
| Cooling | Corsair H110i |
| GPU | NVIDIA GeForce RTX 3060 Ti LHR (GA104, rev a1) — **8 GB VRAM** |
| RAM | 24 GB DDR4 |

**Key constraint:** 8 GB VRAM determines which models can run fully GPU-accelerated. Anything larger partially offloads to CPU/RAM (slower). The i7-6700 has AVX2 (no AVX-512), fine for llama.cpp but ~20-30% slower on CPU inference than modern chips. DDR4 bandwidth (~30-35 GB/s) further limits partially-offloaded models.

## Architecture

The desktop acts as a single-purpose "inference appliance" — just Ollama. The application on the client device owns all orchestration.

```
Client device (app/laptop)                 Desktop (Ollama, GPU)
──────────────────────────                 ─────────────────────
                                           Ollama (8 GB VRAM)
                                           ├── nomic-embed-text  (~0.5 GB)
                                           ├── llama3.1:8b       (~5.5 GB)
                                           └── (models swapped as needed)
App logic
├── Vector DB (Chroma / Qdrant / SQLite)
├── Reranker (optional, CPU, see below)
├── Orchestration pipeline
│   1. Embed query         ──HTTP──►       /api/embeddings
│   2. Vector search       (local)
│   3. Rerank              (local, CPU, optional)
│   4. Build prompt
│   5. Generate            ──HTTP──►       /api/chat
└── UI / API
```

## Model recommendations

All VRAM figures assume Q4_K_M quantization unless noted. Assessment as of April 2025 — re-evaluate on the schedule noted per category.

### Embeddings (re-evaluate every ~6 months)

For generating and querying search embeddings. Must use the **same model** for both indexing and querying.

| Model | Dims | VRAM | Pros | Cons |
|---|---|---|---|---|
| **nomic-embed-text** (v1.5) | 768 | ~0.5 GB | Ollama-native, Matryoshka dims (truncate to 256/512), fast | Slightly behind top-tier on MTEB |
| mxbai-embed-large | 1024 | ~1.2 GB | Strong MTEB scores, Ollama-native | Larger vectors = more storage |
| snowflake-arctic-embed:m | 768 | ~0.5 GB | Good quality/size ratio | Less community adoption |
| all-minilm (L6-v2) | 384 | ~0.3 GB | Tiny, extremely fast | Lower retrieval quality |

**Pick:** `nomic-embed-text` — default for most Ollama RAG setups, Matryoshka lets you trade quality for storage later.

### General purpose (re-evaluate every ~3-4 months)

| Model | VRAM | Pros | Cons |
|---|---|---|---|
| **llama3.1:8b** | ~5.5 GB | Strong all-rounder, large ecosystem, good instruction following | 8B class ceiling |
| gemma2:9b | ~6 GB | Excellent for size, strong reasoning | Slightly higher VRAM |
| mistral:7b | ~5 GB | Fast, good structured output | Weaker complex reasoning |
| phi3:14b | ~8.5 GB | Punches above weight class | Partial GPU offload needed, slower |
| qwen2.5:7b | ~5 GB | Strong multilingual, good coding | Less English-centric community |

**Pick:** `llama3.1:8b` as daily driver. Try `phi3:14b` with partial offload when quality matters more than speed.

### Coding (re-evaluate every ~3 months)

| Model | VRAM | Pros | Cons |
|---|---|---|---|
| **qwen2.5-coder:7b** | ~5 GB | Very strong coding benchmarks for size | Newer, less battle-tested |
| deepseek-coder-v2:lite (16B) | ~9 GB | Excellent code quality, MoE | Won't fully fit in 8 GB VRAM |
| codegemma:7b | ~5 GB | Good completion, instruct variant available | Smaller context window |
| codellama:7b | ~5 GB | Code-specialized Llama, FIM support | Aging, surpassed by newer models |

**Pick:** `qwen2.5-coder:7b`. For a quality step-up with partial offload, try `deepseek-coder-v2:lite`.

### Vision / image processing (re-evaluate every ~4-6 months)

| Model | VRAM | Pros | Cons |
|---|---|---|---|
| **moondream2** | ~3.5 GB (fp16) | Tiny, fast, good OCR/description | Limited complex reasoning |
| llava-llama3:8b | ~6 GB | Llama 3 backbone, deeper image understanding | Higher VRAM |
| llava:7b | ~5.5 GB | Mature, well-supported | Older architecture |
| bakllava:7b | ~5.5 GB | Mistral-based, good quality | Less tooling |

**Pick:** `moondream2` for quick tasks. `llava-llama3:8b` when deeper reasoning about images is needed.

### Data extraction / structured output (re-evaluate every ~3-4 months)

Use the general-purpose model with Ollama's JSON mode (`format: json` in the API call). No need for a separate model — structured output is a prompting/format concern at this tier.

`llama3.1:8b` has excellent JSON mode and tool-use training. `qwen2.5:7b` also has strong native function-calling support.

## Reranking

Ollama has **no `/api/rerank` endpoint** — it only exposes `/api/generate`, `/api/chat`, and `/api/embeddings`. Reranking is a separate concern managed by the client application.

**Start without a reranker.** With a small corpus and `nomic-embed-text`, vector similarity alone is likely sufficient. Add a reranker only when retrieval quality becomes a bottleneck.

When you do need one, options from best to worst for this setup:

1. **Cross-encoder on client CPU** (recommended) — run `bge-reranker-base` (~400 MB) via `sentence-transformers` on the client machine. Adds ~100-200ms for 50-100 candidates. No VRAM contention on the desktop.
2. **Second inference server on desktop** — FastAPI wrapper around `sentence-transformers` or `llama.cpp` with a GGUF reranker. Works but adds operational complexity and competes for VRAM.
3. **RankGPT-style via Ollama `/api/chat`** — prompt the LLM to rank documents. Technically works but wastes a full inference pass (seconds) for something a cross-encoder does in ~100ms.
4. **External API (Cohere, Jina)** — simple but adds a cloud dependency to an otherwise self-hosted setup.

Watch [ollama/ollama#6350](https://github.com/ollama/ollama/issues/6350) for a potential native rerank endpoint.

See also: `topics/machine-learning/vectorization/reranker.md`

## TODO

1. **Prepare the desktop**
   - Clean install Ubuntu Server (or strip unnecessary services from desktop Ubuntu)
   - Install latest NVIDIA drivers + CUDA toolkit
   - Verify GPU: `nvidia-smi`
   - Configure static IP or hostname on local network

2. **Install and configure Ollama**
   - Install: `curl -fsSL https://ollama.com/install.sh | sh`
   - Set `OLLAMA_HOST=0.0.0.0` in the systemd service file (listen on LAN, not just localhost)
   - Pull initial models: `ollama pull nomic-embed-text && ollama pull llama3.1:8b`
   - Test from another device: `curl http://<desktop-ip>:11434/api/tags`

3. **Network and access**
   - Assign static IP or DHCP reservation on router
   - Optional: reverse proxy (Caddy/nginx) for HTTPS or basic auth on LAN
   - Optional: Tailscale for access outside home network

4. **Set up embedding pipeline**
   - Choose vector store (ChromaDB, Qdrant, or SQLite with sqlite-vss)
   - Write ingestion script: read files → chunk → embed via Ollama API → store
   - Write search endpoint: embed query → vector similarity → return results

5. **Integrate with client devices**
   - Point editor plugins / scripts at the Ollama API
   - For coding: configure Continue.dev or similar to use the local endpoint
   - For RAG: connect search pipeline to the general-purpose model

6. **Monitoring and maintenance**
   - GPU monitoring: `nvidia-smi dmon` or Grafana + Prometheus with nvidia_gpu_exporter
   - Track power consumption (expect 150-250W under inference load)
   - Auto-update script for Ollama and models
   - Re-evaluate model choices every 3-6 months

## Caveats

- **8 GB VRAM is the hard ceiling.** Only one ~7B model fits at a time with full GPU acceleration. Ollama swaps models automatically but incurs a ~2-5 second cold start.
- **Concurrent requests.** Batch embedding + querying simultaneously will cause slowdowns. Consider embedding in off-hours.
- **Power draw.** 80-100W idle, 200-250W under GPU load. Running 24/7 ≈ $15-30/month. Consider wake-on-LAN + auto-suspend if not always needed.
- **VRAM vs. context length.** Longer contexts consume more VRAM for KV cache. A 7B model at 4K context is fine; at 32K it may OOM. Stick with default context sizes.
- **Quantization floor.** Q4_K_M is the sweet spot. Don't go below Q3 — quality degrades noticeably. Q5/Q6 eats more VRAM for marginal gains.
- **DDR4 bandwidth.** CPU-offloaded layers are bottlenecked at ~30-35 GB/s. Partial offload works but tokens/sec drops significantly.
- **Security.** Binding to `0.0.0.0` exposes Ollama to all LAN devices. If the network has guests or IoT, add firewall rules or basic auth via reverse proxy.
- **Disk space.** Each 7B Q4 model ≈ 4 GB on disk. Keep Ollama's model directory on an SSD — HDD adds significant load times.
- **Model churn.** Local LLM landscape moves fast. Keep tooling model-agnostic via the Ollama API so you can swap models without code changes.
