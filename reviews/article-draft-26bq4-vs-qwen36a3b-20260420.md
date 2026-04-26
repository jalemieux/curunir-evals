---
layout: default
title: "4 Active Experts vs 3: Gemma 26B-A4B vs Qwen3.6 35B-A3B on the Same Box"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. This entry drops the usual Sonnet 4.6 baseline and runs two local CPU-only Q4_K_M models head-to-head on the same hardware. Single-run, no repeated trials — directional, not definitive.*

# 4 Active Experts vs 3: Gemma 26B-A4B vs Qwen3.6 35B-A3B on the Same Box

The [Qwen3.6 35B-A3B article](article-draft-qwen36a3b-sonnet46-20260420) flagged two failure modes earlier today: empty responses from the local inference endpoint, and a confident wrong guess on the model-config prompt. It also noted that Qwen's context window (131K) finally cleared the multi-file reads the original [Gemma 26B Q4_K_M run](article-draft-26bq4-sonnet46-20260411) couldn't handle at 8K.

This run closes that loop. Same box. Same Unsloth Dynamic Q4_K_M scheme. Same 131K context. Same harness commit (`1adc308`). Same 24 prompts. The only variable is the model — Gemma 4 26B-A4B vs Qwen3.6 35B-A3B. A direct test of what an extra active expert buys you when the total weight class is roughly comparable (26B vs 35B, 4B active vs 3B active).

24 of 24 vs 22 of 24. The denser model wins on reliability. No empty responses, no bailouts, no refusals on Gemma; Qwen dropped two prompts to silent completions. On the twelve prompts where they're interchangeable, they're truly interchangeable. On the four prompts where both struggle, they struggle in strikingly similar ways — to the point that one failure (prompt 22, "what model am I running") produces nearly identical wrong answers from both.

## The Setup

| | Gemma 4 26B-A4B | Qwen3.6 35B-A3B |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Local (OpenAI-compatible API) |
| **Hardware** | AMD Ryzen 7 8745HS (8c/16t), 32GB RAM, Radeon 780M iGPU (unused) | (same box) |
| **OS** | Ubuntu | Ubuntu |
| **Architecture** | 26B MoE (~4B active) | 35B MoE (~3B active) |
| **Quantization** | Unsloth Dynamic Q4_K_M | Unsloth Dynamic Q4_K_M |
| **Inference engine** | llama.cpp (CPU-only) | llama.cpp (CPU-only) |
| **Context window** | 131,072 tokens | 131,072 tokens |
| **Harness commit** | `1adc308` | `1adc308` |
| **Cost** | Free | Free |
| **Privacy** | Full — nothing leaves the machine | Full — nothing leaves the machine |

Same harness, same tools, same system prompt, same physical hardware. Both ran through [Curunir](https://github.com/jalemieux/curunir).

Full results: [Gemma 4 26B-A4B](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260420-081000-openai_gemma-4-26B-A4B-it-UD-Q4_K_M.md) | [Qwen3.6 35B-A3B](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260419-224212-openai_Qwen3_6-35B-A3B-UD-Q4_K_M.md)

One note before reading the prompt-level detail: this Gemma run is different from the [April 11 26BQ4 run](article-draft-26bq4-sonnet46-20260411). That earlier one ran at 8K context, hit two "conversation is too long" bailouts on prompts 6 and 21, and had a single empty response on prompt 1. This one, at 131K, clears all three cleanly. The hardware hasn't changed. The model hasn't changed. The context-window bump alone closed the infrastructure-driven gap.

## Results

### Gemma 26B-A4B completed 24 of 24 prompts. Qwen3.6 35B-A3B completed 22.

No empty responses from Gemma. No bailouts. Two empty responses from Qwen on prompts 7 and 17. On the 22 prompts both completed, the quality delta is small — and on four of those, the two models fail in nearly identical ways.

### Where They're Equal (12 prompts)

**Basic tool use (1–3):** Both grepped for async and found the same two files, both read `identity.md` and produced one-sentence summaries, both listed the working directory with `pwd && ls`. Tool-call counts match.

**Memory retrieval (8, 9):** Both read `memory/README.md` and `projects.md` in two calls; both produced the same project breakdown. Both read the same Sarah Okafor profile in 3–4 calls. Substantively equivalent.

**Identity and skills (10, 11):** Both identified themselves as curunir. Both listed the same 11-skill manifest. Gemma did it in 0 tool calls; Qwen re-read `identity.md` first. Same answer.

**Haiku (12):** Both wrote one. No tool calls.

**Web-search skill (13):** Both had to improvise — the `web-search` SKILL.md doesn't exist on disk. Both tried `run_skill`, fell back to curl against the Brave API, and delivered a multi-source summary of "asyncio best practices 2025." Gemma took 12 tool calls and 2,513 tokens; Qwen took 7 tool calls and 1,709 tokens. Qwen is leaner; Gemma's summary is slightly more organized. Call it a draw.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz`, both correctly flagged it as an eval sentinel appearing only in eval files, not code.

**Delegate comparison (20):** Neither read code. Both produced solid general-knowledge comparisons with tables. Qwen's "1–3 tool calls: direct. Procedural workflow: delegate." rule-of-thumb is the sharper line; Gemma's table is slightly more exhaustive. Comparable quality.

**Scheduled tasks (23):** Both ran `Schedule list`, got nothing, reported cleanly.

On these twelve prompts, the responses are effectively interchangeable. Tool selection, instruction following, and output formatting all hold up equivalently under Q4_K_M at ~5–10 tok/s.

### Where They Match on Hard Prompts (2 prompts)

**Code tracing (6):** Both produced full phase-by-phase traces of the WebSocket-to-tool-executor path, both cited files and line numbers, both included ASCII summary diagrams. Gemma did it in 9 tool calls, 10 iterations, 2,955 output tokens, 593 seconds of wall time. Qwen did it in 14 tool calls, 15 iterations, 4,176 tokens, 814 seconds. Qwen read more files (`ws.py`, `base.py`, `run.py`, `agent.py`, `llm.py`, `router.py`, `dispatcher.py`, `skill_tool.py`, `schemas.py`) against Gemma's core five. Both are codebase-grounded. Qwen's trace has more phases; Gemma's is tighter. Neither is wrong, and neither is Sonnet.

**Design decisions (21):** Both read `agent.py`, `dispatcher.py`, and `skills.py` and identified the same three decisions: the two-tier context trim, the sync/async dispatch split, and the frontmatter-driven skill contract. Line ranges match — both cited `agent.py:224–267` (Qwen) / `226–267` (Gemma), `dispatcher.py:42–56` / `43–54`, `skills.py:14–21`. Gemma used 3 tool calls, Qwen used 5. Gemma is more efficient; both are substantively identical.

These are the two hardest codebase-grounded prompts in the suite, and the two hardest for local CPU models at this weight class. Both models clear them. The earlier 26BQ4 run couldn't, because of context, not capability.

### Where Gemma Is Better (3 prompts)

**What do you know about me (7):** Gemma read nine memory files in nine iterations and produced a full user profile — family, projects, contacts, communication preferences, Sarah Okafor, current open tasks. 1,128 output tokens. Qwen read two files (`memory/README.md`, `preferences.md`) in two iterations and then emitted nothing. `Error: LLM returned empty response.` The exact files Qwen read are a correct starting point; it just never produced the summary.

**Deep-research deps (14):** Gemma found the skill file on the second read (`skills/deep-research/SKILL.md` after `context/skills/deep-research/SKILL.md` missed) and produced an answer grounded in the actual SKILL.md content — conditional source loading rules like "reddit-research: Consumer products, dev tools, sentiment/opinion" and the cross-referencing pattern. Qwen missed the path (`context/skills/**/SKILL.md` returned nothing) and answered from the system-prompt description instead. Same underlying knowledge, but Gemma's is codebase-grounded and Qwen's is manifest-derived.

**Failed import (17):** Gemma ran `python -c "import nonexistent_module"`, got `ModuleNotFoundError`, and explained it cleanly — exit code, Python's import search behavior, no special handling needed. Qwen ran the same command and emitted an empty response. Same setup, same tool output, different completion behavior.

The pattern across 7 and 17 is the same: Qwen finishes a tool call, the tool succeeds, and the completion emits no tokens. Gemma on the same hardware through the same endpoint on the same day does not exhibit this.

### Where Qwen Is Better (1 prompt)

**Skills using attach (5):** Qwen correctly identified deep-research as the only skill that uses the `attach` tool. It explicitly flagged email-send as a grep false positive — email-send's `attachments` parameter passes file paths to the Gmail API, which is a different mechanism from the agent `attach` tool. Gemma listed both deep-research and email-send as using `attach` and justified email-send's inclusion with "the `attach` tool is used to attach files (PDFs, CSVs, etc.) to outgoing emails" — conflating the Gmail API parameter with the agent tool. The [April 11 26BQ4 run](article-draft-26bq4-sonnet46-20260411) drew the distinction correctly. This run didn't. Single-run variance, same model family, same hardware.

### Where Qwen Failed (2 prompts)

Two silent failures, both `Error: LLM returned empty response`. No text, no error, no further tool calls.

- **Prompt 7** (memory retrieval): tool calls succeeded, completion emitted nothing.
- **Prompt 17** (error recovery on failed import): tool call succeeded, completion emitted nothing.

Gemma on the same box, same quant, same day: zero empty responses across all 24 prompts. This is strong single-run evidence that the empty-response failure mode is model-specific, not a property of the serving stack. The earlier [Qwen article](article-draft-qwen36a3b-sonnet46-20260420) left that question open — pointing at two local runs with empty responses and asking whether it was the inference runtime, a sampling edge, or a quant quirk. This head-to-head narrows the suspect list. Same runtime, same quant scheme, same hardware, same day — only one of the two models goes silent.

### Where Both Came Up Short (4 prompts)

**Multi-step planning (4):** Both used one tool call (read `identity.md`) and produced an "Option A: skill, Option B: built-in tool" framework answer. Both explicitly declined to investigate the actual dispatcher or tool-schema code, despite having 40-call budgets and full tool access. Gemma: 775 tokens, 77 seconds. Qwen: 1,003 tokens, 96 seconds. Same under-investigation failure mode both Q4 runs share with the earlier 26BQ4 article — the model recognizes the prompt is about adding a tool, retrieves a plausible general-purpose playbook from its weights, and stops.

**Context overflow (19):** Both wrong, but wrong differently. Gemma answered from knowledge with no tool calls and invented a pseudo-plausible story about memory-file offloading and identity-prompt continuity. Qwen read `identity.md` once and concluded "there's no documented context-overflow handling" — which is false, since `agent.py:226–267` implements exactly that. Qwen then correctly cited those lines on prompt 21, minutes later in the same session. The knowledge is reachable when the model opens the file. Neither answered prompt 19 by opening the file.

**Model config (22):** Both read `identity.md` and `agents.yaml`, both concluded "I'm running on Gemini because `gemini-search` is one of my skills," both stopped at 2–3 tool calls. Identical wrong answers from two different models, same reasoning path. Neither ran `printenv | grep MODEL`. This failure mode — inferring an answer from adjacent context rather than checking the authoritative source — is now confirmed across two independent local MoE runs. It looks like a property of how these models interpret the prompt, not of either model's individual weights.

**Test count (24):** Gemma ran 5 glob/find/bash combinations and concluded "0." Qwen ran 4 globs and concluded "Zero." The real answer is 202 (`pytest --collect-only`). Nine models into this series, still zero correct answers. No model has thought to run the test runner.

## Throughput and Latency

Same CPU, same quant scheme, same harness. Raw numbers across all 24 prompts:

| | Gemma 26B-A4B | Qwen3.6 35B-A3B |
|---|:-:|:-:|
| **Total wall time** | 2,170 s (36.2 min) | 2,388 s (39.8 min) |
| **Avg completion tok/s** | 7.61 | 7.15 |
| **Total completion tokens** | 15,334 | 14,595 |

Gemma produced ~5% more output across the eval and did it ~6% faster per token, finishing the full 24-prompt suite about 3.6 minutes sooner. The obvious expectation — fewer active experts should be faster per forward pass — doesn't hold here. Qwen routes through ~3B active vs Gemma's ~4B but reads slower in practice, likely because the 35B total weight footprint puts more pressure on the Ryzen's memory subsystem (32 GB DDR5, no GPU VRAM to fall back on). Active-param count predicts compute; total-param count predicts memory bandwidth. On a 32 GB CPU box running Q4_K_M, bandwidth is the bottleneck.

Two prompts dominate the wall-time delta:

- **Prompt 6 (WebSocket trace):** Gemma 593 s, Qwen 815 s. Qwen read more files and wrote ~40% more output tokens. The extra depth costs time.
- **Prompt 13 (web-search):** Gemma 277 s, Qwen 409 s. Both had to improvise around the missing SKILL.md; Qwen's improvisation took more iterations of wall-clock idle time even though it made fewer tool calls.

A confounder: Qwen's two empty-response failures (prompts 7 and 17) finished *fast* — 33.8 s and 18.2 s respectively, against Gemma's 178 s and 32.5 s. If Qwen had actually answered those prompts like Gemma did, its total wall time would be noticeably higher. The throughput comparison understates the real gap.

In practical terms: both models are usable for non-interactive agent workflows on this hardware. Neither is fast enough for conversational use — single complex prompts take 5–15 minutes, and the full eval is 30–40 minutes end-to-end. For scheduled jobs, background agents, and batch processing where wall time matters less than unit economics and privacy, either model works; Gemma just finishes sooner.

## Comparison

| | Gemma 26B-A4B | Qwen3.6 35B-A3B |
|---|:-:|:-:|
| **Prompts completed** | 24/24 | 22/24 |
| **Total wall time (24 prompts)** | 36.2 min | 39.8 min |
| **Avg completion tok/s** | 7.61 | 7.15 |
| **Empty responses** | 0 | 2 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Mixed (empty on 7) |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Mixed (empty on 17) |
| **Code tracing** | Strong | Strong (deeper) |
| **Multi-step planning** | Weak (generic) | Weak (generic) |
| **Instruction precision** | Pass | Mixed |
| **Self-directed exploration** | Mixed | Mixed |
| **Efficiency** | Strong | Mixed |
| **Knows when to stop** | Yes (sometimes too early on 5) | Yes (sometimes too early on 14) |

## What I Take Away

**Four active experts beats three on reliability at this weight class.** Gemma 26B-A4B clears 24/24. Qwen3.6 35B-A3B clears 22/24. Same box, same quant, same context window, same harness, same day. The difference is architectural: Gemma routes through ~4B active parameters, Qwen through ~3B. Total model size doesn't predict the delta — Qwen has 35B total weights and loses anyway. What matters is how much live capacity runs each forward pass.

**The empty-response failure is now confirmed model-specific, not hardware-specific.** The [Qwen article](article-draft-qwen36a3b-sonnet46-20260420) couldn't distinguish a model property from a serving-stack issue on single-run data. This run narrows it: same hardware, same inference runtime, same quant scheme, same day — Gemma produces zero empty responses across 24 prompts while Qwen produces two. Whatever causes the silent-completion mode lives in the model-and-sampler interaction, not in the Ryzen box or the llama.cpp build.

**Prompt 22 has become a pattern, not a fluke.** Two different local MoE models, run through the same harness, both concluded they must be running on Gemini because `gemini-search` is an available skill. Same reasoning path, same wrong answer, neither ran `printenv`. This is a prompt-specific failure mode, not a model-specific one — which means it's a harness or system-prompt signal worth fixing. The tool to answer correctly is one invocation away; both models chose to infer instead.

**Qwen's extra context depth shows up on prompt 6, not across the board.** Qwen's WebSocket-trace response is longer and reads more files than Gemma's — 14 tool calls vs 9, 4,176 tokens vs 2,955. That's real codebase work. It does not generalize to prompt 4, where Qwen under-invests exactly as much as Gemma does. Bigger context windows don't produce more thorough reasoning on their own; the model still has to decide to use them.

**On a 32 GB CPU box, memory bandwidth is the bottleneck, not compute.** Qwen routes through ~3B active parameters per token — one full billion fewer than Gemma's ~4B — and is *slower* per token (7.15 vs 7.61 tok/s) and slower end-to-end (39.8 min vs 36.2 min for the full 24-prompt suite). The predicted compute advantage of fewer active experts shows up only when memory isn't the limit. On this hardware, with no GPU and 32 GB of DDR5, the 35B total-weight footprint costs more bandwidth per forward pass than the 26B footprint saves through sparsity. Active-param count is a useful selector when the model fits comfortably; total-param count starts to dominate once memory pressure kicks in.

**The Q4_K_M CPU tier at 131K is now a stable floor.** Both of these models clear 90%+ of the eval on a $600 Ryzen box with no GPU. Both hit the hard codebase-grounded prompts. Both share the same three failure modes (generic planning, Gemini guess, no pytest). For workflows that tolerate wall times measured in minutes, either model is viable — Gemma for more reliable completion, Qwen for deeper single-prompt exploration when it decides to commit.

---

*Tested on Curunir. Gemma 4 26B-A4B and Qwen3.6 35B-A3B both at harness commit `1adc308`, both at Unsloth Dynamic Q4_K_M, both on an AMD Ryzen 7 8745HS (CPU-only, 131K context). Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 20, 2026.*
