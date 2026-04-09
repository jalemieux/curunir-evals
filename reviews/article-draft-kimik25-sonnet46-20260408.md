---
layout: default
title: "Kimi K2.5: When Path Hallucination Kills Agentic Tool Use"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline.*

# Kimi K2.5: When Path Hallucination Kills Agentic Tool Use

Moonshot AI's Kimi K2.5 is a large Chinese cloud model that benchmarks well on reasoning tasks. The question: does that reasoning translate to agentic tool use?

The answer: no. Kimi K2.5 completed 14 of 24 prompts. Sonnet completed 23. And the failure mode isn't reasoning — it's something more fundamental.

## The Setup

| | Kimi K2.5 | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | OpenRouter (cloud) | Anthropic (cloud) |
| **Provider** | Moonshot AI | Anthropic |
| **Cost** | Paid (OpenRouter) | Paid (Anthropic) |
| **Privacy** | Data sent to OpenRouter/Moonshot | Data sent to Anthropic |

Same harness, same tools, same system prompt. Both ran through [Curunir](https://github.com/jalemieux/curunir) over WebSocket.

Full results: [Kimi K2.5](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260408-200138-openrouter_moonshotai_kimi-k2_5.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### Kimi completed 14 of 24 prompts. Sonnet completed 23.

Ten failures. But what makes this result interesting isn't the count — it's the pattern. Kimi's failures almost all share a single root cause: **the model hallucinates file paths**.

Instead of using `pwd` or `ls` to discover the filesystem, Kimi guesses paths from training data: `/home/user/repos/curunir/...`, `/var/home/user/...`, `/var/lib/curunir/...`, `/Users/jlemieux/re/curunir/...`. These paths don't exist. The tool calls fail. Kimi burns through its tool budget retrying wrong paths, and produces no response.

The working directory is `/app`. Every other model in the series figured this out on the first prompt. Kimi keeps forgetting between prompts.

### Where They're Equal (8 prompts)

**Async grep (1):** Both found 2 files. Kimi needed two grep calls (the first may have had wrong scope), but got there. Equal.

**Working directory (3):** Both ran `pwd` and `ls`, listed folders correctly. Kimi even added a description column. Equal.

**Haiku (12):** Both wrote one. No tools.

**Deep-research deps (14):** Both loaded the skill and listed dependencies correctly.

**Reddit skill (15):** Both loaded reddit-research and explained the two-step pipeline.

**Failed import (17):** Both ran the command, handled the ModuleNotFoundError cleanly.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz` and identified it as a sentinel test case.

**Scheduled tasks (23):** Both checked the scheduler, found nothing.

On prompts where Kimi doesn't need to navigate the filesystem — or where the first prompt already established the layout — it performs fine.

### Where Sonnet Is Better (5 prompts)

**Identity file (10):** Sonnet found and read `context/identity.md` in 4 tool calls. Kimi tried a wrong path first (`/app/.kimi/skills/identity/SKILL.md`), then globbed, then tried another wrong path with angle brackets in it, before finally reading the right file. Got the answer, but burned 4 of 8 tool calls on path fumbling.

**Web search (13):** Both loaded web-search and hit the Brave API. Kimi fetched 5 source URLs (more than Sonnet's 3) and produced a comprehensive summary. Both strong — but Kimi was slightly less structured. Close.

**Delegate comparison (20):** Both answered from general knowledge. Kimi's response was well-organized with a comparison table and a clear "fan out" metaphor. Actually quite good. Sonnet was similarly structured. Close.

**Design decisions (21):** Kimi wasted 6 of 9 tool calls trying wrong paths before finding the right files. But once it read them, the analysis was strong: coherent group trimming, sync/async bifurcation via `asyncio.to_thread()`, frontmatter-driven declarative discovery. Same themes as Sonnet, with comparable justification. The path fumbling ate half its budget but didn't kill the response.

**Model config (22):** Kimi found the answer in 1 tool call — a bash command checking env variables. Sonnet took 7. Kimi was more efficient here.

### Where Sonnet Won Outright

**Context overflow (19):** Sonnet failed its usual way — 8 tool calls, no response. Kimi used 1 tool call (wrong path), then answered from general knowledge:

> Curunir uses **delegation** for context-heavy tasks. Large documents, image analysis, or multi-step research get routed to a **sub-agent with a clean context window**. The sub-agent has full tool access but runs isolated — only the final answer returns to the main session.

Correct in spirit, concise. Kimi beat Sonnet on the prompt that Sonnet consistently fails. But this is a hollow win — Kimi's answer wasn't grounded in the code, and Sonnet's failure is a known reproducible pattern at this point.

### Where Kimi Failed (10 prompts)

Here's the pattern:

**Path hallucination failures (prompts 2, 5, 6, 7, 8, 9, 11, 16):**

| Prompt | What happened | Paths tried |
|--------|--------------|-------------|
| **2 (identity summary)** | Read wrong path, globbed, read correct path — LIMIT HIT (3/3) | `/home/user/repos/curunir/context/identity.md` |
| **5 (attach skills)** | Found skills via grep, tried to read — empty response | `/var/home/user/skills/deep-research/SKILL.md`, `/var/home/user/skills/email-send/SKILL.md` |
| **6 (code trace)** | Searched for `.ts` and `.go` files first, found ws.py — empty response | `/Users/jlemieux/re/curunir/src/channels/ws.py`, `/Users/jlemieux/re/curunir/run.py` |
| **7 (about me)** | Read wrong path, globbed, found files — LIMIT HIT (8/8) | `/var/lib/curunir/context/memory/README.md` (twice) |
| **8 (projects)** | Read wrong path, bash fallback — error | `/usr/src/context/memory/README.md` |
| **9 (people)** | Read wrong path repeatedly, bash fallback — LIMIT HIT (10/10) | `/context/memory/README.md` (twice) |
| **11 (skills list)** | Globbed for SKILL.md files — LIMIT HIT (2/2) | N/A (glob worked but 2-call budget was too tight) |
| **16 (missing file)** | Read wrong path, globbed — empty response | `/src/nonexistent/fake_module.py` |

The paths are different each time — `/home/user/`, `/var/home/user/`, `/var/lib/curunir/`, `/Users/jlemieux/re/curunir/`, `/src/`. Kimi isn't consistently wrong about the prefix; it's *randomly* wrong, pulling different path conventions from different training examples.

On prompt 6, Kimi searched for `.ts` and `.go` files before searching for `.py` files, suggesting it doesn't remember (or doesn't use) the context that this is a Python project.

**Error/empty responses (prompts 4, 24):**

- **Prompt 4 (summarize tool):** Two tool calls (glob + grep), then "Sorry, I encountered an error processing your message." Likely an API-level error, not a reasoning failure.
- **Prompt 24 (test count):** Six glob/bash calls, then empty response. Similar to other models that failed this prompt, but Kimi couldn't even produce a wrong answer.

### Where Both Failed

**Test count (24):** Sonnet answered 0 (wrong). Kimi returned nothing. The real answer is 202. Sonnet at least produced a response.

## Comparison

| | Kimi K2.5 | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 14/24 | 23/24 |
| **Basic tool use** | Mixed | Pass |
| **Memory retrieval** | Fail (path issues) | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Mixed | Pass |
| **Code tracing** | Fail | Strong |
| **Multi-step planning** | Fail | Strong |
| **Instruction precision** | Weak | Strong |
| **Self-directed exploration** | Fail | Strong |
| **Efficiency** | Mixed (efficient when it works) | Mixed |
| **Knows when to stop** | Yes | No (prompt 19) |

## What I Take Away

**Path hallucination is a catastrophic failure mode for agentic tool use.** Kimi K2.5 doesn't lack reasoning capability — on prompts 19, 20, 21, and 22 it produced substantive, well-structured answers. The problem is upstream: it can't reliably determine where files are. It guesses paths from training data instead of using the tools available to it (`pwd`, `ls`, `Glob`). A model that hallucinates file paths will burn its tool budget on failed reads before it ever gets to reason about the content.

**The model has no persistent state awareness between prompts.** Prompt 3 correctly identifies `/app` as the working directory. Prompts 5, 6, 7, 8, 9 all try completely different wrong paths. Each prompt starts fresh with no memory of what it learned earlier — but unlike other models, Kimi doesn't re-establish the basics before diving into tool calls.

**When paths are provided or unnecessary, Kimi performs well.** Skill loading (14, 15), web search (13), haiku (12), delegate comparison (20), model config (22) — these prompts either provide explicit targets or don't require filesystem navigation. On these, Kimi is competitive. The skill analysis on prompt 21, once it finally found the files, was genuinely strong — comparable to Sonnet's.

**Reasoning capability ≠ agentic capability.** Kimi likely benchmarks well on tasks where the input is provided in-context. But an agentic loop requires the model to *find* its inputs — to navigate a filesystem, discover structure, recover from wrong paths. This is a different skill from reasoning about code that's already in front of you. Kimi has the second skill but not the first.

**The gap between "can call tools" and "can drive an agent" is wider than it looks.** Every model in this series can emit valid JSON tool calls. Every model understands function schemas. But the Gemma E4B couldn't self-direct exploration, and now Kimi can't reliably navigate a filesystem. The mechanical ability to call tools is the easy part. The hard part is the upstream decision-making: what to call, with what arguments, and what to try next when something fails.

---

*Tested on Curunir. Kimi K2.5 at harness commit `004dd18`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 8, 2026.*
