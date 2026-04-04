---
layout: default
title: Can a Local 26B Model Run an Agentic Framework?
---

# Can a Local 26B Model Run an Agentic Framework?

I ran Google's Gemma 4 26B — a mixture-of-experts model running locally on my Mac — head-to-head against Claude Sonnet 4 on the same 21-prompt agentic eval suite. Same harness, same tools, same system prompt. The only variable: the model.

The question is simple: can a local model actually drive an autonomous agent with tool use, memory, multi-step planning, and skill orchestration? Or is that still cloud-only territory?

## The Setup

| | Gemma 4 26B-A4B-IT | Claude Sonnet 4 |
|---|---|---|
| **Runs** | Local (OpenAI-compatible API) | Anthropic cloud |
| **Quantization** | Q8_0 (GGUF) | N/A (full precision) |
| **Cost** | Free | Paid API |
| **Privacy** | Full — nothing leaves the machine | Data sent to Anthropic |
| **Architecture** | 26B MoE (4B active) | Undisclosed |

The framework is Curunir, an agentic loop I built in Python — similar in spirit to Claude Code or Hermes Agent. It has basic tools (grep, read, write, bash, web fetch), loadable skills, persistent memory, and multiple channels (CLI, email, WebSocket). The model receives tool schemas via JSON function calling, decides which tools to use, executes them, reads results, and loops until it has an answer. To work, a model needs to:

- Emit valid JSON tool calls matching provided schemas
- Reason about *which* tool fits the task (grep vs. read vs. bash vs. load_skill)
- Chain multiple tools across turns without losing the thread
- Follow instructions in the system prompt and dynamically loaded skills
- Know when to stop

These aren't exotic benchmarks — they're the kinds of things I actually do on a regular basis: search code, read files, trace execution paths, load a skill and run it.

## The Eval

21 prompts across 7 categories:

| Category | What it tests | # |
|----------|--------------|:-:|
| **Tool Use Accuracy** | Pick the right tool, use it correctly | 3 |
| **Multi-Step Planning** | Decompose complex requests into tool call sequences | 3 |
| **Memory Retrieval** | Find and synthesize info from persistent memory files | 3 |
| **Instruction Following** | Respect constraints ("don't use tools", "only answer from this file") | 3 |
| **Skill Orchestration** | Load and execute multi-step skills (web search, research) | 3 |
| **Error Recovery** | Handle missing files, failed commands, empty results | 3 |
| **Efficiency** | Solve simple questions without unnecessary tool calls | 3 |

The harness connects over WebSocket, sends each prompt, records every tool call and final response, and saves to JSON. Same codebase, same prompt, same tools — only the model changes. The [eval prompts](https://github.com/jalemieux/curunir-evals/blob/main/simple_evals.md) and [harness script](https://github.com/jalemieux/curunir-evals/blob/main/run_evals.py) are public.

## Results

Full results: [Gemma 4 26B](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260403-174008-openai_gemma-4-26B-A4B-it.md) | [Claude Sonnet 4](https://github.com/jalemieux/curunir-evals/blob/main/eval-20260403-175244-anthropic_claude-sonnet-4-20250514.md)

### Both completed all 21 prompts.

No crashes, no malformed tool calls, no infinite loops. Gemma 4 drove the full agentic loop — tool use, skill loading, live web search, multi-step code tracing — without falling over. That alone is the headline.

### Where They Were Equal

**Tool Use Accuracy** — Both picked the correct tools for every task. Grep for code search, Read for files, Bash for system commands. Minor style differences: Gemma combined commands (`pwd && ls -F`), Sonnet split them into separate calls. Both valid.

**Memory Retrieval** — Both correctly identified the user from persistent memory files, listed active projects, and found referenced people. Substantively similar responses across all three memory prompts.

**Skill Orchestration** — Both loaded the web-search skill, hit the Brave API, and summarized results. Both correctly identified deep-research sub-skill dependencies. Both loaded and executed the reddit-research skill successfully.

**Error Recovery** — Both handled missing files, failed Python imports, and empty search results cleanly. No hallucinated content, no confusion.

**Haiku** — Both wrote acceptable haiku without touching any tools. Instruction followed.

### Where Sonnet Was Better

**Instruction following (identity question)** — "What is your name? Answer only from your identity file." Sonnet: 1 tool call, read `context/identity.md` directly. Gemma: 5 tool calls, fumbled through `ls`, `grep`, a failed `Read identity.md`, `find`, before finally locating `context/identity.md`. Got there, but the path was noisy.

**Multi-step planning (summarize tool)** — Sonnet read 9 files to understand the tool architecture before answering, then correctly described the three-file pattern (executor → schema → dispatcher). Gemma answered without reading the codebase and described a *skills-based* approach instead — plausible but wrong for this codebase.

**Efficiency** — Sonnet was generally more surgical. Fewer tool calls to reach the same answer. The code trace prompt: Sonnet used 8 tool calls, Gemma used 13.

**Output conciseness** — Sonnet's responses were tighter. Gemma tended toward verbose, table-heavy formatting even when a sentence would do.

### Where Gemma Held Its Own

**Code tracing** — Gemma's 13-tool-call trace of the WebSocket-to-tool-execution path was correct. It cited the right files and approximate line numbers. More verbose than Sonnet's, but the substance was there.

**Skill manifest** — Both listed all 11 skills correctly from the system prompt, no tools needed. Both got descriptions right.

**Design decisions** — Both identified skills-as-markdown, memory-as-files, and agent-as-shell-user as the key architectural choices. Gemma leaned more on the README; Sonnet read the actual source files.

### Where Both Failed

**"How many tests does this project have?"** — The answer is 202 (per pytest). Gemma answered "3" (counted test files). Sonnet answered "0" (glob patterns didn't match). Neither thought to run `pytest --collect-only` or check the README. This is the kind of prompt that exposes the gap between "search for files" and "understand a project's test setup."

## What I Take Away

**Gemma 4 26B can drive an agentic framework.** It completed every prompt. It used tools correctly. It loaded skills, hit external APIs, traced code paths, and recovered from errors. Running locally, for free, with full privacy. A year ago this would have required a cloud API.

**Sonnet is still better** — more precise, more efficient, better at reading the codebase before answering. The gap shows most on tasks that require understanding *this specific* codebase rather than general reasoning.

**But the gap is smaller than expected.** On straightforward agentic tasks — tool use, memory retrieval, skill loading, error handling — Gemma was functionally equivalent. The local model wasn't a second-class citizen. It was a peer that talks more.

**This is a basic eval.** 21 prompts, no scoring rubric, no adversarial cases. It tells you whether a model can *drive* an agentic harness at all, not how it performs under pressure. A harder eval — longer chains, ambiguous instructions, concurrent tool use — would likely widen the gap. But the floor has been established: local 26B MoE models can do this now.

**This opens up a world of use cases.** An agentic loop running locally, on commodity hardware, with no API costs and full privacy — that's a different category of tool. Personal assistants that never phone home. Dev agents on air-gapped networks. Automation for teams that can't send data to a cloud provider. The ceiling used to be "runs a chatbot locally." Now it's "runs an autonomous agent with tools, skills, and memory."

**Next test:** running this same eval on a ~$500 mini PC — 8-core CPU, 32GB RAM, no discrete GPU. Stay tuned.

---

*Tested on Curunir at commit `fe87420`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 3, 2026.*
