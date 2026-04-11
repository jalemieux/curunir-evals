---
layout: default
title: "Same Model, Half the Bits, No GPU"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline. This is a qualitative smoke test — single-run, no repeated trials — useful for spotting capability gaps, not for definitive model rankings.*

# Same Model, Half the Bits, No GPU

The [first article in this series](article-draft-26b-sonnet46-20260407) ran Gemma 4 26B at Q8_0 on a MacBook Pro with 48GB unified memory and Metal GPU offload. It completed all 24 prompts — the only local model to do so. This run takes the same model, drops the quantization to Q4_K_M, moves it off the Mac to an AMD Ryzen desktop with no discrete GPU, and runs inference on CPU only with an 8K context window.

21 of 24. Three prompts dropped — one blank response on the very first prompt, two from the model declaring "the conversation is too long." Where it works, the answers are nearly identical to the Q8_0 run. Where it breaks, the 8K context ceiling is the bottleneck, not the quantization.

## The Setup

| | Gemma 4 26B Q4_K_M | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Hardware** | AMD Ryzen 7 8745HS (8c/16t), 32GB RAM, Radeon 780M iGPU (unused) | Anthropic infrastructure |
| **OS** | Ubuntu 24.04 | — |
| **Architecture** | 26B MoE (4B active) | Undisclosed |
| **Quantization** | Q4_K_M (GGUF, Unsloth Dynamic) | N/A (full precision) |
| **Inference engine** | llama.cpp `b8740` (`e34f04215`), GCC 13.3.0 | — |
| **GPU offload** | None (`-ngl 0`, CPU-only) | — |
| **Context window** | 8,192 tokens | — |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

Same harness, same tools, same system prompt. Both ran through [Curunir](https://github.com/jalemieux/curunir).

Full results: [Gemma 4 26B Q4_K_M](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260409-233506-openai_gemma-4-26B-A4B-it-UD-Q4_K_M.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### Gemma 26B Q4_K_M completed 21 of 24 prompts. Sonnet completed 23.

Three failures across two distinct modes: one empty response on the first prompt, and two "conversation is too long" bailouts on the most context-heavy prompts. On the 21 completed prompts, the quality delta from the [Q8_0 run](article-draft-26b-sonnet46-20260407) is minimal — same strengths (efficiency, willingness to answer from knowledge), same weaknesses (generic planning, no codebase grounding on multi-step tasks).

### Where They're Equal (16 prompts)

**Basic tool use (2–3):** Both read `identity.md` and summarized correctly. Both listed the working directory with `pwd && ls`. (Prompt 1 is a Gemma failure — discussed below.)

**Attach skills (5):** Both found deep-research and email-send via glob + grep. Gemma correctly identified deep-research's use of the agent `attach()` tool and email-send's `--attach` CLI flag — the same distinction Sonnet draws.

**Memory retrieval (7–9):** Both retrieved user profile, project list, and people from memory. Gemma was thorough — 4 iterations on prompt 7, 5 on prompt 9. It noted that "James" was mentioned as an example filename in the memory README but had no actual person file. Substantively equivalent.

**Identity and skills (10–11):** Both found and read the identity file. Both listed 11 skills from the manifest without tool calls.

**Haiku (12):** Both wrote one.

**Skill loading (14–15):** Both loaded deep-research and reddit-research, listed dependencies and explained the two-step pipeline correctly.

**Error recovery (16–17):** Both handled a missing file and a failed Python import cleanly. No hallucination, no confusion.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz`, found it in eval files, and correctly identified it as a sentinel test case used to verify search tool behavior.

**Delegate comparison (20):** Neither read code. Both gave solid general-knowledge comparisons — scope, context isolation, when to use each.

**Scheduled tasks (23):** Both checked the scheduler, found nothing.

On these 16 prompts, the responses are interchangeable. Tool schemas work. The dispatch loop works. The Q4_K_M quantization didn't degrade the model's ability to pick the right tool or follow instructions.

### Where Gemma Q4_K_M Is Better (2 prompts)

**Context overflow (19):** Sonnet exhausted its 8-call budget searching for documentation about context overflow — reading memory files, grepping for "overflow", "truncat", "compaction" across multiple patterns. Never produced a response. Gemma answered in zero tool calls:

> Three strategies: 1. Delegation — complex tasks offloaded to sub-agents with separate context windows. 2. Persistent Memory — durable knowledge stored in context/memory/, searched as needed. 3. Concise Communication — direct and brief, minimizing token consumption.

Same behavior as the Q8_0 run. Same behavior as [E4B](article-draft-e4b-sonnet46-20260407). The willingness to answer from knowledge rather than tools continues to save this prompt for local models across quantization levels.

**Model config (22):** Gemma found the answer in 1 tool call (`env | grep MODEL`). Sonnet took 7 — checking memory files, `.env`, config files, `pyproject.toml`, `docker-compose.yml`, and finally `printenv`. Same efficiency advantage as the Q8_0 run.

### Where Sonnet Is Better (2 prompts)

**Multi-step planning (4):** Gemma used zero tool calls and described a generic framework approach: "define the tool interface, implement core logic, register the tool, update the system prompt, create tests." Plausible for some framework. The response explicitly says "I don't have your specific codebase in front of me" — while sitting in the codebase with full tool access. Sonnet read 12 files across 9 iterations and described the exact five-step process with file names, import patterns, and the schema registration loop. Same gap as Q8_0.

**Web search (13):** Both loaded web-search and hit the Brave API for "asyncio best practices 2025." Sonnet then fetched three source URLs and synthesized a 9-point summary with citations. Gemma returned a solid summary from the search results but didn't go deeper. The post-search synthesis gap matches the Q8_0 pattern.

### Where Gemma Q4_K_M Failed (3 prompts)

Three failures, two distinct modes.

**Prompt 1 — Empty response:** "Find all Python files under src/tools/ with 'async'." No tool calls. No response. No stats. A complete blank on the very first prompt of the eval.

Every other model in the series handles prompt 1. The Q8_0 version of this same model grepped and found 2 files without difficulty. This is the one result that looks like a quantization or inference artifact rather than a capability gap. The model produced nothing — not a wrong answer, not a refusal, just silence. With single-run evals, there's no way to distinguish a one-off fluke from a systematic issue.

**Prompts 6 and 21 — "Conversation is too long":** Code tracing (prompt 6) and design decisions (prompt 21) both require reading multiple source files and synthesizing across them. Gemma started both correctly — on prompt 6, it read `ws.py`, `agent.py`, and `dispatcher.py` before stopping. On prompt 21, it read all three requested files (`agent.py`, `dispatcher.py`, `skills.py`). Then, in both cases: "Sorry, the conversation is too long. Please start a new thread."

This is a new failure mode in the series. No other model has produced this response. The cause is straightforward: with `-c 8192`, multi-file reads fill the context window. The model recognizes it's out of space and stops. The Q8_0 run on the Mac handled both prompts — likely running with a larger context window and more headroom.

These aren't reasoning failures. They're infrastructure failures. The 8K context ceiling is too low for prompts that require accumulating file contents across multiple tool calls. Bumping `-c` to 16384 or 32768 would likely recover both prompts — the 32GB of RAM can accommodate a larger KV cache even at CPU-only speeds.

### Where Sonnet Failed

**Prompt 19 — Context overflow:** Sonnet's only failure. 8/8 tool calls searching for documentation, no response. The series' most consistent failure — every eval run has reproduced it.

### Where Both Failed

**Test count (24):** Gemma tried 7 tool calls — all bash `find` and `grep` variants — and concluded "I could not find any test files in this project." Sonnet searched with 5 tool calls and answered 0. The real answer is 202 (`pytest --collect-only`). Seven models into the series, zero correct answers. Neither thinks to run the test runner.

## Comparison with Q8_0 Run

This is the more revealing comparison — same model, different quantization, different hardware.

| | Q8_0 (Mac, Metal) | Q4_K_M (Ubuntu, CPU) |
|---|:-:|:-:|
| **Prompts completed** | 24/24 | 21/24 |
| **Code tracing (6)** | Pass (13 tool calls) | Fail (context limit) |
| **Design decisions (21)** | Pass | Fail (context limit) |
| **Prompt 1 (basic grep)** | Pass | Fail (empty response) |
| **Multi-step planning (4)** | Weak (generic) | Weak (generic) |
| **Context overflow (19)** | Pass (0 tools) | Pass (0 tools) |
| **Throughput** | Metal-accelerated | ~3–7 tok/s (CPU) |

The reasoning quality is the same. The planning is equally generic. The tool-use efficiency is equally strong. What changed is the infrastructure: less context, slower inference, no GPU. The Q4_K_M didn't make the model dumber — it made the operating envelope smaller.

## Comparison

| | Gemma 26B Q4_K_M | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 21/24 | 23/24 |
| **Basic tool use** | Mixed (prompt 1 failed) | Pass |
| **Memory retrieval** | Pass | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Fail (context limit) | Strong |
| **Multi-step planning** | Weak (general knowledge) | Strong (codebase-grounded) |
| **Instruction precision** | Pass | Strong |
| **Efficiency** | Strong (fewer calls) | Mixed |
| **Knows when to stop** | Yes | No (prompt 19) |

## What I Take Away

**Context window is the real bottleneck, not quantization.** Two of three failures are the model saying "conversation is too long." Not wrong answers, not malformed tool calls — just running out of room. The same model at Q8_0 with more context completed those prompts. At 8K, any prompt requiring multiple file reads is at risk. The fix is one flag: `-c 16384`. The three lost prompts are likely recoverable without changing the model or the hardware.

**Q4_K_M on CPU is usable for agentic work.** 3–7 tok/s on an 8-core Ryzen with no GPU. Slow, but the model completes prompts in 15–90 seconds of wall time. For non-interactive workflows — background agents, scheduled tasks, batch processing — this works. For conversational use, the latency is noticeable but not prohibitive. The [GLM-5 Turbo](article-draft-glm5turbo-sonnet46-20260408) and [MiniMax M2.7](article-draft-minimaxm27-sonnet46-20260408) articles showed cloud models at 15–40 tok/s. The Q4_K_M on CPU is slower, but not by the order of magnitude you'd expect from a $600 box competing with cloud infrastructure.

**The quality delta from Q8 to Q4 is smaller than expected.** On the 21 completed prompts, the answers are nearly interchangeable with the Q8_0 run. Same strengths, same weaknesses, same phrasing patterns. The quantization didn't visibly degrade reasoning, tool selection, or instruction following. Unsloth Dynamic's Q4_K_M preserves the capabilities that matter for agentic use.

**The empty response on prompt 1 is an open question.** Every other model handles the first prompt. The Q8_0 handles it. Q4_K_M produces nothing. This might be a quantization artifact, an inference seed issue, or a one-off fluke. With single-run evals, there's no way to distinguish. It's the only result in the series where a model produces literally nothing on a straightforward tool-use prompt.

**Budget hardware can run a functional agent.** An AMD Ryzen 7 8745HS, 32GB RAM, no discrete GPU, Ubuntu, CPU-only inference. That's the hardware running a 26B MoE agent with tool use, memory, skills, and live web search — completing 21 of 24 prompts, matching Sonnet on 16 of them. Not fast. Not complete on every prompt. But functional, free, and fully private. The [E4B article](article-draft-e4b-sonnet46-20260407) established that 4B is the floor for agentic tool use. This establishes that a $600 Linux box is the floor for agentic hardware — at least for the 26B model.

---

*Tested on Curunir. Gemma 26B Q4_K_M at harness commit `ff0315f`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 11, 2026.*
