---
layout: default
title: "How Fast Is Gemma 4 26B on a MacBook Pro?"
---

*Companion to the [26B agentic eval](article-draft-26b-sonnet46-20260407). That piece asked whether the model is capable enough to drive an agent loop. This one asks the more basic question it glossed over: how fast does it actually run?*

# How Fast Is Gemma 4 26B on a MacBook Pro?

In the [agentic eval](article-draft-26b-sonnet46-20260407) I showed Gemma 4 26B can drive a local agent loop — tool use, memory, skills, multi-step planning, error recovery. What I didn't dwell on was the raw question that decides whether any of it matters: how fast is this thing?

This post is the performance characterization I should have published first. Same machine, same model, same llama.cpp build. Numbers only.

The headline: **1610 tokens/sec prompt processing, 54 tokens/sec generation**, on an Apple M5 Pro with 48 GB unified memory, using llama.cpp's Metal backend with Accelerate and flash attention. That's fast enough to feel like a real-time chat model, and the curves are flat enough that longer contexts don't collapse the experience.

Here's what the envelope actually looks like.

## The Setup

| | Value |
|---|---|
| **Hardware** | MacBook Pro, Apple M5 Pro, 48 GB unified memory |
| **Model** | [`unsloth/gemma-4-26B-A4B-it-GGUF`](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) |
| **Architecture** | MoE — 25.23 B total params, ~4 B active per token |
| **Quantization** | Q8_0 (25.00 GiB on disk) |
| **llama.cpp** | commit `d6f303004` (tag `b8738`) |
| **Build** | Metal + Accelerate (BLAS) + SME + dotprod + i8mm |
| **GPU working set** | 40,200 MB (recommended max, Metal) |

The build was literally:

```bash
cmake -B build
cmake --build build --config Release -j
```

No custom flags. On macOS, llama.cpp's defaults already enable Metal, link Accelerate, and detect CPU features — on Apple Silicon it found `dotprod + i8mm + sme` and auto-compiled with `-mcpu=native+dotprod+i8mm+nosve+sme`. The SME path matters: M5 Pro exposes Scalable Matrix Extension, and llama.cpp has SME-tuned kernels that take advantage of it on the CPU side.

Two benign warnings at configure time: OpenMP not found (irrelevant — Accelerate and Metal carry the compute) and ccache not found (rebuild speedup only). Neither affects runtime throughput.

## The Benchmark

`llama-bench` is llama.cpp's built-in throughput tool. It reports two metrics that between them describe nearly everything you care about for interactive use:

- **`pp<N>`** — **prompt processing** at batch size `N`. Tokens/sec for feeding prompt context into the model. This decides how long you wait before the first token streams.
- **`tg<N>`** — **token generation** for `N` output tokens. Tokens/sec once the model is generating. This sets the chat feel.

Both are measured with multiple repetitions per test and reported with a standard deviation, so you can tell noise from signal. Every number below is real measurement, not a single-run anecdote.

## Baseline

```bash
./build/bin/llama-bench -m $model
```

| test | t/s |
|---|---|
| pp512 | 1610.52 ± 10.28 |
| tg128 | 53.72 ± 0.40 |

For a 25 GiB model on a laptop, this is fast. 54 tokens/sec is comfortably above what I consider "real-time feel" territory — roughly 20 t/s is the floor for a chat experience that doesn't make you wait, and 54 is snappy enough that you stop noticing the latency. 1610 t/s prompt processing means a 4 k prompt preloads in about 2.5 seconds, which is imperceptible in practice.

The standard deviation on tg128 is 0.74 % of the mean. This machine/model/backend combination is very stable — small run-to-run deltas in later tests will be meaningful.

## Prompt and Generation Sweep

```bash
./build/bin/llama-bench -m $model -p 128,512,2048 -n 64,128,256
```

| test | t/s |
|---|---|
| pp128 | 1082.24 ± 12.14 |
| pp512 | 1622.75 ± 12.56 |
| pp2048 | 1545.26 ± 3.79 |
| tg64 | 54.56 ± 0.18 |
| tg128 | 54.58 ± 0.08 |
| tg256 | 54.30 ± 0.33 |

The prompt processing curve tells a clear story:

- **pp128 is slow.** Small batches don't fill the Metal execution units; there's fixed launch overhead per kernel and the matmul shapes are too small for peak throughput.
- **pp512 is the sweet spot.** The matmul kernels are running flat out.
- **pp2048 drops only ~5 %.** Attention cost is growing with sequence length (quadratic in the worst case), but not enough to collapse throughput. Extrapolating, an 8 k prefill should still land around ~1300 t/s — about 6 seconds to ingest. This is the single most important number if you care about long-context agentic workloads.

The generation curve is flatter than the table even suggests: **54.56 → 54.58 → 54.30** across 64, 128, and 256 tokens. The standard deviation of ±0.08 on tg128 is ~0.15 % of the mean — about as tight as benchmark data gets.

That flatness is the signature of a well-behaved MoE on unified memory. Generation is **bandwidth-bound on the 4 B active expert weights**, not on the attention cache. The KV cache at 256 tokens is small enough that it isn't pressuring anything yet. You should see this number hold up until the cache grows large enough to compete for memory bandwidth — several thousand tokens of context, probably.

## Flash Attention On vs Off

```bash
./build/bin/llama-bench -m $model -fa 0,1
```

| fa | pp512 | tg128 |
|---|---|---|
| 0 | 1609.76 ± 6.67 | 54.25 ± 0.15 |
| 1 | 1645.65 ± 4.07 | 55.08 ± 0.12 |

**Deltas:** pp +2.2 %, tg +1.5 %. Both are statistically significant (roughly 10× the stdev for each metric) but small in absolute terms.

The reason is simple: at 512-token prompts and 128-token generation, attention is a tiny slice of total compute. The expert FFN matmuls dominate, and flash attention doesn't touch those. Flash attention's benefit grows quadratically with context length, so it stays quiet until context gets long. **At 8 k+ context this gap should open up into the 10–20 % range on pp**, and become visible on tg as the KV cache starts pressuring generation bandwidth. That's the follow-up run I want to do next.

One thing worth calling out: **`-fa 1` is not the default in `llama-bench`**. The baseline run above (no `-fa` flag) sits squarely on the fa=0 numbers, not the fa=1 numbers — so if you want flash attention in practice you have to ask for it explicitly. In `llama-cli` and `llama-server` you want `--flash-attn`; in `llama-bench` you want `-fa 1`. Cheap to enable, small but free upside at short context, bigger upside as context grows. Always turn it on.

## Thread Count

```bash
./build/bin/llama-bench -m $model -t 4,6,8
```

| threads | pp512 | tg128 |
|---|---|---|
| 4 | 1610.35 ± 10.69 | 54.17 ± 0.57 |
| 6 | 1598.98 ± 21.82 | 53.95 ± 0.41 |
| 8 | 1607.88 ± 7.00 | 52.50 ± 1.34 |

Thread count is a no-op on this workload. All three pp numbers land within 1 % of each other — inside the noise band. This is the correct behavior: when Metal is carrying the compute, CPU threads are only orchestrating kernel launches and buffer management. More threads can't make that phase faster; they just add scheduler overhead.

The one data point worth a second look: **tg at 8 threads is ~1.5 t/s lower with 3× the stdev** of the other runs (±1.34 vs ±0.4). The mean move is on the edge of statistical significance, but the jump in variability is unambiguous. My read is that with `-t 8` the orchestration threads start catching jitter from efficiency-core scheduling or QoS contention on the M5 Pro's performance cores. You don't lose much in absolute terms, but you lose reproducibility.

**Practical takeaway:** leave `-t` at the default (6). It's in the flat part of the curve and leaves CPU headroom for whatever else the system is doing. If you see anyone claim "bump `-t` for more perf on Mac" — this table is the counter-argument.

## What It Means

### The MoE signature

The numbers above are what a well-behaved 4-B-active MoE looks like on Apple Silicon:

- **Generation throughput ≈ dense 4 B model speed**, not 26 B model speed. You're not paying the 26 B tax on the hot loop — only on the prefill.
- **Prompt throughput ≈ 26 B model speed**, because prefill touches all the weights regardless of routing.
- **Both curves are stable** across reasonable context and generation lengths.

A back-of-envelope sanity check on the generation number: 54 tokens/sec × ~4 B active params × ~1 byte/param (Q8_0) ≈ **215 GB/s of effective memory bandwidth used**. That's a healthy fraction of what Apple Silicon's unified memory can push on this tier of hardware. In practical terms, llama.cpp's Metal kernels are leaving very little on the table — if you were hoping to squeeze 2× more out of this stack by tuning, you'd be disappointed. The ceiling here is memory bandwidth, not software.

### What this buys you

At 54 t/s, Gemma 4 26B on a MacBook Pro is:

- **Fast enough for interactive chat.** You don't wait for responses; they stream at reading speed or faster.
- **Fast enough for agentic loops.** A five-tool-call loop with ~200 tokens of response each runs in ~20 seconds. Usable for real work, not just demos.
- **Fast enough for background tasks.** Summarization, code review, research synthesis — all run faster than you can consume the output.
- **Slow enough that batch jobs need planning.** Running this over a 10,000-document corpus is still a multi-hour job, not a minute. For scale you still want cloud.

And because it runs locally:

- Zero marginal cost per token.
- Full privacy — nothing leaves the machine.
- No rate limits, no quota, no account.
- Works offline, on a plane, on an air-gapped network.

### Two questions, two answers

The capability question — *is this model good enough to actually drive an agent?* — is what the [companion eval](article-draft-26b-sonnet46-20260407) answers. Short version: yes, with caveats around codebase-grounded reasoning where Sonnet is still meaningfully stronger.

The performance question, which this post answers, is simpler: **yes, with no caveats at all**. On an M5 Pro, Gemma 4 26B is a real tool, not a demo.

## What I'd Benchmark Next

The numbers above describe short-context behavior. The interesting territory is what happens as context grows:

```bash
./build/bin/llama-bench -m $model -p 2048,4096,8192,16384 -n 128 -fa 0,1
```

Two things that tells you:

1. **Where the prompt processing curve bends.** At some sequence length pp throughput will drop noticeably. Knowing where sets your realistic context budget.
2. **How much flash attention actually buys you at long context.** This is where the FA delta should become material.

I'd also want to sweep quantization (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`) on the same model to build a speed-vs-quality tradeoff table. It's especially interesting for MoE models because the active params are so much smaller than the total — the bandwidth relief from lower quant is correspondingly smaller, which is not how people usually intuit the tradeoff.

Both of those are coming in the next piece.

---

*Tested on llama.cpp commit `d6f303004` (tag `b8738`), built with defaults on macOS. April 9, 2026.*
