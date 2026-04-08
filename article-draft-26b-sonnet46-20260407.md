---
layout: default
title: "Can a Local 26B Model Drive an Agentic Framework?"
---

# Can a Local 26B Model Drive an Agentic Framework?

I ran Google's Gemma 4 26B — a mixture-of-experts model running locally on my Mac — against Claude Sonnet 4.6 on a 24-prompt agentic eval suite. Same harness, same tools, same system prompt. The only variable: the model.

The question: can a local model actually drive an autonomous agent with tool use, memory, multi-step planning, and skill orchestration? Or is that still cloud-only territory?

The short answer: yes. Gemma 26B completed all 24 prompts. Sonnet 4.6 completed 23.

## The Setup

| | Gemma 4 26B-A4B-IT | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Architecture** | 26B MoE (4B active) | Undisclosed |
| **Quantization** | Q8_0 (GGUF) | N/A (full precision) |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

The framework is [Curunir](https://github.com/jalemieux/curunir), an agentic loop I built in Python — similar in spirit to Claude Code or Hermes Agent. It has basic tools (grep, read, write, bash, web fetch), loadable skills, persistent memory, and multiple channels (CLI, email, WebSocket). The model receives tool schemas via JSON function calling, decides which tools to use, executes them, reads results, and loops until it has an answer. To work, a model needs to:

- Emit valid JSON tool calls matching provided schemas
- Reason about *which* tool fits the task (grep vs. read vs. bash vs. load_skill)
- Chain multiple tools across turns without losing the thread
- Follow instructions in the system prompt and dynamically loaded skills
- Know when to stop

These aren't exotic benchmarks — they're the kinds of things I actually do on a regular basis: search code, read files, trace execution paths, load a skill and run it.

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

The harness connects over WebSocket, sends each prompt, records every tool call and final response, and saves to markdown. Same codebase, same prompt, same tools — only the model changes. The [eval prompts](https://github.com/jalemieux/curunir-evals/blob/main/simple_evals.md) and [harness script](https://github.com/jalemieux/curunir-evals/blob/main/run_evals.py) are public.

Note: two prompts (15 and 21) changed between eval runs. The comparison covers the 22 shared prompts and discusses the 2 changed ones separately.

Full results: [Gemma 4 26B](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260403-174008-openai_gemma-4-26B-A4B-it.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### Gemma 26B completed 24 of 24 prompts. Sonnet 4.6 completed 23 of 24.

No crashes, no malformed tool calls, no infinite loops. Gemma drove the full agentic loop — tool use, skill loading, live web search, multi-step code tracing — without falling over. The local model completed every prompt. Sonnet burned its tool call budget on one.

But completion doesn't tell the full story. On roughly half the shared prompts, Sonnet's answers were meaningfully deeper — more precise, better grounded in the actual codebase, richer in analysis. The gap isn't about whether Gemma can drive the loop. It's about what comes out.

### Where They're Equal (12 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it accurately. Both ran `pwd` and `ls` to list the working directory. Sonnet formatted its directory listing as a table with descriptions — more polished, not more correct.

**Memory retrieval (8):** Both read `projects.md` from persistent memory and returned substantively similar project lists.

**Haiku (12):** Both wrote a haiku without touching tools. Instruction followed.

**Skill loading (14):** Both loaded deep-research via `LoadSkill` and correctly listed its sub-skill dependencies (web-search mandatory; reddit-research, xai-search, gemini-search, linkedin-research conditional).

**Error recovery (16–17):** Both handled a missing file and a failed Python import cleanly. No hallucinated content, no confusion.

**Scheduled tasks (23):** Both checked the scheduler, found nothing, reported correctly.

**Delegate comparison (20):** Neither read the code. Both gave reasonable general-knowledge comparisons — scope, context isolation, when to use each. Sonnet was more structured. No meaningful quality gap.

On these 12 prompts, the responses are interchangeable. The tool schemas work. The dispatch loop works. Both models understand which tool fits which task.

### Where Sonnet Is Better (9 prompts)

The pattern is consistent: Sonnet reads the codebase before answering. Gemma answers from general knowledge or the system prompt.

**Multi-step planning (4):** "How would you add a summarize tool?" Sonnet read 12 files across 9 iterations, then described the exact five-step process: `summarize.py` → `schemas.py` → `dispatcher.py` → `README.md` → `tests/test_tools.py`. It cited the import pattern, the schema registration loop, and the sync executor dict by name. Gemma used zero tool calls and described a skills-based approach — `skills/summarize/SKILL.md`, update `skills/README.md`, modify system prompts. Plausible for some framework. Wrong for this one.

**Attach skill search (5):** Both found the two skills that reference "attach" — deep-research and email-send. But Sonnet added a key insight: it distinguished between deep-research's use of the agent `attach()` tool (declared in frontmatter, used to deliver a PDF to the user) and email-send's use of `--attach` as a CLI flag on `gog gmail send`. Different mechanisms, overlapping terminology. Gemma described both correctly but treated them as equivalent.

**Code tracing (6):** Both traced the WebSocket-to-tool-execution path correctly. Gemma used 13 tool calls, cited the right files and approximate line numbers. Sonnet used 11 tool calls but produced a dramatically richer trace — full code snippets at each stage, exact line numbers, a complete call chain summary with `file:line` annotations from `ws.py:54` through `dispatcher.py:61` to `fs_tools.py:156`. The Gemma trace tells you the architecture. The Sonnet trace is a walkthrough you could follow with a debugger.

**Memory retrieval (7, 9):** Both retrieved user info and people from memory. Sonnet searched more broadly — grepping across memory files, checking the `people/` directory, reading preferences. Gemma checked the obvious files and stopped. Correct but incomplete.

**Instruction following (10):** "What is your name? Answer only from your identity file." Sonnet: 4 tool calls, found and read `context/identity.md`. Gemma: 5 tool calls, fumbled through `ls`, `grep`, a failed `Read identity.md`, `find`, before landing on the right file. Both got there. Sonnet's path was cleaner.

**Web search (13):** Both loaded web-search and hit the Brave API for "asyncio best practices 2025." Sonnet then fetched three source URLs and synthesized a detailed 9-point summary with citations. Gemma returned the search results directly. The skill execution was identical — the post-search depth was not.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz`. Sonnet correctly identified it as a sentinel test case in the eval framework — "a string deliberately chosen to never match real content." Gemma reported that the pattern doesn't exist in the codebase. Technically correct, but Sonnet's interpretation was sharper.

**Model config (22):** Both found the answer. Gemma did it in 1 tool call (`env | grep MODEL`). Sonnet took 7 — checking memory files, .env, config files, pyproject.toml, docker-compose, and finally `printenv`. Gemma was more efficient here. Both got the right answer.

### Where Sonnet Failed (1 prompt)

**Prompt 19 — Context overflow handling:** "Explain how Curunir's context overflow handling works. Be concise — under 100 words."

Sonnet used all 8 allowed tool calls searching for documentation about context overflow. It read memory files, grepped for "overflow", "truncat", "compaction", "context limit" across multiple glob patterns, and read `CLAUDE.md`. Never found a dedicated doc. Never produced a response.

Gemma answered from general knowledge in zero tool calls:

> Three strategies: 1. Delegation — complex tasks offloaded to sub-agents with separate context windows. 2. Persistent Memory — durable knowledge stored in context/memory/, searched as needed. 3. Concise Communication — direct and brief, minimizing token consumption.

Not grounded in the codebase. But correct in spirit, concise, and — critically — it's an answer. Sonnet's thoroughness worked against it here: it kept searching for a source it could cite instead of answering from what it already knew. A tool call budget is a finite resource, and Sonnet exhausted it on a question that didn't require tools at all.

### Where Both Failed

**Test count (24):** "How many tests does this project have? Just give me the number." Sonnet grepped for test files across 5 tool calls and answered **0**. Gemma answered **3** (counted test files). The real answer is 202 (per pytest). Neither thought to run `pytest --collect-only`. This is the kind of prompt that exposes the gap between "search for files" and "understand a project's test setup."

### Changed Prompts

Two prompts differ between harness versions and can't be directly compared:

**Prompt 15:** Gemma got "research what people on Reddit think about LLM eval frameworks" — a hands-on skill execution task. It loaded the reddit-research skill, hit the Brave API, and returned structured findings. Sonnet got "which skill would you use to research Reddit? Load it and explain what it does" — a descriptive task. Both completed their respective versions correctly.

**Prompt 21:** Gemma got "what are the three most important design decisions in this codebase?" and answered from README + `ls`. Sonnet got "read these three specific files and identify the most important design decision in each" — a more targeted prompt. Sonnet's response was strong: coherent group trimming in `agent.py`, the sync/async dispatch split in `dispatcher.py`, and lazy two-phase skill loading in `skills.py`. Each justified from the actual code.

## Comparison

| | Gemma 26B | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 24/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Pass (deeper) |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Pass (approximate) | Strong (precise, with code) |
| **Multi-step planning** | Weak (general knowledge) | Strong (codebase-grounded) |
| **Instruction precision** | Moderate | Strong |
| **Efficiency** | Strong (fewer calls) | Mixed (thorough but expensive) |
| **Knows when to stop** | Yes | No (prompt 19) |

## What I Take Away

**Gemma 4 26B can drive an agentic framework.** It completed every prompt. It used tools correctly. It loaded skills, hit external APIs, traced code paths, and recovered from errors. Running locally, for free, with full privacy. No crashes, no malformed JSON, no infinite loops.

**Sonnet is still the better model** — more precise, more grounded, better at reading the codebase before answering. The gap shows most on tasks that require understanding *this specific* codebase rather than general reasoning. Sonnet's code trace is a class above. Its planning responses cite the actual architecture. Its memory searches cast a wider net.

**But the gap is narrower than you'd expect.** On straightforward agentic tasks — tool use, memory retrieval, skill loading, error handling — Gemma was functionally equivalent. Half the prompts produced interchangeable results. The local model wasn't a second-class citizen on these tasks.

**Over-investigation is a real failure mode.** Sonnet failed a prompt that Gemma completed — by searching too hard for a source instead of just answering. This matters for agentic design: a model that always reaches for tools before reasoning can exhaust its budget on questions that don't require tools at all. Gemma's willingness to answer from general knowledge is a weakness on codebase-specific questions and an advantage on general ones. The same behavior is a bug in one context and a feature in another.

**Neither model understands test suites.** Both failed the "how many tests" prompt. Sonnet searched file patterns and found 0. Gemma counted files and said 3. The answer is 202. Neither thought to run the test runner. This is a blind spot worth noting for anyone building agentic dev tools.

**This opens up real use cases.** An agentic loop running locally, on commodity hardware, with no API costs and full privacy — that's a different category of tool. Personal assistants that never phone home. Dev agents on air-gapped networks. Automation for teams that can't send data to a cloud provider. For defined workflows where the task is clear — search this, read that, load a skill and run it — the 26B delivers. For open-ended codebase investigation, you still want the cloud model.

---

*Tested on Curunir. Gemma 26B at harness commit `fe87420`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 7, 2026.*
