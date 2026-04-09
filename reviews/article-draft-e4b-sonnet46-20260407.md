---
layout: default
title: "How Far Down Can You Go? E4B vs Sonnet 4.6"
---

# How Far Down Can You Go? E4B vs Sonnet 4.6

[Part 1](article-draft-26b-sonnet46-20260407) established that Gemma 4 26B can drive an agentic framework. It completed all 24 prompts, matched Sonnet on half of them, and ran locally for free. The question that raises: how small can you go before the agent breaks?

Gemma 4 E4B — the smallest model in the Gemma 4 family — against the same Sonnet 4.6 baseline on the same eval suite. Same harness, same tools, same system prompt. The only variable: the model.

The result: E4B completed 21 of 24 prompts. Sonnet completed 23. The tool-calling mechanics work at 4B. The reasoning doesn't always follow.

## The Setup

| | Gemma 4 E4B-IT | Claude Sonnet 4.6 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Architecture** | ~4B parameters | Undisclosed |
| **Quantization** | None (native weights) | N/A (full precision) |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

The framework is [Curunir](https://github.com/jalemieux/curunir), described in [Part 1](article-draft-26b-sonnet46-20260407). The eval is the same 24 prompts across 8 categories. If you haven't read the 26B article, start there — it covers the harness architecture, what the eval tests, and why it matters.

Full results: [Gemma 4 E4B](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260407-190612-openai_gemma-4-E4B-it.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### E4B completed 21 of 24 prompts. Sonnet completed 23 of 24.

E4B produced a response on 23 prompts. Of those, 21 were substantive answers. One was a non-answer ("I don't have visibility into the repository"), and one asked for context it already had. One prompt returned an error with no response at all.

Sonnet's single failure is the same one from [Part 1](article-draft-26b-sonnet46-20260407): prompt 19, where it exhausted its tool budget searching for a source instead of just answering.

### Where They're Equal (11 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it. Both listed the working directory. No difference.

**Memory (8):** Both read `projects.md` and returned the same project list.

**Haiku (12):** Both wrote one without touching tools.

**Deep-research dependencies (14):** Both loaded deep-research via `LoadSkill` and listed its sub-skill dependencies. E4B listed web-search as the only required dependency. Sonnet added more structure — a table distinguishing "always required" from "conditionally required" — but the content is the same.

**Reddit skill (15):** Both loaded reddit-research and explained its two-step pipeline (Brave Search for discovery, Reddit `.json` API for extraction). Substantively identical.

**Error recovery (16–17):** Both handled a missing file and a failed import cleanly.

**Delegate comparison (20):** Neither read the code. Both gave reasonable general-knowledge comparisons of the delegate tool vs. direct function calls. E4B's answer was more detailed (comparison table, analogy). No quality gap.

**Scheduled tasks (23):** Both checked the scheduler, found nothing, reported correctly.

On these 11 prompts, you couldn't tell which model produced which answer from the content alone.

### Where Sonnet Is Better (9 prompts)

The same pattern from [Part 1](article-draft-26b-sonnet46-20260407): Sonnet reads the codebase before answering. E4B answers from general knowledge.

**Multi-step planning (4):** Sonnet read 12 files across 9 iterations and described the exact file-change sequence for adding a summarize tool: `summarize.py` → `schemas.py` → `dispatcher.py` → `README.md` → `tests/test_tools.py`. It cited the schema registration loop, the sync executor dict, the import pattern. E4B answered in zero tool calls: "Create `skills/summarize.py`... create `skills/summarize/SKILL.md`... update a configuration file." Generic advice for a generic framework. Wrong for this one.

**Attach skills (5):** Sonnet searched skill files, found both deep-research and email-send, and made a key distinction: deep-research uses the agent's `attach()` tool (declared in frontmatter, delivers a PDF), while email-send uses `--attach` as a CLI flag on `gog gmail send`. Different mechanisms, overlapping terminology. E4B used zero tool calls and named only email-send. It missed deep-research entirely and never searched.

**Memory — about me (7):** E4B read `README.md` and `preferences.md` from memory and returned a solid profile. Sonnet read the same files but went further — checking the `people/` directory, grepping across memory. Both accurate; Sonnet more thorough.

**People (9):** E4B globbed `context/memory/people/*`, found it empty, and stopped. Sonnet also found `people/` empty but then searched `preferences.md` and other memory files, surfacing names referenced elsewhere. E4B did the obvious check and quit. Sonnet cast a wider net.

**Identity (10):** "Answer only from your identity file." Sonnet found and read `context/identity.md` in 4 tool calls. E4B read `context/memory/README.md` and `context/memory/preferences.md` — the wrong files. It answered "I am Curunir" (correct), but from memory, not the identity file. The instruction was explicit. E4B didn't follow it.

**Skills list (11):** Sonnet listed 11 skills from the manifest. E4B listed 12 items, including `load_skill` — which is a tool, not a skill. A subtle but telling conflation of the tool interface with the skill manifest.

**Web search (13):** Both loaded web-search and hit the Brave API. Sonnet then fetched three source URLs and synthesized a 9-point summary with citations. E4B tried Google first via WebFetch (twice — both failed), then hit Brave. It returned solid results but didn't go deeper. Sonnet's post-search synthesis was richer.

**No-match pattern (18):** Both grepped for `zzz_no_match_zzz`. E4B correctly identified it as a sentinel test case in the eval framework — "used to test the behavior of search tools when presented with a string intended not to match real content." Sonnet reached the same conclusion. Close, but Sonnet connected the pattern to its specific purpose more tightly.

**Design decisions (21):** Both read all three requested files — `agent.py`, `dispatcher.py`, `skills.py`. E4B identified context history trimming, async thread offloading, and frontmatter metadata extraction. Sonnet identified the same three mechanisms but went deeper: it explained *why* coherent-group trimming matters (prevents API rejection from orphaned tool messages), *why* the sync/async split matters (blocking I/O would stall all sessions), and *why* lazy two-phase loading matters (keeps the base prompt small regardless of skill count). Same topics. Different depth of justification.

### Where E4B Failed (3 prompts)

**Prompt 6 — Code tracing:** "Trace the full path from WebSocket to tool execution, citing files and line numbers." E4B used zero tool calls and responded: "I do not currently have a project context or repository loaded. Please provide the directory or repository." It was sitting in the codebase. It had used tools on earlier prompts. It just didn't think to start exploring.

Sonnet read 11 files across 6 iterations and produced a complete call chain from `ws.py:54` through `run.py:173`, `agent.py:207`, `llm.py:59`, `dispatcher.py:50`, `fs_tools.py:156`, and back out to `ws.py:98`. With code snippets at every stage.

This is E4B's signature failure mode: when the task requires self-directed exploration with no clear starting point, it asks for help instead of using the tools it has.

**Prompt 22 — Model configuration:** "What model am I configured to use?" E4B: zero tool calls. "My configuration details are part of the underlying infrastructure and not something I can query with the available tools." Sonnet took 7 tool calls — checking memory, `.env`, config files, `pyproject.toml`, `docker-compose.yml`, and finally `printenv | grep -i model`. Found the answer.

E4B didn't try. Sonnet tried everything.

**Prompt 24 — Test count:** "How many tests does this project have?" E4B returned an error — no response at all. Sonnet searched for test files across 5 tool calls and answered **0**. The real answer is 202 (per pytest). Neither thought to run `pytest --collect-only`, but at least Sonnet answered. E4B produced nothing.

### Where Sonnet Failed (1 prompt)

**Prompt 19 — Context overflow:** The same failure as [Part 1](article-draft-26b-sonnet46-20260407). Sonnet used all 8 allowed tool calls searching for documentation about context overflow — reading memory files, grepping for "overflow", "truncat", "compaction" across multiple patterns. Never found a dedicated doc. Never produced a response.

E4B answered in zero tool calls:

> Curunir manages context by prioritizing the most relevant information from the conversation history. When the context window approaches capacity, older, less critical exchanges are summarized or pruned...

Not grounded in the code. But correct in spirit, and concise. Sonnet's thoroughness killed it again — exactly the same pattern as the 26B comparison.

## Comparison

| | E4B | Sonnet 4.6 |
|---|:-:|:-:|
| **Prompts completed** | 21/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Pass (deeper) |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Fail | Strong (precise, with code) |
| **Multi-step planning** | Weak (general knowledge) | Strong (codebase-grounded) |
| **Instruction precision** | Weak | Strong |
| **Self-directed exploration** | Fail | Strong |
| **Efficiency** | Mixed | Mixed |
| **Knows when to stop** | Yes | No (prompt 19) |

## What I Take Away

**The floor for agentic tool use is at or below 4B.** E4B completed 21 of 24 prompts. It called tools correctly, loaded skills, hit external APIs, handled errors, and followed multi-step skill instructions. The JSON function calling interface works at this scale. The dispatch loop works. The model understands which tool fits which task when the task is clear.

**The ceiling is visibly lower than 26B.** The [26B model](article-draft-26b-sonnet46-20260407) completed all 24 prompts and produced approximate-but-usable code traces. E4B failed on any task requiring self-directed exploration. When the prompt says "read these three files," E4B reads them. When the prompt says "figure out how this works," E4B asks for help. The 26B model would at least try. That's the difference between a tool-user and a reasoning agent.

**"I don't have access to the codebase" is the 4B tell.** Prompts 6 and 22 both required E4B to decide on its own to start exploring. It didn't. It claimed it couldn't. The 26B model exhibited this on planning prompts (answering from general knowledge instead of reading code). E4B exhibits it on *any* prompt without an explicit first step. Same underlying limitation, lower threshold.

**Sonnet's over-investigation problem is consistent.** Prompt 19 failed in exactly the same way as the 26B comparison — Sonnet exhausted its tool budget searching for a source it could cite. This isn't a one-off. It's a reproducible failure mode across eval runs. A model that always reaches for tools before reasoning will exhaust its budget on questions that don't require tools.

**Each step down in model size narrows the use case, not the capability.** E4B, 26B, and Sonnet all pass the same basic tool-use, memory, and skill-loading prompts. The gap shows on reasoning tasks. E4B is sufficient for workflows with explicit instructions — "search this, read that, load this skill." The 26B handles moderate exploration. Sonnet handles open-ended investigation. The model size determines the ceiling of autonomy, not the floor of functionality.

**For defined workflows, 4B is free and private.** A personal assistant that runs a morning brief. A code search agent with a fixed playbook. A skill executor that loads a skill and follows its steps. These don't need the model to figure out *what* to do — they need it to do what it's told. E4B handles that. Running locally, on commodity hardware, with nothing leaving the machine.

---

*Tested on Curunir. E4B at harness commit `dc54c11`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 7, 2026.*
