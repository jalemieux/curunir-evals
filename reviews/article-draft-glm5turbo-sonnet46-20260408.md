---
layout: default
title: "GLM-5 Turbo vs Sonnet 4.6: A Statistical Tie"
---

*This article is part of the [Agentic Eval Series](./), where we run different models through the same 24-prompt eval suite on [Curunir](https://github.com/jalemieux/curunir) — an agentic framework with tool use, memory, skills, and multi-step planning. Same harness, same prompts, same tools. The only variable is the model. Claude Sonnet 4.6 is the baseline.*

# GLM-5 Turbo vs Sonnet 4.6: A Statistical Tie

The first two articles in this series compared local Gemma models against Sonnet 4.6. The [26B](article-draft-26b-sonnet46-20260407) completed all 24 prompts but was shallower on reasoning. The [E4B](article-draft-e4b-sonnet46-20260407) proved the floor for agentic tool use but collapsed on self-directed exploration. Both were local, free, and private — and both were clearly a tier below Sonnet on tasks requiring codebase-grounded analysis.

This time: a cloud model. Zhipu AI's GLM-5 Turbo, accessed via OpenRouter, against the same Sonnet 4.6 baseline on the same 24-prompt eval suite.

The result: 23/24 vs 23/24. Same completion rate. Different failures. And on the prompts where both succeeded, the gap between them is hard to find.

## The Setup

| | GLM-5 Turbo | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | OpenRouter (cloud) | Anthropic (cloud) |
| **Provider** | Zhipu AI | Anthropic |
| **Cost** | Paid (OpenRouter) | Paid (Anthropic) |
| **Privacy** | Data sent to OpenRouter/Zhipu | Data sent to Anthropic |

Both models ran through [Curunir](https://github.com/jalemieux/curunir), the same agentic framework used in all previous evals. Same harness, same tools, same system prompt. The only variable is the model.

Full results: [GLM-5 Turbo](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260408-193814-openrouter_z-ai_glm-5-turbo.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### Both completed 23 of 24 prompts. Each failed a different one.

This is the first model in the series to match Sonnet's completion rate. And the quality gap that defined the Gemma comparisons — Sonnet reading the codebase while Gemma answered from general knowledge — doesn't apply here. GLM-5 Turbo reads the code. It cites files and line numbers. It grounds its answers in the actual architecture.

### Where They're Equal (15 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it. Both listed the working directory. GLM added match counts per file (12 in dispatcher, 4 in delegate) — a nice touch. Sonnet added a description column for directories. Neither difference matters.

**Attach skills (5):** Both found deep-research and email-send. Both made the key distinction: deep-research uses the agent's `attach()` tool (declared in frontmatter, delivers a PDF), while email-send uses `--attach` as a CLI flag on `gog gmail send`. Different mechanisms, overlapping terminology. GLM also flagged false positives in skill-factory and eval artifacts — a small thoroughness win that doesn't change the substance.

**Memory — projects (8):** Both read `projects.md` and returned the same project list.

**Skills list (11):** Both listed 11 skills from the manifest, zero tool calls. Answered from the system prompt.

**Haiku (12):** Both wrote one without touching tools.

**Deep-research deps (14):** Both loaded the skill and listed its sub-skill dependencies correctly. GLM also listed the built-in tool dependencies (attach, web_fetch, bash) — more complete.

**Reddit skill (15):** Both loaded reddit-research and explained its two-step pipeline. Substantively identical.

**Error recovery (16–17):** Both handled a missing file and a failed import cleanly.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz` and identified it as a sentinel test case used to verify no-match behavior. Both noted the self-referential loop — the pattern only exists in eval files that quote the question.

**Delegate comparison (20):** Neither read the code. Both gave solid general-knowledge comparisons with clear use-case tables.

**Scheduled tasks (23):** Both checked the scheduler, found nothing, reported correctly.

On these 15 prompts, the outputs are interchangeable. In several cases GLM's response was slightly more detailed (match counts, tool deps, false positive filtering) without being worse on any.

### Where Sonnet Is Better (3 prompts)

The gap that defined the Gemma comparisons — Sonnet reading the codebase while the other model answers from thin air — barely shows up here. When it does, it's subtle.

**Memory — about me (7):** Both searched memory files and returned accurate profiles. Sonnet read 2 files; GLM read 5. Both correct. Sonnet was more focused; GLM cast a wider net. Neither missed anything significant.

**Identity file (10):** "Answer only from your identity file." Sonnet found and read `context/identity.md` in 4 tool calls. GLM read `context/memory/README.md`, `preferences.md`, and `core-insights.md` — memory files, not the identity file. It answered "Curunir" correctly, but from the wrong source. The instruction was explicit. Sonnet followed it; GLM didn't.

**People (9):** Both found the `people/` directory empty. Both searched other memory files. Sonnet grepped more broadly and surfaced names from across the memory system. GLM did the same and also found references to "Thariq" and "Kimi K2.5" in journal insights — a wider net. Close, with Sonnet slightly more structured.

### Where GLM Is Better (3 prompts)

**Context overflow (19):** Sonnet used all 8 allowed tool calls searching for documentation about context overflow — grepping for "overflow", "truncat", "compaction", "context limit" across multiple patterns. Never found a dedicated doc. Never produced a response. This is the same failure mode from [Part 1](article-draft-26b-sonnet46-20260407) and [Part 2](article-draft-e4b-sonnet46-20260407) — it's now reproduced across three separate comparisons.

GLM used 3 tool calls (grep, glob, grep), then answered:

> Curunir handles context overflow via its **delegate** tool. When a task would bloat the main conversation, it spins up an isolated sub-agent with a clean context window. The sub-agent does all intermediate work independently, and only the final answer returns to the parent conversation. This keeps the primary context lean. Additionally, the agent loop caps at **15 iterations** with **history truncation at ~600K characters** as a safety backstop.

Grounded in the code. Concise. Under 100 words. This isn't "answered from general knowledge" like the Gemma models — GLM actually searched, found relevant signals, and synthesized an answer from what it found.

**Model config (22):** "Find what model I'm configured to use, with as few tool calls as possible." GLM: 4 tool calls. Sonnet: 7 tool calls (checking memory, .env, config files, pyproject.toml, docker-compose, and finally `printenv`). Both found the answer. GLM was more efficient.

**Web search (13):** Both loaded web-search, hit Brave, and fetched source URLs. Sonnet fetched 3 URLs; GLM fetched 3 URLs. Both produced comprehensive, well-structured summaries with citations. GLM organized by best practices, common pitfalls, and 2025 trends. Sonnet produced a numbered 9-point list. Both strong — GLM's structure was slightly more useful.

### Where They Match on Hard Prompts

This is where the comparison diverges from the Gemma articles. The Gemma models struggled on tasks requiring deep codebase exploration. GLM doesn't.

**Multi-step planning (4):** "Walk me through every file I'd need to change to add a summarize tool." Sonnet read 12 files across 9 iterations and described the exact five-step process. GLM read 12 files across 6 iterations and described a six-step process — the same core sequence (summarize.py → schemas.py → dispatcher.py → README.md → tests) plus `agent.py:_TOOL_KEY_ARGS` as an additional step Sonnet mentioned in docs but not as a separate action. Both codebase-grounded. Both precise. Both include code snippets showing the exact patterns to follow.

The 26B model answered this from general knowledge. The E4B did the same. GLM read the code. That's the difference between this comparison and the previous two.

**Code tracing (6):** "Trace the full path from WebSocket to tool execution." Sonnet: 11 tool calls, 6 iterations, full trace with code snippets from `ws.py:54` through `run.py:173`, `agent.py:207`, `llm.py:59`, `dispatcher.py:50`, `fs_tools.py:156`. GLM: 11 tool calls, 4 iterations, equally detailed trace with the same file:line annotations, code snippets at each stage, and a summary diagram.

Both traces are walkthroughs you could follow with a debugger. The 26B produced an approximate trace. The E4B refused to try. GLM matched Sonnet's depth on the hardest agentic task in the suite.

**Design decisions (21):** Both read all three files. Both identified the same three themes: coherent group trimming in agent.py, sync/async dispatch split in dispatcher.py, and frontmatter-driven skill discovery in skills.py. GLM added the ContextWindowExceededError recovery mechanism as part of its agent.py analysis. Sonnet emphasized lazy two-phase loading. Both justified from the actual code. Interchangeable quality.

### Where Each Failed

**GLM — Prompt 8 (projects):** "What projects am I working on? Look in memory first." GLM returned: "Sorry, I encountered an error processing your message." No tool calls recorded. A hard failure — crash or empty response — not a reasoning failure.

**Sonnet — Prompt 19 (context overflow):** Exhausted its 8-call tool budget searching for documentation. No response produced. The same failure as every previous eval run.

Both failures are on prompts the other model completed easily. Neither is a reasoning failure in the traditional sense — one is an infrastructure/API issue, the other is a consistent over-investigation pattern.

### Where Both Failed

**Test count (24):** "How many tests does this project have?" Sonnet searched for test files across 5 tool calls and answered **0**. GLM did the same across 3 tool calls and answered **0**. The real answer is 202 (per pytest). Neither thought to run `pytest --collect-only`. This prompt has now stumped every model in the series.

## Comparison

| | GLM-5 Turbo | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 23/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Strong (precise, with code) | Strong (precise, with code) |
| **Multi-step planning** | Strong (codebase-grounded) | Strong (codebase-grounded) |
| **Instruction precision** | Moderate (prompt 10) | Strong |
| **Self-directed exploration** | Strong | Strong |
| **Efficiency** | Strong (fewer calls) | Mixed (thorough but expensive) |
| **Knows when to stop** | Yes | No (prompt 19) |

## What I Take Away

**GLM-5 Turbo is the first model in this series to match Sonnet's depth.** The Gemma models could drive the agentic loop — call tools, load skills, handle errors. But on tasks requiring codebase understanding — code tracing, multi-step planning, design analysis — they answered from general knowledge. GLM reads the code. It produces traces with file:line annotations. It cites the actual schema registration loop. On the hardest prompts in the suite, the outputs are interchangeable with Sonnet's.

**The completion rate is identical: 23/24 each.** Different failures, neither a reasoning collapse. GLM hit an API error on a straightforward memory prompt. Sonnet burned its tool budget on a prompt that didn't need tools. Neither failure tells you much about the model's capability ceiling.

**Sonnet's over-investigation problem is now a confirmed pattern.** Prompt 19 has failed in the same way across three separate comparison articles — Sonnet exhausts its tool budget looking for a source it can cite instead of answering from what it already knows. GLM, like both Gemma models before it, answered this prompt. The difference: GLM actually searched first and synthesized from what it found, rather than answering purely from general knowledge. It found the right balance between "search everything" and "just answer."

**Instruction precision is the one clear Sonnet edge.** Prompt 10 — "answer only from your identity file" — is the only prompt where Sonnet's response was meaningfully more correct. It found the right file. GLM answered correctly but from the wrong source. This is a narrow gap, but it's real.

**This changes the competitive picture.** The Gemma articles showed that local models can drive an agent but cloud models produce richer analysis. GLM-5 Turbo — a Chinese cloud model routed through OpenRouter — produces analysis at Sonnet's level. For teams evaluating which model to wire into an agentic framework, GLM belongs in the conversation alongside Sonnet, not in a lower tier with the local models.

**The test count prompt remains unsolved.** Four models, zero correct answers. Every model searches for test files instead of running the test runner. This is a consistent blind spot in how models approach development tooling — they reach for search when they should reach for execution.

---

*Tested on Curunir. GLM-5 Turbo at harness commit `dc54c11`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 8, 2026.*
