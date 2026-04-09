---
layout: default
title: "Can a 4B Local Model Run an Agentic Framework?"
---

# Can a 4B Local Model Run an Agentic Framework?

The [26B eval](article-draft) established that a local MoE model can drive an agentic loop — Gemma 4 26B completed all 21 prompts, used tools correctly, and was functionally close to Sonnet on straightforward tasks. The natural follow-up: how far down can you go?

Gemma 4 E4B — a small, efficient model in the Gemma 4 family — same eval suite, same harness, same tools. The result: 21 of 24 prompts completed. The basics work. But the quality gap with Sonnet is wider than it was at 26B, and the failure modes are different.

## The Setup

| | Gemma 4 E4B-IT | Claude Sonnet 4 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Parameters** | ~4B | Undisclosed |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |

The framework is Curunir, an agentic harness I built in Python — tools (grep, read, write, bash, web fetch), loadable skills, persistent memory, and multiple channels (CLI, email, WebSocket). The model receives tool schemas via JSON function calling, decides which tools to use, executes them, reads results, and loops until it has an answer.

E4B ran at harness commit `f545bd4`. The Sonnet baseline ran at `fe87420`. The prompt set and tool surface are identical.

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

Full results: [Gemma 4 E4B](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260406-212633-openai_gemma-4-E4B-it.md) | [Claude Sonnet 4](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260403-175244-anthropic_claude-sonnet-4-20250514.md)

## Results

### E4B completed 21 of 24 prompts. Sonnet completed all 24.

E4B produced text responses to 23 of 24 prompts. Of those, 21 were substantive answers. Two were non-answers (asked for context it already had, or gave a generic statement instead of investigating). One prompt produced no response at all — the model burned all its tool calls in a loop.

But completion doesn't tell the full story. On 10 of the 21 prompts E4B completed, Sonnet's answer was meaningfully better — more precise, grounded in actual code, or more thorough. The gap isn't about whether E4B can drive the loop. It's about what comes out.

### Where They're Equal: Tool Mechanics (11 prompts)

**Basic tool use (1–3):** Both grepped for "async" and found 2 files. Both read `identity.md` and summarized it accurately. Both ran `pwd` and `ls` to list the working directory. Correct results, valid JSON, no differences worth noting.

**Memory (8):** Both read `projects.md` from persistent memory and returned substantively similar project lists.

**Haiku (12):** Both wrote a haiku without touching tools. Instruction followed.

**Skill loading (14):** Both loaded deep-research via `LoadSkill` and correctly listed its sub-skill dependencies (web-search mandatory; reddit-research, xai-search, gemini-search, linkedin-research conditional).

**Error recovery (16–17):** Both handled a missing file (`src/nonexistent/fake_module.py`) and a failed Python import cleanly. Read the error, reported it, moved on.

**Efficiency (23–24):** Both checked the scheduler (empty) and globbed for test files (found 0). Neither thought to run `pytest` or check the README, so both got the test count wrong — the project has 202 tests. Same failure mode as the [26B eval](article-draft).

On these 11 prompts, the responses are interchangeable. The tool schemas work. The dispatch loop works. The model understands which tool fits which task.

### Where Sonnet Is Better: Reasoning Depth (10 prompts)

The pattern is consistent: E4B completes the task but doesn't engage with the codebase. Sonnet reads the code.

**Multi-step planning (4–6):** The starkest gap. Asked to describe how to add a summarize tool, Sonnet read 9 source files and described the exact three-file pattern (`summarize_tool.py` → `schemas.py` → `dispatcher.py`). E4B answered from general knowledge with zero tool calls: "Create `skills/summarize.py`... add to `agent_config.py`..." Plausible for some framework, wrong for this one.

Asked to find skills using "attach," Sonnet grepped skill files and found both (deep-research and email-send). E4B loaded email-send, found one, then said it would need "a catalog of all available skills" to find others. It never thought to grep.

Code tracing: Sonnet cited 8 files with specific line numbers (`ws.py:54`, `agent.py:158`, `dispatcher.py:47`). E4B used 10 tool calls — Glob, Bash, and 7 grep variants — and produced a rough architectural overview. It identified the right components (WebSocket → router → agent → dispatcher) but hedged throughout: "Although the exact `on_message` function was not fully visible..." Sonnet read the files and cited what was there. E4B searched and described what it expected to find.

**Memory retrieval (7, 9):** Both retrieved user preferences when asked "What do you know about me?" Sonnet was more thorough — it also read `projects.md` and `tasks.md` and ran a Grep across memory files. Asked about remembered people, Sonnet searched broadly and found names referenced in preferences and project notes (Tahir Farooqui, Yohei Nakajima, and others). E4B checked `context/memory/people/`, found it empty, and stopped. Correct but incomplete — it didn't think to look elsewhere.

**Instruction following (10–11):** "What is your name? Answer only from your identity file." Sonnet read the file (1 tool call). E4B answered from the system prompt without reading the file (0 tool calls). Right answer, didn't follow the instruction. Listing skills: Sonnet listed 11 skills from the manifest. E4B listed skills *and* tools (`load_skill`, `delegate`, `schedule`, `glob`, `grep`, `read`, `edit`, `write`, `bash`, `web_fetch`) — 21 items instead of 11. A clear conflation of the tool interface with the skill manifest.

**Skill orchestration (13):** Both loaded web-search and ran searches for "asyncio best practices 2025." E4B tried Google first via WebFetch, then loaded the skill and hit the Brave API. Sonnet loaded the skill, hit Brave, then fetched 7 source URLs for deeper content. Both got results; Sonnet's were more substantive.

**Output quality (18–19):** Asked about a no-match search pattern, both found `zzz_no_match_zzz` only in eval/documentation files. Sonnet correctly identified it as a test pattern; E4B noted the matches but was less precise about what they meant.

Asked to explain context overflow handling, Sonnet read memory files and grep'd for the mechanism, then cited the specific char truncation and delegate tool isolation. E4B answered from general knowledge — persistent memory, delegation, conciseness — without reading any code. Correct in spirit, ungrounded in fact.

### Where E4B Failed (3 prompts)

**Prompt 15 — Reddit research:** The model got stuck in a loop. It read `context/memory/README.md` and `context/memory/reddit-research` alternately — 10 times total, exhausting the tool call budget — without ever loading the reddit-research skill or producing a response. It never called `LoadSkill`, never hit an API, never broke out of the cycle. Sonnet loaded the skill, hit the Brave API and Reddit, and returned substantive findings about LLM eval framework sentiment.

**Prompt 21 — Design decisions:** "What are the three most important design decisions in this codebase?" E4B responded: "Please provide the codebase or the specific files you are referring to." It was sitting in the codebase. It had read files from it on earlier prompts. It had grep and glob available. It didn't use them. Sonnet read 8 files (README, config, skills, router, agent, dispatcher) and identified skills-as-markdown, channel-agnostic queues, and opt-in tool extension as the three key decisions.

**Prompt 22 — Model configuration:** "What model am I configured to use? Find the answer with as few tool calls as possible." E4B: "I am running as a large language model... I do not have a specific, user-facing model name." Zero tool calls. Sonnet grep'd for model references and checked environment variables. Found `anthropic/claude-sonnet-4-20250514` in two calls.

The three failures share a trait: the task requires the model to *initiate* exploration without a clear starting point. E4B can follow a tool call chain — grep for this, read that, summarize the result. What it struggles with is deciding to start one when the prompt doesn't hand it an obvious first step.

### The Delegate Comparison: A Draw

Prompt 20 asked both models to compare the delegate tool to a simple function call. Neither read the code. Both gave reasonable general-knowledge answers — scope, isolation, context management. E4B produced a detailed comparison table; Sonnet was more concise. No meaningful quality gap. This is the kind of prompt where a 4B model shines: pure reasoning with no codebase exploration required.

## Comparison to the 26B Model

The [26B eval](article-draft) used 21 prompts (the Output Quality category wasn't added yet). The 26B completed all 21. E4B completed 21 of 24 — a similar completion count but on a harder eval, and with a wider quality gap on the prompts it did complete.

| | E4B | 26B | Sonnet |
|---|:-:|:-:|:-:|
| **Prompts completed** | 21/24 | 21/21 | 24/24 |
| **Basic tool use** | Pass | Pass | Pass |
| **Memory retrieval** | Pass | Pass | Pass |
| **Skill loading** | Pass | Pass | Pass |
| **Error recovery** | Pass | Pass | Pass |
| **Code tracing** | Weak | Pass (verbose) | Pass (precise) |
| **Multi-step planning** | Weak | Weak | Strong |
| **Instruction precision** | Weak | Moderate | Strong |

The 26B model was a peer that talks too much. The E4B model is a capable tool-caller that doesn't think to investigate.

## What I Take Away

**Basic tool use is solved at 4B.** Grep, read, bash, glob, web_fetch, schedule — E4B handled all of these correctly when the task was clear. Valid JSON tool calls, correct schema adherence, appropriate tool selection. The model understands the tool interface.

**The gap is reasoning about code, not calling tools.** On every prompt where Sonnet outperformed E4B, the difference was the same: Sonnet read the codebase before answering. E4B answered from general knowledge or the system prompt. It can *use* tools when told to, but it doesn't instinctively reach for them when the answer requires investigation.

**Skill loading works at 4B.** E4B loaded web-search and deep-research correctly, parsed their instructions, and executed searches. This was the capability I expected to break at this scale — it didn't. The model can inject a long markdown document into context and follow its steps, at least for straightforward skill workflows.

**Small models loop.** The prompt 15 failure — reading the same two files alternately for 10 iterations — is a failure mode specific to this model scale. The 26B and Sonnet never exhibited it. Once E4B enters a repetitive pattern, it can't recognize the pattern isn't working and try something different.

**"Please provide the codebase" is the tell.** When E4B doesn't know where to start, it asks for help instead of exploring. Prompts 21 and 22 both required the model to decide on its own to grep or read files. It didn't. This is the inverse of the looping problem: instead of doing the wrong thing repeatedly, it does nothing. Both failures point to the same root cause — limited planning and self-direction at 4B.

**The floor for "can drive an agentic loop" is at or below 4B.** A 4B model completed 21 of 24 prompts on an eval that covers tool use, memory, skills, error recovery, and code analysis. That's a functional agent. But the quality ceiling is visibly lower than the 26B, which is visibly lower than Sonnet. Each step up in model size buys you depth of reasoning, not breadth of capability.

**This matters for use-case selection.** A 4B model running locally is fast, free, and private. For workflows where the tasks are well-defined — search this, read that, summarize the result — it works. For anything that requires the model to explore a codebase, chain multi-step reasoning, or recover from a dead end, you need a larger model. The question isn't "does it work?" but "is it sufficient for what you're building?"

---

*Tested on Curunir at commit `f545bd4`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 6, 2026.*
