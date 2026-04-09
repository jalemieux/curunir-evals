---
layout: default
title: "MiniMax M2.7: Another Cloud Model Goes Toe-to-Toe with Sonnet"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline.*

# MiniMax M2.7: Another Cloud Model Goes Toe-to-Toe with Sonnet

The [GLM-5 Turbo article](article-draft-glm5turbo-sonnet46-20260408) showed that a Chinese cloud model could match Sonnet 4.6 on agentic tasks — 23/24 vs 23/24, with comparable depth on code tracing and planning. The [Kimi K2.5 article](article-draft-kimik25-sonnet46-20260408) showed what happens when a model can't reliably navigate a filesystem: 14/24, ten failures, almost all from path hallucination.

MiniMax M2.7 — another cloud model via OpenRouter — falls between them, closer to GLM: 22/24 completed, with codebase-grounded analysis that matches or exceeds Sonnet on several hard prompts.

## The Setup

| | MiniMax M2.7 | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | OpenRouter (cloud) | Anthropic (cloud) |
| **Provider** | MiniMax | Anthropic |
| **Cost** | Paid (OpenRouter) | Paid (Anthropic) |
| **Privacy** | Data sent to OpenRouter/MiniMax | Data sent to Anthropic |

Same harness, same tools, same system prompt. Both ran through [Curunir](https://github.com/jalemieux/curunir) over WebSocket.

Full results: [MiniMax M2.7](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260408-220032-openrouter_minimax_minimax-m2_7.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### MiniMax completed 22 of 24 prompts. Sonnet completed 23.

MiniMax's two failures are both tool-budget exhaustions on search-heavy prompts — not reasoning failures, not crashes, not path hallucination. When it gets to read the code, the analysis is strong. On one prompt, it offered a genuine architectural critique that no other model in the series has raised.

### Where They're Equal (16 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it. Both listed the working directory with descriptions. No difference.

**Attach skills (5):** Both found deep-research and email-send, both described the distinction between the agent `attach()` tool and the CLI `--attach` flag. MiniMax did it in 4 tool calls; Sonnet took 7. Same substance, MiniMax more efficient.

**Memory — about me (7):** Both searched memory files and returned accurate, detailed profiles. MiniMax cast a slightly wider net (6 tool calls vs 2) but the content was comparable.

**Projects (8):** Both read `projects.md` and returned organized project lists with status. MiniMax formatted it as a table with status column — slightly more structured.

**Identity (10):** Both found and read `context/identity.md`. Both answered correctly from the right source. MiniMax took 3 tool calls; Sonnet took 4.

**Skills list (11):** Both listed 11 skills from the manifest, zero tool calls.

**Haiku (12):** Both wrote one without touching tools.

**Deep-research deps (14):** Both loaded the skill and listed sub-skill dependencies correctly.

**Reddit skill (15):** Both loaded reddit-research and explained the two-step pipeline.

**Error recovery (16–17):** Both handled a missing file and a failed import cleanly.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz` and identified it as a deliberate test artifact.

**Delegate comparison (20):** Neither read the code. Both gave well-structured comparisons with use-case tables.

**Scheduled tasks (23):** Both checked the scheduler, found nothing.

On these 16 prompts, the responses are interchangeable. MiniMax was often slightly more efficient (fewer tool calls for the same result).

### Where They Match on Hard Prompts

Like GLM-5 Turbo, MiniMax reads the codebase before answering. The Gemma models answered from general knowledge on these prompts. MiniMax doesn't.

**Multi-step planning (4):** "Walk me through every file I'd need to change to add a summarize tool." MiniMax: 10 tool calls across 7 iterations. Read dispatcher, schemas, init, CLAUDE.md, README, fs_tools, system_prompt. Produced a 6-step walkthrough: schemas.py → summarize.py → dispatcher.py → README.md → tests → CLAUDE.md. Cited the `_register()` loop, the `_SYNC_EXECUTORS` dict, the existing executor signatures. Sonnet: 12 tool calls across 9 iterations, same core sequence. Both codebase-grounded. Both precise.

**Code tracing (6):** "Trace the full path from WebSocket to tool execution." MiniMax: 11 tool calls, 6 iterations. Full trace from `ws.py:54` through `run.py:173`, `agent.py:144`, `dispatcher.py:40`, down to `fs_tools.py:156`. Code snippets at every stage. An ASCII diagram showing the complete flow including the return path. Sonnet: 11 tool calls, 6 iterations, equivalently detailed trace. Both are walkthroughs you could follow with a debugger.

**Web search (13):** Both loaded web-search, hit Brave, and fetched source URLs. MiniMax fetched 5 URLs (including the Python official docs and a discuss.python.org thread). Sonnet fetched 3. Both produced comprehensive summaries. MiniMax included a gotcha table and a testing section. Close — MiniMax slightly more thorough.

### Where MiniMax Is Better (3 prompts)

**Context overflow (19):** Sonnet used all 8 tool calls searching for documentation and produced no response — the same failure from every previous article in this series. MiniMax used 2 tool calls (read memory README, grep for relevant patterns), then answered:

> The agent loop enforces a **15-iteration cap** and **truncates conversation history at ~600K characters**. When the limit is hit, older messages are dropped to make room for new ones. This prevents the context window from overflowing while preserving recent context. The loop also auto-captures learnings to persistent memory so important information survives beyond the truncated window.

Grounded in the code. Concise. Under 100 words. Like GLM, MiniMax found the right balance — searched first, then synthesized an answer from what it found rather than exhausting its budget looking for a dedicated doc that doesn't exist.

**Design decisions (21):** Both read all three files and identified similar themes. But MiniMax went further — it offered genuine architectural critiques that no other model in the series has raised:

On `dispatcher.py`: "every sync tool call still creates a new thread each time it's invoked. There's no thread pool reuse, which could be a bottleneck under heavy tool call volume."

On `skills.py`: "the frontmatter parsing is naive (no real YAML parser, just line-splitting)."

On `agent.py`: "tools are executed one at a time, awaiting each before the next LLM call — not batched. This is a deliberate trade-off: it keeps the loop simple and the history stateful, but it means a long tool chain blocks the entire event loop."

These aren't complaints — they're observations about real trade-offs in the code, with an understanding of why the choices were made. Sonnet identified the same design decisions but described them more approvingly without surfacing the trade-off edges.

**Model config (22):** MiniMax: 3 tool calls. Sonnet: 7 tool calls. Both found the answer. MiniMax was more than twice as efficient.

### Where Sonnet Is Better (1 prompt)

**People (9):** "Who are the people you remember?" MiniMax used all 10 tool calls reading memory files, archived conversations, and people directories — then hit the budget with no response. Sonnet used 5 tool calls and produced a structured list of people found across memory. MiniMax searched more broadly (including archived conversations), but its thoroughness killed it — same pattern as Sonnet's prompt 19 failure, just on a different prompt.

### Where Each Failed

**MiniMax — Prompt 9 (people):** Exhausted 10-call budget reading memory files and archived conversations. Never produced a response. The data was there — MiniMax found it — but it kept reading more files instead of synthesizing what it had.

**MiniMax — Prompt 24 (test count):** Exhausted 8-call budget globbing for test files in every pattern it could think of: `*test*`, `*spec*`, `tests/**/*.py`, `test*`, `*_test.py`, `test_*.py`, `*.test.js`, `*Test.java`. Never ran `pytest`. No response.

**Sonnet — Prompt 19 (context overflow):** The same failure as every previous eval. 8 tool calls, no response.

### Where Both Failed

**Test count (24):** MiniMax hit its budget searching. Sonnet answered 0 (wrong). The real answer is 202. Five models in, zero correct answers on this prompt. MiniMax's search patterns are notable: after exhausting Python patterns, it tried `.test.js` and `*Test.java` — not anchored on the project language. But it only did this after trying the right patterns first, so it's a budget issue more than a reasoning one.

## Comparison

| | MiniMax M2.7 | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 22/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass (1 budget failure) | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Strong (precise, with code) | Strong (precise, with code) |
| **Multi-step planning** | Strong (codebase-grounded) | Strong (codebase-grounded) |
| **Instruction precision** | Strong | Strong |
| **Self-directed exploration** | Strong | Strong |
| **Efficiency** | Strong (fewer calls) | Mixed (thorough but expensive) |
| **Architectural insight** | Strong (identifies trade-offs) | Good (describes decisions) |
| **Knows when to stop** | Mostly (prompt 9) | No (prompt 19) |

## What I Take Away

**MiniMax M2.7 is the second model in this series to match Sonnet's depth on hard prompts.** Code tracing, multi-step planning, design analysis — all codebase-grounded, all with file:line citations. GLM-5 Turbo was the first. MiniMax confirms it wasn't a one-off. The gap between Sonnet and capable cloud models on agentic tasks is closing.

**MiniMax's design analysis is the sharpest in the series.** The thread pool observation, the naive frontmatter parsing note, the sequential-vs-batched tool execution trade-off — these are things a human code reviewer would flag. Every other model described the design decisions approvingly. MiniMax described them critically. That's a meaningful difference for anyone using an agent to understand a codebase.

**Budget exhaustion is the new failure mode for capable models.** Kimi failed because it couldn't find files. Gemma E4B failed because it wouldn't try. MiniMax and Sonnet fail because they search too thoroughly — they keep reading files instead of synthesizing what they've already found. On prompt 9, MiniMax did exactly what Sonnet does on prompt 19: kept reaching for more data when it already had enough. Over-investigation is not unique to Sonnet. It's a property of capable models with finite tool budgets.

**Efficiency is a consistent MiniMax advantage.** Across prompts where both succeeded, MiniMax typically used fewer tool calls: 4 vs 7 on attach skills, 3 vs 4 on identity, 10 vs 12 on planning, 3 vs 7 on model config. The responses are equally detailed — MiniMax just gets there faster.

**The test count prompt remains the universal blind spot.** Five models, zero correct answers. The real answer (202, per `pytest --collect-only`) requires running the test runner, not searching for test files. Every model reaches for grep/glob when it should reach for execution.

---

*Tested on Curunir. MiniMax M2.7 at harness commit `004dd18`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 8, 2026.*
