---
layout: default
title: "Qwen3.6 35B-A3B on CPU: A Sparser MoE, Different Failure Modes"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline. This is a qualitative smoke test — single-run, no repeated trials — useful for spotting capability gaps, not for definitive model rankings.*

# Qwen3.6 35B-A3B on CPU: A Sparser MoE, Different Failure Modes

The [previous local-hardware article](article-draft-26bq4-sonnet46-20260411) ran Gemma 4 26B Q4_K_M on an AMD Ryzen 7 8745HS — 32GB of RAM, no GPU, CPU-only. It completed 21 of 24; the three failures were almost entirely about an 8K context ceiling hitting multi-file reads too hard.

This run is the same box. Different model: Qwen3.6 35B-A3B at Unsloth Dynamic Q4_K_M. More total weights (35B vs 26B), fewer active experts (3B vs 4B), and a 128K context window instead of 8K.

22 of 24 prompts completed. No context-limit bailouts — the bigger window takes multi-file reads in stride. The two failures are empty responses from the inference endpoint: the model finishes a tool call and then emits nothing. A third prompt returns a confident wrong answer. On the prompts Qwen3.6 clears, the quality is uneven — one delivers a 15-iteration code trace that out-depths Sonnet, another answers a multi-step planning prompt with a single tool call and "I don't have your specific codebase in front of me," in a codebase it has full tool access to.

## The Setup

| | Qwen3.6 35B-A3B | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Hardware** | AMD Ryzen 7 8745HS (8c/16t), 32GB RAM, Radeon 780M iGPU (unused) | Anthropic infrastructure |
| **OS** | Ubuntu | — |
| **Architecture** | 35B MoE (3B active) | Undisclosed |
| **Quantization** | Unsloth Dynamic Q4_K_M | N/A |
| **Inference engine** | llama.cpp (CPU-only) | — |
| **Context window** | 131,072 tokens | — |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

Same harness, same tools, same system prompt. Both ran through [Curunir](https://github.com/jalemieux/curunir).

Full results: [Qwen3.6 35B-A3B](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260419-224212-openai_Qwen3_6-35B-A3B-UD-Q4_K_M.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

A note on the harness version gap: Qwen3.6 ran at commit `1adc308`, Sonnet at `4e6d576`. The codebase evolved between those — the `delegate` tool was renamed to `run_skill`, a `people/sarah-okafor.md` memory file was added, and a few folders shifted. Where the two runs return different specifics for the same prompt (e.g., "find Python files with async"), both answers are correct for their snapshot.

## Results

### Qwen3.6 completed 22 of 24 prompts. Sonnet completed 23.

Two empty responses (prompts 7 and 17) and one confidently wrong answer (prompt 22). No context-overflow failures — the 128K window holds. The bigger problem is inconsistency: the model oscillates between over- and under-committing to tool use, sometimes within the same category.

### Where They're Equal (13 prompts)

**Basic tool use (1–3):** Both grepped for async, read `identity.md`, and listed the working directory. Qwen found `run_skill.py` where Sonnet found `delegate.py` — the tool was renamed between the runs; both correct for their snapshot.

**Memory retrieval (8, 9):** Both read the memory files and returned correct project lists and people summaries. Qwen picked up the newer `sarah-okafor.md` file that didn't exist in Sonnet's snapshot and surfaced a usable profile from it.

**Identity and skills (10, 11):** Both identified themselves as curunir. Both listed the same 11-skill manifest with minimal or zero tool calls.

**Haiku (12):** Both wrote one. No tool calls.

**Deep-research deps (14):** Both described the conditional source-selection pattern correctly. Qwen hit a path mismatch — it globbed `context/skills/deep-research/SKILL.md`, found nothing, and answered from the system-prompt description. Sonnet went through `load_skill` and got the full SKILL.md. Both arrived at substantively equivalent answers.

**Error recovery (16, 18):** Both handled the missing file cleanly. Both correctly flagged `zzz_no_match_zzz` as an eval sentinel rather than a codebase string.

**Delegate comparison (20):** Neither read code. Both produced solid general-knowledge comparisons of scope, context isolation, and usage. Qwen's rule of thumb — "1–3 tool calls: direct. Procedural workflow: delegate." — is a sharper one-liner than Sonnet's.

**Scheduled tasks (23):** Both ran `Schedule list`, found nothing.

On these prompts, the responses are essentially interchangeable. Tool schemas work. Dispatch works. Q4 quantization didn't degrade tool selection or instruction following.

### Where They Match on Hard Prompts (2 prompts)

**Code tracing (6):** Qwen went *bigger* than Sonnet. 15 iterations, 14 tool calls, **4,176 output tokens** — a full phase-by-phase trace of the WebSocket-to-tool-executor path with a summary diagram in ASCII art. It read `ws.py`, `base.py`, `run.py`, `agent.py`, `llm.py`, `router.py`, `dispatcher.py`, `skill_tool.py`, and `schemas.py`, cited file:line for every step, and covered both the sync/async dispatch split and the context-overflow recovery path. Sonnet covered the same ground in 11 tool calls and 3,245 tokens. Both are codebase-grounded. Qwen's version takes 814 seconds of wall time to produce (≈ 13.5 minutes).

**Design decisions (21):** Qwen read all three requested files and called out specific line ranges: `agent.py:224–267` for the two-tier context strategy, `dispatcher.py:42–56` for the sync/async split, `skills.py:14–21` for the frontmatter-driven skill contract. Same grounding and same line-level specificity as Sonnet. 166 seconds of wall time.

Two hard prompts, both codebase-grounded, both matching Sonnet's depth. The 128K window and the willingness to read many files back-to-back pay off here — neither of these was reachable for the 26BQ4 run on the same hardware.

### Where Qwen3.6 Is Better (2 prompts)

**Attach skills (5):** Sonnet surfaced two candidates — deep-research and email-send — and included a distinction at the end that email-send's `--attach` is a CLI flag, not the agent tool. Qwen drew the line more cleanly: it identified deep-research as the only skill that actually uses the `attach` tool, and called out email-send as a grep false positive with a one-paragraph explanation. Same information, sharper structure.

**Context overflow (19):** Sonnet exhausted its 8-call budget searching for documentation and never produced a response — the series' canonical Sonnet failure. Qwen read `identity.md` and answered in one iteration. The content is partially wrong: the codebase *does* implement explicit context-overflow handling in `agent.py`. A partial answer beats no answer, but there's an uncomfortable inconsistency here — on prompt 21, Qwen correctly identifies the two-tier context strategy at `agent.py:224–267`. The knowledge is reachable when it opens the file; on prompt 19 it didn't.

### Where Sonnet Is Better (4 prompts)

**Multi-step planning (4):** Qwen used one tool call — a read of `identity.md` — and produced a generic "Option A: skill, Option B: built-in tool" framework with the disclaimer "I don't have your specific codebase in front of me." It had a 40-call budget and read none of the source. Sonnet read 12 files in 9 iterations and walked through the exact five-step process: `summarize.py`, `schemas.py` registration, `dispatcher.py` routing, README sync, tests. This is the same failure mode as the [Gemma 26BQ4 run](article-draft-26bq4-sonnet46-20260411) — a generic response from a model sitting on full tool access.

**Reddit skill (15):** The prompt explicitly says "Load it." Qwen didn't — it tried `run_skill`, got an error, globbed `context/skills/reddit-research/**`, found nothing on disk, and answered from the manifest description. Sonnet loaded the skill cleanly and explained the two-step Brave-then-Reddit-JSON pipeline with the rate-limit and User-Agent gotchas. Instruction-following gap, not a reasoning gap — and the same path assumption that affected prompt 14.

**Model config (22):** Qwen read `identity.md` and `agents.yaml` in three iterations, concluded "I'm configured to run on Gemini" based on the presence of a `gemini-search` skill, and stopped. The answer is wrong. Sonnet ran `printenv | grep MODEL` and returned the actual configured model. Qwen didn't hit its tool budget — it decided it knew the answer from adjacent signals and didn't verify. This is a new failure mode in the series: confident guessing from nearby context instead of checking the authoritative source. The fix — one `printenv | grep MODEL` — was one tool invocation away.

**People (9):** Both completed, but Sonnet's five-call summary is cleaner. Qwen used 5 iterations and occasionally redundant globs to find the same file. Substantively equivalent; stylistically Sonnet wins.

### Where Qwen3.6 Failed (2 prompts)

Both failures are identical in shape: `Error: LLM returned empty response.` No text, no further tool calls, no completion.

- **Prompt 7 (about the user):** Qwen read `context/memory/README.md` and `preferences.md` — exactly the right files — and then emitted nothing.
- **Prompt 17 (failed Python import):** Qwen ran `python -c "import nonexistent_module"`, saw the `ModuleNotFoundError`, and then emitted nothing.

This matches the [Gemma 26BQ4 empty-response failure on prompt 1](article-draft-26bq4-sonnet46-20260411) on the same hardware — the model gets to the point where it should summarize or explain, and produces no text. Both models were served through a local OpenAI-compatible endpoint on this Ryzen box. Whether the cause is the inference runtime, a sampling edge case, or a quantization quirk, single-run data can't say. What it can say: this is now two local runs on this hardware with the same class of silent failure.

### Where Both Failed

**Test count (24):** Qwen used 4 globs and concluded "Zero. This project has no test files." Sonnet used 5 calls and answered "0." The real answer is 202 (`pytest --collect-only`). Eight models into the series, still zero correct answers. No model has thought to run the test runner.

## Comparison

| | Qwen3.6 35B-A3B | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 22/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Mixed (empty on 7) | Pass |
| **Skill loading** | Mixed (didn't load on 15) | Pass |
| **Error recovery** | Mixed (empty on 17) | Pass |
| **Code tracing** | Strong (deeper than Sonnet) | Strong |
| **Multi-step planning** | Weak (1 tool call, generic) | Strong (codebase-grounded) |
| **Instruction precision** | Mixed | Strong |
| **Self-directed exploration** | Uneven | Strong |
| **Efficiency** | Mixed (wrong guess on 22) | Mixed |
| **Knows when to stop** | Yes (sometimes too early) | No (prompt 19) |

## Comparison with Gemma 26B Q4_K_M (Same Box)

Two local Q4_K_M models on the same Ryzen 8745HS, different architectures:

| | Gemma 26B Q4_K_M | Qwen3.6 35B-A3B |
|---|:-:|:-:|
| **Active params** | ~4B | ~3B |
| **Context window** | 8K | 128K |
| **Prompts completed** | 21/24 | 22/24 |
| **Code tracing (6)** | Fail (context) | Strong (814s) |
| **Design decisions (21)** | Fail (context) | Strong |
| **Multi-step planning (4)** | Weak (generic) | Weak (generic) |
| **Context overflow (19)** | Pass (zero tools) | Partial |
| **Empty responses** | Prompt 1 | Prompts 7, 17 |
| **Model config (22)** | Pass (1 call) | Fail (wrong guess) |

The 128K window unlocks the two hard prompts the 26BQ4 couldn't finish — no more "conversation is too long" bailouts. Qwen3.6 trades that for a second empty response, a confident wrong answer on config, and under-commitment on prompt 4. Different weaknesses, broadly similar completion rate.

## What I Take Away

**Sparse MoEs buy you ceiling, not consistency.** A 35B model with 3B active experts runs on CPU at roughly the same throughput as a 26B-A4B on the same box. You get more latent capacity, longer context, deeper responses on the hard prompts. What you don't get is uniform tool-call discipline. Qwen3.6 will read nine files when it decides to trace code, then read one file when it decides to plan a feature — both prompts had tool budgets that could have supported either strategy.

**The empty-response failure is now a pattern on this hardware, not a fluke.** The 26BQ4 run had one. This run has two. Both are locally-served GGUF models through an OpenAI-compatible endpoint on the same Ryzen box. The shape is the same: the model produces a tool call, the tool succeeds, and then the completion emits no tokens. This is worth isolating in its own investigation rather than treating as a model property — the repeat across two different models points at the serving stack, not the weights.

**Confident guessing is a new failure mode.** On prompt 22, Qwen decided it must be running on Gemini because `gemini-search` was one of its available skills, and stopped at three tool calls. It didn't exhaust its budget — it exhausted its interest. This is different from over-investigation (Sonnet's prompt 19) and different from over-reading (GLM-5.1's prompt 4). Qwen inferred an answer from adjacent context and didn't verify. The fix was one tool call.

**Prompt 6 is the reason to keep trying larger local models.** 15 iterations, 4,176 output tokens, 814 seconds of wall time. A complete phase-by-phase trace of the WebSocket-to-tool-executor path with cited file:line numbers and a summary ASCII diagram. It out-depths Sonnet's response on the same prompt. That this happens on a 32GB desktop with no GPU is the reason this series keeps running.

**The Q4 CPU local-model tier is converging.** [Gemma 26BQ4](article-draft-26bq4-sonnet46-20260411) cleared 21/24. Qwen3.6 35B-A3B clears 22/24. Both against the same Sonnet 4.6 baseline, on the same $600 box. The failure modes differ, but the ceiling is similar: interchangeable-quality answers on the easy two-thirds of the eval, codebase-grounded work on some of the hard ones, domain-specific failures on the rest. For workflows that tolerate wall times measured in minutes, this is a usable tier.

---

*Tested on Curunir. Qwen3.6 35B-A3B at harness commit `1adc308`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 20, 2026.*
