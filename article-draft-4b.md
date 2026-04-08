---
layout: default
title: "Gemma 4B Q8_0: The 4B Floor Holds"
---

# Gemma 4B Q8_0: The 4B Floor Holds

The [E4B eval](article-draft-e4b) established that a 4B-class model can drive an agentic loop — 21 of 24 prompts completed, basic tool use solid, but a visible gap on anything requiring self-directed exploration. One data point. Was that the E4B specifically, or the 4B parameter scale?

Gemma 4 4B Q8_0 — a different 4B variant, quantized to 8-bit, running locally — provides the second data point. Same eval suite, same harness, same 24 prompts. The result: 21 of 24 prompts completed. Same number. Nearly the same failures.

## The Setup

| | Gemma 4 4B Q8_0 | Claude Sonnet 4 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Parameters** | 4B | Undisclosed |
| **Quantization** | Q8_0 (GGUF) | N/A (full precision) |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

The framework is Curunir — tools (grep, read, write, bash, web fetch), loadable skills, persistent memory, multiple channels. The model receives tool schemas via JSON function calling, decides which tools to use, executes them, reads results, and loops.

4B Q8_0 ran at harness commit `a56ee81`. The Sonnet baseline ran at `fe87420`. Same 24 prompts.

## The Eval

24 prompts across 8 categories:

| Category | What it tests | # |
|----------|--------------|:-:|
| **Tool Use Accuracy** | Pick the right tool, use it correctly | 3 |
| **Multi-Step Planning** | Decompose complex requests into tool call sequences | 3 |
| **Memory Retrieval** | Find and synthesize info from persistent memory files | 3 |
| **Instruction Following** | Respect constraints ("don't use tools", "only answer from this file") | 3 |
| **Skill Orchestration** | Load and execute multi-step skills (web search, research) | 3 |
| **Error Recovery** | Handle missing files, failed commands, empty results | 3 |
| **Output Quality** | Explain architecture, compare tools, identify design decisions | 3 |
| **Efficiency** | Solve simple questions without unnecessary tool calls | 3 |

Full results: [Gemma 4 4B Q8_0](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260406-231312-openai_gemma-4-4B-Q8_0.md) | [Claude Sonnet 4](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260403-175244-anthropic_claude-sonnet-4-20250514.md)

## Results

### 4B Q8_0 completed 21 of 24 prompts. Sonnet completed all 24.

The model produced text responses to 23 of 24 prompts. Of those, 21 were substantive. Two were non-answers: "Please provide the codebase or specific files" (prompt 21) and "Please specify which project" (prompt 24). One prompt (15) produced no response — the model burned its entire tool call budget reading the same file in a loop.

### Where They're Equal (10 prompts)

**Basic tool use (1-3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it. Both ran `pwd` and `ls` to list the working directory. Identical results.

**Memory (8):** Both read `projects.md` from persistent memory and returned similar project lists.

**Haiku (12):** Both wrote a haiku without tools. Instruction followed.

**Skill loading (14):** Both loaded deep-research via `LoadSkill` and correctly identified its sub-skill dependencies.

**Error recovery (16-17):** Both handled a missing file and a failed Python import cleanly.

**Efficiency (23):** Both checked the scheduler and found nothing.

**Delegate comparison (20):** Both gave reasonable general-knowledge answers comparing the delegate tool to a function call. Neither read the code. Both acceptable.

### Where Sonnet Is Better (11 prompts)

The pattern matches the E4B findings exactly: the 4B model answers from general knowledge where Sonnet reads the codebase.

**Multi-step planning (4):** "How would you add a summarize tool?" Sonnet read 9 source files, described the exact three-file pattern — `summarize_tool.py` -> `schemas.py` -> `dispatcher.py`. The 4B Q8_0 used zero tool calls and described a generic plugin architecture: "Create `tools/summarize_tool.py`... add to `config/available_skills.json`." Plausible for some framework. Wrong for this one. Same error as E4B.

**Skill search (5):** "Find every skill using the attach tool." Sonnet found both — deep-research and email-send. The 4B Q8_0 found email-send only. It used Glob, Grep, and Read but stopped after one match.

**Code tracing (6):** Sonnet traced the full WebSocket-to-tool-execution path across 8 files with line numbers. The 4B Q8_0 got the first half right — WebSocket reception, JSON parsing, queue insertion, all with correct citations from `ws.py`. Then it stalled. The response ends mid-thought: "To complete the trace, I need to find the consumer of `self.in_queue`." Seven tool calls, half a trace.

**Memory retrieval (7, 9):** "What do you know about me?" — both found the user profile, but Sonnet searched more broadly (5 files plus grep vs 2 files). "Who are the people you remember?" — Sonnet found names scattered across memory files. The 4B Q8_0 checked `context/memory/people/` (empty), found two names in `projects.md`, stopped.

**Instruction following (10-11):** "Answer only from your identity file" — Sonnet read the file (1 tool call). The 4B Q8_0 answered from the system prompt (0 tool calls). Right answer, wrong process. Listing skills: Sonnet listed 11 skills correctly. The 4B Q8_0 listed 14 items, mixing skills with tools (`load_skill`, `delegate`, `schedule`). Same conflation as E4B.

**Skill orchestration (13):** Both loaded web-search and searched for "asyncio best practices." The 4B Q8_0 tried Google via WebFetch twice before falling back to the Brave API as the skill specified. Sonnet loaded the skill, hit Brave directly, then fetched 7 source URLs for deeper content.

**Pattern analysis (18):** Both grepped for `zzz_no_match_zzz` and found it only in eval/doc files. Sonnet identified these as eval artifacts and concluded the pattern doesn't exist in source code. The 4B Q8_0 listed the matching files without interpretation.

**Context overflow (19):** Sonnet read memory files and grep'd for the mechanism, citing specific features (character truncation, delegate isolation). The 4B Q8_0 answered from general knowledge — accurate in spirit, ungrounded in the codebase.

**Model configuration (22):** Sonnet grepped for model references and checked environment variables — found `anthropic/claude-sonnet-4-20250514` in two calls. The 4B Q8_0 read memory files looking for the answer, found the persona description but not the model name. It never thought to grep config files or check env vars.

### Where 4B Q8_0 Failed (3 prompts)

**Prompt 15 — Reddit research:** The model read `context/memory/README.md` ten times in a row, burning its entire tool call budget. Never loaded the reddit-research skill. Never hit an API. Produced no response. Sonnet loaded the skill, queried Brave and Reddit, returned structured findings. Same failure mode as E4B — same prompt, same loop.

**Prompt 21 — Design decisions:** "What are the three most important design decisions in this codebase?" Response: "Please provide the codebase or specific files you would like me to analyze." It was in the codebase. It had tools. Same failure as E4B — verbatim.

**Prompt 24 — Test count:** "How many tests does this project have? Just give me the number." Response: "Please specify which project or directory you are referring to." The E4B at least tried — globbed for test files, got the wrong number. The 4B Q8_0 didn't try. Sonnet also got the number wrong (found 0 via glob when the answer is 202), but it attempted the work. The quality of failure degrades with model scale: Sonnet searched comprehensively and missed, E4B searched narrowly and miscounted, the 4B Q8_0 asked for help.

## The E4B Mirror

Two 4B-class Gemma 4 variants. Same eval. Here's how they line up:

| | 4B Q8_0 | E4B | Sonnet |
|---|:-:|:-:|:-:|
| **Prompts completed** | 21/24 | 21/24 | 24/24 |
| **Basic tool use** | Pass | Pass | Pass |
| **Memory retrieval** | Pass | Pass | Pass |
| **Skill loading** | Pass | Pass | Pass |
| **Error recovery** | Pass | Pass | Pass |
| **Code tracing** | Half (stalled) | Weak (approximate) | Strong (precise) |
| **Multi-step planning** | Weak | Weak | Strong |
| **Instruction precision** | Weak | Weak | Strong |

Both failed prompt 15 (the loop). Both failed prompt 21 ("please provide the codebase"). They traded one failure each: E4B failed prompt 22 (model config, zero tool calls), while 4B Q8_0 at least attempted it with 2 tool calls. The 4B Q8_0 failed prompt 24 (test count, asked for clarification), while E4B at least tried to glob for tests.

The shared failures are more telling than the differences. Prompts 15 and 21 require the model to *initiate* exploration with no obvious starting point. Both 4B variants collapse in the same way — one loops, the other punts. The parameter scale doesn't have enough planning capacity for open-ended codebase investigation.

## Timing: What 5 tok/s Feels Like

This is the first eval in the series with per-prompt timing data. The 4B Q8_0 generated tokens at 5-7 tokens/second on most prompts, dropping to 1.4 tok/s on the shortest response (the haiku).

| Prompt | Wall time | Note |
|--------|----------|------|
| 12 (haiku) | 13s | Shortest — single turn, no tools |
| 16 (missing file) | 35s | Quick error recovery |
| 3 (list directory) | 69s | Simple tool use |
| 4 (planning) | 173s | Long response, no tools |
| 5 (skill search) | 376s | 4 iterations |
| 6 (code tracing) | 539s | 7 iterations, incomplete |

The full eval took roughly 50 minutes. Sonnet completes the same suite in under 3 minutes via API. That's a ~17x wall-time difference.

For interactive use, sub-minute prompts feel acceptable. The multi-iteration prompts (5, 6, 13, 15) take 4-9 minutes each. An agent that takes that long per complex task is viable for batch workflows — let it run in the background — but not for conversational use.

## What I Take Away

**The 4B floor is confirmed.** Two different 4B variants, same eval, same completion count (21/24), same dominant failure modes. The E4B result wasn't a fluke. The 4B parameter scale can drive an agentic loop — tool use, memory, skills, error recovery — but can't self-direct exploration on open-ended prompts.

**The failure mode is consistent.** Both 4B models loop on prompt 15 and punt on prompt 21. These aren't random errors — they're reproducible limitations of the scale. When a 4B model doesn't have an obvious first tool call, it either repeats what it knows (loop) or asks for help (punt). Neither recovers.

**Quantization doesn't visibly degrade agentic capability.** The Q8_0 model performed at parity with E4B across all categories. If 8-bit quantization costs anything at this scale, it's below the noise floor of this eval. You can run the smaller GGUF file and get the same agentic behavior.

**5 tok/s is the practical speed floor for interactive agentic use.** Simple prompts resolve in under a minute. Multi-iteration tasks take 4-9 minutes. Fine for background automation. Too slow for conversational coding assistance.

**The series so far:**

| Model | Scale | Completed | Quality vs Sonnet | Use case |
|-------|-------|-----------|-------------------|----------|
| [Gemma 4 26B](article-draft) | 26B MoE (4B active) | 21/21* | Functional peer, verbose | General agentic tasks |
| [Gemma 4 E4B](article-draft-e4b) | ~4B | 21/24 | Tool mechanics solid, reasoning gap | Defined workflows |
| Gemma 4 4B Q8_0 | 4B quantized | 21/24 | Same as E4B | Defined workflows |
| Claude Sonnet 4 | Cloud | 24/24 | Baseline | Everything |

*\*The 26B eval used 21 prompts (before the Output Quality category was added).*

The question from the [first article](article-draft) was whether local models could drive an agentic framework at all. The answer was yes at 26B. The [second article](article-draft-e4b) pushed it to 4B and found the floor. This third eval confirms it wasn't an artifact of one model — the 4B scale itself is the boundary where self-directed exploration breaks down. Above it (26B), you gain reasoning depth. At Sonnet scale, you get reliable open-ended investigation.

The interesting next step isn't going smaller — it's going sideways. Different model families at the same scale (Phi, Llama, Qwen), or harder prompts that stress the boundaries this eval has mapped.

---

*Tested on Curunir at commit `a56ee81`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 7, 2026.*
