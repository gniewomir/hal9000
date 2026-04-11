---
id: 019d7cd7-d560-7754-a90c-ce7a90bca7fd
references: []
---

# Parameters in Large Language Models

## The simple version

Think of an LLM as a massive spreadsheet filled with numbers. Each number is a **parameter**. Before training, these numbers are essentially random noise. During training the model reads enormous amounts of text and, through trial and error, nudges every single number a tiny bit so that the model becomes better at predicting what word comes next. After billions of these nudges the numbers encode everything the model "knows" — grammar, facts, reasoning patterns, style, even common sense.

When someone says a model has **7 billion parameters**, they mean there are 7 billion of these individually tuned numbers inside. More parameters generally means the model can memorize more patterns and handle subtler distinctions, but it also means more memory, more compute, and more energy to run.

A useful analogy: parameters are to an LLM what synaptic strengths are to a brain. The architecture is the wiring diagram; the parameters are how strongly each wire conducts.

## Diving deeper

### What parameters actually are

Parameters are the **learnable coefficients** of the mathematical functions that compose the model. In a Transformer-based LLM (GPT, LLaMA, Claude, etc.) the vast majority fall into a few categories:

- **Weight matrices** — dense matrices inside linear layers. Every attention projection (Query, Key, Value, Output) and every feed-forward/MLP block contains one or more weight matrices. They perform the core vector-to-vector transformations that give the model its representational power.
- **Biases** — small per-neuron additive offsets applied after a linear transform. Many modern architectures (LLaMA, Mistral) drop biases entirely to simplify and save memory.
- **Embedding tables** — a lookup matrix of shape `(vocab_size, hidden_dim)`. Each row is a learned vector for one token in the vocabulary. In models that tie input and output embeddings, this single table can account for a significant fraction of total parameters.
- **Layer-norm / RMSNorm parameters** — per-dimension scale (and sometimes shift) vectors used to stabilize activations between layers. Small in count, but critical for training stability.

### How training shapes them

1. **Initialization** — parameters start from a controlled random distribution (e.g. Xavier/He init) so that signals neither vanish nor explode as they pass through layers.
2. **Forward pass** — input tokens are embedded, passed through layers, and produce a probability distribution over the next token.
3. **Loss computation** — the predicted distribution is compared to the actual next token using cross-entropy loss.
4. **Backpropagation** — gradients of the loss with respect to every parameter are computed via the chain rule.
5. **Optimizer step** — an optimizer (typically AdamW) uses the gradients (plus momentum and second-moment estimates) to update each parameter by a small amount controlled by the **learning rate**.
6. **Repeat** — trillions of tokens later, the parameters converge to values that make the model a competent text predictor.

### Parameter count vs. model quality

Parameter count is a **necessary but not sufficient** predictor of capability:

- **Scaling laws** (Kaplan et al., Hoffmann et al. / "Chinchilla") showed that model quality follows power-law curves in parameters *and* training tokens. A 7B model trained on enough data can outperform a 70B model trained on too little.
- **Architecture matters** — Mixture-of-Experts (MoE) models like Mixtral have a huge total parameter count but only activate a fraction per token, decoupling capacity from per-token compute.
- **Data quality matters** — a well-curated dataset can outweigh raw parameter count; the Phi family of models demonstrated strong performance at small parameter sizes by focusing on high-quality data.

### Memory footprint

The parameter count directly determines how much memory a model needs at inference:

| Precision | Bytes per parameter | 7B model | 70B model |
|-----------|--------------------:|----------:|----------:|
| FP32      | 4                   | 28 GB     | 280 GB    |
| BF16/FP16 | 2                   | 14 GB     | 140 GB    |
| INT8      | 1                   | 7 GB      | 70 GB     |
| INT4      | 0.5                 | 3.5 GB    | 35 GB     |

Training requires additional memory for gradients, optimizer states, and activations — roughly 3–4x the model weights for AdamW in full precision.

## Examples

**LLaMA 3 8B** — 8 billion parameters organized into 32 Transformer layers with a hidden dimension of 4096 and 32 attention heads. Fits comfortably on a single 24 GB consumer GPU in INT4 quantization.

**GPT-3** — 175 billion parameters across 96 layers, 12,288 hidden dimension, 96 attention heads. Required a cluster of high-end GPUs just for inference when it launched in 2020, and its training cost was estimated at several million dollars.

**Mixtral 8×7B (MoE)** — roughly 47 billion total parameters, but only about 13 billion are **active** per token because a router selects 2 out of 8 expert MLP blocks for each token. This gives near-70B quality at closer to 13B inference cost.

**LoRA fine-tuning** — instead of updating all parameters, LoRA injects small rank-decomposed matrices (often 0.1–1% of total parameter count) that are the *only* parameters trained. A LoRA adapter for a 7B model might add only 10–50 million trainable parameters while keeping the base weights frozen.

## Related concepts

| Concept | One-liner |
|---------|-----------|
| **Weights** | The bulk of parameters; matrices that transform vectors layer by layer. |
| **Biases** | Small per-neuron offsets added after linear transforms (omitted in many modern architectures). |
| **Embedding table** | Parameters that map token IDs to dense vectors; often a large slice of total count. |
| **Attention heads** | Parallel attention projections; more heads = more Q/K/V/O weight matrices. |
| **FFN / MLP block** | Up/down projections between residual blocks; typically the largest non-embedding parameter group. |
| **Quantization** | Reducing bits per parameter to shrink memory footprint, sometimes at a quality cost. |
| **LoRA / adapters** | Training a small extra set of parameters instead of full fine-tuning. |
| **Active parameters (MoE)** | In Mixture-of-Experts, only a subset of total parameters fires per token. |
| **Hyperparameters** | Settings like learning rate, batch size, and layer count — chosen by humans, *not* learned. |
| **Scaling laws** | Empirical power-law relationships between parameter count, data size, and model loss. |
| **FLOPs** | Floating-point operations per forward pass; scales with parameters and sequence length. |
| **VRAM** | GPU memory required; roughly parameter count × bytes-per-parameter at chosen precision. |
| **Overfitting** | Too many parameters relative to data causes the model to memorize rather than generalize. |
