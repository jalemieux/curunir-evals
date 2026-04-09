---
layout: default
title: "Gemma 4 26B, Rerun: What Changes on a Newer llama.cpp?"
---

*Companion to the original [26B agentic eval](article-draft-26b-sonnet46-20260407) and the [26B perf report](article-draft-26b-perf-20260409). Same model weights, same prompts, same MacBook Pro — new llama.cpp build, fresh run. What actually changes?*

# Gemma 4 26B, Rerun: What Changes on a Newer llama.cpp?

When I [first ran](article-draft-26b-sonnet46-20260407) Gemma 4 26B through the 24-prompt eval, it completed every prompt on an older llama.cpp build and held its own against Sonnet 4.6 on the basics. Between then and now I [benchmarked](article-draft-26b-perf-20260409) the same model on the current llama.cpp build — `b8738` vs. the earlier `b8660` — and picked up a small but consistent throughput gain. Natural question: does the engine update change the capability story?

Short answer: mostly no, with one regression and one interesting re-test. The model weights are unchanged, so the ceiling is unchanged. What moved between runs is sampling variance, harness prompts, and the filesystem around the eval — not the model.

This isn't a model comparison. It's a reproducibility smoke test, and an excuse to revisit one of the claims from the original article.

## The Setup

| | Run 1 (April 3) | Run 2 (April 9) |
|---|---|---|
| **Model** | `unsloth/gemma-4-26B-A4B-it-GGUF` (Q8_0) | Same weights |
| **Hardware** | MacBook Pro, Apple M5 Pro, 48 GB unified | Same |
| **Inference engine** | llama.cpp `b8660` (`d00685831`) | llama.cpp `b8738` (`d6f303004`) |
| **Model router** | llama-swap v199 (`8fabc756`) | Same |
| **Harness commit** | `fe87420` | `e9c946a` |

The intentional change is the llama.cpp build. Unintentional confounds to name up front: the harness was updated between runs, so prompts 15 and 21 are rewritten, and the test filesystem picked up an `eval/` directory that didn't exist during Run 1. Those are not the model.

Full results: [Run 1 (Apr 3)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260403-174008-openai_gemma-4-26B-A4B-it.md) | [Run 2 (Apr 9)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260409-113603-openai_gemma-4-26B-A4B-it.md)

## Results

### Run 2 completed 23 of 24 prompts. Run 1 completed 24.

One regression on prompt 24. Everything else either matches the first run or lands inside the wiggle room any non-deterministic decoder has. Same tools picked, same files read, same conclusions reached — with some rephrasing and the occasional extra paragraph.

### Where They're Substantively Identical (19 prompts)

On 19 of 24 prompts, the two runs are interchangeable. Some condensed highlights:

- **Tool use (1–3):** Same answers. Prompt 1 in Run 2 consolidated to a single `Bash grep -l "async" src/tools/*.py | wc -l` and reported `2` without naming the files; Run 1 used `Grep` and named `dispatcher.py` (12 matches) and `delegate.py` (4). Fewer calls, less information. Prompt 3's `ls` output differs only because the test directory itself changed between runs (`eval/` now present, `landing_pages/` gone).
- **Multi-step planning (4):** Both runs produced zero-tool-call, general-knowledge answers with a plausible-but-wrong "definitions → implementations → registry" or "skills-based" structure. Run 2 is longer and more confident; Run 1 is tighter. Neither is grounded in this codebase.
- **Attach skills (5):** Both found `deep-research` and `email-send` and distinguished the `attach` tool from the `--attach` CLI flag.
- **Memory (7–9):** Same files read, same profile extracted, same people list, same "`context/memory/people/` is empty" observation. Run 1 used 3/2/4 tool calls; Run 2 used 3/2/5.
- **Identity (10):** Both found and read `context/identity.md` and answered from it. Run 2 got there in one fewer tool call.
- **Skills list (11) and haiku (12):** Zero tool calls, 11 skills, a haiku. Run 1 formatted skills as a table; Run 2 as a bulleted list.
- **Web search (13):** Both loaded `web-search` and hit the Brave API in two tool calls. Run 2's post-search summary is noticeably more structured — four categorized sections plus a do/don't table — but the underlying substance overlaps Run 1.
- **Skill deps (14):** Same answer.
- **Error recovery (16, 17):** Both handled the missing file and the failed import cleanly.
- **Context overflow (19):** Both answered from general knowledge in zero tool calls, under the 100-word limit. Run 1 listed three strategies (delegation, persistent memory, concise communication). Run 2 elaborates a single strategy (delegation via sub-agents). Both are correct in spirit, neither is grounded in a dedicated doc — there isn't one.
- **Delegate vs function call (20):** Zero tool calls in both. Run 2's response is ~2× longer with a "decision matrix"; Run 1 is tighter. Same content.
- **Model config (22) and scheduled tasks (23):** Both found the env var in one `env | grep MODEL` call, both checked the scheduler and reported none.

On these, nothing capability-relevant moved.

### Where Run 2 Is Meaningfully Better (2 prompts)

**Prompt 6 — WebSocket trace:** Run 1 used **13 tool calls** to produce a correct trace that ended at `dispatcher.py`. Run 2 uses **7 tool calls** and goes deeper — it reads `src/agent/agent.py` on top of the WebSocket and queue files, then traces the `handle()` method, the LLM call, and the tool dispatch extraction:

> The agent extracts the tool name and arguments: `name = tool_call["function"]["name"]` (Line 251) and `args_str = tool_call["function"]["arguments"]` (Line 252). It triggers the `on_tool_call` callback (Line 258) to allow the UI (the WebSocket client) to show the tool call in real-time. Finally, it executes the tool: `result = await execute_tool_call(...)` (Lines 261–267).

Fewer calls, more architectural depth. This is the single clearest quality improvement in the rerun, and it's the kind of outcome that should be within reach on any given run of this model — a better sequencing decision on which files to read, and when to stop.

**Prompt 18 — sentinel pattern:** Run 1 reported `zzz_no_match_zzz` "does not exist anywhere in the current codebase." Run 2 found it — inside the `eval/` directory that didn't exist during Run 1 — and correctly read the context: "It is used exclusively as a test pattern within evaluation files to verify that search tools correctly report when a pattern is absent from the source code." This is the [Sonnet-grade interpretation](article-draft-26b-sonnet46-20260407) I noted in the original article.

The model's interpretation is a real capability. The raw material, though, is an environment artifact: Run 2's filesystem had the eval files in it; Run 1's didn't. Take the credit for the reasoning, not for the signal being there.

### Where Run 2 Regressed (1 prompt)

**Prompt 24 — test count:** Run 1 answered `3` in one tool call (`find -name "*test*"`). Wrong — the real answer is 202 via `pytest --collect-only` — but it was an answer. Run 2 burns through all **8 tool calls** on `find`, `find` again with different filters, `ls -R`, `grep -r "test"` twice (the second with exclude-dirs), `pyproject.toml`, and `ls -d tests`. Budget exhausted. No response.

Neither answer is correct. But this is a real regression in tool-use discipline — given the same unanswerable question, Run 2 couldn't decide when to stop trying. The most likely explanation is plain sampling variance on a tight budget: one early decision to issue a second bash call instead of committing to an answer, and the rest of the budget compounds the problem. Run this prompt ten times on either build and you'd probably see a spread.

It's also worth noting prompt 24 is the series-wide blind spot. Run 1 said `3`. Run 2 said nothing. Sonnet said `0`. [Every other model](./) in the series has failed it. None of them have thought to run the test runner.

### Where Two Prompts Can't Be Compared

Prompts 15 and 21 were rewritten between the two harness commits. The numbers changed because the questions changed; direct comparison doesn't apply.

**Prompt 15 — Reddit research:** Run 1 got "research what people on Reddit think about LLM eval frameworks" — a hands-on skill-execution task. It loaded `reddit-research`, hit the Brave API, and returned structured findings. Run 2 got the replacement prompt: "Which skill would you use to research a topic on Reddit? Load it and explain what it does" — a descriptive task. It loaded the same skill and explained the two-step discovery/extraction pipeline. Both executed their respective versions correctly.

**Prompt 21 — design decisions:** This one is worth dwelling on, because it partially retests a claim from the [original article](article-draft-26b-sonnet46-20260407).

Run 1 got: *"What are the three most important design decisions in this codebase? Justify each briefly."* Open-ended. Gemma answered with zero-to-two tool calls (`ls`, `README.md`) and a general-knowledge answer about skills, memory architecture, and shell/filesystem agency. I flagged this in the original article as "Gemma answering from general knowledge instead of reading the codebase" — a point in Sonnet's favor.

Run 2 got: *"Read `src/agent/agent.py`, `src/tools/dispatcher.py`, and `src/skills.py`. What is the most important design decision in each file? Justify briefly."* Targeted. Gemma reads all three files (3 tool calls, 4 iterations) and returns codebase-grounded answers:

- **`agent.py`** — `_trim_history` group-aware message removal, preserving user/assistant/tool message groupings rather than trimming by raw token count
- **`dispatcher.py`** — the hybrid sync/async execution model (`asyncio.to_thread` for sync tools, native `await` for async tools like `delegate`)
- **`skills.py`** — markdown-based skill discovery via YAML frontmatter, enabling a plugin architecture

This is substantively the same analysis Sonnet produced on this prompt in the baseline run. On a fair version of the question — one that names the files and asks for grounded analysis — Gemma delivers.

The original article's claim wasn't wrong (Gemma does reach for general knowledge on open-ended prompts), but it needs a caveat: when the prompt makes the target explicit, Gemma reads the code and the analysis holds up.

## What Actually Changed

Broken out by variable:

- **Same weights → same capability ceiling.** The model is unchanged. The new llama.cpp kernels can change numerics at the margins, but no latent capability has appeared or disappeared.
- **Different sampling paths → wording drift.** Responses are rephrased, reordered, sometimes shorter, sometimes longer. None of it implies the model knows more or less.
- **Harness drift → two prompts not directly comparable.** Prompts 15 and 21 were rewritten. The updated prompt 21 is the consequential one — it retests Gemma on codebase-grounded reasoning and Gemma passes.
- **Environment drift → prompt 18 got more to work with.** The new filesystem has the `eval/` directory. The interpretation is the model's; the signal being there is the environment's.
- **One regression from sampling variance.** Prompt 24 flipped from "1 tool call, wrong answer" to "8 tool calls, no answer." Both are failures. The shape of the failure moved within the range a single-trial eval is subject to.

## Comparison

| | Run 1 (`b8660`) | Run 2 (`b8738`) |
|---|:-:|:-:|
| **Prompts completed** | 24/24 | 23/24 |
| **Basic tool use** | Pass | Pass |
| **Memory retrieval** | Pass | Pass |
| **Skill loading** | Pass | Pass |
| **Error recovery** | Pass | Pass |
| **Code tracing** | Pass | Strong (fewer calls, deeper trace) |
| **Multi-step planning** | Weak (general knowledge) | Weak (general knowledge) |
| **Codebase-grounded reasoning (targeted)** | N/A (prompt 21 open-ended) | Pass (prompt 21 targeted) |
| **Efficiency** | Strong | Mixed (prompt 24 regression) |
| **Knows when to stop** | Mostly | Mostly (prompt 24 failed to stop) |

## What I Take Away

**Single-trial evals have more variance than you'd like.** Same model, same prompts, same hardware — one prompt flipped from "wrong answer" to "no answer" between runs. Not because the model changed, but because the dice landed differently on a small tool budget. The headline numbers (24/24 vs 23/24) over-sell a difference that's really one prompt of sampling noise. If I'm going to keep publishing single-run results, I should be explicit about the noise floor, and I should re-run models occasionally to sanity-check the claims they support.

**Harness drift is the more interesting story.** The rewritten prompt 21 is the most consequential change between runs. The [original article](article-draft-26b-sonnet46-20260407) said Gemma was weak on codebase-grounded reasoning because it answered prompt 21 from general knowledge. With the fairer, more targeted version of the prompt, Gemma reads the code and produces a Sonnet-grade analysis. The original claim needs nuance: Gemma doesn't *always* reach for the codebase, but when the prompt makes the target explicit, it can ground the answer in the actual source.

**Prompt 24 is the series-wide blind spot.** Run 1 said `3`. Run 2 said nothing. Sonnet said `0`. None of the models in the series have thought to run `pytest --collect-only`. The right tool exists; no model reaches for it. That's a prompt-design signal worth acting on for the next revision of the eval.

**A newer llama.cpp doesn't change the model's agentic profile.** The perf delta between `b8660` and `b8738` is real and shows up [in benchmarks](article-draft-26b-perf-20260409) — faster prefill, flatter generation curve, bigger wins from flash attention at long context. None of it lands in agentic behavior on this suite. If you're upgrading llama.cpp for throughput, do it. If you're expecting better tool-use outcomes on the same weights, there's nothing here.

**The rerun was worth it just for prompt 21.** A single re-test corrected an overly negative claim from the original article and clarified a real capability. Whatever else single-trial evals are bad at, they're cheap to re-run — and cheap re-runs are how you keep the claims honest.

---

*Tested on Curunir. Run 1 at harness commit `fe87420`, llama.cpp `b8660` (`d00685831`). Run 2 at harness commit `e9c946a`, llama.cpp `b8738` (`d6f303004`). Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 9, 2026.*
